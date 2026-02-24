# FastAPI Integration Guide

**Python:** 3.11+  **Framework:** FastAPI + Uvicorn

## Install

```bash
pip install fastapi uvicorn[standard] python-dotenv pyjwt
pip install -e ../python    # install Authy
```

## 1. AuthManager singleton

```python
# auth.py
import os
from authy import AuthManager, LocalProvider, LocalProviderConfig, hash_password

# Build once at startup — swap find_user for a real DB query
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

    # Optional: Google OAuth
    if os.environ.get("GOOGLE_CLIENT_ID"):
        from authy import GoogleProvider, GoogleProviderConfig
        manager.register(GoogleProvider(GoogleProviderConfig(
            client_id=os.environ["GOOGLE_CLIENT_ID"],
            client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
            redirect_uri=os.environ["BASE_URL"] + "/auth/google/callback",
            jwt_secret=secret,
        )))

    return manager

auth_manager = create_auth_manager()
```

## 2. Auth dependency

```python
# auth.py (continued)
from fastapi import Cookie, HTTPException
from typing import Annotated

def get_current_user(token: Annotated[str | None, Cookie()] = None):
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        return auth_manager.verify_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

CurrentUser = Annotated[dict, Depends(get_current_user)]
```

## 3. Auth routes

```python
# main.py
from fastapi import FastAPI, Response, Request
from fastapi.responses import RedirectResponse, JSONResponse
import jwt as pyjwt

from auth import auth_manager, get_current_user, CurrentUser

app = FastAPI()

# --- Local login ---
@app.post("/auth/login")
async def login(body: dict, response: Response):
    result = await auth_manager.authenticate("local", body)
    if not result.success:
        return JSONResponse({"error": result.error}, status_code=401)

    response.set_cookie("token", result.token, httponly=True,
                        secure=False, samesite="lax")  # secure=True in production
    return {"user": {"id": result.user.id, "email": result.user.email,
                     "name": result.user.name, "provider": result.user.provider}}

# --- Google OAuth step 1 ---
@app.get("/auth/google")
async def google_start(response: Response):
    result = await auth_manager.authenticate("google", {"action": "get_auth_url"})
    if not result.success:
        return JSONResponse({"error": result.error}, status_code=500)

    meta = pyjwt.decode(result.token, options={"verify_signature": False})
    response.set_cookie("pkce_verifier", meta["code_verifier"], httponly=True, samesite="lax")
    return RedirectResponse(meta["auth_url"])

# --- Google OAuth step 2 ---
@app.get("/auth/google/callback")
async def google_callback(request: Request, code: str, state: str, response: Response):
    code_verifier = request.cookies.get("pkce_verifier", "")
    result = await auth_manager.authenticate("google", {
        "action": "callback", "code": code,
        "state": state, "code_verifier": code_verifier,
    })
    if not result.success:
        return RedirectResponse("/login?error=auth_failed")

    response.delete_cookie("pkce_verifier")
    resp = RedirectResponse("/dashboard")
    resp.set_cookie("token", result.token, httponly=True, secure=False, samesite="lax")
    return resp

# --- Logout ---
@app.post("/auth/logout")
async def logout(response: Response):
    response.delete_cookie("token")
    return {"ok": True}

# --- Protected endpoint ---
@app.get("/api/me")
async def me(user: CurrentUser):
    return user
```

## 4. Pydantic request model (optional, for strict typing)

```python
from pydantic import BaseModel

class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/auth/login")
async def login(body: LoginRequest, response: Response):
    result = await auth_manager.authenticate("local", body.model_dump())
    ...
```

## 5. Run it

```bash
uvicorn main:app --reload --port 8000
```

```bash
# Login
curl -c cookies.txt -X POST http://localhost:8000/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"alice","password":"password123"}'

# Protected endpoint
curl -b cookies.txt http://localhost:8000/api/me
```

## Environment variables

```ini
JWT_SECRET=a-long-random-string
BASE_URL=http://localhost:8000

# Optional
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
```

See the runnable example: [`examples/fastapi-app/`](../examples/fastapi-app/)
