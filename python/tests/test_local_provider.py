"""Tests for LocalProvider."""
import pytest

from authy import LocalProvider, LocalProviderConfig
from authy.utils import hash_password, verify_token


JWT_SECRET = "test-secret-key-for-unit-tests"


async def _make_find_user(password: str):
    hashed = hash_password(password)

    async def find_user(username: str):
        if username == "alice":
            return {"id": "user-1", "email": "alice@example.com", "name": "Alice", "password_hash": hashed}
        return None

    return find_user


@pytest.fixture
async def provider():
    find_user = await _make_find_user("correct-password")
    return LocalProvider(LocalProviderConfig(jwt_secret=JWT_SECRET, token_ttl=3600), find_user)


async def test_success_valid_credentials(provider):
    result = await provider.authenticate({"username": "alice", "password": "correct-password"})
    assert result.success is True
    assert result.user.email == "alice@example.com"
    assert result.user.provider == "local"
    assert result.token is not None


async def test_failure_wrong_password(provider):
    result = await provider.authenticate({"username": "alice", "password": "wrong"})
    assert result.success is False
    assert result.error == "Invalid credentials"
    assert result.token is None


async def test_failure_unknown_user(provider):
    result = await provider.authenticate({"username": "nobody", "password": "any"})
    assert result.success is False
    assert result.error == "Invalid credentials"


async def test_failure_missing_credentials(provider):
    result = await provider.authenticate({})
    assert result.success is False
    assert "required" in result.error.lower()


async def test_issues_valid_jwt(provider):
    result = await provider.authenticate({"username": "alice", "password": "correct-password"})
    assert result.token is not None
    payload = verify_token(result.token, JWT_SECRET)
    assert payload["sub"] == "user-1"
    assert payload["email"] == "alice@example.com"
    assert payload["provider"] == "local"


def test_provider_name():
    async def noop(u):
        return None
    p = LocalProvider(LocalProviderConfig(jwt_secret="s"), noop)
    assert p.name == "local"
