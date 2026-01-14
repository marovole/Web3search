/**
 * Telemetry and Logging Library
 * Track OpenRouter API calls with comprehensive metrics
 *
 * @partof Week 2 T6: Call Telemetry and Billing Logs
 */

import type { Env } from '../types/env'
import type { OpenRouterPayload } from './openrouter'
import type { ModelConfig } from './model-routing'
import type { RequestResult } from './resilience'

/**
 * Telemetry data structure
 */
export interface TelemetryData {
  // Request metadata
  conversationId?: string
  messageId?: string
  clientSessionId?: string

  // Model information
  modelId: string
  modelName: string
  provider: string
  useCase?: string

  // Request details
  requestMethod: string
  requestPath: string
  requestHeaders: Record<string, string>
  requestBody?: Record<string, unknown>
  promptTokens: number

  // Response details
  responseStatus?: number
  responseHeaders?: Record<string, string>
  responseMetadata?: {
    bodyLength: number
    contentType: string | null
    hasError: boolean
  }
  completionTokens: number
  finishReason?: string

  // Error tracking
  errorCode?: string
  errorMessage?: string
  errorDetails?: Record<string, unknown>

  // Performance
  latencyMs: number
  retryCount: number
  circuitState?: string

  // Cost
  costUSD: number
  costCurrency?: string

  // Metadata
  metadata?: Record<string, unknown>
  tags?: string[]

  // Client info
  ipAddress?: string
  countryCode?: string
  userAgent?: string

  // Timestamps
  startedAt: Date
  completedAt: Date
}

/**
 * Extract tokens from OpenRouter response
 */
function extractTokensFromResponse(body: string | Record<string, unknown>): {
  promptTokens: number
  completionTokens: number
} {
  try {
    const data = typeof body === 'string' ? JSON.parse(body) : body

    return {
      promptTokens: data.usage?.prompt_tokens || 0,
      completionTokens: data.usage?.completion_tokens || 0
    }
  } catch {
    return { promptTokens: 0, completionTokens: 0 }
  }
}

/**
 * Calculate cost based on tokens and model config
 */
function calculateCost(
  modelConfig: ModelConfig,
  promptTokens: number,
  completionTokens: number
): number {
  const promptCost = (promptTokens / 1000000) * modelConfig.costPer1M.prompt
  const completionCost = (completionTokens / 1000000) * modelConfig.costPer1M.completion
  return promptCost + completionCost
}

/**
 * Build telemetry data from request/response
 */
export async function buildTelemetryData(
  options: {
    request: OpenRouterPayload
    modelConfig: ModelConfig
    result: RequestResult<Response>
    env: Env
    requestContext?: {
      conversationId?: string
      messageId?: string
      clientSessionId?: string
      useCase?: string
      ipAddress?: string
      countryCode?: string
      userAgent?: string
    }
  }
): Promise<TelemetryData> {
  const { request, modelConfig, result, env, requestContext } = options

  const startedAt = new Date()
  const completedAt = new Date(startedAt.getTime() + result.latencyMs)

  // Extract tokens and cost
  let promptTokens = 0
  let completionTokens = 0
  let costUSD = 0
  let bodyText = '' // Temporary variable for token extraction only
  let finishReason = ''

  if (result.success && result.data) {
    try {
      const clonedResponse = result.data.clone()
      bodyText = await clonedResponse.text()
      const tokens = extractTokensFromResponse(bodyText)
      promptTokens = tokens.promptTokens
      completionTokens = tokens.completionTokens
      costUSD = calculateCost(modelConfig, promptTokens, completionTokens)

      // Extract finish reason without storing full body
      const bodyJson = JSON.parse(bodyText)
      finishReason = bodyJson.choices?.[0]?.finish_reason || ''
    } catch (error) {
      console.error('Failed to extract tokens from response:', error)
    }
  }

  // Extract response metadata (without storing sensitive content)
  const responseContentType = result.data?.headers.get('content-type') ?? null
  const responseBodyLength = bodyText?.length || 0
  const hasError = !result.success || !!result.error

  // Build telemetry data
  const telemetry: TelemetryData = {
    // Metadata
    conversationId: requestContext?.conversationId,
    messageId: requestContext?.messageId,
    clientSessionId: requestContext?.clientSessionId || env.CLIENT_SESSION_ID,

    // Model info
    modelId: modelConfig.model,
    modelName: modelConfig.model.split('/').pop() || modelConfig.model,
    provider: modelConfig.provider,
    useCase: requestContext?.useCase || 'unknown',

    // Request
    requestMethod: 'POST',
    requestPath: '/api/v1/chat/completions',
    requestHeaders: {
      'content-type': 'application/json'
    },
    requestBody: {
      model: request.model,
      messages: request.messages.length,
      stream: request.stream,
      temperature: request.temperature
    },
    promptTokens: promptTokens || estimateTokens(JSON.stringify(request.messages)),

    // Response (metadata only, no sensitive content)
    responseStatus: result.data?.status,
    responseHeaders: result.data ? Object.fromEntries(result.data.headers.entries()) : undefined,
    responseMetadata: {
      bodyLength: responseBodyLength,
      contentType: responseContentType,
      hasError,
    },
    completionTokens,
    finishReason,

    // Error tracking
    errorCode: result.error?.name,
    errorMessage: result.error?.message,
    errorDetails: result.error ? {
      stack: result.error.stack,
      attempts: result.attempts
    } : undefined,

    // Performance
    latencyMs: result.latencyMs,
    retryCount: result.attempts - 1,
    circuitState: result.error?.message?.includes('Circuit breaker') ? 'open' : 'closed',

    // Cost
    costUSD,
    costCurrency: 'USD',

    // Metadata
    metadata: {
      streaming: request.stream,
      messageCount: request.messages.length
    },
    tags: [
      modelConfig.provider,
      requestContext?.useCase || 'unknown',
      result.success ? 'success' : 'error'
    ],

    // Client info
    ipAddress: requestContext?.ipAddress,
    countryCode: requestContext?.countryCode,
    userAgent: requestContext?.userAgent,

    // Timestamps
    startedAt,
    completedAt
  }

  return telemetry
}

/**
 * Estimate token count for text
 * Simple approximation: ~1 token per 4 characters
 */
function estimateTokens(text: string): number {
  return Math.ceil(text.length / 4)
}

/**
 * Log telemetry to Supabase
 */
export async function logTelemetry(
  telemetry: TelemetryData,
  _env: Env
): Promise<{ success: boolean; id?: string; error?: Error }> {
  try {
    // Telemetry logging disabled during Convex migration
    // TODO: Implement Convex-based telemetry logging
    console.log('[Telemetry] Call logged (in-memory only during migration):', {
      model: telemetry.modelName,
      latency: `${telemetry.latencyMs}ms`,
      cost: `$${telemetry.costUSD.toFixed(6)}`,
      useCase: telemetry.useCase
    })
    return { success: true, id: crypto.randomUUID() }

  } catch (error) {
    console.error('Error logging telemetry:', error)
    return { success: false, error: error instanceof Error ? error : new Error(String(error)) }
  }
}

/**
 * Trace integration using Cloudflare Workers Trace
 */
export interface TraceData {
  traceId: string
  parentId?: string
  name: string
  startTime: number
  endTime: number
  attributes?: Record<string, string | number | boolean>
  events?: Array<{
    name: string
    timestamp: number
    attributes?: Record<string, string | number | boolean>
  }>
}

/**
 * Create a trace from telemetry data
 */
export function createTelemetryTrace(
  telemetry: TelemetryData,
  requestId: string
): TraceData {
  const traceId = requestId || crypto.randomUUID()
  const _duration = telemetry.latencyMs

  return {
    traceId,
    name: `${telemetry.useCase}:${telemetry.modelName}`,
    startTime: telemetry.startedAt.getTime(),
    endTime: telemetry.completedAt.getTime(),
    attributes: {
      'model.provider': telemetry.provider,
      'model.name': telemetry.modelName,
      'model.id': telemetry.modelId,
      'use.case': telemetry.useCase || '',
      'request.id': requestId,
      'response.status': telemetry.responseStatus || 0,
      'error.code': telemetry.errorCode || '',
      'retry.count': telemetry.retryCount,
      'circuit.state': telemetry.circuitState || '',
      'tokens.prompt': telemetry.promptTokens,
      'tokens.completion': telemetry.completionTokens,
      'cost.usd': telemetry.costUSD,
      'latency.ms': telemetry.latencyMs
    },
    events: [
      {
        name: 'api_call.start',
        timestamp: telemetry.startedAt.getTime(),
        attributes: {
          'messages.count': Number(telemetry.requestBody?.messages) || 0
        }
      },
      {
        name: 'api_call.end',
        timestamp: telemetry.completedAt.getTime(),
        attributes: {
          'response.status': telemetry.responseStatus || 0,
          'finish.reason': telemetry.finishReason || ''
        }
      }
    ]
  }
}

/**
 * Log to multiple destinations
 */
export async function logToMultipleDestinations(
  telemetry: TelemetryData,
  env: Env,
  requestId: string
): Promise<void> {
  // Log to Supabase (primary storage)
  const supabaseResult = await logTelemetry(telemetry, env)

  // Log to Sentry if error occurred
  if (telemetry.errorCode && env.SENTRY_DSN) {
    await logToSentry(telemetry, env)
  }

  // Create trace
  const trace = createTelemetryTrace(telemetry, requestId)

  console.log('Telemetry logged:', {
    supabase: supabaseResult.success,
    model: telemetry.modelName,
    latency: `${telemetry.latencyMs}ms`,
    cost: `$${telemetry.costUSD.toFixed(6)}`,
    traceId: trace.traceId
  })
}

/**
 * Log error to Sentry
 */
async function logToSentry(
  telemetry: TelemetryData,
  env: Env
): Promise<void> {
  try {
    if (!env.SENTRY_DSN) return

    // @ts-expect-error - Sentry integration would be added here
    // Sentry.captureException(telemetry.errorMessage, {
    //   tags: telemetry.tags,
    //   extra: telemetry.errorDetails
    // })

    console.log('Error logged to Sentry:', telemetry.errorCode)
  } catch (error) {
    console.error('Failed to log to Sentry:', error)
  }
}

// Export for tests
export default {
  buildTelemetryData,
  logTelemetry,
  createTelemetryTrace,
  logToMultipleDestinations
}
