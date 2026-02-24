"""
Authy AuthManager setup for the FastAPI example.

Swap the in-memory USERS dict and _find_user function for real
database calls (SQLAlchemy, asyncpg, motor, etc.) to use in production.
"""
import os
from typing import Annotated

from fastapi import Cookie, Depends, HTTPException

from authy import (
    AuthManager,
    LocalProvider,
    LocalProviderConfig,
    hash_password,
)

# ---------------------------------------------------------------------------
# In-memory user store  (replace with DB in production)
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
# FastAPI dependency — injects the current user into route functions
# ---------------------------------------------------------------------------
def get_current_user(token: Annotated[str | None, Cookie()] = None) -> dict:
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        return auth_manager.verify_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


CurrentUser = Annotated[dict, Depends(get_current_user)]
