import { Request, Response, NextFunction } from 'express';
import { AuthManager } from '@authy/core';

export interface AuthenticatedRequest extends Request {
  user?: Record<string, unknown>;
}

export function requireAuth(manager: AuthManager) {
  return async (req: AuthenticatedRequest, res: Response, next: NextFunction) => {
    // Accept token from httpOnly cookie or Authorization header
    const token =
      req.cookies?.token ??
      req.headers.authorization?.replace(/^Bearer\s+/i, '');

    if (!token) {
      return res.status(401).json({ error: 'Not authenticated' });
    }

    try {
      req.user = await manager.verifyToken(token) as Record<string, unknown>;
      next();
    } catch {
      res.status(401).json({ error: 'Invalid or expired token' });
    }
  };
}
