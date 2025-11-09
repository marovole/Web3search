import { Hono } from 'hono'
import { checkSupabaseHealth } from '../lib/supabase'
import type { Env } from '../types/env'

// 记录 Worker 启动时间，用于计算 uptime
const BOOT_TIME = Date.now()

// 健康状态阈值（毫秒）
const DEGRADED_THRESHOLD_MS = 750

const router = new Hono<{ Bindings: Env }>()

/**
 * 健康检查端点
 * GET /health
 *
 * 返回服务健康状态、Supabase 连接状态、运行时间等信息
 */
router.get('/health', async (c) => {
  // 检查 Supabase 数据库连接
  const supabase = await checkSupabaseHealth(c.env)

  // 根据 Supabase 状态和延迟判断整体健康状态
  let status: 'healthy' | 'degraded' | 'unhealthy' = 'healthy'

  if (supabase.status === 'error') {
    status = 'unhealthy'
  } else if (supabase.latencyMs > DEGRADED_THRESHOLD_MS) {
    status = 'degraded'
  }

  // 构建响应数据
  const responseBody = {
    status,
    timestamp: new Date().toISOString(),
    uptimeMs: Date.now() - BOOT_TIME,
    version: c.env.APP_VERSION ?? 'unknown',
    supabase,
  }

  // 根据健康状态返回对应的 HTTP 状态码
  const httpStatus = status === 'unhealthy' ? 503 : 200

  // 返回 JSON 响应，禁用缓存
  return c.json(
    responseBody,
    httpStatus,
    {
      'Cache-Control': 'no-store, max-age=0',
    }
  )
})

export default router
