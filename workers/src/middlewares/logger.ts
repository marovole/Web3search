import type { MiddlewareHandler } from 'hono'
import type { Env } from '../types/env'

/**
 * 结构化日志中间件
 * 记录每个请求的详细信息和响应时间
 */
export const logger = (): MiddlewareHandler<{ Bindings: Env }> => async (c, next) => {
  const requestId = crypto.randomUUID()
  const started = performance.now()

  try {
    await next()
  } finally {
    const durationMs = Math.round(performance.now() - started)

    // 结构化日志输出
    const logPayload = {
      event: 'worker.request',
      requestId,
      method: c.req.method,
      path: c.req.path,
      status: c.res.status,
      durationMs,
      timestamp: new Date().toISOString(),
    }

    // 添加响应头
    c.header('X-Request-Id', requestId, { append: false })
    c.header('X-Response-Time', `${durationMs}ms`, { append: false })

    // 输出 JSON 格式的日志（便于后续分析）
    console.log(JSON.stringify(logPayload))
  }
}
