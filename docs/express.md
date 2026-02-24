# Express Integration Guide

**Runtime:** Node.js 18+  **Language:** TypeScript

## Install

```bash
npm install express express-session cookie-parser
npm install @types/express @types/express-session @types/cookie-parser --save-dev
# Authy (from this repo)
npm install ../typescript
```

## 1. Create the AuthManager singleton

Put this in `src/auth.ts` so routes share one instance:

```typescript
// src/auth.ts
import { AuthManager, LocalProvider, GoogleProvider, M365Provider } from '@authy/core';

async function buildFindUser() {
  // Replace with your real DB call.
  // Password must be a bcrypt hash — use hashPassword() from @authy/core to create it.
  const { hashPassword } = await import('@authy/core');
  const users: Record<string, { id: string; email: string; name: string; passwordHash: string }> = {
    alice: { id: '1', email: 'alice@example.com', name: 'Alice',
             passwordHash: await hashPassword('password123') },
  };
  return async (username: string) => users[username] ?? null;
}

export async function createAuthManager(): Promise<AuthManager> {
  const secret = process.env.JWT_SECRET ?? 'change-me-in-production';
  const manager = new AuthManager(secret);

  manager.register(new LocalProvider({
    jwtSecret: secret,
    tokenTtl: 3600,
    findUser: await buildFindUser(),
  }));

  // Optional: Google OAuth — requires GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET
  if (process.env.GOOGLE_CLIENT_ID) {
    const { GoogleProvider } = await import('@authy/core');
    manager.register(new GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
      redirectUri: process.env.BASE_URL + '/auth/google/callback',
      jwtSecret: secret,
    }));
  }

  return manager;
}
```

## 2. Auth routes

```typescript
// src/routes/auth.ts
import { Router, Request, Response } from 'express';
import { AuthManager } from '@authy/core';
import jwt from 'jsonwebtoken';

export function authRouter(manager: AuthManager): Router {
  const router = Router();

  // --- Local login ---
  router.post('/login', async (req: Request, res: Response) => {
    const result = await manager.authenticate('local', req.body);
    if (!result.success) {
      return res.status(401).json({ error: result.error });
    }
    res.cookie('token', result.token, { httpOnly: true, secure: process.env.NODE_ENV === 'production', sameSite: 'lax' });
    res.json({ user: result.user });
  });

  // --- Google OAuth step 1: redirect to Google ---
  router.get('/google', async (req: Request, res: Response) => {
    const result = await manager.authenticate('google', { action: 'getAuthUrl' });
    if (!result.success) return res.status(500).json({ error: result.error });

    // Decode the meta-token to get authUrl + codeVerifier (no verification needed here)
    const meta = jwt.decode(result.token!) as Record<string, string>;
    // Store PKCE verifier and state server-side (httpOnly cookie)
    res.cookie('pkce_verifier', meta.codeVerifier, { httpOnly: true, sameSite: 'lax' });
    res.cookie('oauth_state', meta.state, { httpOnly: true, sameSite: 'lax' });
    res.redirect(meta.authUrl);
  });

  // --- Google OAuth step 2: exchange code ---
  router.get('/google/callback', async (req: Request, res: Response) => {
    const { code, state } = req.query as Record<string, string>;
    const codeVerifier = req.cookies.pkce_verifier ?? '';

    const result = await manager.authenticate('google', { action: 'callback', code, state, codeVerifier });
    if (!result.success) return res.status(401).json({ error: result.error });

    res.clearCookie('pkce_verifier');
    res.clearCookie('oauth_state');
    res.cookie('token', result.token, { httpOnly: true, secure: process.env.NODE_ENV === 'production', sameSite: 'lax' });
    res.redirect('/dashboard');
  });

  // --- Logout ---
  router.post('/logout', (_req, res) => {
    res.clearCookie('token');
    res.json({ ok: true });
  });

  return router;
}
```

## 3. Auth middleware

```typescript
// src/middleware/requireAuth.ts
import { Request, Response, NextFunction } from 'express';
import { AuthManager } from '@authy/core';

export function requireAuth(manager: AuthManager) {
  return (req: Request, res: Response, next: NextFunction) => {
    const token = req.cookies.token
      ?? req.headers.authorization?.replace('Bearer ', '');
    if (!token) return res.status(401).json({ error: 'Not authenticated' });

    try {
      (req as any).user = manager.verifyToken(token);
      next();
    } catch {
      res.status(401).json({ error: 'Invalid or expired token' });
    }
  };
}
```

## 4. Wire it together

```typescript
// src/server.ts
import 'dotenv/config';
import express from 'express';
import cookieParser from 'cookie-parser';
import { createAuthManager } from './auth';
import { authRouter } from './routes/auth';
import { requireAuth } from './middleware/requireAuth';

async function start() {
  const app = express();
  app.use(express.json());
  app.use(cookieParser());

  const manager = await createAuthManager();

  app.use('/auth', authRouter(manager));

  // Protected routes
  app.get('/api/me', requireAuth(manager), (req, res) => {
    res.json((req as any).user);
  });

  app.listen(3000, () => console.log('http://localhost:3000'));
}

start();
```

## 5. Test it

```bash
# Login
curl -c cookies.txt -X POST http://localhost:3000/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"alice","password":"password123"}'

# Access protected endpoint
curl -b cookies.txt http://localhost:3000/api/me
```

## Environment variables

```ini
JWT_SECRET=a-long-random-string
BASE_URL=http://localhost:3000

# Optional — remove to disable Google login
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
```

See the runnable example: [`examples/express-app/`](../examples/express-app/)
