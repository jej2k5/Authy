"""
AuthManager setup and helpers for the Flask example.

Replace the in-memory USERS dict and _find_user with real DB calls.
Flask is synchronous by default, so all Authy async calls go through
asyncio.run() via the run_async() helper.
"""
import asyncio
import os
from functools import wraps

from flask import g, jsonify, request

from authy import AuthManager, LocalProvider, LocalProviderConfig, hash_password

# ---------------------------------------------------------------------------
# In-memory user store
# ---------------------------------------------------------------------------
_PASSWORD_HASH = hash_password("password123")
_BOB_HASH      = hash_password("letmein")

USERS = {
    "alice": {"id": "1", "email": "alice@example.com", "name": "Alice", "password_hash": _PASSWORD_HASH},
    "bob":   {"id": "2", "email": "bob@example.com",   "name": "Bob",   "password_hash": _BOB_HASH},
}


async def _find_user(username: str):
    return USERS.get(username)


# ---------------------------------------------------------------------------
# Async helper (Flask WSGI is sync — wrap coroutines with asyncio.run)
# ---------------------------------------------------------------------------
def run_async(coro):
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# AuthManager singleton
# ---------------------------------------------------------------------------
def _build_manager() -> AuthManager:
    secret = os.environ.get("JWT_SECRET", "change-me")
    manager = AuthManager(jwt_secret=secret)

    manager.register(LocalProvider(
        LocalProviderConfig(jwt_secret=secret, token_ttl=3600),
        _find_user,
    ))

    if os.environ.get("GOOGLE_CLIENT_ID"):
        from authy import GoogleProvider, GoogleProviderConfig
        manager.register(GoogleProvider(GoogleProviderConfig(
            client_id=os.environ["GOOGLE_CLIENT_ID"],
            client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
            redirect_uri=os.environ["BASE_URL"] + "/auth/google/callback",
            jwt_secret=secret,
        )))

    if os.environ.get("M365_CLIENT_ID"):
        from authy import M365Provider, M365ProviderConfig
        manager.register(M365Provider(M365ProviderConfig(
            client_id=os.environ["M365_CLIENT_ID"],
            client_secret=os.environ["M365_CLIENT_SECRET"],
            tenant_id=os.environ["M365_TENANT_ID"],
            redirect_uri=os.environ["BASE_URL"] + "/auth/m365/callback",
            jwt_secret=secret,
        )))

    return manager


auth_manager: AuthManager = _build_manager()


# ---------------------------------------------------------------------------
# require_auth decorator — reads httpOnly cookie, verifies JWT
# ---------------------------------------------------------------------------
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
