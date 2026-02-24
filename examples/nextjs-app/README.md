# Authy — Next.js Example (App Router)

A Next.js 14 app demonstrating Authy authentication with the App Router.

## Quick start

```bash
cp .env.example .env.local   # add JWT_SECRET (required) + optional OAuth creds
npm install
npm run dev
```

Open http://localhost:3000 — you'll be redirected to `/login`.

**Test accounts:**

| Username | Password |
|---|---|
| alice | password123 |
| bob | letmein |

## Project structure

```
app/
├── api/
│   ├── auth/[...provider]/route.ts   ← all auth endpoints (login, OAuth, logout)
│   └── providers/route.ts            ← list active providers
├── login/page.tsx                    ← login form (client component)
├── dashboard/
│   ├── page.tsx                      ← protected server component
│   └── LogoutButton.tsx              ← client component for logout
└── layout.tsx
lib/
└── auth.ts                           ← AuthManager singleton
middleware.ts                         ← JWT verification on every request
```

## Auth endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/auth/local` | Local login — body: `{ username, password }` |
| `GET` | `/api/auth/google` | Start Google OAuth |
| `GET` | `/api/auth/google/callback` | Google OAuth callback |
| `GET` | `/api/auth/m365` | Start M365 OAuth |
| `GET` | `/api/auth/m365/callback` | M365 OAuth callback |
| `DELETE` | `/api/auth/logout` | Clear session cookie |

## How protection works

`middleware.ts` runs on every request. It reads the `token` httpOnly cookie,
verifies it with `jose`'s `jwtVerify`, and redirects to `/login` if missing
or invalid. Server Components additionally call `getCurrentUser()` which
performs the same check — this is belt-and-suspenders for the dashboard page.

## Enable OAuth

```ini
# .env.local
GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=xxx

M365_CLIENT_ID=xxx
M365_CLIENT_SECRET=xxx
M365_TENANT_ID=xxx
```

Callback URLs to register in Google / Azure console:
- `http://localhost:3000/api/auth/google/callback`
- `http://localhost:3000/api/auth/m365/callback`
