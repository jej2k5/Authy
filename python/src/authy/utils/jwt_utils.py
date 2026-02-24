"""JWT sign/verify utilities using PyJWT."""
from __future__ import annotations

import time
import jwt


DEFAULT_TTL = 3600


def sign_token(payload: dict, secret: str, ttl_seconds: int = DEFAULT_TTL) -> str:
    """Sign a JWT with HS256."""
    now = int(time.time())
    claims = {**payload, "iat": now, "exp": now + ttl_seconds}
    return jwt.encode(claims, secret, algorithm="HS256")


def verify_token(token: str, secret: str) -> dict:
    """Verify and decode a JWT. Raises jwt.InvalidTokenError on failure."""
    return jwt.decode(token, secret, algorithms=["HS256"])
