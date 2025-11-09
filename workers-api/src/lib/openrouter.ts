/**
 * OpenRouter API Client
 * Wrapper for OpenRouter API with native fetch, timeout handling, and error types
 */

import type { Env } from '../types/env'
import type { ChatCompletionMessage } from '../types/chat'

const OPENROUTER_URL = 'https://openrouter.ai/api/v1/chat/completions'
const DEFAULT_TIMEOUT_MS = 30_000

/**
 * Payload for OpenRouter chat completion request
 */
export interface OpenRouterPayload {
  model: string
  messages: ChatCompletionMessage[]
  stream?: boolean
  temperature?: number
  max_tokens?: number
  top_p?: number
  metadata?: Record<string, unknown>
}

/**
 * OpenRouter client interface
 */
export interface OpenRouterClient {
  request: (payload: OpenRouterPayload) => Promise<Response>
}

/**
 * Custom error for OpenRouter API failures
 * Includes HTTP status code and response payload for debugging
 */
export class OpenRouterError extends Error {
  constructor(
    public status: number,
    public payload: unknown
  ) {
    super(`OpenRouter request failed (${status})`)
    this.name = 'OpenRouterError'
  }
}

/**
 * Create OpenRouter API client
 * Uses native fetch with timeout and proper error handling
 *
 * @param env - Cloudflare Workers environment bindings
 * @returns OpenRouter client instance
 * @throws Error if OPENROUTER_API_KEY is not configured
 */
export const createOpenRouterClient = (env: Env): OpenRouterClient => {
  const apiKey = env.OPENROUTER_API_KEY
  if (!apiKey) {
    throw new Error('OPENROUTER_API_KEY is not configured')
  }

  const headers = {
    'Authorization': `Bearer ${apiKey}`,
    'HTTP-Referer': 'https://web3search.pages.dev',
    'X-Title': 'Web3search',
    'Content-Type': 'application/json',
  }

  const request: OpenRouterClient['request'] = async (payload) => {
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), DEFAULT_TIMEOUT_MS)

    try {
      const response = await fetch(OPENROUTER_URL, {
        method: 'POST',
        headers,
        body: JSON.stringify(payload),
        signal: controller.signal,
      })

      if (!response.ok) {
        let body: unknown
        try {
          body = await response.json()
        } catch {
          body = await response.text()
        }
        throw new OpenRouterError(response.status, body)
      }

      return response
    } finally {
      clearTimeout(timeout)
    }
  }

  return { request }
}
