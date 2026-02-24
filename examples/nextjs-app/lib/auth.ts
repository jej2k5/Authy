import {
  AuthManager,
  LocalProvider,
  GoogleProvider,
  M365Provider,
  hashPassword,
} from '@authy/core';

type UserRecord = { id: string; email: string; name: string; passwordHash: string };

// Module-level singleton — Next.js reuses the module across requests in dev
let _manager: AuthManager | null = null;

export async function getAuthManager(): Promise<AuthManager> {
  if (_manager) return _manager;

  const secret = process.env.JWT_SECRET!;
  if (!secret) throw new Error('JWT_SECRET environment variable is required');

  _manager = new AuthManager(secret);

  // ---------------------------------------------------------------------------
  // In-memory user store — replace findUser with a real DB call
  // ---------------------------------------------------------------------------
  const users = new Map<string, UserRecord>([
    ['alice', { id: '1', email: 'alice@example.com', name: 'Alice', passwordHash: await hashPassword('password123') }],
    ['bob',   { id: '2', email: 'bob@example.com',   name: 'Bob',   passwordHash: await hashPassword('letmein')    }],
  ]);

  _manager.register(new LocalProvider({
    jwtSecret: secret,
    tokenTtl: 3600,
    findUser: async (username) => users.get(username) ?? null,
  }));

  if (process.env.GOOGLE_CLIENT_ID) {
    _manager.register(new GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
      redirectUri: `${process.env.NEXT_PUBLIC_BASE_URL}/api/auth/google/callback`,
      jwtSecret: secret,
    }));
  }

  if (process.env.M365_CLIENT_ID) {
    _manager.register(new M365Provider({
      clientId: process.env.M365_CLIENT_ID,
      clientSecret: process.env.M365_CLIENT_SECRET!,
      tenantId: process.env.M365_TENANT_ID!,
      redirectUri: `${process.env.NEXT_PUBLIC_BASE_URL}/api/auth/m365/callback`,
      jwtSecret: secret,
    }));
  }

  return _manager;
}
