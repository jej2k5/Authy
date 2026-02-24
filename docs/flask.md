# Flask Integration Guide

**Python:** 3.11+  **Framework:** Flask 3+

## Install

```bash
pip install flask python-dotenv pyjwt
pip install -e ../python    # install Authy
```

## 1. AuthManager singleton

```python
# auth.py
import asyncio, os
from authy import AuthManager, LocalProvider, LocalProviderConfig, hash_password

_password_hash = hash_password("password123")

USERS = {
    "alice": {"id": "1", "email": "alice@example.com",
              "name": "Alice", "password_hash": _password_hash},
}

async def _find_user(username: str):
    return USERS.get(username)

def create_auth_manager() -> AuthManager:
    secret = os.environ.get("JWT_SECRET", "change-me")
    manager = AuthManager(jwt_secret=secret)
    manager.register(LocalProvider(
        LocalProviderConfig(jwt_secret=secret, token_ttl=3600),
        _find_user,
    ))
    return manager

auth_manager = create_auth_manager()

# Flask is synchronous — helper to call async Authy methods
def run_async(coro):
    return asyncio.run(coro)
```

## 2. Auth decorator

```python
# auth.py (continued)
from functools import wraps
from flask import request, jsonify, g

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get("token")
        if not token:
            return jsonify(error="Not authenticated"), 401
        try:
            g.user = auth_manager.verify_token(token)
        except Exception:
            return jsonify(error="Invalid or expired token"), 401
        return f(*args, **kwargs)
    return decorated
```

## 3. Auth Blueprint

```python
# blueprints/auth.py
from flask import Blueprint, request, jsonify, make_response, redirect, g
import jwt as pyjwt
import os

from auth import auth_manager, run_async

bp = Blueprint("auth", __name__, url_prefix="/auth")

# --- Local login ---
@bp.route("/login", methods=["POST"])
def login():
    result = run_async(auth_manager.authenticate("local", request.json or {}))
    if not result.success:
        return jsonify(error=result.error), 401

    resp = make_response(jsonify(user={
        "id": result.user.id, "email": result.user.email,
        "name": result.user.name, "provider": result.user.provider,
    }))
    resp.set_cookie("token", result.token, httponly=True,
                    secure=False, samesite="Lax")  # secure=True in production
    return resp

# --- Google OAuth step 1 ---
@bp.route("/google")
def google_start():
    result = run_async(auth_manager.authenticate("google", {"action": "get_auth_url"}))
    if not result.success:
        return jsonify(error=result.error), 500

    meta = pyjwt.decode(result.token, options={"verify_signature": False})
    resp = make_response(redirect(meta["auth_url"]))
    resp.set_cookie("pkce_verifier", meta["code_verifier"], httponly=True, samesite="Lax")
    return resp

# --- Google OAuth step 2 ---
@bp.route("/google/callback")
def google_callback():
    code = request.args.get("code", "")
    state = request.args.get("state", "")
    code_verifier = request.cookies.get("pkce_verifier", "")

    result = run_async(auth_manager.authenticate("google", {
        "action": "callback", "code": code,
        "state": state, "code_verifier": code_verifier,
    }))
    if not result.success:
        return redirect("/login?error=auth_failed")

    resp = make_response(redirect("/dashboard"))
    resp.set_cookie("token", result.token, httponly=True, secure=False, samesite="Lax")
    resp.delete_cookie("pkce_verifier")
    return resp

# --- Logout ---
@bp.route("/logout", methods=["POST"])
def logout():
    resp = make_response(jsonify(ok=True))
    resp.delete_cookie("token")
    return resp
```

## 4. Wire it together

```python
# app.py
from flask import Flask, jsonify, g
from auth import require_auth
from blueprints.auth import bp as auth_bp

app = Flask(__name__)
app.register_blueprint(auth_bp)

@app.get("/api/me")
@require_auth
def me():
    return jsonify(g.user)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
```

## 5. Run it

```bash
flask run --port 5000
```

```bash
# Login
curl -c cookies.txt -X POST http://localhost:5000/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"alice","password":"password123"}'

# Protected endpoint
curl -b cookies.txt http://localhost:5000/api/me
```

## Note on async

Flask 2.0+ supports `async def` route functions natively if you install `flask[async]`.
Using `asyncio.run()` works fine with Flask's default synchronous WSGI mode and is
simpler when you only need to call Authy at a few points. For heavily async workloads,
consider FastAPI instead.

## Environment variables

```ini
JWT_SECRET=a-long-random-string
BASE_URL=http://localhost:5000

# Optional
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
```

See the runnable example: [`examples/flask-app/`](../examples/flask-app/)
