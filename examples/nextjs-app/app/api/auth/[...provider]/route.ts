import { NextRequest, NextResponse } from 'next/server';
import { getAuthManager } from '@/lib/auth';
import jwt from 'jsonwebtoken';

const COOKIE_OPTS = {
  httpOnly: true,
  secure: process.env.NODE_ENV === 'production',
  sameSite: 'lax' as const,
  path: '/',
};

// ---------------------------------------------------------------------------
// POST /api/auth/local   — local username / password login
// Body: { username: string; password: string }
// ---------------------------------------------------------------------------
export async function POST(req: NextRequest) {
  const manager = await getAuthManager();
  const body = await req.json();
  const result = await manager.authenticate('local', body);

  if (!result.success) {
    return NextResponse.json({ error: result.error }, { status: 401 });
  }

  const res = NextResponse.json({
    user: {
      id: result.user!.id,
      email: result.user!.email,
      name: result.user!.name,
      provider: result.user!.provider,
    },
  });
  res.cookies.set('token', result.token!, COOKIE_OPTS);
  return res;
}

// ---------------------------------------------------------------------------
// GET /api/auth/google            — start OAuth (redirect to provider)
// GET /api/auth/google/callback   — handle code exchange
// Same pattern for /api/auth/m365 and /api/auth/m365/callback
// ---------------------------------------------------------------------------
export async function GET(
  req: NextRequest,
  { params }: { params: { provider: string[] } },
) {
  const manager = await getAuthManager();
  const [providerName, action] = params.provider;

  // --- OAuth callback: exchange code for JWT ---
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
    res.cookies.set('token', result.token!, COOKIE_OPTS);
    res.cookies.delete('pkce_verifier');
    return res;
  }

  // --- OAuth start: get authorization URL and redirect ---
  const result = await manager.authenticate(providerName, { action: 'getAuthUrl' });

  if (!result.success) {
    return NextResponse.json(
      { error: `${providerName} provider not configured` },
      { status: 500 },
    );
  }

  const meta = jwt.decode(result.token!) as Record<string, string>;
  const res = NextResponse.redirect(meta.authUrl);
  res.cookies.set('pkce_verifier', meta.codeVerifier, {
    ...COOKIE_OPTS,
    maxAge: 5 * 60,
  });
  return res;
}

// ---------------------------------------------------------------------------
// DELETE /api/auth/logout
// ---------------------------------------------------------------------------
export async function DELETE() {
  const res = NextResponse.json({ ok: true });
  res.cookies.delete('token');
  return res;
}
