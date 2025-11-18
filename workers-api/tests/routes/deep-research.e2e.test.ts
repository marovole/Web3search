/**
 * End-to-end tests for Deep Research workflow
 *
 * Tests the complete research pipeline:
 * - POST /api/v1/deep-research - Create research task
 * - GET /api/v1/deep-research/:id - Retrieve task status
 * - GET /api/v1/deep-research/stream - Stream research results via SSE
 *
 * All external dependencies (Supabase, OpenRouter, Search Providers) are mocked
 * to ensure tests are fast, deterministic, and independent of external services.
 */

import { beforeEach, describe, expect, it, vi } from 'vitest'
import { Hono } from 'hono'
import type { ExecutionContext } from '@cloudflare/workers-types'
import type { Env } from '../../src/types/env'

// ============================================================================
// Test Fixtures
// ============================================================================

/** Mock search results returned by search providers */
const MOCK_SEARCH_RESULTS = [
  {
    id: 'brave-web3-1',
    query: 'web3 fundamentals',
    provider: 'brave',
    url: 'https://example.com/source/1',
    title: 'Understanding Web3: A Comprehensive Guide',
    snippet: 'Web3 represents the next generation of the internet...',
    relevance_score: 0.9,
    accessed_at: new Date().toISOString(),
  },
]

// ============================================================================
// Mock Helper Functions
// ============================================================================

type TaskFetchResult = { data: Record<string, unknown> | null; error: unknown }

/** Creates an in-memory KV namespace for testing */
const createInMemoryKV = (): KVNamespace => {
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

/** Creates a mock ExecutionContext for Workers environment */
function createExecutionContext(): ExecutionContext {
  return {
    waitUntil: vi.fn(),
    passThroughOnException: vi.fn(),
  } as unknown as ExecutionContext
}

/** Creates a mock Env with sensible defaults */
function createMockEnv(overrides: Partial<Env> = {}): Env {
  return {
    ENVIRONMENT: 'test',
    SUPABASE_URL: 'https://example.supabase.co',
    SUPABASE_ANON_KEY: 'test-anon-key',
    OPENROUTER_API_KEY: 'test-openrouter-key',
    CACHE: createInMemoryKV(),
    CLIENT_SESSION_ID: 'test-session-123',
    ...overrides,
  } as Env
}

/** Creates a mock Supabase client with configurable responses */
function createSupabaseMock(getTaskResult: () => TaskFetchResult) {
  const conversationUpsert = vi.fn(async () => ({ error: null }))
  const messageInsert = vi.fn(async () => ({ error: null, data: { id: 'msg-1' } }))
  const taskInsert = vi.fn(async () => ({ error: null, data: { id: 'task-123' } }))

  const buildTaskQuery = () => ({
    select: vi.fn().mockReturnThis(),
    eq: vi.fn().mockReturnThis(),
    single: vi.fn(async () => getTaskResult()),
  })

  const from = vi.fn((table: string) => {
    if (table === 'conversations') return { upsert: conversationUpsert }
    if (table === 'messages') return { insert: messageInsert }
    if (table === 'deep_research_tasks') {
      return {
        insert: taskInsert,
        select: vi.fn(() => buildTaskQuery()),
        update: vi.fn(async () => ({ error: null })),
      }
    }
    return { insert: vi.fn(async () => ({ error: null })) }
  })

  return { from, conversationUpsert, messageInsert, taskInsert }
}

// ============================================================================
// Global Test State
// ============================================================================

let currentTaskFetch: TaskFetchResult = {
  data: { id: 'task-123', status: 'pending', result: null },
  error: null,
}

let currentSupabase = createSupabaseMock(() => currentTaskFetch)

// ============================================================================
// Module Mocks
// ============================================================================

vi.mock('../../src/lib/supabase', () => ({
  __esModule: true,
  getSupabaseClient: vi.fn(() => currentSupabase),
  createSupabaseClient: vi.fn(() => currentSupabase),
}))

vi.mock('../../src/lib/search-providers', () => ({
  __esModule: true,
  fetchSearchResultsForQueries: vi.fn(async () => MOCK_SEARCH_RESULTS),
}))

import deepResearch, * as deepResearchModule from '../../src/routes/deep-research'

// ============================================================================
// Test App Setup
// ============================================================================

const deepResearchApp = new Hono<{ Bindings: Env }>()
deepResearchApp.route('/api/v1/deep-research', deepResearch)

const BASE_URL = 'https://example.com/api/v1/deep-research'

// ============================================================================
// HTTP Helper Functions
// ============================================================================

/** POST to create a research task */
async function postResearch({
  body,
  env,
  ctx,
}: {
  body: Record<string, unknown>
  env?: Env
  ctx?: ExecutionContext
}) {
  const request = new Request(BASE_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'cf-connecting-ip': '203.0.113.42',
    },
    body: JSON.stringify(body),
  })
  return deepResearchApp.fetch(request, env ?? createMockEnv(), ctx ?? createExecutionContext())
}

/** GET to fetch research task status */
async function fetchResearchTask(id: string, env?: Env) {
  const request = new Request(`${BASE_URL}/${id}`, {
    method: 'GET',
    headers: {
      'cf-connecting-ip': '203.0.113.42',
    },
  })
  return deepResearchApp.fetch(request, env ?? createMockEnv())
}

/** GET stream to receive research results via SSE */
async function streamResearch({ query, env }: { query?: string; env?: Env } = {}) {
  const url = new URL(`${BASE_URL}/stream`)
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

/** Drains an SSE response stream and returns all content */
async function drainSse(response: Response): Promise<string> {
  const reader = response.body?.getReader()
  if (!reader) return ''

  const decoder = new TextDecoder()
  let buffer = ''
  while (true) {
    const { value, done } = await reader.read()
    if (done) break
    if (value) {
      buffer += decoder.decode(value, { stream: true })
    }
  }
  return buffer
}

// ============================================================================
// Test Suite
// ============================================================================

beforeEach(() => {
  currentTaskFetch = {
    data: { id: 'task-123', status: 'pending', result: null },
    error: null,
  }
  currentSupabase = createSupabaseMock(() => currentTaskFetch)
})

describe.skip('Deep Research E2E - TODO: Fix mocking issues', () => {
  it('creates a research task and enqueues background processing', async () => {
    const env = createMockEnv()
    const ctx = createExecutionContext()

    const response = await postResearch({
      body: {
        query: 'Explain web3 fundamentals',
        research_depth: 'comprehensive',
      },
      env,
      ctx,
    })

    expect(response.status).toBe(202)
    const body = (await response.json()) as { task_id: string }
    expect(body.task_id).toBe('task-123')

    // Verify database operations
    expect(currentSupabase.from).toHaveBeenCalledWith('deep_research_tasks')
    expect(ctx.waitUntil).toHaveBeenCalled()
  })

  it('retrieves stored task via GET /:id', async () => {
    currentTaskFetch = {
      data: {
        id: 'task-456',
        status: 'completed',
        result: { summary: 'Research completed successfully' },
      },
      error: null,
    }
    currentSupabase = createSupabaseMock(() => currentTaskFetch)

    const response = await fetchResearchTask('task-456')
    expect(response.status).toBe(200)

    const payload = (await response.json()) as { task: { id: string; status: string } }
    expect(payload.task.id).toBe('task-456')
    expect(payload.task.status).toBe('completed')
  })

  it('streams progress through SSE and persists the assistant message', async () => {
    // Spy on internal research pipeline functions
    const planSpy = vi
      .spyOn(deepResearchModule, 'generateResearchPlan')
      .mockResolvedValue({
        search_queries: ['web3 fundamentals', 'blockchain basics'],
        plan: 'Research plan: investigate web3 concepts',
      })

    const searchSpy = vi
      .spyOn(deepResearchModule, 'searchSources')
      .mockResolvedValue(MOCK_SEARCH_RESULTS)

    const analyzeSpy = vi.spyOn(deepResearchModule, 'analyzeSources').mockResolvedValue({
      citations: [
        {
          source_id: 'brave-web3-1',
          quote: 'Web3 represents the next generation...',
          relevance_score: 0.8,
        },
      ],
      tokens: { prompt: 10, completion: 20 },
      cost: 0,
    })

    const synthesizeSpy = vi.spyOn(deepResearchModule, 'synthesizeFindings').mockResolvedValue({
      result: {
        summary: 'Web3 is the decentralized internet',
        answer: 'Web3 fundamentals include blockchain, smart contracts, and decentralization.',
        key_findings: ['Decentralization', 'Blockchain technology', 'Smart contracts'],
        sources: MOCK_SEARCH_RESULTS,
        citations: [],
        research_depth: 'standard',
        total_sources: 1,
        total_citations: 1,
        confidence_score: 0.9,
      },
      summary: 'Web3 is the decentralized internet',
      answer: 'Web3 fundamentals include blockchain, smart contracts, and decentralization.',
    })

    currentSupabase = createSupabaseMock(() => currentTaskFetch)

    const response = await streamResearch({ query: 'web3 fundamentals' })
    expect(response.status).toBe(200)
    expect(response.headers.get('Content-Type')).toContain('text/event-stream')

    // Drain and verify SSE stream
    const streamPayload = await drainSse(response)
    expect(streamPayload).toContain('progress')
    expect(streamPayload).toContain('complete')

    // Verify message persistence
    expect(currentSupabase.messageInsert).toHaveBeenCalled()
    const calls = currentSupabase.messageInsert.mock.calls
    const assistantInsert = calls[calls.length - 1]?.[0] as { role: string; content: string }
    expect(assistantInsert?.role).toBe('assistant')
    expect(assistantInsert?.content).toContain('Web3 fundamentals')

    // Cleanup spies
    planSpy.mockRestore()
    searchSpy.mockRestore()
    analyzeSpy.mockRestore()
    synthesizeSpy.mockRestore()
  })
})
