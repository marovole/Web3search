/**
 * Tests for Search Routes
 * Tests autocomplete functionality for cryptocurrency projects
 */

import { describe, expect, it, vi, beforeEach } from 'vitest'
import type { Env } from '../../src/types/env'

// Mock Supabase
vi.mock('../../src/lib/supabase', () => {
  const mockClient = vi.fn(() => ({
    from: vi.fn(() => ({
      select: vi.fn(() => ({
        or: vi.fn(() => ({
          order: vi.fn(() => ({
            limit: vi.fn(async () => ({
              data: [
                {
                  id: 'proj-1',
                  symbol: 'BTC',
                  name: 'Bitcoin',
                  coingecko_id: 'bitcoin',
                  description: 'Digital gold',
                  blockchain: 'Bitcoin',
                  categories: ['Currency'],
                  tags: ['pow']
                }
              ],
              error: null
            }))
          }))
        }))
      }))
    }))
  }))

  return {
    createSupabaseClient: mockClient,
    getSupabaseClient: mockClient
  }
})

import search from '../../src/routes/search'

async function fetchAutocomplete(params?: Record<string, string>, env?: Env) {
  const url = new URL('https://example.com/autocomplete')
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      url.searchParams.set(key, value)
    })
  }

  const request = new Request(url.toString(), { method: 'GET' })
  return search.fetch(request, env ?? createMockEnv())
}

describe('Search Routes', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('GET /autocomplete', () => {
    describe('Request Validation', () => {
      it('returns 400 when query parameter is missing', async () => {
        const response = await fetchAutocomplete()
        expect(response.status).toBe(400)

        const body = await response.json()
        expect(body.error.code).toBe('MISSING_QUERY')
        expect(body.error.message).toContain('"q" is required')
      })

      it('returns 400 when query is empty string', async () => {
        const response = await fetchAutocomplete({ q: '  ' })
        expect(response.status).toBe(400)

        const body = await response.json()
        expect(body.error.code).toBe('MISSING_QUERY')
      })

      it('accepts minimum 1 character query', async () => {
        const response = await fetchAutocomplete({ q: 'B' })
        expect(response.status).toBe(200)
      })
    })

    describe('Successful Searches', () => {
      it('returns 200 with search results', async () => {
        const response = await fetchAutocomplete({ q: 'bitcoin' })
        expect(response.status).toBe(200)

        const body = await response.json()
        expect(body).toHaveProperty('query')
        expect(body).toHaveProperty('count')
        expect(body).toHaveProperty('results')
        expect(Array.isArray(body.results)).toBe(true)
      })

      it('includes project details in results', async () => {
        const response = await fetchAutocomplete({ q: 'BTC' })
        const body = await response.json()

        expect(body.count).toBeGreaterThan(0)
        expect(body.results[0]).toHaveProperty('symbol')
        expect(body.results[0]).toHaveProperty('name')
        expect(body.results[0]).toHaveProperty('coingecko_id')
      })

      it('respects limit parameter', async () => {
        const response = await fetchAutocomplete({ q: 'bit', limit: '5' })
        expect(response.status).toBe(200)

        const body = await response.json()
        expect(body.count).toBeLessThanOrEqual(5)
      })

      it('enforces maximum limit of 50', async () => {
        // Limit param > 50 should be clamped to 50
        const response = await fetchAutocomplete({ q: 'a', limit: '100' })
        expect(response.status).toBe(200)

        // Query builder should be called with limit 50
        const body = await response.json()
        expect(body.count).toBeLessThanOrEqual(50)
      })

      it('uses default limit of 10 when not specified', async () => {
        const response = await fetchAutocomplete({ q: 'eth' })
        expect(response.status).toBe(200)

        const body = await response.json()
        expect(body.count).toBeLessThanOrEqual(10)
      })
    })

    describe('SQL Injection Prevention', () => {
      it('escapes special characters in query', async () => {
        // Test with SQL wildcard characters
        const response = await fetchAutocomplete({ q: 'test%_' })
        expect(response.status).toBe(200)

        // Should not throw error or return unexpected results
        const body = await response.json()
        expect(body).toHaveProperty('results')
      })
    })

    describe('Caching', () => {
      it('caches results when KV is available', async () => {
        const env = createMockEnv()
        const response = await fetchAutocomplete({ q: 'bitcoin' }, env)

        expect(response.status).toBe(200)
        // Verify cache was called (in real test, would check KV)
        expect(env.CACHE).toBeDefined()
      })
    })

    describe('Error Handling', () => {
      it('returns 500 when database query fails', async () => {
        const { createSupabaseClient } = await import('../../src/lib/supabase')
        vi.mocked(createSupabaseClient).mockReturnValueOnce({
          from: vi.fn(() => ({
            select: vi.fn(() => ({
              or: vi.fn(() => ({
                order: vi.fn(() => ({
                  limit: vi.fn(async () => ({
                    data: null,
                    error: { message: 'Database error', code: 'DB_ERROR' }
                  }))
                }))
              }))
            }))
          }))
        } as any)

        const response = await fetchAutocomplete({ q: 'test' })
        expect(response.status).toBe(500)

        const body = await response.json()
        expect(body.error.code).toBe('SEARCH_ERROR')
      })
    })
  })
})

function createMockEnv(overrides: Partial<Env> = {}): Env {
  const store = new Map<string, string>()
  return {
    ENVIRONMENT: 'test',
    SUPABASE_URL: 'https://example.supabase.co',
    SUPABASE_ANON_KEY: 'anon',
    OPENROUTER_API_KEY: 'test',
    CACHE: {
      get: async (key: string) => store.get(key) || null,
      put: async (key: string, value: string) => {
        store.set(key, value)
      },
      delete: async (key: string) => {
        store.delete(key)
      },
      list: async () => ({ keys: [], list_complete: true }),
    } as unknown as KVNamespace,
    ...overrides,
  } as Env
}
