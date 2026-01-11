/**
 * Tests for Rate Limit Middleware
 * Validates KV-backed sliding window rate limiting with fault tolerance
 */

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { Hono } from 'hono'
import {
  createRateLimitMiddleware,
  type RateLimitOptions,
} from '../../src/middlewares/rate-limit'
import type { Env } from '../../src/types/env'

// ============================================
// Test Helpers
// ============================================

const BASE_URL = 'https://example.com/resource'

/**
 * Create a test app with rate limiting applied
 */
function createRateLimitedApp(options: RateLimitOptions) {
  const app = new Hono<{ Bindings: Env }>()
  app.use('*', createRateLimitMiddleware(options))
  app.get('/resource', (c) => c.json({ ok: true }))
  return app
}

/**
 * Send a request to the rate-limited app
 */
async function sendRateLimitedRequest(
  app: Hono<{ Bindings: Env }>,
  env: Env,
  headers: Record<string, string> = {}
) {
  const request = new Request(BASE_URL, {
    method: 'GET',
    headers,
  })

  return app.fetch(request, env)
}

/**
 * Build the KV key used by the rate limiter
 * Must match the implementation's key format including configHash
 */
function createConfigHash(scope: string, limit: number, windowSeconds: number): string {
  const config = `${scope}:${limit}:${windowSeconds}`
  let hash = 0
  for (let i = 0; i < config.length; i++) {
    const char = config.charCodeAt(i)
    hash = ((hash << 5) - hash) + char
    hash = hash & hash
  }
  return Math.abs(hash).toString(36)
}

function buildKvKey(
  scope: string,
  identifier: string,
  windowSeconds: number,
  timeMs: number,
  limit: number = 5
) {
  const windowId = Math.floor(timeMs / 1000 / windowSeconds)
  const configHash = createConfigHash(scope, limit, windowSeconds)
  return `ratelimit:${configHash}:${scope}:${identifier}:${windowId}`
}

// ============================================
// KV Mock Implementation
// ============================================

type KVEntry = {
  value: string
  expiration?: number
}

type KVOptions = {
  throwOnGet?: boolean
  throwOnPut?: boolean
}

/**
 * Create an in-memory KV namespace for testing
 * Supports TTL, error injection, and expiration tracking
 */
function createInMemoryKV(options: KVOptions = {}) {
  const store = new Map<string, KVEntry>()

  const kv: KVNamespace = {
    get: async (key: string) => {
      if (options.throwOnGet) {
        throw new Error('KV get failed')
      }

      const entry = store.get(key)
      if (!entry) return null

      // Check if expired
      const now = Math.floor(Date.now() / 1000)
      if (entry.expiration && entry.expiration <= now) {
        store.delete(key)
        return null
      }

      return entry.value
    },

    put: async (key: string, value: string, opts?: { expirationTtl?: number }) => {
      if (options.throwOnPut) {
        throw new Error('KV put failed')
      }

      const entry: KVEntry = { value }
      if (opts?.expirationTtl) {
        entry.expiration = Math.floor(Date.now() / 1000) + opts.expirationTtl
      }

      store.set(key, entry)
    },

    delete: async (key: string) => {
      store.delete(key)
    },

    list: async () => ({
      keys: Array.from(store.entries()).map(([name, entry]) => ({
        name,
        expiration: entry.expiration ?? null,
        metadata: null,
      })),
      list_complete: true,
    }),
  } as KVNamespace

  return { kv, store }
}

type MockEnvResult = {
  env: Env
  store: Map<string, KVEntry>
}

/**
 * Create a mock environment with configurable KV behavior
 */
function createMockEnv(
  kvOptions: KVOptions = {},
  overrides: Partial<Env> = {}
): MockEnvResult {
  const { kv, store } = createInMemoryKV(kvOptions)

  const env: Env = {
    ENVIRONMENT: 'production',
    SUPABASE_URL: 'https://example.supabase.co',
    SUPABASE_ANON_KEY: 'anon-key',
    OPENROUTER_API_KEY: 'test-key',
    CACHE: kv,
    ...overrides,
  }

  return { env, store }
}

// ============================================
// Rate Limit Middleware Tests
// ============================================

describe('createRateLimitMiddleware', () => {
  beforeEach(() => {
    // Use fake timers for deterministic time-based testing
    vi.useFakeTimers()
  })

  afterEach(() => {
    // Restore real timers
    vi.useRealTimers()
    vi.clearAllMocks()
  })

  describe('Basic Rate Limiting', () => {
    it('allows the first request and sets rate limit headers', async () => {
      const nowMs = 5000
      vi.setSystemTime(nowMs)

      const { env, store } = createMockEnv()
      const app = createRateLimitedApp({
        scope: 'test-endpoint',
        limit: 5,
        windowSeconds: 60,
      })

      const response = await sendRateLimitedRequest(app, env, {
        'cf-connecting-ip': '203.0.113.1',
      })

      // Request should succeed
      expect(response.status).toBe(200)
      expect(await response.json()).toEqual({ ok: true })

      // Rate limit headers should be set
      expect(response.headers.get('X-RateLimit-Limit')).toBe('5')
      expect(response.headers.get('X-RateLimit-Remaining')).toBe('4')

      // KV should have the counter with proper TTL
      const key = buildKvKey('test-endpoint', '203.0.113.1', 60, nowMs, 5)
      const entry = store.get(key)
      expect(entry?.value).toBe('1')
      expect(entry?.expiration).toBe(Math.floor(nowMs / 1000) + 120)
    })

    it('increments counter for subsequent requests', async () => {
      const nowMs = 10000
      vi.setSystemTime(nowMs)

      const { env, store } = createMockEnv()
      const app = createRateLimitedApp({
        scope: 'test-endpoint',
        limit: 3,
        windowSeconds: 30,
      })

      const headers = { 'cf-connecting-ip': '203.0.113.2' }

      // First request
      const response1 = await sendRateLimitedRequest(app, env, headers)
      expect(response1.headers.get('X-RateLimit-Remaining')).toBe('2')

      // Second request
      const response2 = await sendRateLimitedRequest(app, env, headers)
      expect(response2.headers.get('X-RateLimit-Remaining')).toBe('1')

      // Third request
      const response3 = await sendRateLimitedRequest(app, env, headers)
      expect(response3.headers.get('X-RateLimit-Remaining')).toBe('0')

      // Verify final counter value
      const key = buildKvKey('test-endpoint', '203.0.113.2', 30, nowMs, 3)
      const entry = store.get(key)
      expect(entry?.value).toBe('3')
    })

    it('blocks requests when limit is exceeded', async () => {
      const nowMs = 45000
      vi.setSystemTime(nowMs)

      const { env } = createMockEnv()
      const app = createRateLimitedApp({
        scope: 'test-endpoint',
        limit: 2,
        windowSeconds: 60,
      })

      const headers = { 'cf-connecting-ip': '203.0.113.3' }

      // Exhaust the limit
      await sendRateLimitedRequest(app, env, headers)
      await sendRateLimitedRequest(app, env, headers)

      // Next request should be blocked
      const response = await sendRateLimitedRequest(app, env, headers)

      expect(response.status).toBe(429)

      const body = await response.json()
      expect(body.error.code).toBe('RATE_LIMITED')
      expect(body.error.message).toContain('Too many requests')

      // Should have retry-after header
      expect(response.headers.get('Retry-After')).toBe('15')
      expect(response.headers.get('X-RateLimit-Limit')).toBe('2')
      expect(response.headers.get('X-RateLimit-Remaining')).toBe('0')
    })
  })

  describe('Retry-After Calculation', () => {
    it('calculates correct retry-after at start of window', async () => {
      const nowMs = 0 // Start of window
      vi.setSystemTime(nowMs)

      const { env } = createMockEnv()
      const app = createRateLimitedApp({
        scope: 'test',
        limit: 1,
        windowSeconds: 60,
      })

      const headers = { 'cf-connecting-ip': '1.1.1.1' }

      await sendRateLimitedRequest(app, env, headers)
      const blocked = await sendRateLimitedRequest(app, env, headers)

      // At start of window, should wait full window duration
      expect(blocked.headers.get('Retry-After')).toBe('60')
    })

    it('calculates correct retry-after mid-window', async () => {
      const nowMs = 30000 // 30 seconds into a 60-second window
      vi.setSystemTime(nowMs)

      const { env } = createMockEnv()
      const app = createRateLimitedApp({
        scope: 'test',
        limit: 1,
        windowSeconds: 60,
      })

      const headers = { 'cf-connecting-ip': '2.2.2.2' }

      await sendRateLimitedRequest(app, env, headers)
      const blocked = await sendRateLimitedRequest(app, env, headers)

      // 30 seconds remaining in window
      expect(blocked.headers.get('Retry-After')).toBe('30')
    })
  })

  describe('Sliding Window Behavior', () => {
    it('resets counter in new time window', async () => {
      const { env, store } = createMockEnv()
      const app = createRateLimitedApp({
        scope: 'test',
        limit: 2,
        windowSeconds: 60,
      })

      const headers = { 'cf-connecting-ip': '3.3.3.3' }

      // First window (t=0s)
      vi.setSystemTime(0)
      await sendRateLimitedRequest(app, env, headers)
      await sendRateLimitedRequest(app, env, headers)

      const firstWindowKey = buildKvKey('test', '3.3.3.3', 60, 0, 2)
      expect(store.get(firstWindowKey)?.value).toBe('2')

      // Advance to next window (t=60s)
      vi.setSystemTime(60000)
      const response = await sendRateLimitedRequest(app, env, headers)

      expect(response.status).toBe(200)
      expect(response.headers.get('X-RateLimit-Remaining')).toBe('1')

      // Should have new key for new window
      const secondWindowKey = buildKvKey('test', '3.3.3.3', 60, 60000, 2)
      expect(store.get(secondWindowKey)?.value).toBe('1')
    })
  })

  describe('KV Fault Tolerance', () => {
    it('allows requests when KV read fails', async () => {
      const warningSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})

      const { env } = createMockEnv({ throwOnGet: true })
      const app = createRateLimitedApp({
        scope: 'test',
        limit: 1,
        windowSeconds: 30,
      })

      const response = await sendRateLimitedRequest(app, env, {
        'cf-connecting-ip': '4.4.4.4',
      })

      // Should succeed despite KV failure
      expect(response.status).toBe(200)

      // Should log warning
      expect(warningSpy).toHaveBeenCalledWith(
        expect.stringContaining('KV read failed; allowing request'),
        expect.any(Error)
      )

      warningSpy.mockRestore()
    })

    it('allows requests when KV write fails', async () => {
      const warningSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})

      const { env } = createMockEnv({ throwOnPut: true })
      const app = createRateLimitedApp({
        scope: 'test',
        limit: 3,
        windowSeconds: 30,
      })

      const response = await sendRateLimitedRequest(app, env, {
        'cf-connecting-ip': '5.5.5.5',
      })

      // Should succeed despite KV failure
      expect(response.status).toBe(200)

      // Should log warning
      expect(warningSpy).toHaveBeenCalledWith(
        expect.stringContaining('KV write failed; continuing'),
        expect.any(Error)
      )

      warningSpy.mockRestore()
    })

    it('skips rate limiting when KV namespace is missing', async () => {
      const warningSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})

      const env = createMockEnv().env
      // @ts-expect-error - Intentionally removing CACHE to test graceful degradation
      env.CACHE = undefined

      const app = createRateLimitedApp({
        scope: 'test',
        limit: 1,
        windowSeconds: 30,
      })

      const response = await sendRateLimitedRequest(app, env, {
        'cf-connecting-ip': '6.6.6.6',
      })

      // Should succeed
      expect(response.status).toBe(200)

      // Should log warning
      expect(warningSpy).toHaveBeenCalledWith(
        expect.stringContaining('KV namespace missing; skipping rate limiting')
      )

      warningSpy.mockRestore()
    })
  })

  describe('Custom Key Functions', () => {
    it('uses custom key extractor for rate limiting', async () => {
      const nowMs = 20000
      vi.setSystemTime(nowMs)

      const { env, store } = createMockEnv()
      const app = createRateLimitedApp({
        scope: 'api-key',
        limit: 1,
        windowSeconds: 30,
        key: (c) => c.req.header('x-api-key') ?? 'anonymous',
      })

      const clientA = { 'cf-connecting-ip': '8.8.8.8', 'x-api-key': 'client-a' }
      const clientB = { 'cf-connecting-ip': '8.8.4.4', 'x-api-key': 'client-b' }

      // Client A: first request succeeds
      const responseA1 = await sendRateLimitedRequest(app, env, clientA)
      expect(responseA1.status).toBe(200)

      // Client A: second request blocked
      const responseA2 = await sendRateLimitedRequest(app, env, clientA)
      expect(responseA2.status).toBe(429)

      // Client B: should have independent counter
      const responseB = await sendRateLimitedRequest(app, env, clientB)
      expect(responseB.status).toBe(200)

      // Verify separate KV keys
      const keys = Array.from(store.keys())
      expect(keys).toEqual(
        expect.arrayContaining([
          buildKvKey('api-key', 'client-a', 30, nowMs, 1),
          buildKvKey('api-key', 'client-b', 30, nowMs, 1),
        ])
      )
    })

    it('falls back to anonymous when custom key returns null', async () => {
      const nowMs = 10000
      vi.setSystemTime(nowMs)

      const { env, store } = createMockEnv()
      const app = createRateLimitedApp({
        scope: 'test',
        limit: 2,
        windowSeconds: 30,
        key: (c) => c.req.header('x-user-id') ?? null,
      })

      // Request without x-user-id header (and no cf-connecting-ip)
      const response = await sendRateLimitedRequest(app, env, {})

      expect(response.status).toBe(200)

      // Should use 'anonymous' as identifier
      const key = buildKvKey('test', 'anonymous', 30, nowMs, 2)
      expect(store.has(key)).toBe(true)
    })
  })

  describe('Identifier Extraction', () => {
    it('uses cf-connecting-ip as default identifier', async () => {
      const nowMs = 5000
      vi.setSystemTime(nowMs)

      const { env, store } = createMockEnv()
      const app = createRateLimitedApp({
        scope: 'test',
        limit: 5,
        windowSeconds: 30,
      })

      await sendRateLimitedRequest(app, env, {
        'cf-connecting-ip': '10.0.0.1',
      })

      const key = buildKvKey('test', '10.0.0.1', 30, nowMs, 5)
      expect(store.has(key)).toBe(true)
    })

    it('falls back to anonymous when no IP header present', async () => {
      const nowMs = 5000
      vi.setSystemTime(nowMs)

      const { env, store } = createMockEnv()
      const app = createRateLimitedApp({
        scope: 'test',
        limit: 5,
        windowSeconds: 30,
      })

      await sendRateLimitedRequest(app, env, {})

      const key = buildKvKey('test', 'anonymous', 30, nowMs, 5)
      expect(store.has(key)).toBe(true)
    })
  })
})
