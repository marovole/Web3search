/**
 * Chat API Routes
 * Handles AI chat with OpenRouter, message history, and SSE streaming
 */

import { Hono } from 'hono'
import type { SupabaseClient } from '@supabase/supabase-js'
import type { Env } from '../types/env'
import type { ChatRequestBody, ChatCompletionMessage } from '../types/chat'
import { createSupabaseClient } from '../lib/supabase'
import { createOpenRouterClient, OpenRouterError } from '../lib/openrouter'
import { createRateLimitMiddleware } from '../middlewares/rate-limit'
import { createCoinGeckoClient } from '../lib/coingecko'

const DEFAULT_MODEL = 'anthropic/claude-3.5-sonnet'
const MAX_HISTORY_MESSAGES = 10
const SYSTEM_PROMPT = `You are Web3search, an AI researcher focused on cryptocurrency fundamentals.
- Provide concise answers with evidence or metrics where possible.
- Highlight uncertainty and refuse malicious requests (phishing, scams, sensitive data).`

const chat = new Hono<{ Bindings: Env }>()

/**
 * POST /quick-chat
 * Quick chat endpoint with OpenRouter integration
 * Supports both streaming (SSE) and non-streaming responses
 */
chat.post(
  '/quick-chat',
  createRateLimitMiddleware({
    scope: 'chat-ip-hour',
    limit: 10,
    windowSeconds: 60 * 60, // 1 hour
    key: (c) => c.req.header('cf-connecting-ip') || 'anonymous',
  }),
  async (c) => {
    // Parse and validate request body
    let body: ChatRequestBody
    try {
      body = await c.req.json<ChatRequestBody>()
    } catch {
      return c.json(
        {
          error: {
            code: 'INVALID_JSON',
            message: 'Body must be valid JSON',
            status: 400,
          },
        },
        400
      )
    }

    const query = body.query?.trim()
    if (!query) {
      return c.json(
        {
          error: {
            code: 'MISSING_QUERY',
            message: 'Field "query" is required',
            status: 400,
          },
        },
        400
      )
    }
    if (query.length > 10_000) {
      return c.json(
        {
          error: {
            code: 'QUERY_TOO_LONG',
            message: 'Query exceeds 10,000 characters',
            status: 400,
          },
        },
        400
      )
    }

    // Initialize clients and conversation
    const supabase = createSupabaseClient(c.env)
    const openrouter = createOpenRouterClient(c.env)
    const coingecko = createCoinGeckoClient()
    const conversationId = body.conversation_id || crypto.randomUUID()
    const shouldStream = body.stream !== false // Default to streaming
    const model = body.model || DEFAULT_MODEL

    // Try to fetch real-time price data if this is a price query
    let priceData: string | null = null
    try {
      const priceInfo = await coingecko.getPriceFromQuery(query)
      if (priceInfo) {
        const direction = priceInfo.price_change_24h >= 0 ? '上涨' : '下跌'
        priceData = `
[Real-time Market Data from CoinGecko]
Coin: ${priceInfo.name} (${priceInfo.symbol})
Current Price: $${priceInfo.price_usd.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 8 })}
24h Change: ${Math.abs(priceInfo.price_change_24h).toFixed(2)}% (${direction})
Market Cap: $${priceInfo.market_cap.toLocaleString('en-US')}
Market Cap Rank: #${priceInfo.market_cap_rank || 'N/A'}

Please use this real-time data in your response.
`
      }
    } catch (error) {
      console.warn('Failed to fetch price data:', error)
    }

    // Ensure conversation exists and fetch history
    await ensureConversationExists(supabase, conversationId)
    const history = await fetchConversationHistory(supabase, conversationId)
    const messageChain = buildMessageChain(history, query, priceData)

    // Save user message
    await persistMessage(supabase, {
      conversation_id: conversationId,
      role: 'user',
      content: query,
      metadata: body.metadata ?? null,
    })

    // Prepare OpenRouter payload
    const payload = {
      model,
      messages: messageChain,
      stream: shouldStream,
      temperature: 0.7,
      max_tokens: 2048,
    }

    try {
      if (shouldStream) {
        // Streaming response (SSE)
        const upstream = await openrouter.request(payload)
        return await streamChatResponse({
          upstream,
          supabase,
          conversationId,
        })
      }

      // Non-streaming response
      const response = await openrouter.request(payload)
      const result = await response.json<{
        choices: Array<{ message?: { content?: string } }>
      }>()
      const assistantContent = result.choices?.[0]?.message?.content?.trim() || ''
      if (!assistantContent) throw new Error('Empty response from OpenRouter')

      const messageId =
        (await persistMessage(
          supabase,
          {
            conversation_id: conversationId,
            role: 'assistant',
            content: assistantContent,
          },
          { returnId: true }
        )) ?? 'unknown'

      return c.json({
        conversation_id: conversationId,
        message_id: messageId,
        content: assistantContent,
        model,
        stream: false,
      })
    } catch (error) {
      if (error instanceof OpenRouterError) {
        const status = error.status === 429 ? 429 : 502
        const message =
          status === 429
            ? 'The AI model is receiving too many requests. Please retry later.'
            : 'Upstream AI provider returned an error.'
        return c.json(
          {
            error: {
              code: 'OPENROUTER_ERROR',
              message,
              status,
            },
          },
          status
        )
      }

      console.error('Chat handler failed', error)
      return c.json(
        {
          error: {
            code: 'CHAT_ERROR',
            message: 'Unable to process chat request',
            status: 500,
          },
        },
        500
      )
    }
  }
)

export default chat

// ============================================
// Helper Functions
// ============================================

/**
 * Ensure conversation exists in database (upsert)
 */
async function ensureConversationExists(
  supabase: SupabaseClient,
  conversationId: string
) {
  const { error } = await supabase
    .from('conversations')
    .upsert({ id: conversationId }, { onConflict: 'id' })
  if (error) console.warn('Failed to upsert conversation', error)
}

/**
 * Fetch conversation history from database
 * Returns up to MAX_HISTORY_MESSAGES recent messages
 */
async function fetchConversationHistory(
  supabase: SupabaseClient,
  conversationId: string
): Promise<ChatCompletionMessage[]> {
  const { data, error } = await supabase
    .from('messages')
    .select('role, content')
    .eq('conversation_id', conversationId)
    .order('created_at', { ascending: true })
    .limit(MAX_HISTORY_MESSAGES)
  if (error) {
    console.warn('Unable to fetch conversation history', error)
    return []
  }
  return data ?? []
}

/**
 * Build message chain for OpenRouter
 * Includes system prompt, history, price data (if any), and current user input
 */
function buildMessageChain(
  history: ChatCompletionMessage[],
  latestUserInput: string,
  priceData: string | null = null
): ChatCompletionMessage[] {
  const userMessage = priceData
    ? `${priceData}\n\nUser Question: ${latestUserInput}`
    : latestUserInput

  return [
    { role: 'system', content: SYSTEM_PROMPT },
    ...history,
    { role: 'user', content: userMessage },
  ]
}

/**
 * Persist message to database
 * Optionally returns the inserted message ID
 */
async function persistMessage(
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
      console.warn('Failed to store message', error)
      return undefined
    }
    return data?.id
  }

  const { error } = await query
  if (error) console.warn('Failed to store message', error)
  return undefined
}

// ============================================
// SSE Streaming Functions
// ============================================

interface StreamParams {
  upstream: Response
  supabase: SupabaseClient
  conversationId: string
}

/**
 * Stream chat response using Server-Sent Events (SSE)
 * Forwards OpenRouter stream to client with keep-alive heartbeats
 * Persists final assistant response to database
 */
async function streamChatResponse({
  upstream,
  supabase,
  conversationId,
}: StreamParams) {
  if (!upstream.body) throw new Error('OpenRouter stream missing body')

  const reader = upstream.body.getReader()
  const decoder = new TextDecoder()
  const encoder = new TextEncoder()
  let buffer = ''
  let assistantContent = ''

  const stream = new ReadableStream({
    start(controller) {
      // Send keep-alive heartbeat every 15 seconds to prevent Cloudflare timeout
      const heartbeat = setInterval(() => {
        controller.enqueue(encoder.encode(': keep-alive\n\n'))
      }, 15_000)

      // Read and forward stream chunks
      ;(async () => {
        try {
          while (true) {
            const { done, value } = await reader.read()
            if (done) {
              clearInterval(heartbeat)
              controller.enqueue(
                encoder.encode('event: done\ndata: {"status":"completed"}\n\n')
              )
              controller.close()

              // Persist final assistant response
              await persistMessage(supabase, {
                conversation_id: conversationId,
                role: 'assistant',
                content: assistantContent,
              })
              break
            }

            // Decode chunk and parse SSE lines
            buffer += decoder.decode(value, { stream: true })
            const lines = buffer.split('\n')
            buffer = lines.pop() || ''

            for (const line of lines) {
              const trimmed = line.trim()
              if (!trimmed.startsWith('data:')) continue

              const data = trimmed.slice(5).trim()
              if (!data || data === '[DONE]') continue

              try {
                const chunk = JSON.parse(data)
                const delta = chunk.choices?.[0]?.delta?.content ?? ''
                if (delta) {
                  assistantContent += delta
                  controller.enqueue(
                    encoder.encode(`data: ${JSON.stringify({ delta })}\n\n`)
                  )
                }
              } catch (error) {
                console.warn('Failed to parse SSE chunk', error)
              }
            }
          }
        } catch (error) {
          clearInterval(heartbeat)
          controller.error(error)
          throw error
        }
      })()
    },
    cancel() {
      reader.cancel().catch(() => {})
    },
  })

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
    },
  })
}
