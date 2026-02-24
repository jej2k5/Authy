"""Authy: Multi-provider authentication framework."""
from .auth_manager import AuthManager
from .providers import GoogleProvider, LocalProvider, M365Provider, SSOProvider
from .types import (
    AuthProvider,
    AuthResult,
    GoogleProviderConfig,
    LocalProviderConfig,
    M365ProviderConfig,
    OidcSSOConfig,
    SamlSSOConfig,
    UserInfo,
)
from .utils import hash_password, sign_token, verify_password, verify_token

__all__ = [
    "AuthManager",
    "AuthProvider",
    "AuthResult",
    "GoogleProvider",
    "GoogleProviderConfig",
    "LocalProvider",
    "LocalProviderConfig",
    "M365Provider",
    "M365ProviderConfig",
    "OidcSSOConfig",
    "SamlSSOConfig",
    "SSOProvider",
    "UserInfo",
    "hash_password",
    "sign_token",
    "verify_password",
    "verify_token",
]
