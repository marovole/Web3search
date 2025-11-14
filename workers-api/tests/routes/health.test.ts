/**
 * Tests for Health Check Routes
 * Tests health status, database connection, and readiness probes
 */

import { describe, expect, it, vi } from 'vitest'
import type { Env } from '../../src/types/env'

// Mock supabase
vi.mock('../../src/lib/supabase', () => ({
  testDatabaseConnection: vi.fn(async () => true),
  createSupabaseClient: vi.fn()
}))

import health from '../../src/routes/health'

async function fetchHealth(path = '/', env?: Env) {
  const request = new Request(`https://example.com${path}`, {
    method: 'GET',
  })
  return health.fetch(request, env ?? createMockEnv())
}

describe('Health Check Routes', () => {
  describe('GET /', () => {
    it('returns 200 when database is connected', async () => {
      const response = await fetchHealth()
      expect(response.status).toBe(200)

      const body = await response.json()
      expect(body.status).toBe('healthy')
      expect(body).toHaveProperty('version')
      expect(body).toHaveProperty('timestamp')
      expect(body).toHaveProperty('responseTime')
    })

    it('includes database status information', async () => {
      const response = await fetchHealth()
      const body = await response.json()

      expect(body.database).toEqual({
        status: 'connected',
        type: 'supabase-postgresql'
      })
    })

    it('includes cache status information', async () => {
      const response = await fetchHealth()
      const body = await response.json()

      expect(body.cache).toHaveProperty('status')
      expect(body.cache).toHaveProperty('type')
    })

    it('includes environment information', async () => {
      const response = await fetchHealth()
      const body = await response.json()

      expect(body.environment).toBe('test')
    })

    it('returns 503 when database is disconnected', async () => {
      const { testDatabaseConnection } = await import('../../src/lib/supabase')
      vi.mocked(testDatabaseConnection).mockResolvedValueOnce(false)

      const response = await fetchHealth()
      expect(response.status).toBe(503)

      const body = await response.json()
      expect(body.status).toBe('degraded')
      expect(body.database.status).toBe('disconnected')
    })

    it('returns 503 when database check throws error', async () => {
      const { testDatabaseConnection } = await import('../../src/lib/supabase')
      vi.mocked(testDatabaseConnection).mockRejectedValueOnce(
        new Error('Connection failed')
      )

      const response = await fetchHealth()
      expect(response.status).toBe(503)

      const body = await response.json()
      expect(body.status).toBe('unhealthy')
      expect(body).toHaveProperty('error')
    })
  })

  describe('GET /ready', () => {
    it('returns 200 when service is ready', async () => {
      const response = await fetchHealth('/ready')
      expect(response.status).toBe(200)

      const body = await response.json()
      expect(body.ready).toBe(true)
    })

    it('returns 503 when service is not ready', async () => {
      const { testDatabaseConnection } = await import('../../src/lib/supabase')
      vi.mocked(testDatabaseConnection).mockResolvedValueOnce(false)

      const response = await fetchHealth('/ready')
      expect(response.status).toBe(503)

      const body = await response.json()
      expect(body.ready).toBe(false)
    })
  })

  describe('GET /live', () => {
    it('always returns 200 with alive true', async () => {
      const response = await fetchHealth('/live')
      expect(response.status).toBe(200)

      const body = await response.json()
      expect(body.alive).toBe(true)
    })
  })
})

function createMockEnv(overrides: Partial<Env> = {}): Env {
  return {
    ENVIRONMENT: 'test',
    SUPABASE_URL: 'https://example.supabase.co',
    SUPABASE_ANON_KEY: 'anon',
    OPENROUTER_API_KEY: 'test',
    CACHE: {} as KVNamespace,
    ...overrides,
  } as Env
}
