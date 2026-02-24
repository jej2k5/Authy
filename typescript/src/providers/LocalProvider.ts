import { type AuthProvider, type AuthResult, type LocalProviderConfig } from '../types.js';
import { verifyPassword } from '../utils/hash.js';
import { signToken } from '../utils/jwt.js';

export interface LocalCredentials {
  username: string;
  password: string;
}

export class LocalProvider implements AuthProvider {
  readonly name = 'local';
  private config: LocalProviderConfig;

  constructor(config: LocalProviderConfig) {
    this.config = config;
  }

  async authenticate(credentials: Record<string, unknown>): Promise<AuthResult> {
    const { username, password } = credentials as unknown as LocalCredentials;

    if (!username || !password) {
      return { success: false, error: 'Username and password are required' };
    }

    try {
      const user = await this.config.findUser(username);
      if (!user) {
        return { success: false, error: 'Invalid credentials' };
      }

      const valid = await verifyPassword(password, user.passwordHash);
      if (!valid) {
        return { success: false, error: 'Invalid credentials' };
      }

      const userInfo = { id: user.id, email: user.email, name: user.name, provider: this.name };
      const token = await signToken(
        { sub: user.id, email: user.email, name: user.name, provider: this.name },
        this.config.jwtSecret,
        this.config.tokenTtl,
      );

      return { success: true, user: userInfo, token };
    } catch (err) {
      return { success: false, error: `Authentication error: ${(err as Error).message}` };
    }
  }
}
