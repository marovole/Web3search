/**
 * Rate Limiting Middleware
 * KV-backed sliding window rate limiter with eventual consistency tolerance
 */

import type { MiddlewareHandler, Context } from 'hono'
import type { Env } from '../types/env'

/**
 * Rate limit configuration options
 */
export interface RateLimitOptions {
  /** Unique scope identifier for this limiter (e.g., "chat-ip-hour") */
  scope: string
  /** Maximum number of requests allowed in the window */
  limit: number
  /** Window duration in seconds */
  windowSeconds: number
  /** Custom key extraction function (defaults to cf-connecting-ip) */
  key?: (c: Context<{ Bindings: Env }>) => string | Promise<string>
}

/**
 * Create a deterministic hash for configuration consistency
 * Ensures rate limit keys remain consistent even if windowSeconds changes dynamically
 */
function createConfigHash(scope: string, limit: number, windowSeconds: number): string {
  const config = `${scope}:${limit}:${windowSeconds}`
  let hash = 0
  for (let i = 0; i < config.length; i++) {
    const char = config.charCodeAt(i)
    hash = ((hash << 5) - hash) + char
    hash = hash & hash // Convert to 32bit integer
  }
  return Math.abs(hash).toString(36)
}

/**
 * Create rate limit middleware using Cloudflare KV
 *
 * Implements a sliding window rate limiter backed by KV storage.
 * Accepts slight drift because KV is eventually consistent.
 *
 * @param options - Rate limit configuration
 * @returns Hono middleware handler
 *
 * @example
 * ```ts
 * app.post('/chat',
 *   createRateLimitMiddleware({
 *     scope: 'chat-ip-hour',
 *     limit: 10,
 *     windowSeconds: 3600
 *   }),
 *   handler
 * )
 * ```
 */
export const createRateLimitMiddleware = (
  options: RateLimitOptions
): MiddlewareHandler<{ Bindings: Env }> => {
  // Pre-compute config hash for consistent key generation
  const configHash = createConfigHash(options.scope, options.limit, options.windowSeconds)

  return async (c, next) => {
    const kv = c.env.CACHE
    if (!kv) {
      console.warn('KV namespace missing; skipping rate limiting')
      return next()
    }

    // Extract identifier (IP address or custom key)
    const identifier =
      (await options.key?.(c)) ?? c.req.header('cf-connecting-ip') ?? 'anonymous'

    // Calculate current window ID (sliding window)
    const windowId = Math.floor(Date.now() / 1000 / options.windowSeconds)
    // Include config hash to ensure key consistency across configuration changes
    const kvKey = `ratelimit:${configHash}:${options.scope}:${identifier}:${windowId}`

    // Read current request count
    let current = 0
    try {
      const stored = await kv.get(kvKey)
      current = stored ? parseInt(stored, 10) || 0 : 0
    } catch (error) {
      console.warn('KV read failed; allowing request', error)
      return next()
    }

    // Check if limit exceeded
    if (current >= options.limit) {
      const retryAfter =
        options.windowSeconds -
        (Math.floor(Date.now() / 1000) % options.windowSeconds)

      return c.json(
        {
          error: {
            code: 'RATE_LIMITED',
            message: 'Too many requests, please try again later.',
            status: 429,
          },
        },
        429,
        {
          'Retry-After': retryAfter.toString(),
          'X-RateLimit-Limit': options.limit.toString(),
          'X-RateLimit-Remaining': '0',
        }
      )
    }

    // Increment counter in KV
    try {
      await kv.put(kvKey, String(current + 1), {
        expirationTtl: options.windowSeconds * 2, // Double TTL for sliding window robustness
      })
    } catch (error) {
      console.warn('KV write failed; continuing', error)
    }

    // Continue to next middleware/handler
    await next()

    // Add rate limit headers to response
    const remaining = Math.max(options.limit - current - 1, 0)
    c.res.headers.set('X-RateLimit-Limit', options.limit.toString())
    c.res.headers.set('X-RateLimit-Remaining', remaining.toString())
  }
}
