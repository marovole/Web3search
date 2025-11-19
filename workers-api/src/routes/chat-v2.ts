/**
 * Chat API Routes v2 - Enhanced with Model Routing & Telemetry
 * Implements Week 2 T10: Quick Chat endpoint with OpenRouter integration
 */

import { Hono } from 'hono'
import type { SupabaseClient } from '@supabase/supabase-js'
import type { Env } from '../types/env'
import type { ChatRequestBody, ChatCompletionMessage } from '../types/chat'
import { getSupabaseClient } from '../lib/supabase'
import { createOpenRouterClient } from '../lib/openrouter'
import { createRateLimitMiddleware } from '../middlewares/rate-limit'
import {
  ROUTING_STRATEGIES,
  buildRoutedPayload,
  getModelConfig,
  validateModelCapabilities
} from '../lib/model-routing'
import { executeOpenRouterRequest } from '../lib/resilience'
import { buildTelemetryData, logToMultipleDestinations } from '../lib/telemetry'
import { parseStreamResponse, createStreamingResponse } from '../lib/streaming'
import {
  ensureConversationExists,
  fetchConversationHistory,
  persistMessage,
} from '../lib/conversation'

const DEFAULT_USE_CASE: keyof typeof ROUTING_STRATEGIES = 'quick-chat'
const MAX_HISTORY_MESSAGES = 10
const SYSTEM_PROMPT = `You are Web3search, an AI researcher focused on cryptocurrency fundamentals.
- Provide concise answers with evidence or metrics where possible.
- Highlight uncertainty and refuse malicious requests (phishing, scams, sensitive data).`

const chatV2 = new Hono<{ Bindings: Env }>()

/**
 * POST /v2/quick-chat
 * Enhanced Quick Chat endpoint with model routing and telemetry
 */
chatV2.post(
  '/quick-chat',
  createRateLimitMiddleware({
    scope: 'chat-v2-ip-hour',
    limit: 20,
    windowSeconds: 60 * 60, // 1 hour
    key: (c) => c.req.header('cf-connecting-ip') || 'anonymous',
  }),
  async (c) => {
    const startTime = Date.now()
    const requestId = crypto.randomUUID()

    // Parse and validate request
    let body: ChatRequestBody & { use_case?: keyof typeof ROUTING_STRATEGIES }
    try {
      body = await c.req.json()
    } catch {
      return c.json({ error: { code: 'INVALID_JSON', message: 'Body must be valid JSON', status: 400 } }, 400)
    }

    const query = body.query?.trim()
    if (!query) {
      return c.json({ error: { code: 'MISSING_QUERY', message: 'Field "query" is required', status: 400 } }, 400)
    }
    if (query.length > 10_000) {
      return c.json({ error: { code: 'QUERY_TOO_LONG', message: 'Query exceeds 10,000 characters', status: 400 } }, 400)
    }

    // Initialize clients
    const supabase = getSupabaseClient(c.env)
    const openrouter = createOpenRouterClient(c.env)
    const conversationId = body.conversation_id || crypto.randomUUID()
    const shouldStream = body.stream !== false
    const useCase = body.use_case || DEFAULT_USE_CASE

    try {
      // Ensure conversation exists
      await ensureConversationExists(supabase, conversationId, { title: query.substring(0, 100) })

      // Fetch conversation history
      const history = await fetchConversationHistory(
        supabase,
        conversationId,
        MAX_HISTORY_MESSAGES
      )
      const messageChain = buildMessageChain(history, query)

      // Save user message
      const userMessageId = await persistMessage(supabase, {
        conversation_id: conversationId,
        role: 'user',
        content: query,
        metadata: body.metadata ?? null,
      }, { returnId: true })

      // Build routed payload with model selection
      const modelId = body.model || ROUTING_STRATEGIES[useCase].primary[0]
      const modelConfig = getModelConfig(modelId)

      if (!modelConfig) {
        return c.json({
          error: {
            code: 'INVALID_MODEL',
            message: `Model ${modelId} not found in routing table`,
            status: 400
          }
        }, 400)
      }

      // Validate model capabilities
      const validation = validateModelCapabilities(modelId, { streaming: shouldStream })
      if (!validation.valid) {
        return c.json({
          error: {
            code: 'MODEL_CAPABILITY_MISMATCH',
            message: `Model missing required capabilities: ${validation.missing.join(', ')}`,
            status: 400
          }
        }, 400)
      }

      const payload = buildRoutedPayload(useCase, messageChain, {
        model: modelId,
        temperature: body.temperature || 0.7,
        maxTokens: body.max_tokens || 2048,
        stream: shouldStream,
      })

      // Execute request with resilience (retry + circuit breaker)
      const result = await executeOpenRouterRequest(
        payload,
        openrouter,
        {
          modelId,
          modelConfig,
          env: c.env,
          retryConfig: {
            maxAttempts: 3,
            initialDelayMs: 100,
            maxDelayMs: 10000,
            backoffFactor: 2,
            timeoutMs: 30000,
            retryableStatuses: [408, 429, 502, 503, 504],
            retryableErrors: ['ECONNRESET', 'ETIMEDOUT', 'ENOTFOUND', 'ECONNREFUSED']
          }
        }
      )

      // Build telemetry data
      const telemetry = await buildTelemetryData({
        request: payload,
        modelConfig,
        result,
        env: c.env,
        requestContext: {
          conversationId,
          messageId: userMessageId,
          clientSessionId: c.env.CLIENT_SESSION_ID,
          useCase,
          ipAddress: c.req.header('cf-connecting-ip'),
          countryCode: c.req.header('cf-ipcountry'),
          userAgent: c.req.header('user-agent')
        }
      })

      // Log telemetry asynchronously (don't block response)
      c.executionCtx.waitUntil(
        logToMultipleDestinations(telemetry, c.env, requestId)
      )

      if (!result.success || !result.data) {
        throw result.error || new Error('Unknown error')
      }

      // Handle streaming response
      if (shouldStream) {
        return await handleStreamingResponse({
          upstream: result.data,
          supabase,
          conversationId,
          userMessageId,
          modelConfig,
          telemetry
        })
      }

      // Handle non-streaming response
      return await handleNonStreamingResponse({
        response: result.data,
        supabase,
        conversationId,
        userMessageId,
        modelConfig,
        telemetry
      })

    } catch (error) {
      console.error('Chat v2 handler failed:', error)

      const errorMessage = error instanceof Error ? error.message : 'Unknown error'
      const statusCode = errorMessage.includes('Circuit breaker') ? 503 :
        errorMessage.includes('429') ? 429 : 500

      return c.json({
        error: {
          code: 'CHAT_ERROR',
          message: errorMessage.includes('Circuit breaker')
            ? 'Service temporarily unavailable due to high error rate'
            : 'Unable to process chat request',
          status: statusCode,
        },
      }, statusCode)
    }
  }
)

export default chatV2

// ============================================
// Helper Functions
// ============================================

function buildMessageChain(
  history: ChatCompletionMessage[],
  latestUserInput: string
): ChatCompletionMessage[] {
  return [
    { role: 'system', content: SYSTEM_PROMPT },
    ...history,
    { role: 'user', content: latestUserInput },
  ]
}

// ============================================
// Response Handlers
// ============================================

interface StreamingResponseParams {
  upstream: Response
  supabase: SupabaseClient
  conversationId: string
  userMessageId: string | undefined
  modelConfig: any
  telemetry: any
}

async function handleStreamingResponse({
  upstream,
  supabase,
  conversationId,
  modelConfig
}: StreamingResponseParams) {
  if (!upstream.body) {
    throw new Error('OpenRouter stream missing body')
  }

  // Create streaming response with our adapter
  let fullContent = ''

  // Create streaming response with our adapter
  return createStreamingResponse(
    upstream.body,
    (chunk) => {
      // Accumulate content
      const content = chunk.choices?.[0]?.delta?.content
      if (content) {
        fullContent += content
      }
    },
    async () => {
      // Save full message to Supabase on completion
      if (fullContent) {
        try {
          await persistMessage(supabase, {
            conversation_id: conversationId,
            role: 'assistant',
            content: fullContent,
          })
          console.log('Streamed response saved to database')
        } catch (error) {
          console.error('Failed to save streamed response:', error)
        }
      }
    }
  )
}

interface NonStreamingResponseParams {
  response: Response
  supabase: SupabaseClient
  conversationId: string
  userMessageId: string | undefined
  modelConfig: any
  telemetry: any
}

async function handleNonStreamingResponse({
  response,
  supabase,
  conversationId,
  modelConfig
}: NonStreamingResponseParams) {
  const result = await response.json() as any
  const assistantContent = result.choices?.[0]?.message?.content?.trim() || ''

  if (!assistantContent) {
    throw new Error('Empty response from OpenRouter')
  }

  const assistantMessageId = await persistMessage(supabase, {
    conversation_id: conversationId,
    role: 'assistant',
    content: assistantContent,
  }, { returnId: true })

  return new Response(JSON.stringify({
    conversation_id: conversationId,
    message_id: assistantMessageId,
    content: assistantContent,
    model: modelConfig.model,
    stream: false,
    usage: result.usage || null
  }), {
    headers: {
      'Content-Type': 'application/json',
      'X-Model': modelConfig.model,
    }
  })
}
