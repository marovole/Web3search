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

      // Should be at least 5ms due to artificial delay (allowing for timing variance)
      expect(numericTime).toBeGreaterThanOrEqual(5)
    })
  })

  describe('Console Logging', () => {
    it('logs request with JSON metrics', async () => {
      await sendLoggerRequest()

      expect(consoleLogSpy).toHaveBeenCalledTimes(1)

      const [logPrefix, logData] = consoleLogSpy.mock.calls[0]
      expect(logPrefix).toBe('[REQUEST]')

      const metrics = JSON.parse(logData)
      expect(metrics).toMatchObject({
        method: 'GET',
        path: '/resource',
        status: 200,
        requestId: MOCK_REQUEST_ID
      })
      expect(metrics).toHaveProperty('durationMs')
      expect(metrics).toHaveProperty('timestamp')
      expect(metrics.slow).toBe(false)
    })

    it('logs slow requests with warning', async () => {
      // Mock a slow response
      vi.spyOn(Date, 'now')
        .mockReturnValueOnce(0) // start time
        .mockReturnValueOnce(1500) // end time (1.5s duration)

      await sendLoggerRequest({ method: 'POST', path: '/slow-endpoint' })

      const [logPrefix, logData] = consoleLogSpy.mock.calls[0]
      expect(logPrefix).toBe('[PERFORMANCE]')

      const metrics = JSON.parse(logData)
      expect(metrics.durationMs).toBeGreaterThan(1000)
      expect(metrics.slow).toBe(true)
    })

    it('logs different HTTP methods correctly', async () => {
      await sendLoggerRequest({ method: 'POST', path: '/slow-endpoint' })

      const [, logData] = consoleLogSpy.mock.calls[0]
      const metrics = JSON.parse(logData)
      expect(metrics.method).toBe('POST')
      expect(metrics.path).toBe('/slow-endpoint')
    })
  })

  describe('IP Address Extraction and Masking', () => {
    it('extracts and masks IP from cf-connecting-ip header (priority 1)', async () => {
      await sendLoggerRequest({
        headers: {
          'cf-connecting-ip': '203.0.113.42',
          'x-real-ip': '198.51.100.1',
        },
      })

      const [, logData] = consoleLogSpy.mock.calls[0]
      const metrics = JSON.parse(logData)
      // IPv4 masking: keeps first two octets
      expect(metrics.ip).toBe('203.0.0.0')
    })

    it('falls back to x-real-ip header and masks it', async () => {
      await sendLoggerRequest({
        headers: {
          'x-real-ip': '198.51.100.1',
        },
      })

      const [, logData] = consoleLogSpy.mock.calls[0]
      const metrics = JSON.parse(logData)
      // IPv4 masking: keeps first two octets
      expect(metrics.ip).toBe('198.51.0.0')
    })

    it('uses "unknown" when no IP headers are present', async () => {
      await sendLoggerRequest()

      const [, logData] = consoleLogSpy.mock.calls[0]
      const metrics = JSON.parse(logData)
      expect(metrics.ip).toBe('unknown')
    })

    it('masks IPv6 addresses correctly', async () => {
      await sendLoggerRequest({
        headers: {
          'cf-connecting-ip': '2001:0db8:85a3:0000:0000:8a2e:0370:7334',
        },
      })

      const [, logData] = consoleLogSpy.mock.calls[0]
      const metrics = JSON.parse(logData)
      // IPv6 masking: keeps first four segments, always 8 total
      expect(metrics.ip).toBe('2001:0db8:85a3:0000:xxxx:xxxx:xxxx:xxxx')
    })

    it('masks compressed IPv6 addresses correctly', async () => {
      await sendLoggerRequest({
        headers: {
          'cf-connecting-ip': '2001:db8::1',
        },
      })

      const [, logData] = consoleLogSpy.mock.calls[0]
      const metrics = JSON.parse(logData)
      // Compressed IPv6 masking: always outputs 8 segments
      // 2001:db8::1 expands to [2001, db8, 1] -> masks to 2001:db8:1:0:xxxx:xxxx:xxxx:xxxx
      expect(metrics.ip).toBe('2001:db8:1:0:xxxx:xxxx:xxxx:xxxx')
    })
  })

  describe('Cloudflare Integration', () => {
    it('logs Cloudflare edge location (colo) when available', async () => {
      // Note: In test environment, cf.colo will be 'unknown'
      // This test verifies the fallback behavior
      await sendLoggerRequest()

      const [, logData] = consoleLogSpy.mock.calls[0]
      const metrics = JSON.parse(logData)
      expect(metrics.colo).toBe('unknown')
    })
  })
})
