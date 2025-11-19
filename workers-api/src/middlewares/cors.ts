/**
 * CORS Middleware
 * Handle Cross-Origin Resource Sharing
 */

import { Context, Next } from 'hono'
import type { Env } from '../types/env'

// Allowed origins for CORS
const ALLOWED_ORIGINS = [
  'https://lulaai.xyz', // Production domain
  'https://web3search.pages.dev', // Cloudflare Pages production
  'http://localhost:5173', // Local development (Vite default)
  'http://localhost:3000', // Alternative local port
]

export async function corsMiddleware(c: Context<{ Bindings: Env }>, next: Next) {
  const origin = c.req.header('origin') || ''

  // Check if origin is allowed
  const isAllowedOrigin =
    ALLOWED_ORIGINS.includes(origin) ||
    origin.endsWith('.lulaai.xyz') || // Allow subdomains
    origin.endsWith('.web3search.pages.dev') || // Allow preview deployments
    (c.env.ENVIRONMENT === 'development' && origin.startsWith('http://localhost'))

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
