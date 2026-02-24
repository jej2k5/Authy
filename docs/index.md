# Authy Integration Guides

How to drop Authy into an existing application. Each guide covers:

- Installing and configuring `AuthManager`
- Protecting routes / pages
- Handling local (username/password) login
- Adding OAuth providers (Google, M365)
- Verifying JWTs on protected endpoints

## Framework guides

| Framework | Language | Guide |
|---|---|---|
| Express | TypeScript | [express.md](express.md) |
| Next.js (App Router) | TypeScript | [nextjs.md](nextjs.md) |
| FastAPI | Python | [fastapi.md](fastapi.md) |
| Flask | Python | [flask.md](flask.md) |
| Streamlit | Python | [streamlit.md](streamlit.md) |

## Runnable examples

Each framework has a self-contained example app under `examples/`:

```
examples/
├── express-app/      → npm install && npm run dev
├── nextjs-app/       → npm install && npm run dev
├── fastapi-app/      → pip install -r requirements.txt && uvicorn main:app --reload
├── flask-app/        → pip install -r requirements.txt && flask run
└── streamlit-app/    → pip install -r requirements.txt && streamlit run app.py
```

Every example works out of the box using a seeded in-memory user store
(`alice` / `password123`). OAuth providers (Google, M365, SSO) are wired
up but require real credentials in `.env` — copy `.env.example` to `.env`
and fill in your values to enable them.

## The integration pattern (all frameworks)

The same three steps apply everywhere:

```
1. Create AuthManager → register providers
2. Auth routes: POST /auth/login  GET /auth/<provider>  GET /auth/<provider>/callback
3. Guard routes: read token from cookie/header → manager.verifyToken()
```

### Local auth credentials flow

```
Browser  ──POST /auth/login {username, password}──▶  Server
Server   ──manager.authenticate('local', creds)──▶   AuthManager
Server   ◀──AuthResult {success, user, token}──────  AuthManager
Browser  ◀──Set-Cookie: token=<jwt>────────────────  Server
```

### OAuth redirect flow (Google / M365 / OIDC SSO)

```
Browser  ──GET /auth/google──────────────────────▶  Server
Server   ──manager.authenticate('google',           AuthManager
             {action:'getAuthUrl'})──────────────▶
Server   ◀──AuthResult.token (meta: authUrl,        AuthManager
             codeVerifier, state)────────────────
Server   ──stores codeVerifier in httpOnly cookie─▶ Browser
Browser  ──redirects to Google───────────────────▶  Google
Google   ──redirects to /auth/google/callback───▶   Server
Server   ──manager.authenticate('google',           AuthManager
             {action:'callback', code, state,
              codeVerifier})─────────────────────▶
Server   ◀──AuthResult {success, user, token}──────  AuthManager
Browser  ◀──Set-Cookie: token=<jwt>────────────────  Server
```
