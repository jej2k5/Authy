"""
Authy FastAPI example.

Run:
    pip install -r requirements.txt
    pip install -e ../../python
    cp .env.example .env
    uvicorn main:app --reload --port 8000

Then open http://localhost:8000
"""
import os
from pathlib import Path

import jwt as pyjwt
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

load_dotenv()

from auth import CurrentUser, auth_manager  # noqa: E402 — must load .env first

app = FastAPI(title="Authy FastAPI Example")

COOKIE_KWARGS = dict(httponly=True, samesite="lax",
                     secure=os.environ.get("NODE_ENV") == "production")

# ---------------------------------------------------------------------------
# Serve the static HTML demo page
# ---------------------------------------------------------------------------
_HTML = (Path(__file__).parent / "static" / "index.html").read_text()

@app.get("/", response_class=HTMLResponse)
async def index():
    return _HTML

# ---------------------------------------------------------------------------
# POST /auth/login — local username / password
# ---------------------------------------------------------------------------
@app.post("/auth/login")
async def login(body: dict, response: Response):
    result = await auth_manager.authenticate("local", body)
    if not result.success:
        return JSONResponse({"error": result.error}, status_code=401)

    response.set_cookie("token", result.token, **COOKIE_KWARGS)
    return {
        "user": {
            "id": result.user.id,
            "email": result.user.email,
            "name": result.user.name,
            "provider": result.user.provider,
        }
    }

# ---------------------------------------------------------------------------
# GET /auth/google — start Google OAuth
# ---------------------------------------------------------------------------
@app.get("/auth/google")
async def google_start(response: Response):
    result = await auth_manager.authenticate("google", {"action": "get_auth_url"})
    if not result.success:
        return JSONResponse({"error": "Google provider not configured"}, status_code=500)

    meta = pyjwt.decode(result.token, options={"verify_signature": False})
    response.set_cookie("pkce_verifier", meta["code_verifier"],
                        httponly=True, samesite="lax", max_age=300)
    return RedirectResponse(meta["auth_url"])

# ---------------------------------------------------------------------------
# GET /auth/google/callback — exchange code for user JWT
# ---------------------------------------------------------------------------
@app.get("/auth/google/callback")
async def google_callback(request: Request, code: str, state: str):
    code_verifier = request.cookies.get("pkce_verifier", "")
    result = await auth_manager.authenticate("google", {
        "action": "callback",
        "code": code,
        "state": state,
        "code_verifier": code_verifier,
    })
    if not result.success:
        return RedirectResponse("/?error=auth_failed")

    resp = RedirectResponse("/")
    resp.set_cookie("token", result.token, **COOKIE_KWARGS)
    resp.delete_cookie("pkce_verifier")
    return resp

# ---------------------------------------------------------------------------
# GET /auth/m365 — start Microsoft 365 OAuth
# ---------------------------------------------------------------------------
@app.get("/auth/m365")
async def m365_start(response: Response):
    result = await auth_manager.authenticate("m365", {"action": "get_auth_url"})
    if not result.success:
        return JSONResponse({"error": "M365 provider not configured"}, status_code=500)

    meta = pyjwt.decode(result.token, options={"verify_signature": False})
    response.set_cookie("pkce_verifier", meta["code_verifier"],
                        httponly=True, samesite="lax", max_age=300)
    return RedirectResponse(meta["auth_url"])

# ---------------------------------------------------------------------------
# GET /auth/m365/callback
# ---------------------------------------------------------------------------
@app.get("/auth/m365/callback")
async def m365_callback(request: Request, code: str, state: str):
    code_verifier = request.cookies.get("pkce_verifier", "")
    result = await auth_manager.authenticate("m365", {
        "action": "callback",
        "code": code,
        "state": state,
        "code_verifier": code_verifier,
    })
    if not result.success:
        return RedirectResponse("/?error=auth_failed")

    resp = RedirectResponse("/")
    resp.set_cookie("token", result.token, **COOKIE_KWARGS)
    resp.delete_cookie("pkce_verifier")
    return resp

# ---------------------------------------------------------------------------
# POST /auth/logout
# ---------------------------------------------------------------------------
@app.post("/auth/logout")
async def logout(response: Response):
    response.delete_cookie("token")
    return {"ok": True}

# ---------------------------------------------------------------------------
# GET /api/me — protected endpoint
# ---------------------------------------------------------------------------
@app.get("/api/me")
async def me(user: CurrentUser):
    return {"user": user}

# ---------------------------------------------------------------------------
# GET /api/providers — list active providers
# ---------------------------------------------------------------------------
@app.get("/api/providers")
async def providers():
    return {"providers": auth_manager.list_providers()}
