import { SignJWT, jwtVerify, type JWTPayload } from 'jose';

const DEFAULT_TTL = 3600; // 1 hour

export async function signToken(
  payload: Record<string, unknown>,
  secret: string,
  ttlSeconds = DEFAULT_TTL,
): Promise<string> {
  const key = new TextEncoder().encode(secret);
  return new SignJWT(payload)
    .setProtectedHeader({ alg: 'HS256' })
    .setIssuedAt()
    .setExpirationTime(`${ttlSeconds}s`)
    .sign(key);
}

export async function verifyToken(
  token: string,
  secret: string,
): Promise<JWTPayload> {
  const key = new TextEncoder().encode(secret);
  const { payload } = await jwtVerify(token, key);
  return payload;
}
