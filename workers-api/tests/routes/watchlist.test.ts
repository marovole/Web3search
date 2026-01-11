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

let mockWatchlistData: unknown[] = []
let mockSingleItem: unknown = null
let mockMaxPosition: unknown = null
let mockDbError: unknown = null

vi.mock('../../src/lib/supabase', () => ({
  getSupabaseClient: vi.fn(() => ({
    from: (_table: string) => {
      // Create a complete chain mock that handles all methods
      const createChain = (): Record<string, unknown> => {
        const chain: Record<string, unknown> = {}
        chain.eq = vi.fn().mockReturnValue(chain)
        chain.select = vi.fn().mockReturnValue(chain)
        chain.single = vi.fn().mockImplementation(async () => {
          if (mockDbError) return { data: null, error: mockDbError }
          return { data: mockSingleItem, error: mockSingleItem ? null : { code: 'PGRST116' } }
        })
        chain.order = vi.fn().mockImplementation((col, opts) => {
          // Handle position query for max position
          if (col === 'position' && opts?.ascending === false) {
            return {
              limit: vi.fn().mockReturnValue({
                single: vi.fn().mockImplementation(async () => {
                  return { data: mockMaxPosition, error: null }
                }),
              }),
            }
          }
          // Handle normal order query - return result that acts as promise
          const resultChain = {
            ...chain,
            then: (resolve: (value: { data: unknown; error: unknown }) => void) => {
              if (mockDbError) {
                resolve({ data: null, error: mockDbError })
              } else {
                resolve({ data: mockWatchlistData, error: null })
              }
            },
          }
          return resultChain
        })
        chain.limit = vi.fn().mockReturnValue(chain)
        chain.insert = vi.fn().mockReturnValue(chain)
        chain.update = vi.fn().mockReturnValue(chain)
        chain.delete = vi.fn().mockImplementation(() => {
          const deleteChain: Record<string, unknown> = {}
          deleteChain.eq = vi.fn().mockReturnValue({
            ...deleteChain,
            eq: vi.fn().mockReturnValue({
              then: (resolve: (value: { error: unknown }) => void) => {
                resolve({ error: mockDbError || null })
              },
            }),
            then: (resolve: (value: { error: unknown }) => void) => {
              resolve({ error: mockDbError || null })
            },
          })
          return deleteChain
        })
        return chain
      }

      return createChain()
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

vi.mock('../../src/middlewares/quota', () => ({
  checkWatchlistQuota: () => async (_c: unknown, next: () => Promise<void>) => next(),
  incrementQuota: vi.fn(),
}))

import watchlist from '../../src/routes/watchlist'

function createTestApp() {
  const app = new Hono<{ Bindings: Env }>()
  app.route('/watchlist', watchlist)
  return app
}

describe('Watchlist Routes', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockWatchlistData = []
    mockSingleItem = null
    mockMaxPosition = null
    mockDbError = null
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('GET /watchlist', () => {
    it('returns list of watchlist items for authenticated user', async () => {
      mockWatchlistData = [
        { id: 'watch-1', token_id: 'bitcoin', symbol: 'BTC', name: 'Bitcoin', position: 0 },
        { id: 'watch-2', token_id: 'ethereum', symbol: 'ETH', name: 'Ethereum', position: 1 },
      ]

      const app = createTestApp()
      const res = await app.fetch(
        new Request('http://localhost/watchlist'),
        createMockEnv()
      )

      expect(res.status).toBe(200)
      const body = await res.json()
      expect(body).toHaveProperty('watchlist')
    })

    it('returns 500 on database error', async () => {
      mockDbError = { message: 'DB error' }

      const app = createTestApp()
      const res = await app.fetch(
        new Request('http://localhost/watchlist'),
        createMockEnv()
      )

      expect(res.status).toBe(500)
      const body = await res.json()
      expect(body.error.code).toBe('DATABASE_ERROR')
    })
  })

  describe('POST /watchlist', () => {
    it('adds item to watchlist with valid input', async () => {
      mockMaxPosition = { position: 1 }
      mockSingleItem = {
        id: 'watch-new',
        token_id: 'bitcoin',
        symbol: 'BTC',
        name: 'Bitcoin',
        position: 2,
      }

      const app = createTestApp()
      const res = await app.fetch(
        new Request('http://localhost/watchlist', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            token_id: 'bitcoin',
            symbol: 'BTC',
            name: 'Bitcoin',
          }),
        }),
        createMockEnv()
      )

      expect(res.status).toBe(201)
      const body = await res.json()
      expect(body.item.symbol).toBe('BTC')
    })

    it('returns 400 for missing required fields', async () => {
      const app = createTestApp()
      const res = await app.fetch(
        new Request('http://localhost/watchlist', {
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

    it('returns 409 for duplicate watchlist item', async () => {
      mockMaxPosition = { position: 0 }
      mockDbError = { code: '23505' }
      mockSingleItem = null

      const app = createTestApp()
      const res = await app.fetch(
        new Request('http://localhost/watchlist', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            token_id: 'bitcoin',
            symbol: 'BTC',
            name: 'Bitcoin',
          }),
        }),
        createMockEnv()
      )

      expect(res.status).toBe(409)
      const body = await res.json()
      expect(body.error.code).toBe('ALREADY_EXISTS')
    })
  })

  describe('GET /watchlist/:id', () => {
    it('returns single watchlist item', async () => {
      mockSingleItem = {
        id: 'watch-1',
        token_id: 'bitcoin',
        symbol: 'BTC',
        name: 'Bitcoin',
        position: 0,
      }

      const app = createTestApp()
      const res = await app.fetch(
        new Request('http://localhost/watchlist/watch-1'),
        createMockEnv()
      )

      expect(res.status).toBe(200)
      const body = await res.json()
      expect(body.item.id).toBe('watch-1')
    })

    it('returns 404 for non-existent item', async () => {
      mockSingleItem = null

      const app = createTestApp()
      const res = await app.fetch(
        new Request('http://localhost/watchlist/non-existent'),
        createMockEnv()
      )

      expect(res.status).toBe(404)
      const body = await res.json()
      expect(body.error.code).toBe('NOT_FOUND')
    })
  })

  describe('PATCH /watchlist/:id', () => {
    it('updates watchlist item with valid fields', async () => {
      mockSingleItem = {
        id: 'watch-1',
        notes: 'Updated note',
        tags: ['favorite'],
      }

      const app = createTestApp()
      const res = await app.fetch(
        new Request('http://localhost/watchlist/watch-1', {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ notes: 'Updated note', tags: ['favorite'] }),
        }),
        createMockEnv()
      )

      expect(res.status).toBe(200)
      const body = await res.json()
      expect(body.item.notes).toBe('Updated note')
    })

    it('returns 400 when no valid fields provided', async () => {
      const app = createTestApp()
      const res = await app.fetch(
        new Request('http://localhost/watchlist/watch-1', {
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

    it('returns 404 for non-existent item', async () => {
      mockSingleItem = null
      mockDbError = { code: 'PGRST116' }

      const app = createTestApp()
      const res = await app.fetch(
        new Request('http://localhost/watchlist/non-existent', {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ notes: 'test' }),
        }),
        createMockEnv()
      )

      expect(res.status).toBe(404)
    })
  })

  describe('DELETE /watchlist/:id', () => {
    it('deletes watchlist item successfully', async () => {
      const app = createTestApp()
      const res = await app.fetch(
        new Request('http://localhost/watchlist/watch-1', {
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
        new Request('http://localhost/watchlist/watch-1', {
          method: 'DELETE',
        }),
        createMockEnv()
      )

      expect(res.status).toBe(500)
      const body = await res.json()
      expect(body.error.code).toBe('DATABASE_ERROR')
    })
  })

  describe('POST /watchlist/reorder', () => {
    it('reorders watchlist items successfully', async () => {
      const app = createTestApp()
      const res = await app.fetch(
        new Request('http://localhost/watchlist/reorder', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            items: [
              { id: 'watch-1', position: 1 },
              { id: 'watch-2', position: 0 },
            ],
          }),
        }),
        createMockEnv()
      )

      expect(res.status).toBe(200)
      const body = await res.json()
      expect(body.success).toBe(true)
    })

    it('returns 400 for missing items array', async () => {
      const app = createTestApp()
      const res = await app.fetch(
        new Request('http://localhost/watchlist/reorder', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({}),
        }),
        createMockEnv()
      )

      expect(res.status).toBe(400)
      const body = await res.json()
      expect(body.error.code).toBe('INVALID_INPUT')
    })
  })
})
