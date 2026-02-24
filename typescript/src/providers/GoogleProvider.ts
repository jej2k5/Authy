import { Issuer, type BaseClient, generators } from 'openid-client';
import { type AuthProvider, type AuthResult, type GoogleProviderConfig, type UserInfo } from '../types.js';
import { signToken } from '../utils/jwt.js';

/**
 * Credentials for the redirect-based OAuth flow.
 *
 * Step 1 — get authorization URL:
 *   credentials = { action: 'getAuthUrl' }
 *   returns AuthResult with token containing { authUrl, codeVerifier, state }
 *
 * Step 2 — exchange code:
 *   credentials = { action: 'callback', code, state, codeVerifier }
 *   returns AuthResult with user + token
 */
export class GoogleProvider implements AuthProvider {
  readonly name = 'google';
  private config: GoogleProviderConfig;
  private client?: BaseClient;

  constructor(config: GoogleProviderConfig) {
    this.config = config;
  }

  private async getClient(): Promise<BaseClient> {
    if (!this.client) {
      const issuer = await Issuer.discover('https://accounts.google.com');
      this.client = new issuer.Client({
        client_id: this.config.clientId,
        client_secret: this.config.clientSecret,
        redirect_uris: [this.config.redirectUri],
        response_types: ['code'],
      });
    }
    return this.client;
  }

  async authenticate(credentials: Record<string, unknown>): Promise<AuthResult> {
    const action = credentials['action'] as string;

    try {
      if (action === 'getAuthUrl') {
        return this.getAuthUrl();
      }
      if (action === 'callback') {
        return this.handleCallback(credentials);
      }
      return { success: false, error: 'Unknown action. Use "getAuthUrl" or "callback"' };
    } catch (err) {
      return { success: false, error: `Google auth error: ${(err as Error).message}` };
    }
  }

  private async getAuthUrl(): Promise<AuthResult> {
    const client = await this.getClient();
    const codeVerifier = generators.codeVerifier();
    const codeChallenge = generators.codeChallenge(codeVerifier);
    const state = generators.state();

    const authUrl = client.authorizationUrl({
      scope: 'openid email profile',
      state,
      code_challenge: codeChallenge,
      code_challenge_method: 'S256',
    });

    // Return auth URL metadata as a short-lived token the caller stores temporarily
    const metaToken = await signToken(
      { authUrl, codeVerifier, state, type: 'oauth_meta' },
      this.config.jwtSecret,
      300, // 5 minutes
    );

    return { success: true, token: metaToken };
  }

  private async handleCallback(credentials: Record<string, unknown>): Promise<AuthResult> {
    const { code, state, codeVerifier } = credentials as {
      code: string;
      state: string;
      codeVerifier: string;
    };

    const client = await this.getClient();
    const params = { code, state };
    const tokenSet = await client.callback(this.config.redirectUri, params, {
      code_verifier: codeVerifier,
      state,
    });

    const claims = tokenSet.claims();
    const userInfo: UserInfo = {
      id: claims.sub,
      email: (claims['email'] as string) ?? '',
      name: (claims['name'] as string) ?? '',
      provider: this.name,
      raw: claims as Record<string, unknown>,
    };

    const token = await signToken(
      { sub: userInfo.id, email: userInfo.email, name: userInfo.name, provider: this.name },
      this.config.jwtSecret,
      this.config.tokenTtl,
    );

    return { success: true, user: userInfo, token };
  }
}
