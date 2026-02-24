import { LocalProvider } from '../src/providers/LocalProvider';
import { hashPassword } from '../src/utils/hash';
import { verifyToken } from '../src/utils/jwt';

const JWT_SECRET = 'test-secret-key-for-unit-tests';

async function makeProvider() {
  const passwordHash = await hashPassword('correct-password');
  return new LocalProvider({
    jwtSecret: JWT_SECRET,
    tokenTtl: 3600,
    findUser: async (username: string) => {
      if (username === 'alice') {
        return { id: 'user-1', email: 'alice@example.com', name: 'Alice', passwordHash };
      }
      return null;
    },
  });
}

describe('LocalProvider', () => {
  it('returns success with valid credentials', async () => {
    const provider = await makeProvider();
    const result = await provider.authenticate({ username: 'alice', password: 'correct-password' });

    expect(result.success).toBe(true);
    expect(result.user?.email).toBe('alice@example.com');
    expect(result.user?.provider).toBe('local');
    expect(result.token).toBeDefined();
  });

  it('returns failure for wrong password', async () => {
    const provider = await makeProvider();
    const result = await provider.authenticate({ username: 'alice', password: 'wrong-password' });

    expect(result.success).toBe(false);
    expect(result.error).toBe('Invalid credentials');
    expect(result.token).toBeUndefined();
  });

  it('returns failure for unknown user', async () => {
    const provider = await makeProvider();
    const result = await provider.authenticate({ username: 'nobody', password: 'any' });

    expect(result.success).toBe(false);
    expect(result.error).toBe('Invalid credentials');
  });

  it('returns failure when credentials are missing', async () => {
    const provider = await makeProvider();
    const result = await provider.authenticate({});

    expect(result.success).toBe(false);
    expect(result.error).toMatch(/required/i);
  });

  it('issues a valid JWT on success', async () => {
    const provider = await makeProvider();
    const result = await provider.authenticate({ username: 'alice', password: 'correct-password' });

    expect(result.token).toBeDefined();
    const payload = await verifyToken(result.token!, JWT_SECRET);
    expect(payload.sub).toBe('user-1');
    expect(payload['email']).toBe('alice@example.com');
    expect(payload['provider']).toBe('local');
  });

  it('has provider name "local"', () => {
    const provider = new LocalProvider({
      jwtSecret: JWT_SECRET,
      findUser: async () => null,
    });
    expect(provider.name).toBe('local');
  });
});
