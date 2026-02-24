import {
  AuthManager,
  LocalProvider,
  GoogleProvider,
  M365Provider,
  hashPassword,
} from '@authy/core';

// ---------------------------------------------------------------------------
// In-memory user store (swap for a real database in production)
// ---------------------------------------------------------------------------
type UserRecord = { id: string; email: string; name: string; passwordHash: string };

let _users: Map<string, UserRecord>;

async function seedUsers(): Promise<Map<string, UserRecord>> {
  if (_users) return _users;
  _users = new Map([
    ['alice', { id: '1', email: 'alice@example.com', name: 'Alice', passwordHash: await hashPassword('password123') }],
    ['bob',   { id: '2', email: 'bob@example.com',   name: 'Bob',   passwordHash: await hashPassword('letmein')    }],
  ]);
  return _users;
}

async function findUser(username: string): Promise<UserRecord | null> {
  const users = await seedUsers();
  return users.get(username) ?? null;
}

// ---------------------------------------------------------------------------
// Build and export a singleton AuthManager
// ---------------------------------------------------------------------------
let _manager: AuthManager;

export async function getAuthManager(): Promise<AuthManager> {
  if (_manager) return _manager;

  await seedUsers();

  const secret = process.env.JWT_SECRET ?? 'change-me';
  _manager = new AuthManager(secret);

  // Always available: local username/password
  _manager.register(new LocalProvider({ jwtSecret: secret, tokenTtl: 3600, findUser }));

  // Optional: Google OAuth — only enabled when env vars are present
  if (process.env.GOOGLE_CLIENT_ID) {
    _manager.register(new GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
      redirectUri: `${process.env.BASE_URL}/auth/google/callback`,
      jwtSecret: secret,
    }));
  }

  // Optional: Microsoft 365
  if (process.env.M365_CLIENT_ID) {
    _manager.register(new M365Provider({
      clientId: process.env.M365_CLIENT_ID,
      clientSecret: process.env.M365_CLIENT_SECRET!,
      tenantId: process.env.M365_TENANT_ID!,
      redirectUri: `${process.env.BASE_URL}/auth/m365/callback`,
      jwtSecret: secret,
    }));
  }

  return _manager;
}
