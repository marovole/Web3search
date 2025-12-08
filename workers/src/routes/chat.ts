import { Hono } from 'hono'
import { stream } from 'hono/streaming'
import { createOpenRouterClient } from '../lib/openrouter'
import { RateLimiter } from '../lib/rate-limiter'
import { getSupabaseClient } from '../lib/supabase'
import { rateLimit } from '../middlewares/rateLimit'
import {
  getOrCreateConversation,
  saveMessage,
  getConversationMessages,
  updateConversationStats,
} from '../lib/conversation'
import type { Env } from '../types/env'
import type { ChatRequest, ChatResponse, ChatStreamChunk } from '../types/chat'
import type { OpenRouterMessage } from '../types/openrouter'

const router = new Hono<{ Bindings: Env }>()

// 对聊天API应用更严格的速率限制
router.use('*', rateLimit.chat)

// ========================================
// 深度研究 API 类型定义
// ========================================

/**
 * 支持的研究维度
 */
type ResearchDimension =
  | 'market_analysis'      // 市场分析
  | 'technical_analysis'   // 技术分析
  | 'sentiment_analysis'   // 情绪分析
  | 'onchain_data'        // 链上数据
  | 'tokenomics'          // 代币经济
  | 'risk_assessment'     // 风险评估

/**
 * 深度研究请求体
 */
interface DeepResearchRequest {
  query: string                      // 研究主题/问题
  conversation_id?: string           // 可选：关联的对话 ID
  dimensions?: ResearchDimension[]   // 可选：选择的研究维度
  model?: string                     // 可选：使用的 AI 模型
  use_cache?: boolean               // 可选：是否使用缓存
}

/**
 * 单个维度的研究结果
 */
interface DimensionResult {
  dimension: ResearchDimension
  summary: string
  timestamp: number
}

/**
 * 缓存的研究报告数据
 */
interface CachedResearchPayload {
  version: number
  model: string
  query_hash: string
  dimensions: Record<string, DimensionResult>
  final_summary: string
  created_at: number
}

/**
 * SSE 事件类型
 */
type SSEEventType =
  | 'dimension_start'
  | 'delta'
  | 'dimension_complete'
  | 'error'
  | 'report_complete'

/**
 * SSE 事件基础结构
 */
interface SSEEvent {
  type: SSEEventType
  dimension?: ResearchDimension
  content?: string
  summary?: string
  message?: string
  conversation_id?: string
  final_summary?: string
  timestamp?: number
  from_cache?: boolean
}

// ========================================
// 深度研究配置常量
// ========================================

/**
 * 默认研究维度（免费用户/快速分析）
 */
const DEFAULT_DIMENSIONS: ResearchDimension[] = [
  'market_analysis',
  'technical_analysis',
  'sentiment_analysis',
]

/**
 * 可选研究维度（高级分析）
 */
const OPTIONAL_DIMENSIONS: ResearchDimension[] = [
  'onchain_data',
  'tokenomics',
  'risk_assessment',
]

/**
 * 所有支持的研究维度
 */
const ALL_DIMENSIONS: ResearchDimension[] = [
  ...DEFAULT_DIMENSIONS,
  ...OPTIONAL_DIMENSIONS,
]

/**
 * 最大并发维度数量
 */
const MAX_DIMENSION_CONCURRENCY = 2

/**
 * 单个维度的最大重试次数
 */
const MAX_DIMENSION_RETRIES = 2

/**
 * 单个维度的超时时间（毫秒）
 */
const DIMENSION_TIMEOUT_MS = 30_000  // 30 秒

/**
 * 缓存版本（用于缓存键生成）
 */
const CACHE_VERSION = 'v1'

/**
 * 维度配置：包含每个维度的标题和提示词
 */
const DIMENSION_CONFIG: Record<
  ResearchDimension,
  { title: string; prompt: string }
> = {
  market_analysis: {
    title: 'Market Analysis',
    prompt: `Analyze the current market performance comprehensively:
- Current price trends and trading volume
- Market capitalization and ranking
- Volatility and price momentum
- Macro factors affecting the market
- Competitive landscape and market share
- Key support and resistance levels

Provide actionable insights with concrete data points and specific metrics.`,
  },
  technical_analysis: {
    title: 'Technical Analysis',
    prompt: `Perform detailed technical analysis:
- Price action and chart patterns
- Key support and resistance levels
- Technical indicators (RSI, MACD, EMAs, Bollinger Bands)
- Volume analysis and trends
- Short-term and medium-term momentum
- Breakout or breakdown signals

Use clear justification and cite specific indicator values.`,
  },
  sentiment_analysis: {
    title: 'Sentiment Analysis',
    prompt: `Evaluate market sentiment across multiple channels:
- Community sentiment on social platforms (Twitter, Reddit, Discord)
- Developer activity and sentiment
- Investor sentiment and positioning
- News and media coverage analysis
- Key catalysts or red flags
- Fear and Greed indicators

Highlight factors that are significantly impacting sentiment.`,
  },
  onchain_data: {
    title: 'On-Chain Data Analysis',
    prompt: `Analyze blockchain activity and on-chain metrics:
- Active addresses and user growth
- Transaction volume and count
- Whale movements and large transfers
- Staking participation and lockup rates
- Smart contract interactions
- Exchange inflows/outflows
- Protocol-level KPIs

Focus on data that indicates real usage and network health.`,
  },
  tokenomics: {
    title: 'Tokenomics Analysis',
    prompt: `Break down the token economics comprehensively:
- Token supply schedule and distribution
- Emission rates and inflation
- Upcoming token unlocks and vesting
- Staking mechanisms and yields
- Token utility and use cases
- Treasury management
- Incentive alignment and sustainability
- Potential dilution risks

Identify any structural concerns or strengths.`,
  },
  risk_assessment: {
    title: 'Risk Assessment',
    prompt: `Evaluate major risk factors across categories:
- Market risks (volatility, liquidity, correlation)
- Technical risks (smart contract bugs, exploits)
- Regulatory risks (compliance, legal challenges)
- Security risks (past hacks, audit status)
- Team and governance risks
- Competitive risks

Rate likelihood and potential impact for each risk. Suggest mitigation strategies where applicable.`,
  },
}

// ========================================
// 深度研究辅助函数
// ========================================

/**
 * 生成缓存键的哈希值
 */
async function generateCacheHash(input: string): Promise<string> {
  const encoder = new TextEncoder()
  const data = encoder.encode(input)
  const hashBuffer = await crypto.subtle.digest('SHA-256', data)
  const hashArray = Array.from(new Uint8Array(hashBuffer))
  return hashArray.map((byte) => byte.toString(16).padStart(2, '0')).join('')
}

/**
 * 写入 SSE 事件
 */
async function writeSSEEvent(streamWriter: any, event: SSEEvent): Promise<void> {
  await streamWriter.write(`data: ${JSON.stringify(event)}\n\n`)
}

/**
 * 验证并标准化研究维度
 * @throws Error 如果没有有效的维度
 */
function validateAndNormalizeDimensions(
  dimensions?: ResearchDimension[]
): ResearchDimension[] {
  // 如果未指定或为空，使用默认维度
  if (!dimensions || dimensions.length === 0) {
    return DEFAULT_DIMENSIONS
  }

  // 过滤并去重有效的维度
  const validDimensions = Array.from(
    new Set(
      dimensions
        .map((dim) => dim.trim().toLowerCase() as ResearchDimension)
        .filter((dim) => ALL_DIMENSIONS.includes(dim))
    )
  )

  if (validDimensions.length === 0) {
    throw new Error('No valid dimensions provided')
  }

  return validDimensions
}

/**
 * 构建特定维度的消息列表
 */
function buildDimensionMessages(
  dimension: ResearchDimension,
  userQuery: string,
  conversationHistory: OpenRouterMessage[]
): OpenRouterMessage[] {
  const config = DIMENSION_CONFIG[dimension]

  return [
    {
      role: 'system',
      content: `You are a senior Web3 research analyst specializing in ${config.title}.
Your task is to produce a comprehensive, data-driven analysis following the guidelines below.
Always cite concrete metrics and sources when possible.
Structure your response with clear sections and bullet points for easy readability.`,
    },
    // 可选：包含最近的对话历史（不超过 5 条）
    ...conversationHistory.slice(-5),
    {
      role: 'user',
      content: `${config.prompt}

Research Target: ${userQuery}

Please provide a detailed ${config.title} focusing on the above criteria.`,
    },
  ]
}

/**
 * 延迟函数（用于重试间隔）
 */
function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

/**
 * 执行单个维度的流式生成（带超时控制）
 */
async function executeDimensionStream(
  dimension: ResearchDimension,
  streamWriter: any,
  chatStreamGenerator: AsyncGenerator<any>
): Promise<string> {
  let fullContent = ''

  // 使用 Promise.race 实现超时控制
  const streamPromise = (async () => {
    try {
      for await (const chunk of chatStreamGenerator) {
        const delta = chunk.choices?.[0]?.delta?.content || ''
        if (delta) {
          fullContent += delta
          await writeSSEEvent(streamWriter, {
            type: 'delta',
            dimension,
            content: delta,
          })
        }

        // 检查是否完成
        if (chunk.choices?.[0]?.finish_reason) {
          break
        }
      }

      return fullContent.trim()
    } catch (error) {
      console.error(`Stream error for dimension ${dimension}:`, error)
      throw error
    }
  })()

  const timeoutPromise = new Promise<string>((_, reject) => {
    setTimeout(() => {
      reject(new Error(`Dimension ${dimension} timed out after ${DIMENSION_TIMEOUT_MS}ms`))
    }, DIMENSION_TIMEOUT_MS)
  })

  // 返回先完成的 Promise（正常完成或超时）
  return await Promise.race([streamPromise, timeoutPromise])
}

/**
 * 带重试机制的维度生成
 */
async function executeDimensionWithRetry(
  dimension: ResearchDimension,
  streamWriter: any,
  createChatStream: () => AsyncGenerator<any>
): Promise<DimensionResult> {
  // 发送维度开始事件
  await writeSSEEvent(streamWriter, {
    type: 'dimension_start',
    dimension,
    timestamp: Date.now(),
  })

  let lastError: Error | null = null

  // 重试循环
  for (let attempt = 0; attempt <= MAX_DIMENSION_RETRIES; attempt++) {
    try {
      const summary = await executeDimensionStream(
        dimension,
        streamWriter,
        createChatStream()
      )

      // 发送维度完成事件
      await writeSSEEvent(streamWriter, {
        type: 'dimension_complete',
        dimension,
        summary,
      })

      return {
        dimension,
        summary,
        timestamp: Date.now(),
      }
    } catch (error) {
      lastError = error instanceof Error ? error : new Error(String(error))
      const isLastAttempt = attempt === MAX_DIMENSION_RETRIES

      console.error(
        `Dimension ${dimension} failed (attempt ${attempt + 1}/${MAX_DIMENSION_RETRIES + 1}):`,
        lastError
      )

      if (!isLastAttempt) {
        // 指数退避：0.5s, 1s, 2s...
        const backoffMs = 500 * Math.pow(2, attempt)
        await delay(backoffMs)
      }
    }
  }

  // 所有重试都失败，发送错误事件
  const errorMessage = lastError?.message || 'Unknown error generating dimension report'
  await writeSSEEvent(streamWriter, {
    type: 'error',
    dimension,
    message: errorMessage,
  })

  throw lastError || new Error(errorMessage)
}

/**
 * 并发执行多个维度的生成
 */
async function executeAllDimensions(
  dimensions: ResearchDimension[],
  streamWriter: any,
  createChatStreamForDimension: (dim: ResearchDimension) => AsyncGenerator<any>
): Promise<Record<string, DimensionResult>> {
  const results: Record<string, DimensionResult> = {}
  let currentIndex = 0

  // Worker 函数：从队列中取出维度并执行
  const worker = async () => {
    while (currentIndex < dimensions.length) {
      const index = currentIndex++
      const dimension = dimensions[index]

      try {
        const result = await executeDimensionWithRetry(
          dimension,
          streamWriter,
          () => createChatStreamForDimension(dimension)
        )
        results[dimension] = result
      } catch (error) {
        console.error(`Failed to generate dimension ${dimension}:`, error)
        // 继续处理其他维度，不中断整体流程
      }
    }
  }

  // 启动并发 workers
  const workerCount = Math.min(MAX_DIMENSION_CONCURRENCY, dimensions.length)
  await Promise.all(Array.from({ length: workerCount }, () => worker()))

  return results
}

/**
 * 生成最终报告摘要（按指定维度顺序）
 */
function generateFinalSummary(
  dimensionResults: Record<string, DimensionResult>,
  orderedDimensions: ResearchDimension[]
): string {
  const sections: string[] = []

  // 按用户请求的维度顺序输出
  for (const dimension of orderedDimensions) {
    const result = dimensionResults[dimension]
    if (!result) continue

    const config = DIMENSION_CONFIG[dimension]
    if (config) {
      sections.push(`### ${config.title}\n\n${result.summary}`)
    }
  }

  if (sections.length === 0) {
    return 'No successful dimension analysis was completed.'
  }

  return sections.join('\n\n---\n\n')
}

/**
 * 从缓存中回放研究报告
 */
async function replayCachedReport(
  streamWriter: any,
  cachedPayload: CachedResearchPayload,
  requestedDimensions: ResearchDimension[],
  conversationId: string
): Promise<void> {
  // 按请求的维度顺序回放
  for (const dimension of requestedDimensions) {
    const cached = cachedPayload.dimensions[dimension]
    if (!cached) continue

    // 模拟流式输出：分块发送
    await writeSSEEvent(streamWriter, {
      type: 'dimension_start',
      dimension,
      timestamp: cached.timestamp,
      from_cache: true,
    })

    // 将缓存的内容分块发送，模拟流式效果（优化：根据内容长度动态调整）
    const summary = cached.summary
    const chunkSize = Math.min(200, Math.ceil(summary.length / 10)) // 动态chunk大小
    const delayMs = 30 // 减少延迟

    for (let i = 0; i < summary.length; i += chunkSize) {
      const chunk = summary.slice(i, i + chunkSize)
      await writeSSEEvent(streamWriter, {
        type: 'delta',
        dimension,
        content: chunk,
        from_cache: true,
      })
      // 添加小延迟以模拟流式效果
      await delay(delayMs)
    }

    await writeSSEEvent(streamWriter, {
      type: 'dimension_complete',
      dimension,
      summary,
      from_cache: true,
    })
  }

  // 发送报告完成事件（包含 conversation_id）
  await writeSSEEvent(streamWriter, {
    type: 'report_complete',
    conversation_id: conversationId,
    final_summary: cachedPayload.final_summary,
    from_cache: true,
  })

  await streamWriter.write('data: [DONE]\n\n')
}

/**
 * 快速聊天端点（流式）
 * POST /chat/quick-chat
 */
router.post('/quick-chat', async (c) => {
  try {
    // 1. 解析请求体
    const body: ChatRequest = await c.req.json()

    // 2. 验证请求参数
    if (!body.query || body.query.trim().length === 0) {
      return c.json(
        { error: 'Bad Request', message: 'query is required and cannot be empty' },
        400
      )
    }

    if (body.query.length > 10000) {
      return c.json(
        { error: 'Bad Request', message: 'query is too long (max 10000 characters)' },
        400
      )
    }

    // 3. 速率限制检查
    if (c.env.CACHE) {
      const clientIP = c.req.header('CF-Connecting-IP') || 'unknown'
      const rateLimiter = new RateLimiter({
        kv: c.env.CACHE,
        limit: 10,  // 每小时 10 次
        window: 3600,
      })

      const rateLimit = await rateLimiter.check(clientIP)
      c.header('X-RateLimit-Limit', rateLimit.limit.toString())
      c.header('X-RateLimit-Remaining', rateLimit.remaining.toString())
      c.header('X-RateLimit-Reset', rateLimit.reset.toString())

      if (rateLimit.remaining === 0) {
        return c.json(
          { error: 'Too Many Requests', message: 'Rate limit exceeded' },
          429
        )
      }
    }

    // 4. 获取或创建对话
    const supabase = getSupabaseClient(c.env)
    const { conversation, isNew } = await getOrCreateConversation(
      supabase,
      body.conversation_id
    )

    // 5. 创建 OpenRouter 客户端
    const openrouter = createOpenRouterClient(c.env.OPENROUTER_API_KEY)
    const selectedModel = body.model || 'deepseek/deepseek-chat-v3-0324'

    // 6. 构建消息历史
    const messages: OpenRouterMessage[] = [
      {
        role: 'system',
        content: 'You are a helpful Web3 and blockchain research assistant. Provide accurate, concise, and well-structured answers.',
      },
    ]

    // 加载历史消息（如果是已存在的对话）
    if (!isNew && body.conversation_id) {
      const history = await getConversationMessages(supabase, conversation.id, 10)
      messages.push(
        ...history.map((msg) => ({
          role: msg.role as 'user' | 'assistant' | 'system',
          content: msg.content,
        }))
      )
    }

    // 添加当前用户消息
    messages.push({
      role: 'user',
      content: body.query,
    })

    // 6. 判断是否流式响应
    const isStream = body.stream !== false  // 默认流式

    if (isStream) {
      // 流式响应
      return stream(c, async (stream) => {
        try {
          let fullContent = ''
          let totalTokens = 0

          // 先保存用户消息
          await saveMessage(supabase, conversation.id, 'user', body.query)

          for await (const chunk of openrouter.chatStream({
            messages,
            model: selectedModel,
          })) {
            const content = chunk.choices[0]?.delta?.content || ''
            if (content) {
              fullContent += content

              const streamChunk: ChatStreamChunk = {
                conversation_id: conversation.id,
                content,
                finish_reason: chunk.choices[0]?.finish_reason || null,
              }

              await stream.write(`data: ${JSON.stringify(streamChunk)}\n\n`)
            }

            if (chunk.choices[0]?.finish_reason) {
              break
            }
          }

          // 保存助手消息到数据库
          await saveMessage(
            supabase,
            conversation.id,
            'assistant',
            fullContent,
            selectedModel,
            totalTokens
          )

          // 更新对话统计信息
          await updateConversationStats(supabase, conversation.id, totalTokens)

          await stream.write('data: [DONE]\n\n')
        } catch (error) {
          console.error('Stream error:', error)
          await stream.write(`data: ${JSON.stringify({ error: 'Stream failed' })}\n\n`)
        }
      })
    } else {
      // 非流式响应
      const response = await openrouter.chat({
        messages,
        model: selectedModel,
      })
      const assistantMessage = response.choices[0]?.message?.content || ''
      const totalTokens = response.usage?.total_tokens || 0

      // 保存用户和助手消息到数据库
      await saveMessage(supabase, conversation.id, 'user', body.query)
      await saveMessage(
        supabase,
        conversation.id,
        'assistant',
        assistantMessage,
        response.model,
        totalTokens
      )

      // 更新对话统计信息
      await updateConversationStats(supabase, conversation.id, totalTokens)

      const chatResponse: ChatResponse = {
        conversation_id: conversation.id,
        message: assistantMessage,
        model: response.model,
        usage: response.usage,
        created_at: new Date().toISOString(),
      }

      return c.json(chatResponse)
    }
  } catch (error) {
    console.error('Chat error:', error)
    return c.json(
      {
        error: 'Internal Server Error',
        message: error instanceof Error ? error.message : 'An unexpected error occurred',
      },
      500
    )
  }
})

/**
 * 深度研究端点（流式多维度分析）
 * POST /chat/deep-research/stream
 */
router.post('/deep-research/stream', async (c) => {
  try {
    // 1. 解析请求体
    const body: DeepResearchRequest = await c.req.json()

    // 2. 验证请求参数
    if (!body.query || body.query.trim().length === 0) {
      return c.json(
        { error: 'Bad Request', message: 'query is required and cannot be empty' },
        400
      )
    }

    if (body.query.length > 10000) {
      return c.json(
        { error: 'Bad Request', message: 'query is too long (max 10000 characters)' },
        400
      )
    }

    // 3. 验证并标准化研究维度
    let selectedDimensions: ResearchDimension[]
    try {
      selectedDimensions = validateAndNormalizeDimensions(body.dimensions)
    } catch (error) {
      return c.json(
        {
          error: 'Bad Request',
          message: error instanceof Error ? error.message : 'Invalid dimensions',
        },
        400
      )
    }

    // 4. 速率限制检查（深度研究使用独立的限制）
    if (!c.env.CACHE) {
      // 如果没有 KV，为安全起见拒绝深度研究服务
      return c.json(
        {
          error: 'Service Unavailable',
          message: 'Deep research is temporarily unavailable. Please try again later.',
        },
        503
      )
    }

    const clientIP = c.req.header('CF-Connecting-IP') || 'unknown'
    const rateLimiter = new RateLimiter({
      kv: c.env.CACHE,
      limit: 3, // 每小时 3 次深度研究
      window: 3600,
    })

    const rateLimit = await rateLimiter.check(`deep-research:${clientIP}`)
    c.header('X-RateLimit-Limit', rateLimit.limit.toString())
    c.header('X-RateLimit-Remaining', rateLimit.remaining.toString())
    c.header('X-RateLimit-Reset', rateLimit.reset.toString())

    if (rateLimit.remaining === 0) {
      return c.json(
        { error: 'Too Many Requests', message: 'Deep research rate limit exceeded' },
        429
      )
    }

    // 5. 获取或创建对话
    const supabase = getSupabaseClient(c.env)
    const { conversation, isNew } = await getOrCreateConversation(
      supabase,
      body.conversation_id
    )

    // 6. 准备 AI 模型和客户端
    const selectedModel = body.model || 'deepseek/deepseek-chat-v3-0324'
    const openrouter = createOpenRouterClient(c.env.OPENROUTER_API_KEY)

    // 7. 加载对话历史（可选，用于上下文）
    const conversationHistory: OpenRouterMessage[] = []
    if (!isNew && body.conversation_id) {
      const history = await getConversationMessages(supabase, conversation.id, 5)
      conversationHistory.push(
        ...history.map((msg) => ({
          role: msg.role as 'user' | 'assistant' | 'system',
          content: msg.content,
        }))
      )
    }

    // 8. 生成缓存键
    const cacheEnabled = Boolean(body.use_cache && c.env.CACHE)
    const cacheKey = cacheEnabled
      ? `deep-research:${CACHE_VERSION}:${await generateCacheHash(
          [selectedModel, ...selectedDimensions, body.query].join('|')
        )}`
      : null

    // 9. 流式响应
    return stream(c, async (streamWriter) => {
      try {
        // 9.1 保存用户消息（无论是否使用缓存都要保存）
        await saveMessage(supabase, conversation.id, 'user', body.query)

        // 9.2 尝试从缓存读取
        if (cacheEnabled && cacheKey && c.env.CACHE) {
          const cached = await c.env.CACHE.get(cacheKey)
          if (cached) {
            try {
              const cachedPayload: CachedResearchPayload = JSON.parse(cached)

              // 即使使用缓存，也要保存助手消息到数据库
              const assistantPayload = {
                type: 'deep_research',
                version: 1,
                query: body.query,
                dimensions: cachedPayload.dimensions,
                final_summary: cachedPayload.final_summary,
                model: cachedPayload.model,
                from_cache: true,
              }

              await saveMessage(
                supabase,
                conversation.id,
                'assistant',
                JSON.stringify(assistantPayload),
                cachedPayload.model
              )

              await updateConversationStats(supabase, conversation.id, 0)

              // 回放缓存，传入 conversation_id
              await replayCachedReport(
                streamWriter,
                cachedPayload,
                selectedDimensions,
                conversation.id
              )
              return
            } catch (error) {
              console.error('Failed to replay cached report, falling back to live generation:', error)
            }
          }
        }

        // 9.3 为每个维度创建 AI stream generator
        const createChatStreamForDimension = (dimension: ResearchDimension) => {
          const messages = buildDimensionMessages(
            dimension,
            body.query,
            conversationHistory
          )
          return openrouter.chatStream({
            model: selectedModel,
            messages,
          })
        }

        // 9.4 并发执行所有维度的生成
        const dimensionResults = await executeAllDimensions(
          selectedDimensions,
          streamWriter,
          createChatStreamForDimension
        )

        // 9.5 生成最终摘要（按用户请求的维度顺序）
        const finalSummary = generateFinalSummary(dimensionResults, selectedDimensions)

        // 9.6 发送报告完成事件
        await writeSSEEvent(streamWriter, {
          type: 'report_complete',
          conversation_id: conversation.id,
          final_summary: finalSummary,
        })

        // 9.7 保存助手消息到数据库
        const assistantPayload = {
          type: 'deep_research',
          version: 1,
          query: body.query,
          dimensions: dimensionResults,
          final_summary: finalSummary,
          model: selectedModel,
        }

        await saveMessage(
          supabase,
          conversation.id,
          'assistant',
          JSON.stringify(assistantPayload),
          selectedModel
        )

        // 9.8 更新对话统计（token 计数暂时设为 0，需要从 OpenRouter 获取）
        await updateConversationStats(supabase, conversation.id, 0)

        // 9.9 写入缓存
        if (cacheEnabled && cacheKey && c.env.CACHE) {
          const cachePayload: CachedResearchPayload = {
            version: 1,
            model: selectedModel,
            query_hash: await generateCacheHash(body.query),
            dimensions: dimensionResults,
            final_summary: finalSummary,
            created_at: Date.now(),
          }

          try {
            await c.env.CACHE.put(cacheKey, JSON.stringify(cachePayload), {
              expirationTtl: 1800, // 30 分钟
            })
          } catch (error) {
            console.error('Failed to write cache:', error)
          }
        }

        // 9.10 发送结束标记
        await streamWriter.write('data: [DONE]\n\n')
      } catch (error) {
        console.error('Deep research stream error:', error)
        await writeSSEEvent(streamWriter, {
          type: 'error',
          message: error instanceof Error ? error.message : 'Deep research stream failed',
        })
        await streamWriter.write('data: [DONE]\n\n')
      }
    })
  } catch (error) {
    console.error('Deep research error:', error)
    return c.json(
      {
        error: 'Internal Server Error',
        message: error instanceof Error ? error.message : 'Failed to process deep research request',
      },
      500
    )
  }
})

/**
 * 获取对话历史
 * GET /chat/conversations/:id
 */
router.get('/conversations/:id', async (c) => {
  try {
    const conversationId = c.req.param('id')
    const supabase = getSupabaseClient(c.env)

    // 查询对话历史消息
    const messages = await getConversationMessages(supabase, conversationId, 100)

    if (messages.length === 0) {
      return c.json(
        { error: 'Not Found', message: 'Conversation not found' },
        404
      )
    }

    return c.json({
      conversation_id: conversationId,
      messages,
    })
  } catch (error) {
    console.error('Get conversation error:', error)
    return c.json(
      {
        error: 'Internal Server Error',
        message: error instanceof Error ? error.message : 'Failed to fetch conversation',
      },
      500
    )
  }
})

export default router
