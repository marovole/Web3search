/**
 * Tests for Conversation Management Utilities
 * Validates Supabase interactions for conversations and messages
 */

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  ensureConversationExists,
  fetchConversationHistory,
  persistMessage,
  type ChatCompletionMessage,
} from '../../src/lib/conversation'
import type { SupabaseClient } from '@supabase/supabase-js'

// ============================================
// Supabase Mock Factory
// ============================================

type SupabaseMockOptions = {
  failUpsert?: boolean
  historyData?: ChatCompletionMessage[]
  historyError?: boolean
  insertError?: boolean
  returnIdError?: boolean
  insertedId?: string
}

/**
 * Create a mock Supabase client with configurable behavior
 */
function createSupabaseMock({
  failUpsert,
  historyData,
  historyError,
  insertError,
  returnIdError,
  insertedId,
}: SupabaseMockOptions = {}) {
  const insertedMessages: Array<{
    table: string
    payload: any
  }> = []

  // Conversation upsert mock
  const conversationUpsert = vi.fn(async (_data, _options) => ({
    error: failUpsert ? { message: 'Upsert failed', code: 'DB_ERROR' } : null,
  }))

  // Message history query chain
  const historyLimit = vi.fn(async () => ({
    data: historyError ? null : historyData ?? [],
    error: historyError ? { message: 'Query failed', code: 'DB_ERROR' } : null,
  }))

  const historyOrder = vi.fn(() => ({
    limit: historyLimit,
  }))

  const historyEq = vi.fn(() => ({
    order: historyOrder,
  }))

  const historySelect = vi.fn(() => ({
    eq: historyEq,
  }))

  // Message insert builder
  const createInsertBuilder = (payload: any) => {
    const insertPromise = Promise.resolve({
      error: insertError ? { message: 'Insert failed', code: 'DB_ERROR' } : null,
    })

    const builder = {
      select: vi.fn(() => ({
        single: vi.fn(async () => ({
          data: returnIdError ? null : { id: insertedId ?? 'msg-generated-123' },
          error: returnIdError
            ? { message: 'Select failed', code: 'DB_ERROR' }
            : null,
        })),
      })),
      then: insertPromise.then.bind(insertPromise),
      catch: insertPromise.catch.bind(insertPromise),
    }

    return builder
  }

  // from() dispatcher
  const fromFunction = vi.fn((table: string) => {
    if (table === 'conversations') {
      return {
        upsert: conversationUpsert,
      }
    }

    if (table === 'messages') {
      return {
        select: historySelect,
        insert: (payload: any) => {
          insertedMessages.push({ table, payload })
          return createInsertBuilder(payload)
        },
      }
    }

    return {}
  })

  const supabase = {
    from: fromFunction,
  } as unknown as SupabaseClient

  return {
    supabase,
    spies: {
      from: fromFunction,
      conversationUpsert,
      historySelect,
      historyEq,
      historyOrder,
      historyLimit,
    },
    insertedMessages,
  }
}

// ============================================
// Conversation Tests
// ============================================

describe('conversation utilities', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('ensureConversationExists', () => {
    it('upserts conversation without title', async () => {
      const { supabase, spies } = createSupabaseMock()

      await ensureConversationExists(supabase, 'conv-abc123')

      expect(spies.conversationUpsert).toHaveBeenCalledOnce()
      expect(spies.conversationUpsert).toHaveBeenCalledWith(
        { id: 'conv-abc123' },
        { onConflict: 'id' }
      )
    })

    it('upserts conversation with title', async () => {
      const { supabase, spies } = createSupabaseMock()

      await ensureConversationExists(supabase, 'conv-xyz789', {
        title: 'Deep Research: Bitcoin fundamentals',
      })

      expect(spies.conversationUpsert).toHaveBeenCalledWith(
        {
          id: 'conv-xyz789',
          title: 'Deep Research: Bitcoin fundamentals',
        },
        { onConflict: 'id' }
      )
    })

    it('logs warning on upsert failure but does not throw', async () => {
      const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})
      const { supabase } = createSupabaseMock({ failUpsert: true })

      await expect(
        ensureConversationExists(supabase, 'conv-fail')
      ).resolves.not.toThrow()

      expect(warnSpy).toHaveBeenCalledWith(
        'Failed to upsert conversation:',
        expect.objectContaining({ message: 'Upsert failed' })
      )

      warnSpy.mockRestore()
    })

    it('handles empty string title by not including it', async () => {
      const { supabase, spies } = createSupabaseMock()

      await ensureConversationExists(supabase, 'conv-empty', { title: '' })

      // Empty string should not be included
      expect(spies.conversationUpsert).toHaveBeenCalledWith(
        { id: 'conv-empty' },
        { onConflict: 'id' }
      )
    })
  })

  describe('fetchConversationHistory', () => {
    it('fetches conversation history successfully', async () => {
      const mockHistory: ChatCompletionMessage[] = [
        { role: 'user', content: 'What is Bitcoin?' },
        { role: 'assistant', content: 'Bitcoin is a decentralized cryptocurrency...' },
        { role: 'user', content: 'How does mining work?' },
      ]

      const { supabase } = createSupabaseMock({ historyData: mockHistory })

      const result = await fetchConversationHistory(supabase, 'conv-123', 10)

      expect(result).toEqual(mockHistory)
    })

    it('queries with correct conversation_id filter', async () => {
      const { supabase, spies } = createSupabaseMock({
        historyData: [],
      })

      await fetchConversationHistory(supabase, 'conv-specific')

      expect(spies.historyEq).toHaveBeenCalledWith(
        'conversation_id',
        'conv-specific'
      )
    })

    it('respects message limit parameter', async () => {
      const { supabase, spies } = createSupabaseMock({ historyData: [] })

      await fetchConversationHistory(supabase, 'conv-123', 20)

      expect(spies.historyLimit).toHaveBeenCalledWith(20)
    })

    it('uses default limit of 10 when not specified', async () => {
      const { supabase, spies } = createSupabaseMock({ historyData: [] })

      await fetchConversationHistory(supabase, 'conv-123')

      expect(spies.historyLimit).toHaveBeenCalledWith(10)
    })

    it('orders messages by created_at ascending', async () => {
      const { supabase, spies } = createSupabaseMock({ historyData: [] })

      await fetchConversationHistory(supabase, 'conv-123')

      expect(spies.historyOrder).toHaveBeenCalledWith('created_at', {
        ascending: true,
      })
    })

    it('returns empty array on query error', async () => {
      const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})
      const { supabase } = createSupabaseMock({ historyError: true })

      const result = await fetchConversationHistory(supabase, 'conv-fail')

      expect(result).toEqual([])
      expect(warnSpy).toHaveBeenCalledWith(
        'Unable to fetch conversation history:',
        expect.objectContaining({ message: 'Query failed' })
      )

      warnSpy.mockRestore()
    })

    it('handles empty conversation gracefully', async () => {
      const { supabase } = createSupabaseMock({ historyData: [] })

      const result = await fetchConversationHistory(supabase, 'conv-empty')

      expect(result).toEqual([])
    })
  })

  describe('persistMessage', () => {
    it('persists user message without returning ID', async () => {
      const { supabase, insertedMessages } = createSupabaseMock()

      const result = await persistMessage(supabase, {
        conversation_id: 'conv-123',
        role: 'user',
        content: 'What is Ethereum?',
      })

      expect(result).toBeUndefined()
      expect(insertedMessages).toHaveLength(1)
      expect(insertedMessages[0].payload).toEqual({
        conversation_id: 'conv-123',
        role: 'user',
        content: 'What is Ethereum?',
        metadata: {},
      })
    })

    it('persists assistant message with metadata', async () => {
      const { supabase, insertedMessages } = createSupabaseMock()

      await persistMessage(supabase, {
        conversation_id: 'conv-456',
        role: 'assistant',
        content: 'Ethereum is a blockchain platform...',
        metadata: {
          model: 'claude-3.5-sonnet',
          tokens: 250,
          latency_ms: 1500,
        },
      })

      expect(insertedMessages[0].payload).toEqual({
        conversation_id: 'conv-456',
        role: 'assistant',
        content: 'Ethereum is a blockchain platform...',
        metadata: {
          model: 'claude-3.5-sonnet',
          tokens: 250,
          latency_ms: 1500,
        },
      })
    })

    it('returns message ID when returnId option is set', async () => {
      const { supabase } = createSupabaseMock({ insertedId: 'msg-returned-789' })

      const messageId = await persistMessage(
        supabase,
        {
          conversation_id: 'conv-789',
          role: 'assistant',
          content: 'Response with ID',
        },
        { returnId: true }
      )

      expect(messageId).toBe('msg-returned-789')
    })

    it('handles null metadata gracefully', async () => {
      const { supabase, insertedMessages } = createSupabaseMock()

      await persistMessage(supabase, {
        conversation_id: 'conv-null',
        role: 'user',
        content: 'Message',
        metadata: null,
      })

      expect(insertedMessages[0].payload.metadata).toEqual({})
    })

    it('logs warning and returns undefined when insert fails', async () => {
      const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})
      const { supabase } = createSupabaseMock({ insertError: true })

      const result = await persistMessage(supabase, {
        conversation_id: 'conv-error',
        role: 'user',
        content: 'This will fail',
      })

      expect(result).toBeUndefined()
      expect(warnSpy).toHaveBeenCalledWith(
        'Failed to store message:',
        expect.objectContaining({ message: 'Insert failed' })
      )

      warnSpy.mockRestore()
    })

    it('logs warning when select().single() fails during returnId', async () => {
      const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})
      const { supabase } = createSupabaseMock({ returnIdError: true })

      const result = await persistMessage(
        supabase,
        {
          conversation_id: 'conv-select-fail',
          role: 'assistant',
          content: 'Cannot retrieve ID',
        },
        { returnId: true }
      )

      expect(result).toBeUndefined()
      expect(warnSpy).toHaveBeenCalledWith(
        'Failed to store message:',
        expect.objectContaining({ message: 'Select failed' })
      )

      warnSpy.mockRestore()
    })
  })

  describe('Edge Cases', () => {
    it('handles multiple sequential operations', async () => {
      const { supabase, spies, insertedMessages } = createSupabaseMock({
        historyData: [{ role: 'user', content: 'Previous message' }],
      })

      // Ensure conversation exists
      await ensureConversationExists(supabase, 'conv-multi', {
        title: 'Multi-operation test',
      })

      // Fetch history
      const history = await fetchConversationHistory(supabase, 'conv-multi')

      // Persist new message
      await persistMessage(supabase, {
        conversation_id: 'conv-multi',
        role: 'user',
        content: 'New message',
      })

      expect(spies.conversationUpsert).toHaveBeenCalledOnce()
      expect(history).toHaveLength(1)
      expect(insertedMessages).toHaveLength(1)
    })

    it('handles very long conversation content', async () => {
      const { supabase, insertedMessages } = createSupabaseMock()

      const longContent = 'x'.repeat(10000)

      await persistMessage(supabase, {
        conversation_id: 'conv-long',
        role: 'assistant',
        content: longContent,
      })

      expect(insertedMessages[0].payload.content).toHaveLength(10000)
    })

    it('handles special characters in content', async () => {
      const { supabase, insertedMessages } = createSupabaseMock()

      await persistMessage(supabase, {
        conversation_id: 'conv-special',
        role: 'user',
        content: 'Message with "quotes" and \\backslashes\\ and émojis 🚀',
      })

      expect(insertedMessages[0].payload.content).toBe(
        'Message with "quotes" and \\backslashes\\ and émojis 🚀'
      )
    })
  })
})
