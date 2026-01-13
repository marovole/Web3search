/**
 * CORS Middleware
 * Handle Cross-Origin Resource Sharing
 */

import { Context, Next } from 'hono'
import type { Env } from '../types/env'

// Allowed origins for CORS
const ALLOWED_ORIGINS = [
  'https://lulaai.xyz', // Production domain
  'https://www.lulaai.xyz', // Production domain with www
  'https://web3search.pages.dev', // Cloudflare Pages production
  'http://localhost:5173', // Local development (Vite default)
  'http://localhost:3000', // Alternative local port
]

// Debug log for CORS issues
const DEBUG_CORS = false

export async function corsMiddleware(c: Context<{ Bindings: Env }>, next: Next) {
  const origin = c.req.header('origin') || ''
  const isProduction = c.env.ENVIRONMENT === 'production'

  // Check if origin is allowed
  const isAllowedOrigin =
    ALLOWED_ORIGINS.includes(origin) ||
    origin.endsWith('.lulaai.xyz') || // Allow subdomains
    origin.endsWith('.web3search.pages.dev') || // Allow preview deployments
    (origin.startsWith('http://localhost') && !isProduction) // Allow localhost only in non-production

  // Block localhost in production
  if (isProduction && origin.startsWith('http://localhost')) {
    return c.text('Forbidden', 403)
  }

  if (DEBUG_CORS) {
    console.log(`[CORS] Origin: ${origin}, Allowed: ${isAllowedOrigin}, Production: ${isProduction}`)
  }

  // Handle preflight requests
  if (c.req.method === 'OPTIONS') {
    if (isAllowedOrigin) {
      return c.newResponse(null, {
        status: 204,
        headers: {
          'Access-Control-Allow-Origin': origin,
          'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type, Authorization',
          'Access-Control-Max-Age': '86400', // 24 hours
          'Access-Control-Allow-Credentials': 'true',
        },
      })
    } else {
      return c.text('Forbidden', 403)
    }
  }

  // Execute request
  await next()

  // Add CORS headers to response
  if (isAllowedOrigin) {
    c.res.headers.set('Access-Control-Allow-Origin', origin)
    c.res.headers.set('Access-Control-Allow-Credentials', 'true')
  }
}
