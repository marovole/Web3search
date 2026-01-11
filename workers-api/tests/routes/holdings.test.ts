import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'
import { Hono } from 'hono'
import type { Env } from '../../src/types/env'

const mockUser = { id: 'user-123', email: 'test@example.com', tier: 'free' }

function createMockEnv(): Env {
  return {
    ENVIRONMENT: 'test',
    SUPABASE_URL: 'https://test.supabase.co',
    SUPABASE_ANON_KEY: 'test-key',
    OPENROUTER_API_KEY: 'test-key',
  } as Env
}

let mockHoldingsData: unknown[] = []
let mockSingleHolding: unknown = null
let mockDbError: unknown = null

vi.mock('../../src/lib/supabase', () => ({
  getSupabaseClient: vi.fn(() => ({
    from: (_table: string) => {
      const deleteChain = {
        eq: vi.fn().mockReturnThis(),
        then: (resolve: (value: { error: unknown }) => void) => {
          resolve({ error: mockDbError || null })
        },
      }

      const baseChain = {
        eq: vi.fn().mockReturnThis(),
        order: vi.fn().mockImplementation(async () => {
          if (mockDbError) return { data: null, error: mockDbError }
          return { data: mockHoldingsData, error: null }
        }),
        single: vi.fn().mockImplementation(async () => {
          if (mockDbError) return { data: null, error: mockDbError }
          return { data: mockSingleHolding, error: mockSingleHolding ? null : { code: 'PGRST116' } }
        }),
        select: vi.fn().mockReturnThis(),
        insert: vi.fn().mockReturnThis(),
        update: vi.fn().mockReturnThis(),
        delete: vi.fn().mockReturnValue(deleteChain),
      }
      return baseChain
    },
  })),
}))

vi.mock('../../src/middlewares/auth', () => ({
  authMiddleware: () => async (c: { set: (key: string, value: unknown) => void }, next: () => Promise<void>) => {
    c.set('user', mockUser)
    await next()
  },
  getCurrentUser: () => mockUser,
}))

import holdings from '../../src/routes/holdings'

function createTestApp() {
  const app = new Hono<{ Bindings: Env }>()
  app.route('/holdings', holdings)
  return app
}

describe('Holdings Routes', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockHoldingsData = []
    mockSingleHolding = null
    mockDbError = null
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('GET /holdings', () => {
    it('returns list of holdings for authenticated user', async () => {
      mockHoldingsData = [
        { id: 'hold-1', token_id: 'bitcoin', symbol: 'BTC', name: 'Bitcoin', quantity: 1.5 },
        { id: 'hold-2', token_id: 'ethereum', symbol: 'ETH', name: 'Ethereum', quantity: 10 },
      ]

      const app = createTestApp()
      const res = await app.fetch(
        new Request('http://localhost/holdings'),
        createMockEnv()
      )

      expect(res.status).toBe(200)
      const body = await res.json()
      expect(body).toHaveProperty('holdings')
      expect(body.holdings).toHaveLength(2)
    })

    it('returns 500 on database error', async () => {
      mockDbError = { message: 'DB error' }

      const app = createTestApp()
      const res = await app.fetch(
        new Request('http://localhost/holdings'),
        createMockEnv()
      )

      expect(res.status).toBe(500)
      const body = await res.json()
      expect(body.error.code).toBe('DATABASE_ERROR')
    })
  })

  describe('POST /holdings', () => {
    it('creates a new holding with valid input', async () => {
      mockSingleHolding = {
        id: 'hold-new',
        token_id: 'bitcoin',
        symbol: 'BTC',
        name: 'Bitcoin',
        quantity: 0.5,
      }

      const app = createTestApp()
      const res = await app.fetch(
        new Request('http://localhost/holdings', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            token_id: 'bitcoin',
            symbol: 'BTC',
            name: 'Bitcoin',
            quantity: 0.5,
          }),
        }),
        createMockEnv()
      )

      expect(res.status).toBe(201)
      const body = await res.json()
      expect(body.holding.symbol).toBe('BTC')
    })

    it('returns 400 for missing required fields', async () => {
      const app = createTestApp()
      const res = await app.fetch(
        new Request('http://localhost/holdings', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ symbol: 'BTC' }),
        }),
        createMockEnv()
      )

      expect(res.status).toBe(400)
      const body = await res.json()
      expect(body.error.code).toBe('INVALID_INPUT')
    })

    it('returns 400 for negative quantity', async () => {
      const app = createTestApp()
      const res = await app.fetch(
        new Request('http://localhost/holdings', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            token_id: 'bitcoin',
            symbol: 'BTC',
            name: 'Bitcoin',
            quantity: -1,
          }),
        }),
        createMockEnv()
      )

      expect(res.status).toBe(400)
      const body = await res.json()
      expect(body.error.code).toBe('INVALID_INPUT')
    })

    it('returns 409 for duplicate holding', async () => {
      mockDbError = { code: '23505' }
      mockSingleHolding = null

      const app = createTestApp()
      const res = await app.fetch(
        new Request('http://localhost/holdings', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            token_id: 'bitcoin',
            symbol: 'BTC',
            name: 'Bitcoin',
            quantity: 1,
          }),
        }),
        createMockEnv()
      )

      expect(res.status).toBe(409)
      const body = await res.json()
      expect(body.error.code).toBe('ALREADY_EXISTS')
    })
  })

  describe('GET /holdings/:id', () => {
    it('returns single holding', async () => {
      mockSingleHolding = {
        id: 'hold-1',
        token_id: 'bitcoin',
        symbol: 'BTC',
        name: 'Bitcoin',
        quantity: 1.5,
      }

      const app = createTestApp()
      const res = await app.fetch(
        new Request('http://localhost/holdings/hold-1'),
        createMockEnv()
      )

      expect(res.status).toBe(200)
      const body = await res.json()
      expect(body.holding.id).toBe('hold-1')
    })

    it('returns 404 for non-existent holding', async () => {
      mockSingleHolding = null

      const app = createTestApp()
      const res = await app.fetch(
        new Request('http://localhost/holdings/non-existent'),
        createMockEnv()
      )

      expect(res.status).toBe(404)
      const body = await res.json()
      expect(body.error.code).toBe('NOT_FOUND')
    })
  })

  describe('PATCH /holdings/:id', () => {
    it('updates holding with valid fields', async () => {
      mockSingleHolding = {
        id: 'hold-1',
        quantity: 2.5,
        notes: 'Updated note',
      }

      const app = createTestApp()
      const res = await app.fetch(
        new Request('http://localhost/holdings/hold-1', {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ quantity: 2.5, notes: 'Updated note' }),
        }),
        createMockEnv()
      )

      expect(res.status).toBe(200)
      const body = await res.json()
      expect(body.holding.quantity).toBe(2.5)
    })

    it('returns 400 when no valid fields provided', async () => {
      const app = createTestApp()
      const res = await app.fetch(
        new Request('http://localhost/holdings/hold-1', {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ invalid_field: 'value' }),
        }),
        createMockEnv()
      )

      expect(res.status).toBe(400)
      const body = await res.json()
      expect(body.error.code).toBe('NO_UPDATES')
    })

    it('returns 404 for non-existent holding', async () => {
      mockSingleHolding = null

      const app = createTestApp()
      const res = await app.fetch(
        new Request('http://localhost/holdings/non-existent', {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ quantity: 1 }),
        }),
        createMockEnv()
      )

      expect(res.status).toBe(404)
    })
  })

  describe('DELETE /holdings/:id', () => {
    it('deletes holding successfully', async () => {
      const app = createTestApp()
      const res = await app.fetch(
        new Request('http://localhost/holdings/hold-1', {
          method: 'DELETE',
        }),
        createMockEnv()
      )

      expect(res.status).toBe(200)
      const body = await res.json()
      expect(body.success).toBe(true)
    })

    it('returns 500 on database error', async () => {
      mockDbError = { message: 'DB error' }

      const app = createTestApp()
      const res = await app.fetch(
        new Request('http://localhost/holdings/hold-1', {
          method: 'DELETE',
        }),
        createMockEnv()
      )

      expect(res.status).toBe(500)
      const body = await res.json()
      expect(body.error.code).toBe('DATABASE_ERROR')
    })
  })
})
