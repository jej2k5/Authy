"""
Authy Flask example.

Run:
    pip install -r requirements.txt
    pip install -e ../../python
    cp .env.example .env
    flask run --port 5000

Then open http://localhost:5000
"""
import os
from pathlib import Path

import jwt as pyjwt
from dotenv import load_dotenv
from flask import Flask, g, jsonify, make_response, redirect, request, send_file

load_dotenv()

from auth import auth_manager, require_auth, run_async  # noqa: E402

app = Flask(__name__)

COOKIE_KWARGS = dict(
    httponly=True,
    samesite="Lax",
    secure=os.environ.get("FLASK_DEBUG", "1") != "1",  # secure=True in production
)

# ---------------------------------------------------------------------------
# Static demo page
# ---------------------------------------------------------------------------
@app.get("/")
def index():
    return send_file(Path(__file__).parent / "static" / "index.html")

# ---------------------------------------------------------------------------
# POST /auth/login — local username / password
# ---------------------------------------------------------------------------
@app.post("/auth/login")
def login():
    result = run_async(auth_manager.authenticate("local", request.get_json(force=True) or {}))
    if not result.success:
        return jsonify(error=result.error), 401

    resp = make_response(jsonify(user={
        "id": result.user.id,
        "email": result.user.email,
        "name": result.user.name,
        "provider": result.user.provider,
    }))
    resp.set_cookie("token", result.token, **COOKIE_KWARGS)
    return resp

# ---------------------------------------------------------------------------
# GET /auth/google — start Google OAuth
# ---------------------------------------------------------------------------
@app.get("/auth/google")
def google_start():
    result = run_async(auth_manager.authenticate("google", {"action": "get_auth_url"}))
    if not result.success:
        return jsonify(error="Google provider not configured"), 500

    meta = pyjwt.decode(result.token, options={"verify_signature": False})
    resp = make_response(redirect(meta["auth_url"]))
    resp.set_cookie("pkce_verifier", meta["code_verifier"],
                    httponly=True, samesite="Lax", max_age=300)
    return resp

# ---------------------------------------------------------------------------
# GET /auth/google/callback
# ---------------------------------------------------------------------------
@app.get("/auth/google/callback")
def google_callback():
    code = request.args.get("code", "")
    state = request.args.get("state", "")
    code_verifier = request.cookies.get("pkce_verifier", "")

    result = run_async(auth_manager.authenticate("google", {
        "action": "callback",
        "code": code,
        "state": state,
        "code_verifier": code_verifier,
    }))
    if not result.success:
        return redirect("/?error=auth_failed")

    resp = make_response(redirect("/"))
    resp.set_cookie("token", result.token, **COOKIE_KWARGS)
    resp.delete_cookie("pkce_verifier")
    return resp

# ---------------------------------------------------------------------------
# GET /auth/m365 — start Microsoft 365 OAuth
# ---------------------------------------------------------------------------
@app.get("/auth/m365")
def m365_start():
    result = run_async(auth_manager.authenticate("m365", {"action": "get_auth_url"}))
    if not result.success:
        return jsonify(error="M365 provider not configured"), 500

    meta = pyjwt.decode(result.token, options={"verify_signature": False})
    resp = make_response(redirect(meta["auth_url"]))
    resp.set_cookie("pkce_verifier", meta["code_verifier"],
                    httponly=True, samesite="Lax", max_age=300)
    return resp

# ---------------------------------------------------------------------------
# GET /auth/m365/callback
# ---------------------------------------------------------------------------
@app.get("/auth/m365/callback")
def m365_callback():
    code = request.args.get("code", "")
    state = request.args.get("state", "")
    code_verifier = request.cookies.get("pkce_verifier", "")

    result = run_async(auth_manager.authenticate("m365", {
        "action": "callback",
        "code": code,
        "state": state,
        "code_verifier": code_verifier,
    }))
    if not result.success:
        return redirect("/?error=auth_failed")

    resp = make_response(redirect("/"))
    resp.set_cookie("token", result.token, **COOKIE_KWARGS)
    resp.delete_cookie("pkce_verifier")
    return resp

# ---------------------------------------------------------------------------
# POST /auth/logout
# ---------------------------------------------------------------------------
@app.post("/auth/logout")
def logout():
    resp = make_response(jsonify(ok=True))
    resp.delete_cookie("token")
    return resp

# ---------------------------------------------------------------------------
# GET /api/me — protected endpoint
# ---------------------------------------------------------------------------
@app.get("/api/me")
@require_auth
def me():
    return jsonify(user=g.user)

# ---------------------------------------------------------------------------
# GET /api/providers — list active providers
# ---------------------------------------------------------------------------
@app.get("/api/providers")
def providers():
    return jsonify(providers=auth_manager.list_providers())


if __name__ == "__main__":
    app.run(debug=True, port=5000)
