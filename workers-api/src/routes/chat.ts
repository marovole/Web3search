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
import { ROUTING_STRATEGIES, getModelConfig } from '../lib/model-routing'
import {
  ensureConversationExists,
  fetchConversationHistory,
  persistMessage,
} from '../lib/conversation'
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
    const history = await fetchConversationHistory(
      supabase,
      conversationId,
      MAX_HISTORY_MESSAGES
    )
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
 * GET /deep-research/stream
 * Deep Research with SSE streaming
 * Streams progress updates through research pipeline stages
 *
 * Query Parameters:
 *   - query (required): The research query (max 2000 characters)
 *   - conversation_id (optional): Existing conversation ID to continue
 *   - model (optional): Model ID to use (defaults to primary deep-research model)
 */
chat.get(
  '/deep-research/stream',
  createRateLimitMiddleware({
    scope: 'deep-research-ip-day',
    limit: 5,
    windowSeconds: 60 * 60 * 24, // 24 hours
    key: (c) => c.req.header('cf-connecting-ip') || 'anonymous',
  }),
  async (c) => {
    // Parse and validate query parameters
    const queryParam = c.req.query('query')
    const conversationParam = c.req.query('conversation_id')
    const modelParam = c.req.query('model')

    // Validate query parameter
    const query = typeof queryParam === 'string' ? queryParam.trim() : ''
    if (!query) {
      return c.json(
        {
          error: {
            code: 'MISSING_QUERY',
            message: 'Query parameter "query" is required',
            status: 400,
          },
        },
        400
      )
    }

    // Enforce query length limit for GET requests (URL length constraints)
    if (query.length > 2000) {
      return c.json(
        {
          error: {
            code: 'URI_TOO_LONG',
            message: 'Query exceeds maximum length of 2000 characters',
            status: 414,
          },
        },
        414
      )
    }

    try {
      const supabase = createSupabaseClient(c.env)

      // Determine model configuration
      const useCase = 'deep-research' as const
      const modelId =
        typeof modelParam === 'string' && modelParam.trim()
          ? modelParam.trim()
          : ROUTING_STRATEGIES[useCase].primary[0]
      const modelConfig = getModelConfig(modelId)

      if (!modelConfig) {
        return c.json(
          {
            error: {
              code: 'INVALID_MODEL',
              message: `Model "${modelId}" not found`,
              status: 400,
            },
          },
          400
        )
      }

      // Ensure conversation exists
      const conversationId =
        typeof conversationParam === 'string' && conversationParam.trim()
          ? conversationParam.trim()
          : crypto.randomUUID()

      await ensureConversationExists(supabase, conversationId, {
        title: `Deep Research: ${query.substring(0, 100)}`,
      })

      // Save user message
      await persistMessage(supabase, {
        conversation_id: conversationId,
        role: 'user',
        content: query,
        metadata: null, // Metadata no longer supported via GET query params
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
  let isCancelled = false

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
        // Skip if stream was cancelled
        if (isCancelled) return

        try {
          const data = JSON.stringify(event)
          controller.enqueue(encoder.encode(`data: ${data}\n\n`))
        } catch (error) {
          // Silently ignore errors if controller is closed
          if (!isCancelled) {
            console.warn('Failed to emit SSE event:', error)
          }
        }
      }

      // Keep-alive heartbeat to prevent Cloudflare timeout
      heartbeat = setInterval(() => {
        if (isCancelled) return
        try {
          controller.enqueue(encoder.encode(': keep-alive\n\n'))
        } catch (error) {
          // Silently ignore if controller is closed
        }
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
          if (heartbeat) {
            clearInterval(heartbeat)
          }
          console.error('Deep Research pipeline failed:', error)

          if (isCancelled) return // Don't try to write to closed stream

          try {
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
          } catch (closeError) {
            // Silently ignore if controller is already closed
            console.warn('Failed to send error event (stream may be closed)')
          }
        }
      })()
    },
    cancel() {
      // Cleanup if client disconnects
      console.log('Deep Research stream cancelled by client')
      isCancelled = true
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
