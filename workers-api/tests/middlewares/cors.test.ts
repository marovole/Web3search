/**
 * Tests for CORS Middleware
 * Validates Cross-Origin Resource Sharing behavior across different scenarios
 */

import { describe, expect, it } from 'vitest'
import { Hono } from 'hono'
import { corsMiddleware } from '../../src/middlewares/cors'
import type { Env } from '../../src/types/env'

// ============================================
// Test Setup
// ============================================

/**
 * Create a minimal test app with CORS middleware
 * This mimics the production middleware stack
 */
const corsApp = new Hono<{ Bindings: Env }>()
corsApp.use('*', corsMiddleware)
corsApp.get('/resource', (c) => c.json({ ok: true }))

const BASE_URL = 'https://example.com/resource'

/**
 * Helper to send CORS-enabled requests with various origins
 */
async function sendCorsRequest({
  method = 'GET',
  origin,
  env,
}: {
  method?: string
  origin?: string
  env?: Env
} = {}) {
  const headers: Record<string, string> = {}
  if (origin) {
    headers.Origin = origin
  }

  const request = new Request(BASE_URL, {
    method,
    headers,
  })

  return corsApp.fetch(request, env ?? createMockEnv())
}

/**
 * Create a mock environment for testing
 */
function createMockEnv(overrides: Partial<Env> = {}): Env {
  return {
    ENVIRONMENT: 'production',
    SUPABASE_URL: 'https://example.supabase.co',
    SUPABASE_ANON_KEY: 'anon-key',
    OPENROUTER_API_KEY: 'test-key',
    CACHE: createInMemoryKV(),
    ...overrides,
  }
}

/**
 * Create an in-memory KV store for testing
 */
function createInMemoryKV(): KVNamespace {
  const store = new Map<string, string>()
  return {
    get: async (key: string) => (store.has(key) ? store.get(key)! : null),
    put: async (key: string, value: string) => {
      store.set(key, value)
    },
    delete: async (key: string) => {
      store.delete(key)
    },
    list: async () => ({
      keys: [],
      list_complete: true,
    }),
  } as unknown as KVNamespace
}

// ============================================
// CORS Middleware Tests
// ============================================

describe('corsMiddleware', () => {
  describe('Preflight Requests (OPTIONS)', () => {
    it('responds 204 with CORS headers for allowed production origin', async () => {
      const response = await sendCorsRequest({
        method: 'OPTIONS',
        origin: 'https://web3search.pages.dev',
      })

      expect(response.status).toBe(204)
      expect(response.headers.get('Access-Control-Allow-Origin')).toBe(
        'https://web3search.pages.dev'
      )
      expect(response.headers.get('Access-Control-Allow-Methods')).toContain('GET')
      expect(response.headers.get('Access-Control-Allow-Headers')).toContain(
        'Content-Type'
      )
      expect(response.headers.get('Access-Control-Allow-Credentials')).toBe('true')
      expect(response.headers.get('Access-Control-Max-Age')).toBe('86400')
    })

    it('responds 204 for localhost origins in production allowlist', async () => {
      const response = await sendCorsRequest({
        method: 'OPTIONS',
        origin: 'http://localhost:5173',
      })

      expect(response.status).toBe(204)
      expect(response.headers.get('Access-Control-Allow-Origin')).toBe(
        'http://localhost:5173'
      )
    })

    it('responds 204 for preview deployment domains', async () => {
      const response = await sendCorsRequest({
        method: 'OPTIONS',
        origin: 'https://feature-branch-abc123.web3search.pages.dev',
      })

      expect(response.status).toBe(204)
      expect(response.headers.get('Access-Control-Allow-Origin')).toBe(
        'https://feature-branch-abc123.web3search.pages.dev'
      )
    })

    it('responds 204 for any localhost port in development environment', async () => {
      const response = await sendCorsRequest({
        method: 'OPTIONS',
        origin: 'http://localhost:8080',
        env: createMockEnv({ ENVIRONMENT: 'development' }),
      })

      expect(response.status).toBe(204)
      expect(response.headers.get('Access-Control-Allow-Origin')).toBe(
        'http://localhost:8080'
      )
    })

    it('rejects preflight with 403 for disallowed origin', async () => {
      const response = await sendCorsRequest({
        method: 'OPTIONS',
        origin: 'https://malicious.com',
      })

      expect(response.status).toBe(403)
      expect(await response.text()).toBe('Forbidden')
      expect(response.headers.has('Access-Control-Allow-Origin')).toBe(false)
    })
  })

  describe('Regular Requests (GET, POST, etc.)', () => {
    it('adds CORS headers for allowed origin', async () => {
      const response = await sendCorsRequest({
        origin: 'https://web3search.pages.dev',
      })

      expect(response.status).toBe(200)
      expect(await response.json()).toEqual({ ok: true })
      expect(response.headers.get('Access-Control-Allow-Origin')).toBe(
        'https://web3search.pages.dev'
      )
      expect(response.headers.get('Access-Control-Allow-Credentials')).toBe('true')
    })

    it('adds CORS headers for preview deployment domains', async () => {
      const response = await sendCorsRequest({
        origin: 'https://pr-42.web3search.pages.dev',
      })

      expect(response.status).toBe(200)
      expect(response.headers.get('Access-Control-Allow-Origin')).toBe(
        'https://pr-42.web3search.pages.dev'
      )
    })

    it('does not add CORS headers when origin is blocked', async () => {
      const response = await sendCorsRequest({
        origin: 'https://unknown.origin',
      })

      expect(response.status).toBe(200)
      expect(await response.json()).toEqual({ ok: true })
      expect(response.headers.has('Access-Control-Allow-Origin')).toBe(false)
      expect(response.headers.has('Access-Control-Allow-Credentials')).toBe(false)
    })

    it('does not add CORS headers when no origin header is present', async () => {
      const response = await sendCorsRequest({
        // No origin header
      })

      expect(response.status).toBe(200)
      expect(response.headers.has('Access-Control-Allow-Origin')).toBe(false)
    })

    it('adds CORS headers for localhost in development', async () => {
      const response = await sendCorsRequest({
        origin: 'http://localhost:9999',
        env: createMockEnv({ ENVIRONMENT: 'development' }),
      })

      expect(response.status).toBe(200)
      expect(response.headers.get('Access-Control-Allow-Origin')).toBe(
        'http://localhost:9999'
      )
    })
  })

  describe('Edge Cases', () => {
    it('blocks localhost in production when not in allowlist', async () => {
      const response = await sendCorsRequest({
        method: 'OPTIONS',
        origin: 'http://localhost:9999',
        env: createMockEnv({ ENVIRONMENT: 'production' }),
      })

      expect(response.status).toBe(403)
      expect(await response.text()).toBe('Forbidden')
    })

    it('blocks subdomains that do not match the preview pattern', async () => {
      const response = await sendCorsRequest({
        method: 'OPTIONS',
        origin: 'https://fake-web3search.pages.dev',
      })

      expect(response.status).toBe(403)
    })

    it('handles empty origin header', async () => {
      const response = await sendCorsRequest({
        method: 'OPTIONS',
        origin: '',
      })

      expect(response.status).toBe(403)
    })
  })
})
