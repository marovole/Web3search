/**
 * Tests for OpenRouter API Client
 * Validates request construction, error handling, and API integration
 */

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  createOpenRouterClient,
  OpenRouterError,
  type OpenRouterPayload,
} from '../../src/lib/openrouter'
import type { Env } from '../../src/types/env'
import type { ChatCompletionMessage } from '../../src/types/chat'

// ============================================
// Test Fixtures
// ============================================

const OPENROUTER_API_URL = 'https://openrouter.ai/api/v1/chat/completions'

const BASE_MESSAGES: ChatCompletionMessage[] = [
  { role: 'user', content: 'Hello, how are you?' },
]

const BASE_PAYLOAD: OpenRouterPayload = {
  model: 'anthropic/claude-3.5-sonnet',
  messages: BASE_MESSAGES,
}

/**
 * Create a mock environment for testing
 */
function createMockEnv(overrides: Partial<Env> = {}): Env {
  return {
    ENVIRONMENT: 'production',
    SUPABASE_URL: 'https://example.supabase.co',
    SUPABASE_ANON_KEY: 'anon-key',
    OPENROUTER_API_KEY: 'test-api-key-12345',
    CACHE: {} as KVNamespace,
    ...overrides,
  }
}

// ============================================
// OpenRouter Client Tests
// ============================================

describe('createOpenRouterClient', () => {
  const fetchMock = vi.fn()

  beforeEach(() => {
    // Mock global fetch
    vi.stubGlobal('fetch', fetchMock)
  })

  afterEach(() => {
    // Restore original implementations
    vi.restoreAllMocks()
    fetchMock.mockReset()
  })

  describe('Client Creation', () => {
    it('throws error when API key is missing', () => {
      const env = createMockEnv({ OPENROUTER_API_KEY: '' })

      expect(() => createOpenRouterClient(env)).toThrow(
        'OPENROUTER_API_KEY is not configured'
      )
    })

    it('throws error when API key is undefined', () => {
      const env = createMockEnv()
      // @ts-expect-error - Intentionally testing undefined API key
      env.OPENROUTER_API_KEY = undefined

      expect(() => createOpenRouterClient(env)).toThrow(
        'OPENROUTER_API_KEY is not configured'
      )
    })

    it('creates client successfully with valid API key', () => {
      const env = createMockEnv()
      const client = createOpenRouterClient(env)

      expect(client).toBeDefined()
      expect(client.request).toBeInstanceOf(Function)
    })
  })

  describe('Request Construction', () => {
    it('sends POST request with correct URL', async () => {
      const env = createMockEnv()
      const client = createOpenRouterClient(env)

      const mockResponse = new Response(JSON.stringify({ success: true }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
      fetchMock.mockResolvedValue(mockResponse)

      await client.request(BASE_PAYLOAD)

      expect(fetchMock).toHaveBeenCalledOnce()
      expect(fetchMock).toHaveBeenCalledWith(
        OPENROUTER_API_URL,
        expect.any(Object)
      )
    })

    it('includes required headers', async () => {
      const env = createMockEnv({ OPENROUTER_API_KEY: 'custom-key' })
      const client = createOpenRouterClient(env)

      const mockResponse = new Response('{}', { status: 200 })
      fetchMock.mockResolvedValue(mockResponse)

      await client.request(BASE_PAYLOAD)

      const callArgs = fetchMock.mock.calls[0][1]
      expect(callArgs.method).toBe('POST')
      expect(callArgs.headers).toEqual({
        Authorization: 'Bearer custom-key',
        'HTTP-Referer': 'https://web3search.pages.dev',
        'X-Title': 'Web3search',
        'Content-Type': 'application/json',
      })
    })

    it('sends payload as JSON string in body', async () => {
      const env = createMockEnv()
      const client = createOpenRouterClient(env)

      const mockResponse = new Response('{}', { status: 200 })
      fetchMock.mockResolvedValue(mockResponse)

      const payload: OpenRouterPayload = {
        model: 'openai/gpt-4',
        messages: [{ role: 'user', content: 'Test message' }],
        temperature: 0.7,
        max_tokens: 1000,
      }

      await client.request(payload)

      const callArgs = fetchMock.mock.calls[0][1]
      expect(callArgs.body).toBe(JSON.stringify(payload))
    })

    it('preserves streaming flag in payload', async () => {
      const env = createMockEnv()
      const client = createOpenRouterClient(env)

      const mockResponse = new Response('{}', { status: 200 })
      fetchMock.mockResolvedValue(mockResponse)

      await client.request({ ...BASE_PAYLOAD, stream: true })

      const callArgs = fetchMock.mock.calls[0][1]
      const sentBody = JSON.parse(callArgs.body)
      expect(sentBody.stream).toBe(true)
    })

    it('includes abort signal for timeout handling', async () => {
      const env = createMockEnv()
      const client = createOpenRouterClient(env)

      const mockResponse = new Response('{}', { status: 200 })
      fetchMock.mockResolvedValue(mockResponse)

      await client.request(BASE_PAYLOAD)

      const callArgs = fetchMock.mock.calls[0][1]
      expect(callArgs.signal).toBeInstanceOf(AbortSignal)
    })
  })

  describe('Successful Responses', () => {
    it('returns response object for successful request', async () => {
      const env = createMockEnv()
      const client = createOpenRouterClient(env)

      const mockResponse = new Response(
        JSON.stringify({
          id: 'completion-123',
          choices: [{ message: { role: 'assistant', content: 'Hello!' } }],
        }),
        {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }
      )
      fetchMock.mockResolvedValue(mockResponse)

      const result = await client.request(BASE_PAYLOAD)

      expect(result).toBe(mockResponse)
      expect(result.status).toBe(200)
    })

    it('handles streaming response with correct content type', async () => {
      const env = createMockEnv()
      const client = createOpenRouterClient(env)

      const mockResponse = new Response('data: {"chunk": "test"}', {
        status: 200,
        headers: { 'Content-Type': 'text/event-stream' },
      })
      fetchMock.mockResolvedValue(mockResponse)

      const result = await client.request({ ...BASE_PAYLOAD, stream: true })

      expect(result.status).toBe(200)
      expect(result.headers.get('Content-Type')).toBe('text/event-stream')
    })
  })

  describe('Error Handling', () => {
    it('throws OpenRouterError with JSON body for 400 errors', async () => {
      const env = createMockEnv()
      const client = createOpenRouterClient(env)

      const errorBody = {
        error: {
          code: 'invalid_request',
          message: 'Invalid model specified',
        },
      }

      const mockResponse = new Response(JSON.stringify(errorBody), {
        status: 400,
        headers: { 'Content-Type': 'application/json' },
      })
      fetchMock.mockResolvedValue(mockResponse)

      await expect(client.request(BASE_PAYLOAD)).rejects.toMatchObject({
        name: 'OpenRouterError',
        status: 400,
        payload: errorBody,
        message: 'OpenRouter request failed (400)',
      })
    })

    it('throws OpenRouterError with JSON body for 401 errors', async () => {
      const env = createMockEnv()
      const client = createOpenRouterClient(env)

      const errorBody = { error: 'Unauthorized' }

      const mockResponse = new Response(JSON.stringify(errorBody), {
        status: 401,
        headers: { 'Content-Type': 'application/json' },
      })
      fetchMock.mockResolvedValue(mockResponse)

      await expect(client.request(BASE_PAYLOAD)).rejects.toMatchObject({
        status: 401,
        payload: errorBody,
      })
    })

    it('throws OpenRouterError with JSON body for 429 rate limit errors', async () => {
      const env = createMockEnv()
      const client = createOpenRouterClient(env)

      const errorBody = { error: 'Rate limit exceeded' }

      const mockResponse = new Response(JSON.stringify(errorBody), {
        status: 429,
        headers: { 'Content-Type': 'application/json' },
      })
      fetchMock.mockResolvedValue(mockResponse)

      await expect(client.request(BASE_PAYLOAD)).rejects.toMatchObject({
        status: 429,
        payload: errorBody,
      })
    })

    it('throws OpenRouterError with JSON body for 500 errors', async () => {
      const env = createMockEnv()
      const client = createOpenRouterClient(env)

      const errorBody = { error: 'Internal server error' }

      const mockResponse = new Response(JSON.stringify(errorBody), {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
      })
      fetchMock.mockResolvedValue(mockResponse)

      await expect(client.request(BASE_PAYLOAD)).rejects.toMatchObject({
        status: 500,
        payload: errorBody,
      })
    })

    it('falls back to text body when JSON parsing fails', async () => {
      const env = createMockEnv()
      const client = createOpenRouterClient(env)

      const mockResponse = {
        ok: false,
        status: 502,
        json: vi.fn().mockRejectedValue(new Error('Invalid JSON')),
        text: vi.fn().mockResolvedValue('Bad Gateway'),
      } as unknown as Response

      fetchMock.mockResolvedValue(mockResponse)

      await expect(client.request(BASE_PAYLOAD)).rejects.toMatchObject({
        status: 502,
        payload: 'Bad Gateway',
      })
    })

    it('includes original error payload in OpenRouterError', async () => {
      const env = createMockEnv()
      const client = createOpenRouterClient(env)

      const errorPayload = {
        error: {
          type: 'invalid_request_error',
          code: 'model_not_found',
          message: 'Model does not exist',
          param: 'model',
        },
      }

      const mockResponse = new Response(JSON.stringify(errorPayload), {
        status: 404,
        headers: { 'Content-Type': 'application/json' },
      })
      fetchMock.mockResolvedValue(mockResponse)

      try {
        await client.request(BASE_PAYLOAD)
        expect.fail('Should have thrown OpenRouterError')
      } catch (error) {
        expect(error).toBeInstanceOf(OpenRouterError)
        expect((error as OpenRouterError).status).toBe(404)
        expect((error as OpenRouterError).payload).toEqual(errorPayload)
      }
    })
  })

  describe('Payload Variations', () => {
    it('supports optional temperature parameter', async () => {
      const env = createMockEnv()
      const client = createOpenRouterClient(env)

      const mockResponse = new Response('{}', { status: 200 })
      fetchMock.mockResolvedValue(mockResponse)

      await client.request({
        ...BASE_PAYLOAD,
        temperature: 0.5,
      })

      const callArgs = fetchMock.mock.calls[0][1]
      const sentBody = JSON.parse(callArgs.body)
      expect(sentBody.temperature).toBe(0.5)
    })

    it('supports optional max_tokens parameter', async () => {
      const env = createMockEnv()
      const client = createOpenRouterClient(env)

      const mockResponse = new Response('{}', { status: 200 })
      fetchMock.mockResolvedValue(mockResponse)

      await client.request({
        ...BASE_PAYLOAD,
        max_tokens: 2000,
      })

      const callArgs = fetchMock.mock.calls[0][1]
      const sentBody = JSON.parse(callArgs.body)
      expect(sentBody.max_tokens).toBe(2000)
    })

    it('supports optional top_p parameter', async () => {
      const env = createMockEnv()
      const client = createOpenRouterClient(env)

      const mockResponse = new Response('{}', { status: 200 })
      fetchMock.mockResolvedValue(mockResponse)

      await client.request({
        ...BASE_PAYLOAD,
        top_p: 0.9,
      })

      const callArgs = fetchMock.mock.calls[0][1]
      const sentBody = JSON.parse(callArgs.body)
      expect(sentBody.top_p).toBe(0.9)
    })

    it('supports optional metadata parameter', async () => {
      const env = createMockEnv()
      const client = createOpenRouterClient(env)

      const mockResponse = new Response('{}', { status: 200 })
      fetchMock.mockResolvedValue(mockResponse)

      const metadata = { user_id: 'user-123', session_id: 'session-456' }

      await client.request({
        ...BASE_PAYLOAD,
        metadata,
      })

      const callArgs = fetchMock.mock.calls[0][1]
      const sentBody = JSON.parse(callArgs.body)
      expect(sentBody.metadata).toEqual(metadata)
    })

    it('handles complex multi-turn conversations', async () => {
      const env = createMockEnv()
      const client = createOpenRouterClient(env)

      const mockResponse = new Response('{}', { status: 200 })
      fetchMock.mockResolvedValue(mockResponse)

      const messages: ChatCompletionMessage[] = [
        { role: 'user', content: 'What is Bitcoin?' },
        {
          role: 'assistant',
          content: 'Bitcoin is a decentralized cryptocurrency...',
        },
        { role: 'user', content: 'How does it work?' },
      ]

      await client.request({
        model: 'anthropic/claude-3.5-sonnet',
        messages,
      })

      const callArgs = fetchMock.mock.calls[0][1]
      const sentBody = JSON.parse(callArgs.body)
      expect(sentBody.messages).toEqual(messages)
    })
  })
})
