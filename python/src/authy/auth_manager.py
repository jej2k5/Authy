"""AuthManager: registry and orchestrator for all authentication providers."""
from __future__ import annotations

from typing import Any

from .types import AuthProvider, AuthResult
from .utils.jwt_utils import verify_token


class AuthManager:
    """Registers providers and routes authentication requests.

    Example::

        manager = AuthManager(jwt_secret="secret")
        manager.register(LocalProvider(config, find_user))
        result = await manager.authenticate("local", {"username": "alice", "password": "pw"})
    """

    def __init__(self, jwt_secret: str) -> None:
        self._jwt_secret = jwt_secret
        self._providers: dict[str, AuthProvider] = {}

    def register(self, provider: AuthProvider, alias: str | None = None) -> "AuthManager":
        """Register a provider. Returns self for chaining."""
        key = alias or provider.name
        self._providers[key] = provider
        return self

    async def authenticate(
        self, provider_name: str, credentials: dict[str, Any]
    ) -> AuthResult:
        """Authenticate using a named provider."""
        provider = self._providers.get(provider_name)
        if provider is None:
            return AuthResult(success=False, error=f"Unknown provider: {provider_name!r}")
        return await provider.authenticate(credentials)

    def verify_token(self, token: str) -> dict[str, Any]:
        """Verify a JWT issued by this framework. Raises jwt.InvalidTokenError on failure."""
        return verify_token(token, self._jwt_secret)

    def list_providers(self) -> list[str]:
        """Return a list of registered provider names."""
        return list(self._providers.keys())
