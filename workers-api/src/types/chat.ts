/**
 * Chat-related shared types
 * Type definitions for chat API, messages, and conversations
 */

export type ChatRole = 'system' | 'user' | 'assistant'

/**
 * Request body for chat endpoints
 */
export interface ChatRequestBody {
  query: string
  conversation_id?: string
  model?: string
  stream?: boolean
  temperature?: number
  max_tokens?: number
  metadata?: Record<string, unknown>
}

/**
 * Standard chat completion message format
 * Compatible with OpenRouter and other providers
 */
export interface ChatCompletionMessage {
  role: ChatRole
  content: string
}

/**
 * Message record stored in database
 * Extends ChatCompletionMessage with persistence fields
 */
export interface MessageRecord extends ChatCompletionMessage {
  id?: string
  conversation_id: string
  created_at?: string
  metadata?: Record<string, unknown> | null
}

/**
 * Response body for non-streaming chat requests
 */
export interface ChatResponseBody {
  conversation_id: string
  message_id: string
  content: string
  model: string
  stream: boolean
}

/**
 * SSE stream chunk for streaming chat responses
 */
export interface ChatStreamChunk {
  delta: string
}
