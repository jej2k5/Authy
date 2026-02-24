"""Tests for SSOProvider (OIDC and SAML, mocked)."""
import pytest

from authy import OidcSSOConfig, SamlSSOConfig, SSOProvider


JWT_SECRET = "test-secret-key"

OIDC_CONFIG = OidcSSOConfig(
    type="oidc",
    issuer_url="https://sso.example.com",
    client_id="mock-client-id",
    client_secret="mock-client-secret",
    redirect_uri="http://localhost:3000/auth/sso/callback",
    jwt_secret=JWT_SECRET,
)

SAML_CONFIG = SamlSSOConfig(
    type="saml",
    sp_entity_id="urn:example:sp",
    idp_sso_url="https://idp.example.com/sso",
    idp_cert="MOCK_CERT",
    jwt_secret=JWT_SECRET,
)


class TestSSOProviderOIDC:
    @pytest.fixture
    def provider(self):
        return SSOProvider(OIDC_CONFIG)

    async def test_provider_name(self, provider):
        assert provider.name == "sso"

    async def test_get_auth_url(self, provider, mocker):
        mocker.patch.object(
            provider,
            "_get_oidc_discovery",
            return_value={
                "authorization_endpoint": "https://sso.example.com/auth",
                "token_endpoint": "https://sso.example.com/token",
            },
        )
        result = await provider.authenticate({"action": "get_auth_url"})
        assert result.success is True
        assert result.token is not None

    async def test_callback_returns_user(self, provider, mocker):
        import jwt as pyjwt
        import time

        mocker.patch.object(
            provider,
            "_get_oidc_discovery",
            return_value={
                "authorization_endpoint": "https://sso.example.com/auth",
                "token_endpoint": "https://sso.example.com/token",
            },
        )
        id_token = pyjwt.encode(
            {"sub": "sso-789", "email": "user@sso.example.com", "name": "SSO User", "exp": int(time.time()) + 3600},
            "mock",
            algorithm="HS256",
        )
        mock_client = mocker.AsyncMock()
        mock_client.__aenter__ = mocker.AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = mocker.AsyncMock(return_value=False)
        mock_client.fetch_token = mocker.AsyncMock(return_value={"id_token": id_token})
        mocker.patch("authy.providers.sso.AsyncOAuth2Client", return_value=mock_client)

        result = await provider.authenticate({
            "action": "callback",
            "code": "code",
            "state": "state",
            "code_verifier": "verifier",
        })
        assert result.success is True
        assert result.user.email == "user@sso.example.com"
        assert result.user.provider == "sso"


class TestSSOProviderSAML:
    @pytest.fixture
    def provider(self):
        return SSOProvider(SAML_CONFIG)

    async def test_get_login_url(self, provider, mocker):
        mock_auth = mocker.MagicMock()
        mock_auth.login.return_value = "https://idp.example.com/sso?SAMLRequest=mock"
        mocker.patch("authy.providers.sso.OneLogin_Saml2_Auth", return_value=mock_auth)

        result = await provider.authenticate({"action": "get_login_url"})
        assert result.success is True
        assert "idp.example.com" in result.token

    async def test_callback_parses_saml_response(self, provider, mocker):
        mock_auth = mocker.MagicMock()
        mock_auth.is_authenticated.return_value = True
        mock_auth.get_nameid.return_value = "saml-user-111"
        mock_auth.get_attributes.return_value = {
            "email": ["saml@example.com"],
            "displayName": ["SAML User"],
        }
        mocker.patch("authy.providers.sso.OneLogin_Saml2_Auth", return_value=mock_auth)

        result = await provider.authenticate({
            "action": "callback",
            "saml_response": "BASE64_SAML_RESPONSE",
        })
        assert result.success is True
        assert result.user.email == "saml@example.com"
        assert result.user.name == "SAML User"
        assert result.user.id == "saml-user-111"

    async def test_callback_handles_auth_failure(self, provider, mocker):
        mock_auth = mocker.MagicMock()
        mock_auth.is_authenticated.return_value = False
        mock_auth.get_errors.return_value = ["invalid_signature"]
        mocker.patch("authy.providers.sso.OneLogin_Saml2_Auth", return_value=mock_auth)

        result = await provider.authenticate({
            "action": "callback",
            "saml_response": "BAD_RESPONSE",
        })
        assert result.success is False
        assert "failed" in result.error.lower()
