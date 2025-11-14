/**
 * Conversation Management Utilities
 * Shared helpers for managing conversations and messages in Supabase
 */

import type { SupabaseClient } from '@supabase/supabase-js'
import type { ChatCompletionMessage } from '../types/chat'

// Re-export ChatCompletionMessage for convenience
export type { ChatCompletionMessage }

/**
 * Ensure conversation exists in database (upsert)
 *
 * @param supabase - Supabase client instance
 * @param conversationId - Unique conversation identifier
 * @param options - Optional conversation metadata
 * @param options.title - Optional conversation title
 *
 * @example
 * ```typescript
 * await ensureConversationExists(supabase, 'conv-123', {
 *   title: 'Deep Research: Bitcoin fundamentals'
 * })
 * ```
 */
export async function ensureConversationExists(
  supabase: SupabaseClient,
  conversationId: string,
  options?: { title?: string }
): Promise<void> {
  const data: Record<string, unknown> = { id: conversationId }
  if (options?.title) {
    data.title = options.title
  }

  const { error } = await supabase
    .from('conversations')
    .upsert(data, { onConflict: 'id' })

  if (error) {
    console.warn('Failed to upsert conversation:', error)
  }
}

/**
 * Fetch conversation history from database
 * Returns recent messages sorted by creation time (oldest first)
 *
 * @param supabase - Supabase client instance
 * @param conversationId - Conversation identifier
 * @param limit - Maximum number of messages to fetch (default: 10)
 * @returns Array of chat messages
 *
 * @example
 * ```typescript
 * const history = await fetchConversationHistory(supabase, 'conv-123', 20)
 * ```
 */
export async function fetchConversationHistory(
  supabase: SupabaseClient,
  conversationId: string,
  limit: number = 10
): Promise<ChatCompletionMessage[]> {
  const { data, error } = await supabase
    .from('messages')
    .select('role, content')
    .eq('conversation_id', conversationId)
    .order('created_at', { ascending: true })
    .limit(limit)

  if (error) {
    console.warn('Unable to fetch conversation history:', error)
    return []
  }

  return (data ?? []) as ChatCompletionMessage[]
}

/**
 * Persist message to database
 * Optionally returns the inserted message ID
 *
 * @param supabase - Supabase client instance
 * @param message - Message data to persist
 * @param message.conversation_id - Parent conversation ID
 * @param message.role - Message role (user or assistant)
 * @param message.content - Message text content
 * @param message.metadata - Optional metadata object
 * @param options - Persistence options
 * @param options.returnId - If true, returns the inserted message ID
 * @returns Message ID if returnId=true, otherwise undefined
 *
 * @example
 * ```typescript
 * // Store message without returning ID
 * await persistMessage(supabase, {
 *   conversation_id: 'conv-123',
 *   role: 'user',
 *   content: 'What is Bitcoin?',
 * })
 *
 * // Store message and get ID
 * const messageId = await persistMessage(
 *   supabase,
 *   {
 *     conversation_id: 'conv-123',
 *     role: 'assistant',
 *     content: 'Bitcoin is...',
 *     metadata: { model: 'claude-3-sonnet', tokens: 150 }
 *   },
 *   { returnId: true }
 * )
 * ```
 */
export async function persistMessage(
  supabase: SupabaseClient,
  message: {
    conversation_id: string
    role: 'user' | 'assistant'
    content: string
    metadata?: Record<string, unknown> | null
  },
  options: { returnId?: boolean } = {}
): Promise<string | undefined> {
  const query = supabase.from('messages').insert(message)

  if (options.returnId) {
    const { data, error } = await query.select('id').single()
    if (error) {
      console.warn('Failed to store message:', error)
      return undefined
    }
    return data?.id
  }

  const { error } = await query
  if (error) {
    console.warn('Failed to store message:', error)
  }

  return undefined
}
