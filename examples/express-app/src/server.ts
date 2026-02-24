import 'dotenv/config';
import express from 'express';
import cookieParser from 'cookie-parser';
import path from 'path';

import { getAuthManager } from './auth';
import { authRouter } from './routes/auth';
import { requireAuth, AuthenticatedRequest } from './middleware/requireAuth';

async function start() {
  const app = express();
  const manager = await getAuthManager();

  // ---------------------------------------------------------------------------
  // Middleware
  // ---------------------------------------------------------------------------
  app.use(express.json());
  app.use(cookieParser());
  app.use(express.static(path.join(__dirname, '..', 'public')));

  // ---------------------------------------------------------------------------
  // Auth routes  (login, OAuth redirects, logout)
  // ---------------------------------------------------------------------------
  app.use('/auth', authRouter(manager));

  // ---------------------------------------------------------------------------
  // Protected API routes
  // ---------------------------------------------------------------------------
  app.get('/api/me', requireAuth(manager), (req: AuthenticatedRequest, res) => {
    res.json({ user: req.user });
  });

  app.get('/api/providers', (_req, res) => {
    res.json({ providers: manager.listProviders() });
  });

  // ---------------------------------------------------------------------------
  // Start
  // ---------------------------------------------------------------------------
  const port = parseInt(process.env.PORT ?? '3000', 10);
  app.listen(port, () => {
    console.log(`\nAuthy Express example running at http://localhost:${port}`);
    console.log('  Providers: ' + manager.listProviders().join(', '));
    console.log('\nTest accounts:');
    console.log('  alice / password123');
    console.log('  bob   / letmein\n');
  });
}

start().catch(console.error);
