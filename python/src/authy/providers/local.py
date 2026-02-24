"""Username/password authentication provider."""
from __future__ import annotations

from typing import Any, Awaitable, Callable

from ..types import AuthProvider, AuthResult, LocalProviderConfig, UserInfo
from ..utils.hash_utils import verify_password
from ..utils.jwt_utils import sign_token


UserRecord = dict[str, str]  # {id, email, name, password_hash}
FindUserFunc = Callable[[str], Awaitable[UserRecord | None]]


class LocalProvider(AuthProvider):
    """Authenticates users via username/password with bcrypt-hashed passwords.

    Args:
        config: LocalProviderConfig with jwt_secret and token_ttl.
        find_user: Async callable that accepts a username and returns a dict
                   with keys ``id``, ``email``, ``name``, ``password_hash``,
                   or ``None`` if the user is not found.
    """

    def __init__(self, config: LocalProviderConfig, find_user: FindUserFunc) -> None:
        self._config = config
        self._find_user = find_user

    @property
    def name(self) -> str:
        return "local"

    async def authenticate(self, credentials: dict[str, Any]) -> AuthResult:
        username = credentials.get("username")
        password = credentials.get("password")

        if not username or not password:
            return AuthResult(success=False, error="Username and password are required")

        try:
            user = await self._find_user(username)
            if user is None:
                return AuthResult(success=False, error="Invalid credentials")

            if not verify_password(password, user["password_hash"]):
                return AuthResult(success=False, error="Invalid credentials")

            user_info = UserInfo(
                id=user["id"],
                email=user["email"],
                name=user["name"],
                provider=self.name,
            )
            token = sign_token(
                {"sub": user["id"], "email": user["email"], "name": user["name"], "provider": self.name},
                self._config.jwt_secret,
                self._config.token_ttl,
            )
            return AuthResult(success=True, user=user_info, token=token)

        except Exception as exc:
            return AuthResult(success=False, error=f"Authentication error: {exc}")
