/**
 * Cloudflare Workers Cron Jobs
 * 处理跨系统的后台任务（健康检查、KV 清理）
 */

import type { Env } from './types/env'
import { getSupabaseClient } from './lib/supabase'
import { createOpenRouterClient } from './lib/openrouter'

/**
 * 健康检查结果接口
 */
interface HealthCheckResult {
  check_name: string
  status: 'healthy' | 'degraded' | 'down'
  latency_ms: number
  error_message?: string
  details?: Record<string, any>
}

/**
 * Cron 任务处理器
 */
export async function handleScheduled(
  event: ScheduledEvent,
  env: Env,
  ctx: ExecutionContext
): Promise<void> {
  const cron = event.cron

  console.log(`[Cron] Triggered: ${cron}`)

  try {
    // 每 5 分钟：健康检查
    if (cron === '*/5 * * * *') {
      await runHealthChecks(env, ctx)
    }

    // 每小时：KV 缓存清理
    if (cron === '0 * * * *') {
      await cleanupExpiredCache(env, ctx)
    }

    // 每 15 分钟：重试失败任务（未来实现）
    // if (cron === '*/15 * * * *') {
    //   await retryFailedTasks(env, ctx)
    // }
  } catch (error) {
    console.error('[Cron] Error:', error)
    // 不抛出错误，避免影响其他 cron 任务
  }
}

/**
 * 健康检查任务
 * 检查 Supabase、OpenRouter、KV 的可用性
 */
async function runHealthChecks(env: Env, ctx: ExecutionContext): Promise<void> {
  console.log('[HealthCheck] Starting health checks...')

  const results: HealthCheckResult[] = []

  // 1. 检查 Supabase 连接
  results.push(await checkSupabase(env))

  // 2. 检查 OpenRouter API
  results.push(await checkOpenRouter(env))

  // 3. 检查 KV 存储
  if (env.CACHE) {
    results.push(await checkKVStorage(env))
  }

  // 4. 保存健康检查结果到 Supabase
  await saveHealthCheckResults(env, results)

  // 5. 检查是否需要告警
  const failedChecks = results.filter((r) => r.status === 'down')
  if (failedChecks.length > 0) {
    console.error('[HealthCheck] Some checks failed:', failedChecks)
    // TODO: 发送告警到 Slack/Email
  }

  console.log('[HealthCheck] Completed. Results:', results)
}

/**
 * 检查 Supabase 数据库连接
 */
async function checkSupabase(env: Env): Promise<HealthCheckResult> {
  const startTime = Date.now()

  try {
    const supabase = getSupabaseClient(env)

    // 简单查询测试连接
    const { data, error } = await supabase
      .from('conversations')
      .select('id')
      .limit(1)

    const latency = Date.now() - startTime

    if (error) {
      return {
        check_name: 'supabase',
        status: 'down',
        latency_ms: latency,
        error_message: error.message,
      }
    }

    // 延迟超过 2 秒视为降级
    const status = latency > 2000 ? 'degraded' : 'healthy'

    return {
      check_name: 'supabase',
      status,
      latency_ms: latency,
      details: { rows_returned: data?.length || 0 },
    }
  } catch (error) {
    return {
      check_name: 'supabase',
      status: 'down',
      latency_ms: Date.now() - startTime,
      error_message: error instanceof Error ? error.message : String(error),
    }
  }
}

/**
 * 检查 OpenRouter API 可用性
 */
async function checkOpenRouter(env: Env): Promise<HealthCheckResult> {
  const startTime = Date.now()

  try {
    const openrouter = createOpenRouterClient(env.OPENROUTER_API_KEY)

    // 调用 models 端点检查可用性
    const response = await fetch('https://openrouter.ai/api/v1/models', {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${env.OPENROUTER_API_KEY}`,
        'HTTP-Referer': 'https://web3search.ai',
        'X-Title': 'Web3Search',
      },
      signal: AbortSignal.timeout(5000), // 5 秒超时
    })

    const latency = Date.now() - startTime

    if (!response.ok) {
      return {
        check_name: 'openrouter',
        status: 'down',
        latency_ms: latency,
        error_message: `HTTP ${response.status}: ${response.statusText}`,
      }
    }

    const status = latency > 3000 ? 'degraded' : 'healthy'

    return {
      check_name: 'openrouter',
      status,
      latency_ms: latency,
    }
  } catch (error) {
    return {
      check_name: 'openrouter',
      status: 'down',
      latency_ms: Date.now() - startTime,
      error_message: error instanceof Error ? error.message : String(error),
    }
  }
}

/**
 * 检查 KV 存储可用性
 */
async function checkKVStorage(env: Env): Promise<HealthCheckResult> {
  const startTime = Date.now()
  const testKey = `healthcheck:${Date.now()}`

  try {
    // 写入测试
    await env.CACHE!.put(testKey, 'test', { expirationTtl: 60 })

    // 读取测试
    const value = await env.CACHE!.get(testKey)

    // 删除测试
    await env.CACHE!.delete(testKey)

    const latency = Date.now() - startTime

    if (value !== 'test') {
      return {
        check_name: 'kv_storage',
        status: 'down',
        latency_ms: latency,
        error_message: 'Read/write mismatch',
      }
    }

    const status = latency > 1000 ? 'degraded' : 'healthy'

    return {
      check_name: 'kv_storage',
      status,
      latency_ms: latency,
    }
  } catch (error) {
    return {
      check_name: 'kv_storage',
      status: 'down',
      latency_ms: Date.now() - startTime,
      error_message: error instanceof Error ? error.message : String(error),
    }
  }
}

/**
 * 保存健康检查结果到 Supabase
 */
async function saveHealthCheckResults(
  env: Env,
  results: HealthCheckResult[]
): Promise<void> {
  try {
    const supabase = getSupabaseClient(env)

    const records = results.map((result) => ({
      check_name: result.check_name,
      status: result.status,
      latency_ms: result.latency_ms,
      error_message: result.error_message || null,
      details: result.details || {},
      observed_at: new Date().toISOString(),
    }))

    const { error } = await supabase.from('healthcheck_events').insert(records)

    if (error) {
      console.error('[HealthCheck] Failed to save results:', error)
    }
  } catch (error) {
    console.error('[HealthCheck] Error saving results:', error)
  }
}

/**
 * KV 缓存清理任务
 * 清理过期的缓存条目（虽然有 TTL，但手动清理可以释放存储空间）
 */
async function cleanupExpiredCache(env: Env, ctx: ExecutionContext): Promise<void> {
  if (!env.CACHE) {
    console.log('[KVCleanup] KV storage not available, skipping')
    return
  }

  console.log('[KVCleanup] Starting KV cache cleanup...')

  try {
    const taskId = await recordTaskStart(env, 'kv-cache-cleanup', 'worker')

    let deletedCount = 0
    let cursor: string | undefined

    // 分页列出所有键（最多处理 1000 个）
    const maxIterations = 10
    let iterations = 0

    do {
      const listResult = await env.CACHE.list({
        prefix: 'deep-research:', // 只清理深度研究缓存
        limit: 100,
        cursor,
      })

      // KV 没有内置的过期检查，只能删除旧键
      // 这里我们可以根据键名中的时间戳判断
      for (const key of listResult.keys) {
        // 删除超过 1 小时的缓存键
        if (key.metadata && typeof key.metadata === 'object') {
          const metadata = key.metadata as { created_at?: number }
          if (metadata.created_at) {
            const ageMs = Date.now() - metadata.created_at
            if (ageMs > 3600000) {
              // 1 小时
              await env.CACHE.delete(key.name)
              deletedCount++
            }
          }
        }
      }

      // 检查是否还有更多结果
      if (listResult.list_complete) {
        break
      }

      cursor = (listResult as any).cursor
      iterations++
    } while (iterations < maxIterations)

    await recordTaskFinish(env, taskId, 'success', deletedCount)

    console.log(`[KVCleanup] Completed. Deleted ${deletedCount} expired keys`)
  } catch (error) {
    console.error('[KVCleanup] Error:', error)
  }
}

/**
 * 记录任务开始
 */
async function recordTaskStart(
  env: Env,
  jobName: string,
  origin: 'worker' | 'pg_cron'
): Promise<string> {
  try {
    const supabase = getSupabaseClient(env)

    const { data, error } = await supabase
      .from('task_runs')
      .insert({
        job_name: jobName,
        origin,
        scheduled_for: new Date().toISOString(),
        started_at: new Date().toISOString(),
        status: 'running',
      })
      .select('id')
      .single()

    if (error || !data) {
      console.error('[Task] Failed to record task start:', error)
      return ''
    }

    return data.id
  } catch (error) {
    console.error('[Task] Error recording task start:', error)
    return ''
  }
}

/**
 * 记录任务完成
 */
async function recordTaskFinish(
  env: Env,
  taskId: string,
  status: 'success' | 'failed',
  rowsAffected: number = 0,
  errorMessage?: string
): Promise<void> {
  if (!taskId) return

  try {
    const supabase = getSupabaseClient(env)

    const { error } = await supabase
      .from('task_runs')
      .update({
        finished_at: new Date().toISOString(),
        status,
        rows_affected: rowsAffected,
        error_message: errorMessage || null,
      })
      .eq('id', taskId)

    if (error) {
      console.error('[Task] Failed to record task finish:', error)
    }
  } catch (error) {
    console.error('[Task] Error recording task finish:', error)
  }
}
