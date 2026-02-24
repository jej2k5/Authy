/**
 * Normalized user info returned by all providers.
 */
export interface UserInfo {
  id: string;
  email: string;
  name: string;
  provider: string;
  /** Raw profile data from the provider */
  raw?: Record<string, unknown>;
}

/**
 * Result returned from every authenticate() call.
 */
export interface AuthResult {
  success: boolean;
  user?: UserInfo;
  token?: string;
  refreshToken?: string;
  error?: string;
}

/**
 * Abstract interface all providers must implement.
 */
export interface AuthProvider {
  readonly name: string;
  authenticate(credentials: Record<string, unknown>): Promise<AuthResult>;
}

// ---------------------------------------------------------------------------
// Provider configurations
// ---------------------------------------------------------------------------

export interface LocalProviderConfig {
  /** JWT secret for signing tokens */
  jwtSecret: string;
  /** Token TTL in seconds (default: 3600) */
  tokenTtl?: number;
  /** Pluggable user lookup: return hashed password for username, or null */
  findUser: (username: string) => Promise<{ id: string; email: string; name: string; passwordHash: string } | null>;
}

export interface GoogleProviderConfig {
  clientId: string;
  clientSecret: string;
  redirectUri: string;
  jwtSecret: string;
  tokenTtl?: number;
}

export interface M365ProviderConfig {
  clientId: string;
  clientSecret: string;
  tenantId: string;
  redirectUri: string;
  jwtSecret: string;
  tokenTtl?: number;
}

export interface OidcSSOConfig {
  type: 'oidc';
  issuerUrl: string;
  clientId: string;
  clientSecret: string;
  redirectUri: string;
  jwtSecret: string;
  tokenTtl?: number;
}

export interface SamlSSOConfig {
  type: 'saml';
  /** Entity ID of this service provider */
  spEntityId: string;
  /** IdP SSO URL */
  idpSsoUrl: string;
  /** IdP certificate (PEM) */
  idpCert: string;
  /** SP private key (PEM) — optional, for signed requests */
  spPrivateKey?: string;
  jwtSecret: string;
  tokenTtl?: number;
}

export type SSOProviderConfig = OidcSSOConfig | SamlSSOConfig;
