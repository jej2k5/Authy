# @authy/core

A multi-provider authentication framework for Node.js / TypeScript. Supports local username/password, Google OAuth 2.0, Microsoft 365 (Entra ID), and generic SSO (OIDC + SAML 2.0) — all behind a unified `AuthManager` interface.

## Features

- **Local provider** — username/password auth with bcrypt-hashed passwords
- **Google provider** — OAuth 2.0 / OIDC via Google Identity (PKCE flow)
- **M365 provider** — OAuth 2.0 via Microsoft Entra ID (Azure AD), with refresh token support
- **SSO provider** — generic OIDC (any compliant issuer) or SAML 2.0
- **JWT issuance** — every successful auth returns a signed HS256 JWT
- **Framework-agnostic** — no hard dependency on Express, Next.js, etc.

## Installation

```bash
npm install @authy/core
```

## Usage

```typescript
import {
  AuthManager,
  LocalProvider,
  GoogleProvider,
  M365Provider,
  SSOProvider,
  hashPassword,
} from '@authy/core';

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

// 3. Authenticate (local)
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

// OAuth — step 2: exchange code after redirect
const step2 = await manager.authenticate('google', {
  action: 'callback',
  code: req.query.code,
  state: req.query.state,
  codeVerifier: session.codeVerifier,
});

// 4. Verify a JWT
const payload = await manager.verifyToken(req.headers.authorization!);
```

## AuthResult

Every `authenticate()` call returns:

| Field | Type | Description |
|---|---|---|
| `success` | `boolean` | Whether authentication succeeded |
| `user` | `UserInfo \| null` | Normalized user info on success |
| `token` | `string \| null` | Signed JWT on success |
| `refreshToken` | `string \| null` | Refresh token (M365 only) |
| `error` | `string \| null` | Error message on failure |

## Hashing passwords

```typescript
import { hashPassword } from '@authy/core';

const hash = await hashPassword('hunter2');
// store hash in your database
```

## License

MIT
