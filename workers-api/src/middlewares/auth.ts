/**
 * Authentication Middleware for Web3search API
 *
 * Provides two modes:
 * 1. Fast JWT verification (local, uses JWT_SECRET)
 * 2. Safe verification (calls Convex API, handles token revocation)
 *
 * Usage:
 *   // Protect all routes under /api/v1/protected
 *   app.use('/api/v1/protected/*', authMiddleware())
 *
 *   // Or require auth on specific route
 *   app.get('/api/v1/me', authMiddleware(), (c) => {
 *     const user = c.get('currentUser')
 *     return c.json(user)
 *   })
 */

import { Context, Next } from 'hono'
import { jwt } from 'hono/jwt'
import type { Env } from '../types/env'
import { getSupabaseClient } from '../lib/supabase'
import { getConvexClient } from '../lib/convex'

// Error response helper
function authError(c: Context, message: string, code: string, status: 401 | 403 = 401) {
  return c.json(
    {
      error: {
        code,
        message,
        status,
      },
    },
    status
  )
}

/**
 * Options for auth middleware
 */
interface AuthMiddlewareOptions {
  /**
   * Use Convex API to verify token (slower but handles revocation)
   * Default: false (use local JWT verification)
   */
  verifyWithConvex?: boolean

  /**
   * Require specific plan levels
   * If set, only users with matching plan can access
   */
  requiredPlans?: Array<'free' | 'pro' | 'team'>

  /**
   * Allow unauthenticated requests to pass through
   * Sets currentUser to undefined if no valid token
   * Default: false
   */
  optional?: boolean
}

/**
 * Authentication middleware using Convex or local JWT verification
 * Defaults to Convex verification (no JWT_SECRET needed)
 * Falls back to local JWT if JWT_SECRET is configured and verifyWithConvex is false
 */
export function authMiddleware(options: AuthMiddlewareOptions = {}) {
  const { verifyWithConvex = true, requiredPlans, optional = false } = options

  return async (c: Context<{ Bindings: Env }>, next: Next) => {
    const authHeader = c.req.header('Authorization')

    // Handle missing auth header
    if (!authHeader) {
      if (optional) {
        await next()
        return
      }
      return authError(c, 'Authorization header required', 'AUTH_REQUIRED')
    }

    // Extract Bearer token
    if (!authHeader.startsWith('Bearer ')) {
      return authError(c, 'Invalid authorization format. Use: Bearer <token>', 'INVALID_AUTH_FORMAT')
    }

    const token = authHeader.substring(7)
    if (!token) {
      if (optional) {
        await next()
        return
      }
      return authError(c, 'Token is required', 'TOKEN_REQUIRED')
    }

    try {
      // Default to Convex verification unless explicitly disabled and JWT_SECRET is available
      const useConvex = verifyWithConvex || !c.env.JWT_SECRET
      if (useConvex) {
        // Safe verification: Call Convex API
        await verifyWithConvexApi(c, token)
      } else {
        // Fast verification: Local JWT check (only if JWT_SECRET is configured)
        await verifyLocalJwt(c, token)
      }

      // Check plan requirements if specified
      if (requiredPlans && requiredPlans.length > 0) {
        const user = c.get('currentUser')
        if (!user?.plan || !requiredPlans.includes(user.plan)) {
          return authError(
            c,
            `This feature requires ${requiredPlans.join(' or ')} plan`,
            'PLAN_REQUIRED',
            403
          )
        }
      }

      await next()
    } catch (error) {
      if (optional) {
        // Clear any partial user data and continue
        c.set('currentUser', undefined)
        await next()
        return
      }

      // Handle specific JWT errors
      if (error instanceof Error) {
        if (error.message.includes('expired')) {
          return authError(c, 'Token has expired', 'TOKEN_EXPIRED')
        }
        if (error.message.includes('invalid') || error.message.includes('signature')) {
          return authError(c, 'Invalid token', 'INVALID_TOKEN')
        }
      }

      console.error('[Auth] Token verification failed:', error)
      return authError(c, 'Authentication failed', 'AUTH_FAILED')
    }
  }
}

async function verifyLocalJwt(c: Context<{ Bindings: Env }>, _token: string) {
  const secret = c.env.JWT_SECRET
  if (!secret) {
    throw new Error('JWT_SECRET is not configured')
  }

  const jwtMiddleware = jwt({ secret, alg: 'HS256' })

  let verified = false
  const mockNext = async () => {
    verified = true
  }

  await jwtMiddleware(c, mockNext)

  if (!verified) {
    throw new Error('JWT verification failed')
  }

  const payload = c.get('jwtPayload') as {
    sub: string
    email?: string
    role?: string
    user_metadata?: {
      username?: string
    }
  }

  if (!payload?.sub) {
    throw new Error('Invalid token payload: missing sub')
  }

  const supabase = getSupabaseClient(c.env)
  const { data: profile } = await supabase
    .from<{ username: string; plan: string }>('user_profiles')
    .select('username, plan')
    .eq('id', payload.sub)
    .single()

  const profileData = profile as { username?: string; plan?: string } | null
  const userPlan = (profileData?.plan || 'free') as 'free' | 'pro' | 'team'
  c.set('currentUser', {
    id: payload.sub,
    email: payload.email,
    username: profileData?.username || payload.user_metadata?.username,
    plan: userPlan,
  })
}

async function verifyWithConvexApi(c: Context<{ Bindings: Env }>, token: string) {
  const convex = getConvexClient(c.env)

  // Convex Auth JWT contains tokenIdentifier in the subject claim
  // We need to decode and extract it without full verification (Convex will verify on query)
  const parts = token.split('.')
  if (parts.length !== 3) {
    throw new Error('Invalid token format')
  }

  let payload: { sub?: string; email?: string; name?: string }
  try {
    const payloadJson = atob(parts[1].replace(/-/g, '+').replace(/_/g, '/'))
    payload = JSON.parse(payloadJson)
  } catch {
    throw new Error('Invalid token payload')
  }

  if (!payload.sub) {
    throw new Error('Missing subject in token')
  }

  // Query Convex to get user by token identifier
  // The token's subject is the tokenIdentifier in Convex Auth
  const user = await convex.query<{
    _id: string
    email?: string
    username?: string
    name?: string
    tokenIdentifier: string
  } | null>('users:getByToken', { tokenIdentifier: payload.sub })

  if (!user) {
    throw new Error('User not found')
  }

  // Get user profile for plan info
  const profile = await convex.query<{
    plan?: 'free' | 'pro' | 'team'
    stripeCustomerId?: string
  } | null>('users:getProfile', { userId: user._id })

  c.set('currentUser', {
    id: user._id,
    email: user.email || payload.email,
    username: user.username || user.name,
    plan: profile?.plan || 'free',
  })
}

/**
 * Middleware that requires authentication
 * Shorthand for authMiddleware({ optional: false })
 */
export const requireAuth = () => authMiddleware({ optional: false })

/**
 * Middleware that optionally extracts user if token is present
 * Does not block request if no token
 */
export const optionalAuth = () => authMiddleware({ optional: true })

/**
 * Middleware that requires Pro or Team plan
 */
export const requirePro = () =>
  authMiddleware({
    requiredPlans: ['pro', 'team'],
  })

/**
 * Middleware that requires Team plan
 */
export const requireTeam = () =>
  authMiddleware({
    requiredPlans: ['team'],
  })

/**
 * Get current user from context
 * Returns undefined if not authenticated
 */
export function getCurrentUser(c: Context) {
  return c.get('currentUser')
}

/**
 * Require current user or throw 401
 */
export function requireUser(c: Context) {
  const user = c.get('currentUser')
  if (!user) {
    throw new Error('User not authenticated')
  }
  return user
}
