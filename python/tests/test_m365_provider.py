"""Tests for M365Provider (mocked network)."""
import pytest

from authy import M365Provider, M365ProviderConfig


JWT_SECRET = "test-secret-key"

CONFIG = M365ProviderConfig(
    client_id="mock-client-id",
    client_secret="mock-client-secret",
    tenant_id="mock-tenant-id",
    redirect_uri="http://localhost:3000/auth/m365/callback",
    jwt_secret=JWT_SECRET,
)


@pytest.fixture
def provider():
    return M365Provider(CONFIG)


async def test_provider_name(provider):
    assert provider.name == "m365"


async def test_get_auth_url_returns_meta_token(provider, mocker):
    mock_discovery = {
        "authorization_endpoint": "https://login.microsoftonline.com/mock-tenant/oauth2/v2.0/authorize",
        "token_endpoint": "https://login.microsoftonline.com/mock-tenant/oauth2/v2.0/token",
    }
    mocker.patch.object(provider, "_get_discovery", return_value=mock_discovery)

    result = await provider.authenticate({"action": "get_auth_url"})
    assert result.success is True
    assert result.token is not None


async def test_callback_returns_user_and_refresh_token(provider, mocker):
    import jwt as pyjwt
    import time

    mock_discovery = {
        "authorization_endpoint": "https://login.microsoftonline.com/mock-tenant/oauth2/v2.0/authorize",
        "token_endpoint": "https://login.microsoftonline.com/mock-tenant/oauth2/v2.0/token",
    }
    mocker.patch.object(provider, "_get_discovery", return_value=mock_discovery)

    id_token = pyjwt.encode(
        {
            "sub": "m365-456",
            "email": "user@company.com",
            "preferred_username": "user@company.com",
            "name": "M365 User",
            "exp": int(time.time()) + 3600,
        },
        "mock",
        algorithm="HS256",
    )

    mock_client = mocker.AsyncMock()
    mock_client.__aenter__ = mocker.AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = mocker.AsyncMock(return_value=False)
    mock_client.fetch_token = mocker.AsyncMock(
        return_value={"id_token": id_token, "refresh_token": "mock-refresh"}
    )
    mocker.patch("authy.providers.m365.AsyncOAuth2Client", return_value=mock_client)

    result = await provider.authenticate({
        "action": "callback",
        "code": "auth-code",
        "state": "state",
        "code_verifier": "verifier",
    })
    assert result.success is True
    assert result.user.email == "user@company.com"
    assert result.user.provider == "m365"
    assert result.refresh_token == "mock-refresh"


async def test_unknown_action(provider):
    result = await provider.authenticate({"action": "nope"})
    assert result.success is False
    assert "unknown action" in result.error.lower()
