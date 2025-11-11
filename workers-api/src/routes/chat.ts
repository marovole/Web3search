/**
 * Chat API Routes
 * Handles AI chat with OpenRouter, message history, and SSE streaming
 */

import { Hono } from 'hono'
import type { SupabaseClient } from '@supabase/supabase-js'
import type { Env } from '../types/env'
import type { ChatRequestBody, ChatCompletionMessage } from '../types/chat'
import type { DeepResearchRequest } from '../types/deep-research'
import { createSupabaseClient } from '../lib/supabase'
import { createOpenRouterClient, OpenRouterError } from '../lib/openrouter'
import { createRateLimitMiddleware } from '../middlewares/rate-limit'
import { createCoinGeckoClient } from '../lib/coingecko'
import { ROUTING_STRATEGIES, getModelConfig } from '../lib/model-routing'
import {
  generateResearchPlan,
  searchSources,
  analyzeSources,
  synthesizeFindings,
} from './deep-research'

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

/**
 * POST /deep-research/stream
 * Deep Research with SSE streaming
 * Streams progress updates through research pipeline stages
 */
chat.post(
  '/deep-research/stream',
  createRateLimitMiddleware({
    scope: 'deep-research-ip-day',
    limit: 5,
    windowSeconds: 60 * 60 * 24, // 24 hours
    key: (c) => c.req.header('cf-connecting-ip') || 'anonymous',
  }),
  async (c) => {
    // Parse and validate request body
    let body: DeepResearchRequest
    try {
      body = await c.req.json<DeepResearchRequest>()
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

    if (query.length > 5000) {
      return c.json(
        {
          error: {
            code: 'QUERY_TOO_LONG',
            message: 'Query exceeds 5000 characters',
            status: 400,
          },
        },
        400
      )
    }

    try {
      const supabase = createSupabaseClient(c.env)

      // Determine model configuration
      const useCase = 'deep-research' as const
      const modelId = body.model || ROUTING_STRATEGIES[useCase].primary[0]
      const modelConfig = getModelConfig(modelId)

      if (!modelConfig) {
        return c.json(
          {
            error: {
              code: 'INVALID_MODEL',
              message: `Model ${modelId} not found`,
              status: 400,
            },
          },
          400
        )
      }

      // Ensure conversation exists
      const conversationId = body.conversation_id || crypto.randomUUID()
      await ensureConversationExists(supabase, conversationId, {
        title: `Deep Research: ${query.substring(0, 100)}`,
      })

      // Save user message
      await persistMessage(supabase, {
        conversation_id: conversationId,
        role: 'user',
        content: query,
        metadata: body.metadata ?? null,
      })

      // Create SSE stream
      return streamDeepResearch({
        query,
        conversationId,
        modelConfig,
        supabase,
        env: c.env,
      })
    } catch (error) {
      console.error('Deep Research stream handler failed:', error)
      return c.json(
        {
          error: {
            code: 'DEEP_RESEARCH_ERROR',
            message: 'Failed to start deep research',
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
  conversationId: string,
  options?: { title?: string }
) {
  const data: any = { id: conversationId }
  if (options?.title) {
    data.title = options.title
  }

  const { error } = await supabase
    .from('conversations')
    .upsert(data, { onConflict: 'id' })
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

// ============================================
// Deep Research Streaming Functions
// ============================================

interface DeepResearchStreamParams {
  query: string
  conversationId: string
  modelConfig: any
  supabase: SupabaseClient
  env: Env
}

/**
 * Stream Deep Research progress using Server-Sent Events (SSE)
 * Emits progress events for each stage: data_collection, analysis, report_generation, complete
 * Persists final assistant response to database
 */
function streamDeepResearch({
  query,
  conversationId,
  modelConfig,
  supabase,
  env,
}: DeepResearchStreamParams): Response {
  const encoder = new TextEncoder()
  let heartbeat: ReturnType<typeof setInterval> | null = null

  const stream = new ReadableStream({
    start(controller) {
      // SSE event emitter helper
      const emit = (event: {
        type: 'progress' | 'content' | 'complete' | 'error'
        stage?: string
        section?: string
        content: string
        session_id?: string
      }) => {
        const data = JSON.stringify(event)
        controller.enqueue(encoder.encode(`data: ${data}\n\n`))
      }

      // Keep-alive heartbeat to prevent Cloudflare timeout
      heartbeat = setInterval(() => {
        controller.enqueue(encoder.encode(': keep-alive\n\n'))
      }, 15_000)

      // Execute research pipeline
      ;(async () => {
        try {
          // Stage 1: Data Collection
          emit({
            type: 'progress',
            stage: 'data_collection',
            content: '正在准备研究计划...',
          })

          const plan = await generateResearchPlan(query, modelConfig, env)

          emit({
            type: 'progress',
            stage: 'data_collection',
            content: `研究计划已生成，将搜索 ${plan.search_queries.length} 个来源...`,
          })

          // Stage 2: Source Search
          const sources = await searchSources(plan.search_queries)

          emit({
            type: 'content',
            section: 'sources',
            content: JSON.stringify({
              count: sources.length,
              queries: plan.search_queries,
            }),
          })

          // Stage 3: Analysis
          emit({
            type: 'progress',
            stage: 'analysis',
            content: '正在分析数据源...',
          })

          const analysis = await analyzeSources(sources, query, modelConfig, env)

          emit({
            type: 'progress',
            stage: 'analysis',
            content: `已分析 ${sources.length} 个来源，发现 ${analysis.citations.length} 条引用...`,
          })

          // Stage 4: Report Generation
          emit({
            type: 'progress',
            stage: 'report_generation',
            content: '正在生成综合报告...',
          })

          const synthesis = await synthesizeFindings(
            analysis,
            query,
            modelConfig,
            env
          )

          // Emit final answer as content (so UI can display it)
          emit({
            type: 'content',
            section: 'answer',
            content: synthesis.answer,
          })

          // Persist assistant response
          await persistMessage(supabase, {
            conversation_id: conversationId,
            role: 'assistant',
            content: synthesis.answer,
            metadata: {
              research_result: synthesis.result,
              citations: analysis.citations,
            },
          })

          // Stage 5: Complete
          emit({
            type: 'complete',
            content: synthesis.summary || 'Research completed successfully',
            session_id: conversationId,
          })

          clearInterval(heartbeat)
          controller.enqueue(
            encoder.encode('event: done\ndata: {"status":"completed"}\n\n')
          )
          controller.close()
        } catch (error) {
          clearInterval(heartbeat)
          console.error('Deep Research pipeline failed:', error)

          const errorMessage =
            error instanceof Error
              ? error.message
              : 'Deep research pipeline encountered an error'

          emit({
            type: 'error',
            content: errorMessage,
          })

          controller.enqueue(
            encoder.encode(
              `event: error\ndata: ${JSON.stringify({ error: errorMessage })}\n\n`
            )
          )
          controller.close()
        }
      })()
    },
    cancel() {
      // Cleanup if client disconnects
      console.log('Deep Research stream cancelled by client')
      if (heartbeat) {
        clearInterval(heartbeat)
      }
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
