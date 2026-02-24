"""Microsoft 365 / Azure AD / Entra ID OAuth 2.0 provider."""
from __future__ import annotations

import secrets
from typing import Any

import httpx
from authlib.integrations.httpx_client import AsyncOAuth2Client

from ..types import AuthProvider, AuthResult, M365ProviderConfig, UserInfo
from ..utils.jwt_utils import sign_token


def _discovery_url(tenant_id: str) -> str:
    return f"https://login.microsoftonline.com/{tenant_id}/v2.0/.well-known/openid-configuration"


class M365Provider(AuthProvider):
    """Microsoft 365 / Entra ID OAuth 2.0 provider.

    Identical two-step redirect flow to GoogleProvider.
    """

    def __init__(self, config: M365ProviderConfig) -> None:
        self._config = config
        self._discovery: dict[str, Any] | None = None

    @property
    def name(self) -> str:
        return "m365"

    async def _get_discovery(self) -> dict[str, Any]:
        if self._discovery is None:
            url = _discovery_url(self._config.tenant_id)
            async with httpx.AsyncClient() as client:
                resp = await client.get(url)
                resp.raise_for_status()
                self._discovery = resp.json()
        return self._discovery

    async def authenticate(self, credentials: dict[str, Any]) -> AuthResult:
        action = credentials.get("action")
        try:
            if action == "get_auth_url":
                return await self._get_auth_url()
            if action == "callback":
                return await self._handle_callback(credentials)
            return AuthResult(success=False, error='Unknown action. Use "get_auth_url" or "callback"')
        except Exception as exc:
            return AuthResult(success=False, error=f"M365 auth error: {exc}")

    async def _get_auth_url(self) -> AuthResult:
        discovery = await self._get_discovery()
        state = secrets.token_urlsafe(32)
        code_verifier = secrets.token_urlsafe(64)

        client = AsyncOAuth2Client(
            client_id=self._config.client_id,
            redirect_uri=self._config.redirect_uri,
            scope="openid email profile offline_access",
            code_challenge_method="S256",
        )
        auth_url, _ = client.create_authorization_url(
            discovery["authorization_endpoint"],
            state=state,
            code_verifier=code_verifier,
        )

        meta_token = sign_token(
            {"auth_url": auth_url, "state": state, "code_verifier": code_verifier, "type": "oauth_meta"},
            self._config.jwt_secret,
            300,
        )
        return AuthResult(success=True, token=meta_token)

    async def _handle_callback(self, credentials: dict[str, Any]) -> AuthResult:
        discovery = await self._get_discovery()
        code = credentials["code"]
        state = credentials["state"]
        code_verifier = credentials["code_verifier"]

        async with AsyncOAuth2Client(
            client_id=self._config.client_id,
            client_secret=self._config.client_secret,
            redirect_uri=self._config.redirect_uri,
            code_challenge_method="S256",
        ) as client:
            token_response = await client.fetch_token(
                discovery["token_endpoint"],
                code=code,
                state=state,
                code_verifier=code_verifier,
            )

        id_token = token_response.get("id_token", "")
        import jwt as pyjwt
        claims = pyjwt.decode(id_token, options={"verify_signature": False})

        user_info = UserInfo(
            id=claims.get("sub", ""),
            email=claims.get("email") or claims.get("preferred_username", ""),
            name=claims.get("name", ""),
            provider=self.name,
            raw=claims,
        )
        token = sign_token(
            {"sub": user_info.id, "email": user_info.email, "name": user_info.name, "provider": self.name},
            self._config.jwt_secret,
            self._config.token_ttl,
        )
        refresh_token = token_response.get("refresh_token")
        return AuthResult(success=True, user=user_info, token=token, refresh_token=refresh_token)
