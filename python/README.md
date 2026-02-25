# authy

A multi-provider authentication framework for Python. Supports local username/password, Google OAuth 2.0, Microsoft 365 (Entra ID), and generic SSO (OIDC + SAML 2.0) — all behind a unified `AuthManager` interface.

## Features

- **Local provider** — username/password auth with bcrypt-hashed passwords
- **Google provider** — OAuth 2.0 / OIDC via Google Identity (PKCE flow)
- **M365 provider** — OAuth 2.0 via Microsoft Entra ID (Azure AD), with refresh token support
- **SSO provider** — generic OIDC (any compliant issuer) or SAML 2.0
- **JWT issuance** — every successful auth returns a signed HS256 JWT
- **Framework-agnostic** — no hard dependency on Flask, FastAPI, Streamlit, etc.
- **Async-first** — all providers use `async`/`await`

## Installation

```bash
pip install authy
```

## Usage

```python
import asyncio, os
from authy import (
    AuthManager,
    LocalProvider, LocalProviderConfig,
    GoogleProvider, GoogleProviderConfig,
    M365Provider, M365ProviderConfig,
    SSOProvider, OidcSSOConfig,
    hash_password,
)

JWT_SECRET = os.environ["JWT_SECRET"]

async def find_user(username: str):
    # Return dict with id/email/name/password_hash, or None
    return await db.users.find_by_username(username)

manager = (
    AuthManager(jwt_secret=JWT_SECRET)
    .register(LocalProvider(LocalProviderConfig(jwt_secret=JWT_SECRET), find_user))
    .register(GoogleProvider(GoogleProviderConfig(
        client_id=os.environ["GOOGLE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
        redirect_uri="https://yourapp.com/auth/google/callback",
        jwt_secret=JWT_SECRET,
    )))
)

async def main():
    # Local login
    result = await manager.authenticate("local", {
        "username": "alice",
        "password": "hunter2",
    })
    if result.success:
        print(result.user)   # UserInfo dataclass
        print(result.token)  # signed JWT

    # OAuth — step 1: get redirect URL
    step1 = await manager.authenticate("google", {"action": "get_auth_url"})

    # OAuth — step 2: exchange code after redirect
    step2 = await manager.authenticate("google", {
        "action": "callback",
        "code": request.query_params["code"],
        "state": request.query_params["state"],
        "code_verifier": session["code_verifier"],
    })

    # Verify a JWT
    payload = manager.verify_token(request.headers["Authorization"])
```

## AuthResult

Every `authenticate()` call returns an `AuthResult` dataclass:

| Field | Type | Description |
|---|---|---|
| `success` | `bool` | Whether authentication succeeded |
| `user` | `UserInfo \| None` | Normalized user info on success |
| `token` | `str \| None` | Signed JWT on success |
| `refresh_token` | `str \| None` | Refresh token (M365 only) |
| `error` | `str \| None` | Error message on failure |

## Hashing passwords

```python
from authy import hash_password

hashed = hash_password("hunter2")
# store hashed in your database
```

## SAML 2.0 SSO

```python
from authy import SSOProvider, SamlSSOConfig

provider = SSOProvider(SamlSSOConfig(
    type="saml",
    sp_entity_id="urn:yourapp:sp",
    idp_sso_url="https://idp.example.com/sso/saml",
    idp_cert="-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----",
    jwt_secret=JWT_SECRET,
))
```

## License

MIT
