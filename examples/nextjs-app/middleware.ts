import { NextRequest, NextResponse } from 'next/server';
import { jwtVerify } from 'jose';

// Paths that do NOT require authentication
const PUBLIC_PREFIXES = ['/login', '/api/auth', '/_next', '/favicon.ico'];

export async function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;

  if (PUBLIC_PREFIXES.some((p) => pathname.startsWith(p))) {
    return NextResponse.next();
  }

  const token = req.cookies.get('token')?.value;
  if (!token) {
    return NextResponse.redirect(new URL('/login', req.url));
  }

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
