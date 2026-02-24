"""Tests for GoogleProvider (mocked network)."""
import pytest

from authy import GoogleProvider, GoogleProviderConfig


JWT_SECRET = "test-secret-key"

CONFIG = GoogleProviderConfig(
    client_id="mock-client-id",
    client_secret="mock-client-secret",
    redirect_uri="http://localhost:3000/auth/google/callback",
    jwt_secret=JWT_SECRET,
)


@pytest.fixture
def provider():
    return GoogleProvider(CONFIG)


async def test_provider_name(provider):
    assert provider.name == "google"


async def test_get_auth_url_returns_meta_token(provider, mocker):
    mock_discovery = {
        "authorization_endpoint": "https://accounts.google.com/o/oauth2/auth",
        "token_endpoint": "https://oauth2.googleapis.com/token",
    }
    mocker.patch.object(provider, "_get_discovery", return_value=mock_discovery)

    result = await provider.authenticate({"action": "get_auth_url"})
    assert result.success is True
    assert result.token is not None


async def test_callback_returns_user(provider, mocker):
    import jwt as pyjwt
    import time

    mock_discovery = {
        "authorization_endpoint": "https://accounts.google.com/o/oauth2/auth",
        "token_endpoint": "https://oauth2.googleapis.com/token",
    }
    mocker.patch.object(provider, "_get_discovery", return_value=mock_discovery)

    id_token = pyjwt.encode(
        {"sub": "google-123", "email": "user@gmail.com", "name": "Google User", "exp": int(time.time()) + 3600},
        "mock",
        algorithm="HS256",
    )

    mock_client = mocker.AsyncMock()
    mock_client.__aenter__ = mocker.AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = mocker.AsyncMock(return_value=False)
    mock_client.fetch_token = mocker.AsyncMock(return_value={"id_token": id_token})
    mocker.patch("authy.providers.google.AsyncOAuth2Client", return_value=mock_client)

    result = await provider.authenticate({
        "action": "callback",
        "code": "auth-code",
        "state": "state",
        "code_verifier": "verifier",
    })
    assert result.success is True
    assert result.user.email == "user@gmail.com"
    assert result.user.provider == "google"
    assert result.token is not None


async def test_unknown_action(provider):
    result = await provider.authenticate({"action": "bad"})
    assert result.success is False
    assert "unknown action" in result.error.lower()
