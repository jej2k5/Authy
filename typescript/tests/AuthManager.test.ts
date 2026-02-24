import { AuthManager } from '../src/AuthManager';
import { LocalProvider } from '../src/providers/LocalProvider';
import { hashPassword } from '../src/utils/hash';

const JWT_SECRET = 'test-manager-secret';

async function buildManager() {
  const passwordHash = await hashPassword('secret');
  const local = new LocalProvider({
    jwtSecret: JWT_SECRET,
    findUser: async (username) =>
      username === 'bob'
        ? { id: 'bob-1', email: 'bob@example.com', name: 'Bob', passwordHash }
        : null,
  });

  return new AuthManager(JWT_SECRET).register(local);
}

describe('AuthManager', () => {
  it('lists registered providers', async () => {
    const manager = await buildManager();
    expect(manager.listProviders()).toContain('local');
  });

  it('authenticates via a registered provider', async () => {
    const manager = await buildManager();
    const result = await manager.authenticate('local', { username: 'bob', password: 'secret' });

    expect(result.success).toBe(true);
    expect(result.user?.email).toBe('bob@example.com');
  });

  it('returns error for unknown provider', async () => {
    const manager = await buildManager();
    const result = await manager.authenticate('github', { token: 'abc' });

    expect(result.success).toBe(false);
    expect(result.error).toMatch(/unknown provider/i);
  });

  it('verifies a valid JWT issued by a provider', async () => {
    const manager = await buildManager();
    const authResult = await manager.authenticate('local', { username: 'bob', password: 'secret' });
    const payload = await manager.verifyToken(authResult.token!);

    expect(payload.sub).toBe('bob-1');
    expect(payload['email']).toBe('bob@example.com');
  });

  it('throws when verifying an invalid JWT', async () => {
    const manager = await buildManager();
    await expect(manager.verifyToken('bad.token.here')).rejects.toThrow();
  });

  it('supports registering providers with aliases', async () => {
    const manager = await buildManager();
    const local2 = new LocalProvider({ jwtSecret: JWT_SECRET, findUser: async () => null });
    manager.register(local2, 'password-auth');
    expect(manager.listProviders()).toContain('password-auth');
  });
});
