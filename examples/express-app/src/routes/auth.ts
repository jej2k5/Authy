import { Router, Request, Response, CookieOptions } from 'express';
import { AuthManager } from '@authy/core';
import jwt from 'jsonwebtoken';

const COOKIE_OPTS: CookieOptions = {
  httpOnly: true,
  sameSite: 'lax',
  secure: process.env.NODE_ENV === 'production',
};

export function authRouter(manager: AuthManager): Router {
  const router = Router();

  // -------------------------------------------------------------------------
  // POST /auth/login — local username / password
  // Body: { username: string, password: string }
  // -------------------------------------------------------------------------
  router.post('/login', async (req: Request, res: Response) => {
    const result = await manager.authenticate('local', req.body);

    if (!result.success) {
      return res.status(401).json({ error: result.error });
    }

    res.cookie('token', result.token!, COOKIE_OPTS);
    res.json({
      user: {
        id: result.user!.id,
        email: result.user!.email,
        name: result.user!.name,
        provider: result.user!.provider,
      },
    });
  });

  // -------------------------------------------------------------------------
  // GET /auth/google — initiate Google OAuth (redirect to Google)
  // -------------------------------------------------------------------------
  router.get('/google', async (_req: Request, res: Response) => {
    const result = await manager.authenticate('google', { action: 'getAuthUrl' });

    if (!result.success) {
      return res.status(500).json({ error: 'Google provider not configured' });
    }

    // Decode without verifying — we only need the payload values here
    const meta = jwt.decode(result.token!) as Record<string, string>;

    // Store PKCE verifier server-side so it's not accessible to JS
    res.cookie('pkce_verifier', meta.codeVerifier, { ...COOKIE_OPTS, maxAge: 5 * 60 * 1000 });
    res.cookie('oauth_state',   meta.state,         { ...COOKIE_OPTS, maxAge: 5 * 60 * 1000 });
    res.redirect(meta.authUrl);
  });

  // -------------------------------------------------------------------------
  // GET /auth/google/callback — exchange code for token
  // -------------------------------------------------------------------------
  router.get('/google/callback', async (req: Request, res: Response) => {
    const { code, state } = req.query as Record<string, string>;
    const codeVerifier = req.cookies?.pkce_verifier ?? '';

    const result = await manager.authenticate('google', {
      action: 'callback',
      code,
      state,
      codeVerifier,
    });

    res.clearCookie('pkce_verifier');
    res.clearCookie('oauth_state');

    if (!result.success) {
      return res.redirect('/?error=auth_failed');
    }

    res.cookie('token', result.token!, COOKIE_OPTS);
    res.redirect('/');
  });

  // -------------------------------------------------------------------------
  // GET /auth/m365 — initiate Microsoft 365 OAuth
  // -------------------------------------------------------------------------
  router.get('/m365', async (_req: Request, res: Response) => {
    const result = await manager.authenticate('m365', { action: 'getAuthUrl' });

    if (!result.success) {
      return res.status(500).json({ error: 'M365 provider not configured' });
    }

    const meta = jwt.decode(result.token!) as Record<string, string>;
    res.cookie('pkce_verifier', meta.codeVerifier, { ...COOKIE_OPTS, maxAge: 5 * 60 * 1000 });
    res.redirect(meta.authUrl);
  });

  // -------------------------------------------------------------------------
  // GET /auth/m365/callback — exchange code for token
  // -------------------------------------------------------------------------
  router.get('/m365/callback', async (req: Request, res: Response) => {
    const { code, state } = req.query as Record<string, string>;
    const codeVerifier = req.cookies?.pkce_verifier ?? '';

    const result = await manager.authenticate('m365', {
      action: 'callback',
      code,
      state,
      codeVerifier,
    });

    res.clearCookie('pkce_verifier');

    if (!result.success) {
      return res.redirect('/?error=auth_failed');
    }

    res.cookie('token', result.token!, COOKIE_OPTS);
    res.redirect('/');
  });

  // -------------------------------------------------------------------------
  // POST /auth/logout — clear the session cookie
  // -------------------------------------------------------------------------
  router.post('/logout', (_req: Request, res: Response) => {
    res.clearCookie('token');
    res.json({ ok: true });
  });

  return router;
}
