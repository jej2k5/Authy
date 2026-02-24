"""Generic SSO provider supporting OIDC and SAML 2.0."""
from __future__ import annotations

import secrets
from typing import Any

import httpx
from authlib.integrations.httpx_client import AsyncOAuth2Client
from onelogin.saml2.auth import OneLogin_Saml2_Auth

from ..types import AuthProvider, AuthResult, OidcSSOConfig, SamlSSOConfig, UserInfo
from ..utils.jwt_utils import sign_token


class SSOProvider(AuthProvider):
    """Generic SSO provider.

    OIDC flow (set ``config.type = 'oidc'``):
        Step 1: ``credentials = {"action": "get_auth_url"}``
        Step 2: ``credentials = {"action": "callback", "code": ..., "state": ..., "code_verifier": ...}``

    SAML 2.0 flow (set ``config.type = 'saml'``):
        Step 1: ``credentials = {"action": "get_login_url"}``  → returns redirect URL in token
        Step 2: ``credentials = {"action": "callback", "saml_response": ...}``
    """

    def __init__(self, config: OidcSSOConfig | SamlSSOConfig) -> None:
        self._config = config
        self._discovery: dict[str, Any] | None = None

    @property
    def name(self) -> str:
        return "sso"

    async def authenticate(self, credentials: dict[str, Any]) -> AuthResult:
        try:
            if self._config.type == "oidc":
                return await self._handle_oidc(credentials)
            if self._config.type == "saml":
                return await self._handle_saml(credentials)
            return AuthResult(success=False, error=f"Unknown SSO type: {self._config.type!r}")
        except Exception as exc:
            return AuthResult(success=False, error=f"SSO error: {exc}")

    # ---------------------------------------------------------------------------
    # OIDC
    # ---------------------------------------------------------------------------

    async def _get_oidc_discovery(self) -> dict[str, Any]:
        assert isinstance(self._config, OidcSSOConfig)
        if self._discovery is None:
            url = self._config.issuer_url.rstrip("/") + "/.well-known/openid-configuration"
            async with httpx.AsyncClient() as client:
                resp = await client.get(url)
                resp.raise_for_status()
                self._discovery = resp.json()
        return self._discovery

    async def _handle_oidc(self, credentials: dict[str, Any]) -> AuthResult:
        assert isinstance(self._config, OidcSSOConfig)
        action = credentials.get("action")

        if action == "get_auth_url":
            discovery = await self._get_oidc_discovery()
            state = secrets.token_urlsafe(32)
            code_verifier = secrets.token_urlsafe(64)
            client = AsyncOAuth2Client(
                client_id=self._config.client_id,
                redirect_uri=self._config.redirect_uri,
                scope="openid email profile",
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

        if action == "callback":
            discovery = await self._get_oidc_discovery()
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
                email=claims.get("email", ""),
                name=claims.get("name", ""),
                provider=self.name,
                raw=claims,
            )
            token = sign_token(
                {"sub": user_info.id, "email": user_info.email, "name": user_info.name, "provider": self.name},
                self._config.jwt_secret,
                self._config.token_ttl,
            )
            return AuthResult(success=True, user=user_info, token=token)

        return AuthResult(success=False, error="Unknown OIDC action")

    # ---------------------------------------------------------------------------
    # SAML 2.0
    # ---------------------------------------------------------------------------

    async def _handle_saml(self, credentials: dict[str, Any]) -> AuthResult:
        assert isinstance(self._config, SamlSSOConfig)
        action = credentials.get("action")

        if action == "get_login_url":
            return self._saml_get_login_url()

        if action == "callback":
            saml_response = credentials.get("saml_response", "")
            return self._saml_parse_response(saml_response)

        return AuthResult(success=False, error="Unknown SAML action")

    def _saml_get_login_url(self) -> AuthResult:
        assert isinstance(self._config, SamlSSOConfig)
        settings = self._build_saml_settings()
        auth = OneLogin_Saml2_Auth({}, old_settings=settings)
        login_url = auth.login()
        return AuthResult(success=True, token=login_url)

    def _saml_parse_response(self, saml_response: str) -> AuthResult:
        assert isinstance(self._config, SamlSSOConfig)
        settings = self._build_saml_settings()
        request_data = {
            "https": "on",
            "http_host": "localhost",
            "script_name": "/auth/sso/callback",
            "server_port": "443",
            "get_data": {},
            "post_data": {"SAMLResponse": saml_response},
        }
        auth = OneLogin_Saml2_Auth(request_data, old_settings=settings)
        auth.process_response()

        if not auth.is_authenticated():
            errors = auth.get_errors()
            return AuthResult(success=False, error=f"SAML authentication failed: {errors}")

        attrs = auth.get_attributes()
        name_id = auth.get_nameid()
        email = (attrs.get("email") or attrs.get(
            "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress", [""]
        ))[0]
        display_name = (attrs.get("displayName") or attrs.get(
            "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name", [""]
        ))[0]

        user_info = UserInfo(
            id=name_id,
            email=email,
            name=display_name,
            provider=self.name,
            raw={k: v for k, v in attrs.items()},
        )
        token = sign_token(
            {"sub": user_info.id, "email": user_info.email, "name": user_info.name, "provider": self.name},
            self._config.jwt_secret,
            self._config.token_ttl,
        )
        return AuthResult(success=True, user=user_info, token=token)

    def _build_saml_settings(self) -> dict[str, Any]:
        assert isinstance(self._config, SamlSSOConfig)
        settings: dict[str, Any] = {
            "idp": {
                "entityId": self._config.idp_sso_url,
                "singleSignOnService": {
                    "url": self._config.idp_sso_url,
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
                },
                "x509cert": self._config.idp_cert,
            },
            "sp": {
                "entityId": self._config.sp_entity_id,
                "assertionConsumerService": {
                    "url": f"{self._config.sp_entity_id}/callback",
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST",
                },
            },
        }
        if self._config.sp_private_key:
            settings["sp"]["privateKey"] = self._config.sp_private_key
        return settings
