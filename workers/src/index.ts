/**
 * Web3 Search Cloudflare Worker
 * 基于 Hono 框架，连接 Supabase 数据库
 */
import { Hono } from 'hono'
import { cors } from './middlewares/cors'
import { logger } from './middlewares/logger'
import healthRouter from './routes/health'
import searchRouter from './routes/search'
import chatRouter from './routes/chat'
import type { Env } from './types/env'

// 创建 Hono 应用实例
const app = new Hono<{ Bindings: Env }>()

// 全局中间件
app.use('*', logger())  // 请求日志记录
app.use('*', cors())    // CORS 处理

// 挂载路由
app.route('/api/v1', healthRouter)
app.route('/api/v1/search', searchRouter)
app.route('/api/v1/chat', chatRouter)

// 404 处理
app.notFound((c) =>
  c.json(
    {
      error: 'Not Found',
      path: c.req.path,
      message: 'The requested endpoint does not exist',
    },
    404
  )
)

// 全局错误处理
app.onError((error, c) => {
  console.error('Unhandled worker error:', {
    error: error.message,
    stack: error.stack,
    path: c.req.path,
    method: c.req.method,
  })

  return c.json(
    {
      error: 'Internal Server Error',
      message: 'An unexpected error occurred',
    },
    500
  )
})

export default app
