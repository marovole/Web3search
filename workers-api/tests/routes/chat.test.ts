/**
 * Tests for Chat Routes - Deep Research SSE Endpoint
 * Focus on GET /deep-research/stream and rate limiting
 */

import { beforeEach, describe, expect, it, vi } from 'vitest'
import { Hono } from 'hono'
import type { Env } from '../../src/types/env'

// Mock deep-research functions (partial mock - preserve default export)
vi.mock('../../src/routes/deep-research', async () => {
  const actual = await vi.importActual<
    typeof import('../../src/routes/deep-research')
  >('../../src/routes/deep-research')

  return {
    ...actual,
    __esModule: true,
    default: actual.default, // Explicitly preserve the default export (the Hono router)
    generateResearchPlan: vi.fn(async () => ({
      search_queries: ['web3 fundamentals'],
      plan: 'mock plan',
    })),
    searchSources: vi.fn(async (_queries: string[], _env: any) => [
      {
        id: 'source-1',
        query: 'web3 fundamentals',
        provider: 'brave',
        url: 'https://example.com/source/1',
        title: 'Mock Source',
        snippet: 'A mock snippet',
        relevance_score: 0.8,
        accessed_at: new Date().toISOString(),
      },
    ]),
    analyzeSources: vi.fn(async () => ({
      citations: [],
      tokens: { prompt: 0, completion: 0 },
      cost: 0,
    })),
    synthesizeFindings: vi.fn(async () => ({
      result: {
        summary: 'mock summary',
        answer: 'mock answer',
        key_findings: [],
        sources: [],
        citations: [],
        research_depth: 'standard',
        total_sources: 0,
        total_citations: 0,
        confidence_score: 1,
      },
      summary: 'mock summary',
      answer: 'mock answer',
    })),
  }
})

// Mock Supabase client
vi.mock('../../src/lib/supabase', () => ({
  createSupabaseClient: vi.fn(() => {
    const conversationUpsert = vi.fn(async () => ({ error: null }))
    const createBuilder = () => {
      const promise = Promise.resolve({ data: [], error: null })
      return {
        select: vi.fn(() => ({
          single: vi.fn(async () => ({ data: { id: 'msg-id' }, error: null })),
        })),
        then: promise.then.bind(promise),
        catch: promise.catch.bind(promise),
      }
    }
    const messageInsert = vi.fn(() => createBuilder())

    return {
      from: vi.fn((table: string) => {
        if (table === 'conversations') {
          return { upsert: conversationUpsert }
        }
        if (table === 'messages') {
          return { insert: messageInsert }
        }
        return { upsert: vi.fn(async () => ({ error: null })) }
      }),
    }
  }),
}))

import deepResearch from '../../src/routes/deep-research'

// Create a test app that mimics production routing structure
// This ensures the router is mounted with the correct path prefix
const deepResearchApp = new Hono<{ Bindings: Env }>()
deepResearchApp.route('/api/v1/deep-research', deepResearch)

// Use the full production path for testing
const BASE_URL = 'https://example.com/api/v1/deep-research/stream'

async function fetchDeepResearch({
  query,
  env,
}: {
  query?: string
  env?: Env
} = {}) {
  const url = new URL(BASE_URL)
  if (query) {
    url.searchParams.set('query', query)
  }

  const request = new Request(url.toString(), {
    method: 'GET',
    headers: {
      'cf-connecting-ip': '203.0.113.42',
    },
  })

  return deepResearchApp.fetch(request, env ?? createMockEnv())
}

describe('Deep Research SSE endpoint', () => {
  it('accepts valid query parameters', async () => {
    const response = await fetchDeepResearch({ query: 'web3 fundamentals' })
    expect(response.status).toBe(200)
  })

  it('returns 400 when query is missing', async () => {
    const response = await fetchDeepResearch()
    expect(response.status).toBe(400)
    const body = await response.json()
    expect(body.error.code).toBe('MISSING_QUERY')
  })

  it('returns 414 when query exceeds maximum length', async () => {
    const response = await fetchDeepResearch({ query: 'a'.repeat(2001) })
    expect(response.status).toBe(414)
    const body = await response.json()
    expect(body.error.code).toBe('URI_TOO_LONG')
  })

  it('sets text/event-stream content type', async () => {
    const response = await fetchDeepResearch({ query: 'tokenized data' })
    expect(response.headers.get('Content-Type')).toBe('text/event-stream')
    await response.body?.cancel?.()
  })
})

function createMockEnv(overrides: Partial<Env> = {}): Env {
  return {
    ENVIRONMENT: 'test',
    SUPABASE_URL: 'https://example.supabase.co',
    SUPABASE_ANON_KEY: 'anon',
    OPENROUTER_API_KEY: 'test',
    CACHE: createInMemoryKV(),
    ...overrides,
  }
}

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

