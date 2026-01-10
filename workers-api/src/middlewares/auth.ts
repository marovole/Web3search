/**
 * Authentication Middleware for Web3search API
 *
 * Provides two modes:
 * 1. Fast JWT verification (local, uses SUPABASE_JWT_SECRET)
 * 2. Safe verification (calls Supabase API, handles token revocation)
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
import { createClient } from '@supabase/supabase-js'
import type { Env } from '../types/env'

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
   * Use Supabase API to verify token (slower but handles revocation)
   * Default: false (use local JWT verification)
   */
  verifyWithSupabase?: boolean

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
 * Fast JWT verification middleware using Hono's built-in jwt middleware
 * Verifies token locally using SUPABASE_JWT_SECRET
 */
export function authMiddleware(options: AuthMiddlewareOptions = {}) {
  const { verifyWithSupabase = false, requiredPlans, optional = false } = options

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
      if (verifyWithSupabase) {
        // Safe verification: Call Supabase API
        await verifyWithSupabaseApi(c, token)
      } else {
        // Fast verification: Local JWT check
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

/**
 * Verify JWT locally using SUPABASE_JWT_SECRET
 * Fast but doesn't check for token revocation
 */
async function verifyLocalJwt(c: Context<{ Bindings: Env }>, token: string) {
  const secret = c.env.SUPABASE_JWT_SECRET
  if (!secret) {
    throw new Error('SUPABASE_JWT_SECRET is not configured')
  }

  // Use Hono's jwt verification
  const jwtMiddleware = jwt({ secret })

  // Create a mock next function to capture the result
  let verified = false
  const mockNext = async () => {
    verified = true
  }

  // Temporarily set the Authorization header for the jwt middleware
  await jwtMiddleware(c, mockNext)

  if (!verified) {
    throw new Error('JWT verification failed')
  }

  // Get the verified payload
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

  // Fetch user profile from Supabase to get plan info
  const supabase = createClient(c.env.SUPABASE_URL, c.env.SUPABASE_ANON_KEY, {
    global: { fetch: (...args) => fetch(...args) },
    auth: { persistSession: false },
  })

  const { data: profile } = await supabase
    .from('user_profiles')
    .select('username, plan')
    .eq('id', payload.sub)
    .single()

  // Set current user in context
  c.set('currentUser', {
    id: payload.sub,
    email: payload.email,
    username: profile?.username || payload.user_metadata?.username,
    plan: profile?.plan || 'free',
  })
}

/**
 * Verify token by calling Supabase Auth API
 * Slower but handles token revocation and user status changes
 */
async function verifyWithSupabaseApi(c: Context<{ Bindings: Env }>, token: string) {
  const supabase = createClient(c.env.SUPABASE_URL, c.env.SUPABASE_ANON_KEY, {
    global: { fetch: (...args) => fetch(...args) },
    auth: { persistSession: false },
  })

  // Verify token with Supabase Auth
  const {
    data: { user },
    error,
  } = await supabase.auth.getUser(token)

  if (error || !user) {
    throw new Error(error?.message || 'Invalid token')
  }

  // Fetch user profile for plan info
  const { data: profile } = await supabase
    .from('user_profiles')
    .select('username, plan')
    .eq('id', user.id)
    .single()

  // Set current user in context
  c.set('currentUser', {
    id: user.id,
    email: user.email,
    username: profile?.username || user.user_metadata?.username,
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
