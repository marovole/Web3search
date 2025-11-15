/**
 * Tests for Reports Routes - Report Generation Endpoint
 * Tests streaming report generation, token calculation, and Supabase persistence
 */

import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { ExecutionContext } from '@cloudflare/workers-types'
import type { Env } from '../../src/types/env'

// Mock OpenRouter
vi.mock('../../src/lib/openrouter', () => ({
  createOpenRouterClient: vi.fn(() => ({
    request: vi.fn(async () => {
      return new Response(
        JSON.stringify({
          choices: [
            {
              message: {
                content: 'Mock section content for testing purposes.',
              },
            },
          ],
          usage: {
            prompt_tokens: 100,
            completion_tokens: 50,
            total_tokens: 150,
          },
        }),
        {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }
      )
    }),
  })),
}))

// Mock Supabase
vi.mock('../../src/lib/supabase', () => ({
  createSupabaseClient: vi.fn(() => ({
    from: vi.fn((table: string) => {
      if (table === 'reports') {
        return {
          insert: vi.fn(() => ({
            select: vi.fn(() => ({
              single: vi.fn(async () => ({
                data: { id: 'report-123' },
                error: null,
              })),
            })),
          })),
        }
      }
      return {
        upsert: vi.fn(async () => ({ error: null })),
      }
    }),
  })),
}))

import { Hono } from 'hono'
import reports from '../../src/routes/reports'

// Create a test app that mimics production routing structure
const reportsApp = new Hono<{ Bindings: Env }>()
reportsApp.route('/api/v1/reports', reports)

const BASE_URL = 'https://example.com/api/v1/reports/generate'

async function fetchReportGenerate({
  body,
  env,
  executionCtx,
}: {
  body?: Record<string, any>
  env?: Env
  executionCtx?: ExecutionContext
} = {}) {
  const request = new Request(BASE_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'cf-connecting-ip': '203.0.113.42',
    },
    body: body ? JSON.stringify(body) : undefined,
  })

  return reportsApp.fetch(
    request,
    env ?? createMockEnv(),
    executionCtx ?? createMockExecutionContext()
  )
}

describe('Reports - Generate Endpoint', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Request Validation', () => {
    it('returns 400 when body is invalid JSON', async () => {
      const request = new Request(BASE_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'cf-connecting-ip': '203.0.113.42',
        },
        body: 'invalid json',
      })

      const response = await reportsApp.fetch(
        request,
        createMockEnv(),
        createMockExecutionContext()
      )
      expect(response.status).toBe(400)

      const body = await response.json()
      expect(body.error.code).toBe('INVALID_JSON')
    })

    it('returns 400 when topic is missing', async () => {
      const response = await fetchReportGenerate({
        body: { sections: [] },
      })
      expect(response.status).toBe(400)

      const body = await response.json()
      expect(body.error.code).toBe('INVALID_REQUEST')
    })

    it('returns 400 when sections array is missing', async () => {
      const response = await fetchReportGenerate({
        body: { topic: 'Bitcoin' },
      })
      expect(response.status).toBe(400)

      const body = await response.json()
      expect(body.error.code).toBe('INVALID_REQUEST')
    })

    it('returns 400 when sections array is empty', async () => {
      const response = await fetchReportGenerate({
        body: { topic: 'Bitcoin', sections: [] },
      })
      expect(response.status).toBe(400)

      const body = await response.json()
      expect(body.error.code).toBe('INVALID_REQUEST')
    })

    it('returns 400 when section is missing id', async () => {
      const response = await fetchReportGenerate({
        body: {
          topic: 'Bitcoin',
          sections: [{ title: 'Introduction' }],
        },
      })
      expect(response.status).toBe(400)

      const body = await response.json()
      expect(body.error.code).toBe('INVALID_SECTION')
    })

    it('returns 400 when section is missing title', async () => {
      const response = await fetchReportGenerate({
        body: {
          topic: 'Bitcoin',
          sections: [{ id: 'intro' }],
        },
      })
      expect(response.status).toBe(400)

      const body = await response.json()
      expect(body.error.code).toBe('INVALID_SECTION')
    })
  })

  describe('Streaming Report Generation', () => {
    it('returns 200 and text/event-stream content type', async () => {
      const response = await fetchReportGenerate({
        body: {
          topic: 'Bitcoin Analysis',
          sections: [
            { id: 'intro', title: 'Introduction' },
            { id: 'analysis', title: 'Market Analysis' },
            { id: 'conclusion', title: 'Conclusion' },
          ],
        },
      })

      expect(response.status).toBe(200)
      expect(response.headers.get('Content-Type')).toBe('text/event-stream')
      expect(response.headers.get('Cache-Control')).toBe('no-cache')
      expect(response.headers.get('Connection')).toBe('keep-alive')

      // Clean up stream
      await response.body?.cancel()
    })

    it('emits report_start event with metadata', async () => {
      const response = await fetchReportGenerate({
        body: {
          topic: 'Ethereum',
          sections: [{ id: 's1', title: 'Section 1' }],
        },
      })

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) throw new Error('No reader available')

      const { value } = await reader.read()
      const text = decoder.decode(value)

      expect(text).toContain('data:')
      expect(text).toContain('report_start')
      expect(text).toContain('Ethereum')
      expect(text).toContain('total_sections')

      reader.cancel()
    })
  })

  describe('Token Usage Calculation', () => {
    it('accumulates tokens from multiple sections', async () => {
      const response = await fetchReportGenerate({
        body: {
          topic: 'DeFi',
          sections: [
            { id: 's1', title: 'Section 1' },
            { id: 's2', title: 'Section 2' },
          ],
        },
      })

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) throw new Error('No reader available')

      let fullText = ''
      let done = false

      while (!done) {
        const { value, done: streamDone } = await reader.read()
        done = streamDone
        if (value) {
          fullText += decoder.decode(value)
        }
      }

      // Should have report_complete event with tokens_used
      expect(fullText).toContain('report_complete')
      expect(fullText).toContain('tokens_used')

      // With 2 sections @ 150 tokens each = 300 total
      // Extract the complete JSON object from SSE data line
      const lines = fullText.split('\n')
      const completeDataLine = lines.find(line =>
        line.startsWith('data:') && line.includes('report_complete')
      )
      if (completeDataLine) {
        const jsonStr = completeDataLine.replace(/^data:\s*/, '')
        const eventData = JSON.parse(jsonStr)
        expect(eventData.tokens_used).toBeGreaterThan(0)
        expect(eventData.tokens_used).toBe(300) // 2 sections * 150 tokens
      }
    })
  })

  describe('Error Handling', () => {
    it('handles OpenRouter API failures gracefully', async () => {
      // Override the mock to simulate failure
      const { createOpenRouterClient } = await import('../../src/lib/openrouter')
      vi.mocked(createOpenRouterClient).mockReturnValueOnce({
        request: vi.fn(async () => {
          throw new Error('Network error')
        }),
      } as any)

      const response = await fetchReportGenerate({
        body: {
          topic: 'Test',
          sections: [{ id: 's1', title: 'Section 1' }],
        },
      })

      expect(response.status).toBe(200) // Still returns stream
      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) throw new Error('No reader available')

      let fullText = ''
      let done = false

      while (!done) {
        const { value, done: streamDone } = await reader.read()
        done = streamDone
        if (value) {
          fullText += decoder.decode(value)
        }
      }

      // Should contain section_error event
      expect(fullText).toContain('section_error')
    })
  })

  describe('Supabase Persistence', () => {
    it('saves report when save_to_database is true', async () => {
      const { createSupabaseClient } = await import('../../src/lib/supabase')
      const mockInsert = vi.fn(() => ({
        select: vi.fn(() => ({
          single: vi.fn(async () => ({
            data: { id: 'saved-report-id' },
            error: null,
          })),
        })),
      }))

      vi.mocked(createSupabaseClient).mockReturnValueOnce({
        from: vi.fn(() => ({
          insert: mockInsert,
        })),
      } as any)

      const response = await fetchReportGenerate({
        body: {
          topic: 'Solana',
          sections: [{ id: 's1', title: 'Overview' }],
          save_to_database: true,
        },
      })

      const reader = response.body?.getReader()
      if (!reader) throw new Error('No reader available')

      // Consume the entire stream
      let done = false
      while (!done) {
        const { done: streamDone } = await reader.read()
        done = streamDone
      }

      // Verify insert was called
      expect(mockInsert).toHaveBeenCalled()
    })

    it('does not save report when save_to_database is false', async () => {
      const { createSupabaseClient } = await import('../../src/lib/supabase')
      const mockInsert = vi.fn()

      vi.mocked(createSupabaseClient).mockReturnValueOnce({
        from: vi.fn(() => ({
          insert: mockInsert,
        })),
      } as any)

      const response = await fetchReportGenerate({
        body: {
          topic: 'Cardano',
          sections: [{ id: 's1', title: 'Analysis' }],
          save_to_database: false,
        },
      })

      const reader = response.body?.getReader()
      if (!reader) throw new Error('No reader available')

      // Consume the entire stream
      let done = false
      while (!done) {
        const { done: streamDone } = await reader.read()
        done = streamDone
      }

      // Verify insert was NOT called
      expect(mockInsert).not.toHaveBeenCalled()
    })
  })
})

function createMockEnv(overrides: Partial<Env> = {}): Env {
  return {
    ENVIRONMENT: 'test',
    SUPABASE_URL: 'https://example.supabase.co',
    SUPABASE_ANON_KEY: 'anon-key',
    OPENROUTER_API_KEY: 'test-key',
    CACHE: createInMemoryKV(),
    ...overrides,
  } as Env
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

function createMockExecutionContext(): ExecutionContext {
  return {
    waitUntil: vi.fn(),
    passThroughOnException: vi.fn(),
  } as unknown as ExecutionContext
}
