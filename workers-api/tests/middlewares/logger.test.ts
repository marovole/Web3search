/**
 * Tests for Logger Middleware
 * Validates request ID generation, telemetry headers, and console logging
 */

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { Hono } from 'hono'
import { loggerMiddleware } from '../../src/middlewares/logger'
import type { Env } from '../../src/types/env'

// ============================================
// Test Setup
// ============================================

/**
 * Create a minimal test app with logger middleware
 * This mimics the production middleware stack
 */
const loggerApp = new Hono<{ Bindings: Env }>()
loggerApp.use('*', loggerMiddleware)
loggerApp.get('/resource', (c) => {
  const requestId = c.get('requestId') as string | undefined
  return c.json({ requestId })
})
loggerApp.post('/slow-endpoint', async (c) => {
  // Simulate a slow endpoint for response time testing
  await new Promise((resolve) => setTimeout(resolve, 10))
  return c.json({ ok: true })
})

const BASE_URL = 'https://example.com/resource'
const MOCK_REQUEST_ID = 'test-request-id-12345'

/**
 * Helper to send requests with custom headers
 */
async function sendLoggerRequest({
  method = 'GET',
  path = '/resource',
  headers = {},
  env,
}: {
  method?: string
  path?: string
  headers?: Record<string, string>
  env?: Env
} = {}) {
  const url = `https://example.com${path}`
  const request = new Request(url, {
    method,
    headers,
  })

  return loggerApp.fetch(request, env ?? createMockEnv())
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
// Logger Middleware Tests
// ============================================

describe('loggerMiddleware', () => {
  let consoleLogSpy: ReturnType<typeof vi.spyOn>
  let cryptoSpy: ReturnType<typeof vi.spyOn>

  beforeEach(() => {
    // Mock console.log to capture log output
    consoleLogSpy = vi.spyOn(console, 'log').mockImplementation(() => {})

    // Mock crypto.randomUUID to return a predictable request ID
    cryptoSpy = vi.spyOn(globalThis.crypto, 'randomUUID')
    cryptoSpy.mockReturnValue(MOCK_REQUEST_ID)
  })

  afterEach(() => {
    // Restore original implementations
    consoleLogSpy.mockRestore()
    cryptoSpy.mockRestore()
  })

  describe('Request ID Generation', () => {
    it('generates a unique request ID for each request', async () => {
      const response = await sendLoggerRequest()

      expect(cryptoSpy).toHaveBeenCalledTimes(1)
      expect(response.headers.get('x-request-id')).toBe(MOCK_REQUEST_ID)
    })

    it('exposes request ID to downstream handlers via context', async () => {
      const response = await sendLoggerRequest()
      const body = await response.json()

      expect(body.requestId).toBe(MOCK_REQUEST_ID)
    })
  })

  describe('Response Headers', () => {
    it('attaches x-request-id header to response', async () => {
      const response = await sendLoggerRequest()

      expect(response.headers.get('x-request-id')).toBe(MOCK_REQUEST_ID)
    })

    it('attaches x-response-time header with valid format', async () => {
      const response = await sendLoggerRequest()
      const responseTime = response.headers.get('x-response-time')

      expect(responseTime).toMatch(/^\d+ms$/)

      // Extract numeric value and verify it's valid
      const numericTime = Number(responseTime?.replace('ms', ''))
      expect(Number.isFinite(numericTime)).toBe(true)
      expect(numericTime).toBeGreaterThanOrEqual(0)
    })

    it('calculates response time correctly for slow endpoints', async () => {
      const response = await sendLoggerRequest({
        method: 'POST',
        path: '/slow-endpoint',
      })

      const responseTime = response.headers.get('x-response-time')
      const numericTime = Number(responseTime?.replace('ms', ''))

      // Should be at least 10ms due to artificial delay
      expect(numericTime).toBeGreaterThanOrEqual(10)
    })
  })

  describe('Console Logging', () => {
    it('logs request start with method, path, and request ID', async () => {
      await sendLoggerRequest()

      expect(consoleLogSpy).toHaveBeenCalledTimes(2)

      const [startLog] = consoleLogSpy.mock.calls.map((args) => args[0])
      expect(startLog).toContain(`[${MOCK_REQUEST_ID}] --> GET /resource`)
    })

    it('logs request completion with status and response time', async () => {
      await sendLoggerRequest()

      expect(consoleLogSpy).toHaveBeenCalledTimes(2)

      const [, endLog] = consoleLogSpy.mock.calls.map((args) => args[0])
      expect(endLog).toContain(`[${MOCK_REQUEST_ID}] <-- GET /resource`)
      expect(endLog).toContain('| Status: 200 |')
      expect(endLog).toMatch(/\| Time: \d+ms/)
    })

    it('logs different HTTP methods correctly', async () => {
      await sendLoggerRequest({ method: 'POST', path: '/slow-endpoint' })

      const [startLog, endLog] = consoleLogSpy.mock.calls.map((args) => args[0])
      expect(startLog).toContain('--> POST /slow-endpoint')
      expect(endLog).toContain('<-- POST /slow-endpoint')
    })
  })

  describe('IP Address Extraction', () => {
    it('extracts IP from cf-connecting-ip header (priority 1)', async () => {
      await sendLoggerRequest({
        headers: {
          'cf-connecting-ip': '203.0.113.42',
          'x-real-ip': '198.51.100.1',
        },
      })

      const [startLog] = consoleLogSpy.mock.calls.map((args) => args[0])
      expect(startLog).toContain('| IP: 203.0.113.42 |')
    })

    it('falls back to x-real-ip header when cf-connecting-ip is missing', async () => {
      await sendLoggerRequest({
        headers: {
          'x-real-ip': '198.51.100.1',
        },
      })

      const [startLog] = consoleLogSpy.mock.calls.map((args) => args[0])
      expect(startLog).toContain('| IP: 198.51.100.1 |')
    })

    it('uses "unknown" when no IP headers are present', async () => {
      await sendLoggerRequest()

      const [startLog] = consoleLogSpy.mock.calls.map((args) => args[0])
      expect(startLog).toContain('| IP: unknown |')
    })
  })

  describe('User-Agent Handling', () => {
    it('includes user-agent in request log', async () => {
      await sendLoggerRequest({
        headers: {
          'user-agent': 'Mozilla/5.0 Test Browser',
        },
      })

      const [startLog] = consoleLogSpy.mock.calls.map((args) => args[0])
      expect(startLog).toContain('| UA: Mozilla/5.0 Test Browser...')
    })

    it('truncates long user-agent strings to 50 characters', async () => {
      const longUA = 'A'.repeat(100)

      await sendLoggerRequest({
        headers: {
          'user-agent': longUA,
        },
      })

      const [startLog] = consoleLogSpy.mock.calls.map((args) => args[0])
      expect(startLog).toContain(`| UA: ${'A'.repeat(50)}...`)
      expect(startLog).not.toContain('A'.repeat(51))
    })

    it('handles missing user-agent gracefully', async () => {
      await sendLoggerRequest()

      const [startLog] = consoleLogSpy.mock.calls.map((args) => args[0])
      expect(startLog).toContain('| UA: unknown...')
    })
  })

  describe('Cloudflare Integration', () => {
    it('logs Cloudflare edge location (colo) when available', async () => {
      // Note: In test environment, cf.colo will be 'unknown'
      // This test verifies the fallback behavior
      await sendLoggerRequest()

      const [startLog] = consoleLogSpy.mock.calls.map((args) => args[0])
      expect(startLog).toContain('| Colo: unknown |')
    })
  })
})
