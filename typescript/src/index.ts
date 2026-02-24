export { AuthManager } from './AuthManager.js';
export { LocalProvider } from './providers/LocalProvider.js';
export { GoogleProvider } from './providers/GoogleProvider.js';
export { M365Provider } from './providers/M365Provider.js';
export { SSOProvider } from './providers/SSOProvider.js';
export { signToken, verifyToken } from './utils/jwt.js';
export { hashPassword, verifyPassword } from './utils/hash.js';
export type {
  AuthProvider,
  AuthResult,
  UserInfo,
  LocalProviderConfig,
  GoogleProviderConfig,
  M365ProviderConfig,
  SSOProviderConfig,
  OidcSSOConfig,
  SamlSSOConfig,
} from './types.js';
