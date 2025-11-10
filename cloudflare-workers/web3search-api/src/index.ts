import { Hono } from 'hono'
import { cors } from 'hono/cors'
import { logger } from 'hono/logger'
import { createClient } from '@supabase/supabase-js'
import { callOpenRouter, OpenRouterMessage } from './lib/openrouter'

// 类型定义
interface Bindings {
  SUPABASE_URL: string
  SUPABASE_ANON_KEY: string
  OPENROUTER_API_KEY: string
  ENVIRONMENT: string
}

const app = new Hono<{ Bindings: Bindings }>()

// 中间件配置
app.use('*', cors({
  origin: (origin) => {
    // 允许所有 web3search.pages.dev 子域名（包括预览部署）
    if (origin.endsWith('.web3search.pages.dev') || origin === 'https://web3search.pages.dev' || origin === 'http://localhost:5173') {
      return origin
    }
    return 'https://web3search.pages.dev'
  },
  allowMethods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowHeaders: ['Content-Type', 'Authorization'],
}))

app.use('*', logger())

// Supabase 客户端工厂
const createSupabaseClient = (env: Bindings) => {
  return createClient(env.SUPABASE_URL, env.SUPABASE_ANON_KEY)
}

// 健康检查端点
app.get('/api/v1/health', async (c) => {
  const startTime = Date.now()

  try {
    // 测试数据库连接
    const supabase = createSupabaseClient(c.env)
    const { error } = await supabase.from('conversations').select('id').limit(1)

    const status = error ? 'degraded' : 'healthy'
    const responseTime = Date.now() - startTime

    return c.json({
      status,
      timestamp: new Date().toISOString(),
      version: '1.0.0',
      response_time: `${responseTime}ms`,
      environment: c.env.ENVIRONMENT || 'unknown',
      database: error ? 'disconnected' : 'connected',
      uptime: 'N/A (worker environment)'
    })
  } catch (error) {
    return c.json({
      status: 'unhealthy',
      timestamp: new Date().toISOString(),
      error: error instanceof Error ? error.message : 'Unknown error',
      response_time: `${Date.now() - startTime}ms`
    }, 503)
  }
})

// 搜索自动完成 API
app.get('/api/v1/search/autocomplete', async (c) => {
  const query = c.req.query('q')

  if (!query || query.trim().length < 2) {
    return c.json({
      error: 'Query parameter is required and must be at least 2 characters',
      suggestions: []
    }, 400)
  }

  try {
    const supabase = createSupabaseClient(c.env)

    // 这里暂时返回示例数据，等数据库迁移完成后替换为实际查询
    const suggestions = [
      `${query} price prediction`,
      `${query} market analysis`,
      `${query} trading volume`,
      `${query} technical indicators`
    ].slice(0, 5)

    return c.json({
      results: suggestions,
      count: suggestions.length
    })
  } catch (error) {
    return c.json({
      error: 'Failed to fetch suggestions',
      message: error instanceof Error ? error.message : 'Unknown error',
      suggestions: []
    }, 500)
  }
})

// 聊天 API（基础版本）
app.post('/api/v1/chat/quick-chat', async (c) => {
  try {
    const body = await c.req.json()
    const {
      query,
      conversation_id,
      model = 'meta-llama/llama-3.2-3b-instruct:free',
      stream = false,
      temperature,
      max_tokens
    } = body

    if (!query || query.trim().length === 0) {
      return c.json({
        error: 'Query parameter is required',
        response: null
      }, 400)
    }

    const messages: OpenRouterMessage[] = [
      { role: 'user', content: query.trim() }
    ]

    const routerResult = await callOpenRouter(c.env, {
      messages,
      stream,
      model,
      temperature,
      max_tokens
    })

    if (stream) {
      const responseStream = routerResult.stream
      if (!responseStream) {
        throw new Error('OpenRouter stream response missing payload')
      }

      const reader = responseStream.getReader()
      const decoder = new TextDecoder()
      return c.streamText(async (stream) => {
        try {
          while (true) {
            const { value, done } = await reader.read()
            if (done) break
            await stream.write(decoder.decode(value))
          }
        } finally {
          reader.releaseLock()
        }
      })
    }

    const payload = routerResult.payload ?? {}
    const content =
      (payload as any).choices?.[0]?.message?.content ||
      'OpenRouter 未返回有效响应'
    const usage = (payload as any).usage ?? {}

    return c.json({
      query: query.trim(),
      response: content,
      conversation_id: conversation_id || `conv_${Date.now()}`,
      model,
      timestamp: new Date().toISOString(),
      tokens: {
        input: query.length,
        output: content.length,
        total: query.length + content.length,
        ...usage
      }
    })
  } catch (error) {
    return c.json({
      error: 'Failed to process chat request',
      message: error instanceof Error ? error.message : 'Unknown error',
      response: null
    }, 500)
  }
})

// 根路径
app.get('/', (c) => {
  return c.json({
    message: 'Web3search API',
    version: '1.0.0',
    status: 'running',
    endpoints: {
      health: '/api/v1/health',
      autocomplete: '/api/v1/search/autocomplete?q=<query>',
      chat: '/api/v1/chat/quick-chat (POST)',
    },
    documentation: 'https://github.com/marovole/Web3search',
    timestamp: new Date().toISOString()
  })
})

// 404 处理
app.notFound((c) => {
  return c.json({
    error: 'Endpoint not found',
    message: `The requested endpoint ${c.req.path} does not exist`,
    available_endpoints: {
      health: '/api/v1/health',
      autocomplete: '/api/v1/search/autocomplete?q=<query>',
      chat: '/api/v1/chat/quick-chat (POST)',
      root: '/'
    }
  }, 404)
})

export default app
