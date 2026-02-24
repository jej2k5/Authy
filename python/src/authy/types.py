"""Core types shared across all Authy providers."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class UserInfo:
    """Normalized user information returned by every provider."""
    id: str
    email: str
    name: str
    provider: str
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class AuthResult:
    """Result returned from every authenticate() call."""
    success: bool
    user: UserInfo | None = None
    token: str | None = None
    refresh_token: str | None = None
    error: str | None = None


class AuthProvider(ABC):
    """Abstract base class that all authentication providers must implement."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique provider name."""

    @abstractmethod
    async def authenticate(self, credentials: dict[str, Any]) -> AuthResult:
        """Authenticate using provider-specific credentials."""


# ---------------------------------------------------------------------------
# Provider configuration dataclasses
# ---------------------------------------------------------------------------

@dataclass
class LocalProviderConfig:
    jwt_secret: str
    token_ttl: int = 3600


@dataclass
class GoogleProviderConfig:
    client_id: str
    client_secret: str
    redirect_uri: str
    jwt_secret: str
    token_ttl: int = 3600


@dataclass
class M365ProviderConfig:
    client_id: str
    client_secret: str
    tenant_id: str
    redirect_uri: str
    jwt_secret: str
    token_ttl: int = 3600


@dataclass
class OidcSSOConfig:
    type: str  # 'oidc'
    issuer_url: str
    client_id: str
    client_secret: str
    redirect_uri: str
    jwt_secret: str
    token_ttl: int = 3600


@dataclass
class SamlSSOConfig:
    type: str  # 'saml'
    sp_entity_id: str
    idp_sso_url: str
    idp_cert: str
    jwt_secret: str
    sp_private_key: str | None = None
    token_ttl: int = 3600
