import { Hono } from 'hono'
import { stream } from 'hono/streaming'
import { createOpenRouterClient } from '../lib/openrouter'
import { RateLimiter } from '../lib/rate-limiter'
import { getSupabaseClient } from '../lib/supabase'
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
    const selectedModel = body.model || 'anthropic/claude-3.5-sonnet'

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
