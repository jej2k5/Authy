import { type AuthProvider, type AuthResult } from './types.js';
import { verifyToken } from './utils/jwt.js';
import { type JWTPayload } from 'jose';

export class AuthManager {
  private providers = new Map<string, AuthProvider>();
  private jwtSecret: string;

  constructor(jwtSecret: string) {
    this.jwtSecret = jwtSecret;
  }

  /** Register a provider under a given name (defaults to provider.name) */
  register(provider: AuthProvider, alias?: string): this {
    const key = alias ?? provider.name;
    this.providers.set(key, provider);
    return this;
  }

  /** Authenticate using a named provider */
  async authenticate(
    providerName: string,
    credentials: Record<string, unknown>,
  ): Promise<AuthResult> {
    const provider = this.providers.get(providerName);
    if (!provider) {
      return { success: false, error: `Unknown provider: ${providerName}` };
    }
    return provider.authenticate(credentials);
  }

  /** Verify a JWT issued by this framework */
  async verifyToken(token: string): Promise<JWTPayload> {
    return verifyToken(token, this.jwtSecret);
  }

  /** List registered provider names */
  listProviders(): string[] {
    return Array.from(this.providers.keys());
  }
}
