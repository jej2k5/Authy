# Next.js Integration Guide (App Router)

**Version:** Next.js 14+  **Language:** TypeScript

## Install

```bash
npm install jsonwebtoken
npm install @types/jsonwebtoken --save-dev
# Authy (from this repo)
npm install ../typescript
```

## 1. AuthManager singleton

```typescript
// lib/auth.ts
import { AuthManager, LocalProvider, GoogleProvider, hashPassword } from '@authy/core';

let _manager: AuthManager | null = null;

export async function getAuthManager(): Promise<AuthManager> {
  if (_manager) return _manager;

  const secret = process.env.JWT_SECRET!;
  _manager = new AuthManager(secret);

  // In-memory user store — swap for a real DB lookup
  const passwordHash = await hashPassword('password123');
  const users: Record<string, { id: string; email: string; name: string; passwordHash: string }> = {
    alice: { id: '1', email: 'alice@example.com', name: 'Alice', passwordHash },
  };

  _manager.register(new LocalProvider({
    jwtSecret: secret,
    tokenTtl: 3600,
    findUser: async (username) => users[username] ?? null,
  }));

  if (process.env.GOOGLE_CLIENT_ID) {
    _manager.register(new GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
      redirectUri: process.env.NEXT_PUBLIC_BASE_URL + '/auth/google/callback',
      jwtSecret: secret,
    }));
  }

  return _manager;
}
```

## 2. Catch-all auth Route Handler

A single file handles all providers and both steps of the OAuth flow:

```typescript
// app/api/auth/[...provider]/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { getAuthManager } from '@/lib/auth';
import jwt from 'jsonwebtoken';

// POST /api/auth/local  — local login
export async function POST(req: NextRequest) {
  const manager = await getAuthManager();
  const body = await req.json();
  const result = await manager.authenticate('local', body);

  if (!result.success) {
    return NextResponse.json({ error: result.error }, { status: 401 });
  }

  const res = NextResponse.json({ user: result.user });
  res.cookies.set('token', result.token!, { httpOnly: true, secure: true, sameSite: 'lax', path: '/' });
  return res;
}

// GET /api/auth/google            — start OAuth
// GET /api/auth/google/callback   — finish OAuth
export async function GET(
  req: NextRequest,
  { params }: { params: { provider: string[] } },
) {
  const manager = await getAuthManager();
  const [providerName, action] = params.provider;   // e.g. ['google'] or ['google', 'callback']

  // --- OAuth callback ---
  if (action === 'callback') {
    const { searchParams } = req.nextUrl;
    const codeVerifier = req.cookies.get('pkce_verifier')?.value ?? '';

    const result = await manager.authenticate(providerName, {
      action: 'callback',
      code: searchParams.get('code'),
      state: searchParams.get('state'),
      codeVerifier,
    });

    if (!result.success) {
      return NextResponse.redirect(new URL('/login?error=auth_failed', req.url));
    }

    const res = NextResponse.redirect(new URL('/dashboard', req.url));
    res.cookies.set('token', result.token!, { httpOnly: true, secure: true, sameSite: 'lax', path: '/' });
    res.cookies.delete('pkce_verifier');
    return res;
  }

  // --- OAuth start ---
  const result = await manager.authenticate(providerName, { action: 'getAuthUrl' });
  if (!result.success) return NextResponse.json({ error: result.error }, { status: 500 });

  const meta = jwt.decode(result.token!) as Record<string, string>;
  const res = NextResponse.redirect(meta.authUrl);
  res.cookies.set('pkce_verifier', meta.codeVerifier, { httpOnly: true, sameSite: 'lax', path: '/' });
  return res;
}

// DELETE /api/auth/logout
export async function DELETE() {
  const res = NextResponse.json({ ok: true });
  res.cookies.delete('token');
  return res;
}
```

## 3. Middleware (protect pages)

```typescript
// middleware.ts  (project root)
import { NextRequest, NextResponse } from 'next/server';
import { jwtVerify } from 'jose';

const PUBLIC_PATHS = ['/login', '/api/auth'];

export async function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;
  if (PUBLIC_PATHS.some(p => pathname.startsWith(p))) return NextResponse.next();

  const token = req.cookies.get('token')?.value;
  if (!token) return NextResponse.redirect(new URL('/login', req.url));

  try {
    const key = new TextEncoder().encode(process.env.JWT_SECRET!);
    await jwtVerify(token, key);
    return NextResponse.next();
  } catch {
    const res = NextResponse.redirect(new URL('/login', req.url));
    res.cookies.delete('token');
    return res;
  }
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
};
```

## 4. Login page

```tsx
// app/login/page.tsx
'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function LoginPage() {
  const router = useRouter();
  const [error, setError] = useState('');

  async function handleLocalLogin(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const res = await fetch('/api/auth/local', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: form.get('username'), password: form.get('password') }),
    });
    if (res.ok) { router.push('/dashboard'); }
    else { setError((await res.json()).error); }
  }

  return (
    <main style={{ maxWidth: 400, margin: '80px auto', fontFamily: 'sans-serif' }}>
      <h1>Sign in</h1>
      <form onSubmit={handleLocalLogin}>
        <input name="username" placeholder="Username" required /><br />
        <input name="password" type="password" placeholder="Password" required /><br />
        {error && <p style={{ color: 'red' }}>{error}</p>}
        <button type="submit">Sign in</button>
      </form>
      <hr />
      <a href="/api/auth/google">Sign in with Google</a>
    </main>
  );
}
```

## 5. Server Component reading the JWT

```tsx
// app/dashboard/page.tsx
import { cookies } from 'next/headers';
import { jwtVerify } from 'jose';

async function getUser() {
  const token = cookies().get('token')?.value;
  if (!token) return null;
  const key = new TextEncoder().encode(process.env.JWT_SECRET!);
  const { payload } = await jwtVerify(token, key);
  return payload;
}

export default async function Dashboard() {
  const user = await getUser();
  return (
    <main>
      <h1>Dashboard</h1>
      <p>Signed in as <strong>{user?.name as string}</strong> ({user?.email as string})</p>
      <form action="/api/auth/logout" method="DELETE">
        <button type="submit">Sign out</button>
      </form>
    </main>
  );
}
```

## Environment variables

```ini
# .env.local
JWT_SECRET=a-long-random-string-min-32-chars
NEXT_PUBLIC_BASE_URL=http://localhost:3000

# Optional OAuth providers
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
```

See the runnable example: [`examples/nextjs-app/`](../examples/nextjs-app/)
