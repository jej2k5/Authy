import { M365Provider } from '../src/providers/M365Provider';

const JWT_SECRET = 'test-secret-key';

const mockConfig = {
  clientId: 'mock-client-id',
  clientSecret: 'mock-client-secret',
  tenantId: 'mock-tenant-id',
  redirectUri: 'http://localhost:3000/auth/m365/callback',
  jwtSecret: JWT_SECRET,
};

jest.mock('openid-client', () => {
  const mockClient = {
    authorizationUrl: jest.fn().mockReturnValue('https://login.microsoftonline.com/mock-tenant/oauth2/v2.0/authorize?mock=1'),
    callback: jest.fn().mockResolvedValue({
      refresh_token: 'mock-refresh-token',
      claims: () => ({
        sub: 'm365-user-456',
        email: 'user@company.com',
        preferred_username: 'user@company.com',
        name: 'M365 User',
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

describe('M365Provider', () => {
  it('has provider name "m365"', () => {
    const provider = new M365Provider(mockConfig);
    expect(provider.name).toBe('m365');
  });

  it('getAuthUrl returns a meta token', async () => {
    const provider = new M365Provider(mockConfig);
    const result = await provider.authenticate({ action: 'getAuthUrl' });

    expect(result.success).toBe(true);
    expect(result.token).toBeDefined();
  });

  it('callback returns user info, token, and refresh token', async () => {
    const provider = new M365Provider(mockConfig);
    const result = await provider.authenticate({
      action: 'callback',
      code: 'auth-code',
      state: 'mock-state',
      codeVerifier: 'mock-code-verifier',
    });

    expect(result.success).toBe(true);
    expect(result.user?.email).toBe('user@company.com');
    expect(result.user?.provider).toBe('m365');
    expect(result.token).toBeDefined();
    expect(result.refreshToken).toBe('mock-refresh-token');
  });

  it('returns error for unknown action', async () => {
    const provider = new M365Provider(mockConfig);
    const result = await provider.authenticate({ action: 'bad' });

    expect(result.success).toBe(false);
    expect(result.error).toMatch(/unknown action/i);
  });
});
