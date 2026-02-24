import { Issuer, type BaseClient, generators } from 'openid-client';
import { ServiceProvider, IdentityProvider, setSchemaValidator } from 'samlify';
import { type AuthProvider, type AuthResult, type SSOProviderConfig, type UserInfo } from '../types.js';
import { signToken } from '../utils/jwt.js';

// Disable XML schema validation (validator must be set externally for production)
setSchemaValidator({ validate: async () => Promise.resolve('') });

/**
 * Generic SSO provider supporting OIDC and SAML 2.0.
 *
 * OIDC flow (same two-step as Google/M365):
 *   Step 1: credentials = { action: 'getAuthUrl' }
 *   Step 2: credentials = { action: 'callback', code, state, codeVerifier }
 *
 * SAML flow:
 *   Step 1: credentials = { action: 'getLoginUrl' }  → returns redirect URL
 *   Step 2: credentials = { action: 'callback', samlResponse }  → parses assertion
 */
export class SSOProvider implements AuthProvider {
  readonly name = 'sso';
  private config: SSOProviderConfig;
  private oidcClient?: BaseClient;

  constructor(config: SSOProviderConfig) {
    this.config = config;
  }

  async authenticate(credentials: Record<string, unknown>): Promise<AuthResult> {
    try {
      if (this.config.type === 'oidc') {
        return this.handleOidc(credentials);
      }
      return this.handleSaml(credentials);
    } catch (err) {
      return { success: false, error: `SSO error: ${(err as Error).message}` };
    }
  }

  // ---------------------------------------------------------------------------
  // OIDC
  // ---------------------------------------------------------------------------

  private async getOidcClient(): Promise<BaseClient> {
    if (!this.oidcClient) {
      if (this.config.type !== 'oidc') throw new Error('Not OIDC config');
      const issuer = await Issuer.discover(this.config.issuerUrl);
      this.oidcClient = new issuer.Client({
        client_id: this.config.clientId,
        client_secret: this.config.clientSecret,
        redirect_uris: [this.config.redirectUri],
        response_types: ['code'],
      });
    }
    return this.oidcClient;
  }

  private async handleOidc(credentials: Record<string, unknown>): Promise<AuthResult> {
    if (this.config.type !== 'oidc') return { success: false, error: 'OIDC config required' };
    const action = credentials['action'] as string;

    if (action === 'getAuthUrl') {
      const client = await this.getOidcClient();
      const codeVerifier = generators.codeVerifier();
      const codeChallenge = generators.codeChallenge(codeVerifier);
      const state = generators.state();

      const authUrl = client.authorizationUrl({
        scope: 'openid email profile',
        state,
        code_challenge: codeChallenge,
        code_challenge_method: 'S256',
      });

      const metaToken = await signToken(
        { authUrl, codeVerifier, state, type: 'oauth_meta' },
        this.config.jwtSecret,
        300,
      );
      return { success: true, token: metaToken };
    }

    if (action === 'callback') {
      const { code, state, codeVerifier } = credentials as {
        code: string; state: string; codeVerifier: string;
      };
      const client = await this.getOidcClient();
      const tokenSet = await client.callback(this.config.redirectUri, { code, state }, {
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

    return { success: false, error: 'Unknown OIDC action' };
  }

  // ---------------------------------------------------------------------------
  // SAML 2.0
  // ---------------------------------------------------------------------------

  private async handleSaml(credentials: Record<string, unknown>): Promise<AuthResult> {
    if (this.config.type !== 'saml') return { success: false, error: 'SAML config required' };
    const action = credentials['action'] as string;

    const sp = ServiceProvider({
      entityID: this.config.spEntityId,
      signingCert: this.config.spPrivateKey,
    });

    const idp = IdentityProvider({
      entityID: this.config.idpSsoUrl,
      singleSignOnService: [{ Binding: 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect', Location: this.config.idpSsoUrl }],
      signingCert: this.config.idpCert,
    });

    if (action === 'getLoginUrl') {
      const { context } = sp.createLoginRequest(idp, 'redirect');
      return { success: true, token: context };
    }

    if (action === 'callback') {
      const samlResponse = credentials['samlResponse'] as string;
      const parseResult = await sp.parseLoginResponse(idp, 'post', {
        body: { SAMLResponse: samlResponse },
      });

      const attrs = parseResult.extract.attributes as Record<string, string>;
      const nameId = parseResult.extract.nameID as string;

      const userInfo: UserInfo = {
        id: nameId,
        email: attrs['email'] ?? attrs['http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress'] ?? '',
        name: attrs['displayName'] ?? attrs['http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name'] ?? '',
        provider: this.name,
        raw: attrs,
      };

      const token = await signToken(
        { sub: userInfo.id, email: userInfo.email, name: userInfo.name, provider: this.name },
        this.config.jwtSecret,
        this.config.tokenTtl,
      );
      return { success: true, user: userInfo, token };
    }

    return { success: false, error: 'Unknown SAML action' };
  }
}
