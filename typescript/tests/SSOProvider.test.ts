import { SSOProvider } from '../src/providers/SSOProvider';

const JWT_SECRET = 'test-secret-key';

const oidcConfig = {
  type: 'oidc' as const,
  issuerUrl: 'https://sso.example.com',
  clientId: 'mock-client-id',
  clientSecret: 'mock-client-secret',
  redirectUri: 'http://localhost:3000/auth/sso/callback',
  jwtSecret: JWT_SECRET,
};

jest.mock('openid-client', () => {
  const mockClient = {
    authorizationUrl: jest.fn().mockReturnValue('https://sso.example.com/auth?mock=1'),
    callback: jest.fn().mockResolvedValue({
      claims: () => ({
        sub: 'sso-user-789',
        email: 'user@sso.example.com',
        name: 'SSO User',
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

jest.mock('samlify', () => {
  const mockSp = {
    createLoginRequest: jest.fn().mockReturnValue({ context: 'https://idp.example.com/sso?SAMLRequest=mock' }),
    parseLoginResponse: jest.fn().mockResolvedValue({
      extract: {
        nameID: 'saml-user-111',
        attributes: {
          email: 'saml@example.com',
          displayName: 'SAML User',
        },
      },
    }),
  };
  return {
    ServiceProvider: jest.fn().mockReturnValue(mockSp),
    IdentityProvider: jest.fn().mockReturnValue({}),
    setSchemaValidator: jest.fn(),
  };
});

describe('SSOProvider (OIDC)', () => {
  it('has provider name "sso"', () => {
    const provider = new SSOProvider(oidcConfig);
    expect(provider.name).toBe('sso');
  });

  it('getAuthUrl returns meta token', async () => {
    const provider = new SSOProvider(oidcConfig);
    const result = await provider.authenticate({ action: 'getAuthUrl' });

    expect(result.success).toBe(true);
    expect(result.token).toBeDefined();
  });

  it('callback returns user info', async () => {
    const provider = new SSOProvider(oidcConfig);
    const result = await provider.authenticate({
      action: 'callback',
      code: 'code',
      state: 'mock-state',
      codeVerifier: 'mock-code-verifier',
    });

    expect(result.success).toBe(true);
    expect(result.user?.email).toBe('user@sso.example.com');
    expect(result.user?.provider).toBe('sso');
  });
});

describe('SSOProvider (SAML)', () => {
  const samlConfig = {
    type: 'saml' as const,
    spEntityId: 'urn:example:sp',
    idpSsoUrl: 'https://idp.example.com/sso',
    idpCert: 'MOCK_CERT',
    jwtSecret: JWT_SECRET,
  };

  it('getLoginUrl returns redirect URL', async () => {
    const provider = new SSOProvider(samlConfig);
    const result = await provider.authenticate({ action: 'getLoginUrl' });

    expect(result.success).toBe(true);
    expect(result.token).toContain('idp.example.com');
  });

  it('callback parses SAML response and returns user info', async () => {
    const provider = new SSOProvider(samlConfig);
    const result = await provider.authenticate({
      action: 'callback',
      samlResponse: 'BASE64_SAML_RESPONSE',
    });

    expect(result.success).toBe(true);
    expect(result.user?.email).toBe('saml@example.com');
    expect(result.user?.name).toBe('SAML User');
    expect(result.user?.id).toBe('saml-user-111');
  });
});
