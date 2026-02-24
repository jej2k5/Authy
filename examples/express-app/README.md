# Authy — Express Example

A minimal Express + TypeScript app demonstrating all Authy providers.

## Quick start

```bash
cp .env.example .env      # optional: add OAuth credentials
npm install
npm run dev
```

Open http://localhost:3000

**Test accounts (always available, no config needed):**

| Username | Password |
|---|---|
| alice | password123 |
| bob | letmein |

## What's included

| File | Purpose |
|---|---|
| `src/auth.ts` | `AuthManager` singleton with in-memory user store |
| `src/server.ts` | Express app wiring |
| `src/routes/auth.ts` | Login, OAuth start/callback, logout routes |
| `src/middleware/requireAuth.ts` | JWT verification middleware |
| `public/index.html` | Simple UI to test all flows |

## Routes

| Method | Path | Description |
|---|---|---|
| `POST` | `/auth/login` | Local username/password login |
| `GET` | `/auth/google` | Start Google OAuth (requires env vars) |
| `GET` | `/auth/google/callback` | Google OAuth callback |
| `GET` | `/auth/m365` | Start M365 OAuth (requires env vars) |
| `GET` | `/auth/m365/callback` | M365 OAuth callback |
| `POST` | `/auth/logout` | Clear session cookie |
| `GET` | `/api/me` | Protected — returns current user JWT payload |
| `GET` | `/api/providers` | List active providers |

## Enable OAuth providers

Add to your `.env`:

```ini
# Google
GOOGLE_CLIENT_ID=xxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=xxxx

# Microsoft 365
M365_CLIENT_ID=xxxx
M365_CLIENT_SECRET=xxxx
M365_TENANT_ID=xxxx
```

In your Google/Azure console, add the callback URLs:
- Google: `http://localhost:3000/auth/google/callback`
- M365: `http://localhost:3000/auth/m365/callback`
