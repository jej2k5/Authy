"""Tests for AuthManager."""
import pytest

from authy import AuthManager, LocalProvider, LocalProviderConfig
from authy.utils import hash_password


JWT_SECRET = "test-manager-secret"


@pytest.fixture
def manager():
    hashed = hash_password("secret")

    async def find_user(username):
        if username == "bob":
            return {"id": "bob-1", "email": "bob@example.com", "name": "Bob", "password_hash": hashed}
        return None

    local = LocalProvider(LocalProviderConfig(jwt_secret=JWT_SECRET), find_user)
    return AuthManager(jwt_secret=JWT_SECRET).register(local)


async def test_list_providers(manager):
    assert "local" in manager.list_providers()


async def test_authenticate_via_registered_provider(manager):
    result = await manager.authenticate("local", {"username": "bob", "password": "secret"})
    assert result.success is True
    assert result.user.email == "bob@example.com"


async def test_unknown_provider_returns_error(manager):
    result = await manager.authenticate("github", {"token": "abc"})
    assert result.success is False
    assert "unknown provider" in result.error.lower()


async def test_verify_valid_token(manager):
    result = await manager.authenticate("local", {"username": "bob", "password": "secret"})
    payload = manager.verify_token(result.token)
    assert payload["sub"] == "bob-1"
    assert payload["email"] == "bob@example.com"


async def test_verify_invalid_token_raises(manager):
    import jwt
    with pytest.raises(jwt.InvalidTokenError):
        manager.verify_token("bad.token.here")


async def test_register_with_alias(manager):
    async def noop(u):
        return None
    local2 = LocalProvider(LocalProviderConfig(jwt_secret=JWT_SECRET), noop)
    manager.register(local2, alias="password-auth")
    assert "password-auth" in manager.list_providers()


async def test_register_chaining(manager):
    assert isinstance(manager, AuthManager)
