# Authy

A multi-provider authentication framework available in both **TypeScript/Node.js** and **Python**. Supports local username/password, Google OAuth 2.0, Microsoft 365 (Entra ID), and generic SSO (OIDC + SAML 2.0) — all behind a unified `AuthManager` interface.

---

## Features

- **Local provider** — username/password auth with bcrypt-hashed passwords
- **Google provider** — OAuth 2.0 / OIDC via Google Identity (PKCE flow)
- **M365 provider** — OAuth 2.0 via Microsoft Entra ID (Azure AD), with refresh token support
- **SSO provider** — generic OIDC (any compliant issuer) or SAML 2.0
- **JWT issuance** — every successful auth returns a signed HS256 JWT
- **Framework-agnostic** — no hard dependency on Express, Flask, FastAPI, etc.
- **Consistent API** — same `AuthManager` / `AuthResult` / `UserInfo` model in both languages

---

## Repository layout

```
Authy/
├── typescript/          # @authy/core — Node.js / TypeScript package
│   ├── src/
│   │   ├── types.ts
│   │   ├── AuthManager.ts
│   │   ├── providers/
│   │   │   ├── LocalProvider.ts
│   │   │   ├── GoogleProvider.ts
│   │   │   ├── M365Provider.ts
│   │   │   └── SSOProvider.ts
│   │   └── utils/
│   │       ├── jwt.ts
│   │       └── hash.ts
│   └── tests/
└── python/              # authy — Python package
    ├── src/authy/
    │   ├── types.py
    │   ├── auth_manager.py
    │   ├── providers/
    │   │   ├── local.py
    │   │   ├── google.py
    │   │   ├── m365.py
    │   │   └── sso.py
    │   └── utils/
    │       ├── jwt_utils.py
    │       └── hash_utils.py
    └── tests/
```

---

## Core concepts

### `AuthResult`

Every `authenticate()` call returns a single result object:

| Field | Type | Description |
|---|---|---|
| `success` | `bool` | Whether authentication succeeded |
| `user` | `UserInfo \| null` | Normalized user info on success |
| `token` | `string \| null` | Signed JWT on success |
| `refreshToken` | `string \| null` | Refresh token (M365 only) |
| `error` | `string \| null` | Error message on failure |

### `UserInfo`

Normalized across all providers:

| Field | Description |
|---|---|
| `id` | Provider-specific user ID (sub claim / NameID) |
| `email` | User's email address |
| `name` | Display name |
| `provider` | Provider name (`"local"`, `"google"`, `"m365"`, `"sso"`) |
| `raw` | Raw claims / attributes from the provider |

### OAuth / OIDC two-step flow

Google, M365, and OIDC SSO all follow the same redirect pattern:

1. Call `authenticate({ action: "getAuthUrl" })` (TS) / `authenticate({"action": "get_auth_url"})` (Python) to get a short-lived meta-token containing the authorization URL, PKCE `code_verifier`, and `state`.
2. Redirect the user to the authorization URL.
3. After the user approves, call `authenticate({ action: "callback", code, state, codeVerifier })` to exchange the code for a user JWT.

---

## TypeScript

### Installation

```bash
cd typescript
npm install
```

**Dependencies:** `jose` (JWT), `bcrypt` (hashing), `openid-client` (OAuth 2.0 / OIDC), `samlify` (SAML 2.0)

### Usage

```typescript
import {
  AuthManager,
  LocalProvider,
  GoogleProvider,
  M365Provider,
  SSOProvider,
  hashPassword,
} from './src/index';

const JWT_SECRET = process.env.JWT_SECRET!;

// 1. Build the manager
const manager = new AuthManager(JWT_SECRET);

// 2. Register providers
manager.register(
  new LocalProvider({
    jwtSecret: JWT_SECRET,
    tokenTtl: 3600,
    findUser: async (username) => {
      // Return { id, email, name, passwordHash } or null
      return db.users.findByUsername(username);
    },
  })
);

manager.register(
  new GoogleProvider({
    clientId: process.env.GOOGLE_CLIENT_ID!,
    clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    redirectUri: 'https://yourapp.com/auth/google/callback',
    jwtSecret: JWT_SECRET,
  })
);

manager.register(
  new M365Provider({
    clientId: process.env.M365_CLIENT_ID!,
    clientSecret: process.env.M365_CLIENT_SECRET!,
    tenantId: process.env.M365_TENANT_ID!,
    redirectUri: 'https://yourapp.com/auth/m365/callback',
    jwtSecret: JWT_SECRET,
  })
);

// SSO — OIDC variant
manager.register(
  new SSOProvider({
    type: 'oidc',
    issuerUrl: 'https://your-idp.example.com',
    clientId: process.env.SSO_CLIENT_ID!,
    clientSecret: process.env.SSO_CLIENT_SECRET!,
    redirectUri: 'https://yourapp.com/auth/sso/callback',
    jwtSecret: JWT_SECRET,
  })
);

// 3. Authenticate
// Local login
const result = await manager.authenticate('local', {
  username: 'alice',
  password: 'hunter2',
});

if (result.success) {
  console.log(result.user);   // UserInfo
  console.log(result.token);  // signed JWT
}

// OAuth — step 1: get redirect URL
const step1 = await manager.authenticate('google', { action: 'getAuthUrl' });
// step1.token contains { authUrl, state, codeVerifier } encoded as a JWT

// OAuth — step 2: exchange code after redirect
const step2 = await manager.authenticate('google', {
  action: 'callback',
  code: req.query.code,
  state: req.query.state,
  codeVerifier: sessionStorage.codeVerifier,
});

// 4. Verify a JWT on subsequent requests
const payload = await manager.verifyToken(req.headers.authorization!);
```

### Hashing passwords for LocalProvider

```typescript
import { hashPassword } from './src/index';

const hash = await hashPassword('hunter2');
// store hash in your database
```

### Running tests

```bash
cd typescript
npm test
```

---

## Python

### Installation

```bash
cd python
pip install -e ".[dev]"
```

**Dependencies:** `authlib` (OAuth 2.0 / OIDC), `PyJWT` (JWT), `bcrypt` (hashing), `httpx` (async HTTP), `python3-saml` (SAML 2.0)

### Usage

```python
import asyncio
from authy import (
    AuthManager,
    LocalProvider, LocalProviderConfig,
    GoogleProvider, GoogleProviderConfig,
    M365Provider, M365ProviderConfig,
    SSOProvider, OidcSSOConfig,
    hash_password,
)
import os

JWT_SECRET = os.environ["JWT_SECRET"]

# 1. Define a user lookup function for LocalProvider
async def find_user(username: str):
    # Return dict with id/email/name/password_hash, or None
    return await db.users.find_by_username(username)

# 2. Build the manager and register providers
manager = (
    AuthManager(jwt_secret=JWT_SECRET)
    .register(LocalProvider(LocalProviderConfig(jwt_secret=JWT_SECRET), find_user))
    .register(GoogleProvider(GoogleProviderConfig(
        client_id=os.environ["GOOGLE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
        redirect_uri="https://yourapp.com/auth/google/callback",
        jwt_secret=JWT_SECRET,
    )))
    .register(M365Provider(M365ProviderConfig(
        client_id=os.environ["M365_CLIENT_ID"],
        client_secret=os.environ["M365_CLIENT_SECRET"],
        tenant_id=os.environ["M365_TENANT_ID"],
        redirect_uri="https://yourapp.com/auth/m365/callback",
        jwt_secret=JWT_SECRET,
    )))
    .register(SSOProvider(OidcSSOConfig(
        type="oidc",
        issuer_url="https://your-idp.example.com",
        client_id=os.environ["SSO_CLIENT_ID"],
        client_secret=os.environ["SSO_CLIENT_SECRET"],
        redirect_uri="https://yourapp.com/auth/sso/callback",
        jwt_secret=JWT_SECRET,
    )))
)

# 3. Authenticate
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
    # step1.token contains { auth_url, state, code_verifier } as a JWT

    # OAuth — step 2: exchange code after redirect
    step2 = await manager.authenticate("google", {
        "action": "callback",
        "code": request.query_params["code"],
        "state": request.query_params["state"],
        "code_verifier": session["code_verifier"],
    })

    # 4. Verify a JWT on subsequent requests
    payload = manager.verify_token(request.headers["Authorization"])
```

### Hashing passwords for LocalProvider

```python
from authy import hash_password

hashed = hash_password("hunter2")
# store hashed in your database
```

### Running tests

```bash
cd python
PYTHONPATH=src python -m pytest tests/ -v
```

---

## SAML 2.0 SSO

Use `SamlSSOConfig` (Python) / `SamlSSOConfig` (TypeScript) instead of the OIDC variant:

```python
from authy import SSOProvider, SamlSSOConfig

provider = SSOProvider(SamlSSOConfig(
    type="saml",
    sp_entity_id="urn:yourapp:sp",
    idp_sso_url="https://idp.example.com/sso/saml",
    idp_cert="-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----",
    jwt_secret=JWT_SECRET,
    # sp_private_key="..." # optional, for signed requests
))

# Step 1: get IdP redirect URL
result = await provider.authenticate({"action": "get_login_url"})
# result.token is the full redirect URL

# Step 2: handle POST-back from IdP
result = await provider.authenticate({
    "action": "callback",
    "saml_response": request.form["SAMLResponse"],
})
```

---

## Environment variables

| Variable | Used by |
|---|---|
| `JWT_SECRET` | All providers (JWT signing key) |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | Google provider |
| `M365_CLIENT_ID` / `M365_CLIENT_SECRET` / `M365_TENANT_ID` | M365 provider |
| `SSO_CLIENT_ID` / `SSO_CLIENT_SECRET` | OIDC SSO provider |
