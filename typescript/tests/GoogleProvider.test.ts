import { GoogleProvider } from '../src/providers/GoogleProvider';

const JWT_SECRET = 'test-secret-key';

const mockConfig = {
  clientId: 'mock-client-id',
  clientSecret: 'mock-client-secret',
  redirectUri: 'http://localhost:3000/auth/google/callback',
  jwtSecret: JWT_SECRET,
};

// Mock openid-client to avoid real network calls
jest.mock('openid-client', () => {
  const mockClient = {
    authorizationUrl: jest.fn().mockReturnValue('https://accounts.google.com/o/oauth2/auth?mock=1'),
    callback: jest.fn().mockResolvedValue({
      claims: () => ({
        sub: 'google-user-123',
        email: 'user@gmail.com',
        name: 'Google User',
      }),
    }),
  };
  return {
    Issuer: {
      discover: jest.fn().mockResolvedValue({
        Client: jest.fn().mockImplementation(() => mockClient),
      }),
    },
    generators: {
      codeVerifier: jest.fn().mockReturnValue('mock-code-verifier'),
      codeChallenge: jest.fn().mockReturnValue('mock-code-challenge'),
      state: jest.fn().mockReturnValue('mock-state'),
    },
  };
});

describe('GoogleProvider', () => {
  it('has provider name "google"', () => {
    const provider = new GoogleProvider(mockConfig);
    expect(provider.name).toBe('google');
  });

  it('getAuthUrl returns a meta token containing authUrl', async () => {
    const provider = new GoogleProvider(mockConfig);
    const result = await provider.authenticate({ action: 'getAuthUrl' });

    expect(result.success).toBe(true);
    expect(result.token).toBeDefined();
  });

  it('callback returns user info and token', async () => {
    const provider = new GoogleProvider(mockConfig);
    const result = await provider.authenticate({
      action: 'callback',
      code: 'auth-code',
      state: 'mock-state',
      codeVerifier: 'mock-code-verifier',
    });

    expect(result.success).toBe(true);
    expect(result.user?.email).toBe('user@gmail.com');
    expect(result.user?.provider).toBe('google');
    expect(result.token).toBeDefined();
  });

  it('returns error for unknown action', async () => {
    const provider = new GoogleProvider(mockConfig);
    const result = await provider.authenticate({ action: 'unknown' });

    expect(result.success).toBe(false);
    expect(result.error).toMatch(/unknown action/i);
  });
});
