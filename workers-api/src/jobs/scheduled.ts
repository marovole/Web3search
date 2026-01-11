/**
 * Scheduled Jobs Module
 * Centralizes all cron/scheduled task implementations
 * Extracted from index.ts to improve code organization
 */

import type { Env } from '../types/env'
import { createStandaloneLogger } from '../lib/logger'

const createJobLogger = (env: Env, jobName: string) =>
  createStandaloneLogger(env.ENVIRONMENT || 'development', `job:${jobName}`)

export async function runHealthChecks(env: Env, _ctx: ExecutionContext) {
  const logger = createJobLogger(env, 'health-check')
  const { getSupabaseClient } = await import('../lib/supabase')
  const { createOpenRouterClient } = await import('../lib/openrouter')

  const results: Array<{
    check_name: string
    status: string
    latency_ms: number
    error_message?: string
    details?: Record<string, unknown>
  }> = []

  const startTime = Date.now()

  try {
    const supabase = getSupabaseClient(env)
    const { error } = await supabase.from('conversations').select('id').limit(1)
    results.push({
      check_name: 'supabase_database',
      status: error ? 'down' : 'healthy',
      latency_ms: Date.now() - startTime,
      details: { error: error?.message },
    })
  } catch (error) {
    results.push({
      check_name: 'supabase_database',
      status: 'down',
      latency_ms: Date.now() - startTime,
      error_message: error instanceof Error ? error.message : 'Unknown error',
      details: { type: 'connection_error' },
    })
  }

  try {
    createOpenRouterClient(env)
    results.push({
      check_name: 'openrouter_api',
      status: 'healthy',
      latency_ms: Date.now() - startTime,
      details: { type: 'client_init_success' },
    })
  } catch (error) {
    results.push({
      check_name: 'openrouter_api',
      status: 'down',
      latency_ms: Date.now() - startTime,
      error_message: error instanceof Error ? error.message : 'Unknown error',
      details: { type: 'client_init_error' },
    })
  }

  if (!env.CACHE) {
    results.push({
      check_name: 'kv_cache',
      status: 'down',
      latency_ms: 0,
      error_message: 'CACHE namespace not bound',
      details: { type: 'not_configured' },
    })
  } else {
    try {
      const testKey = 'health-check-test'
      await env.CACHE.put(testKey, 'test', { expirationTtl: 60 })
      const value = await env.CACHE.get(testKey)
      await env.CACHE.delete(testKey)
      results.push({
        check_name: 'kv_cache',
        status: value === 'test' ? 'healthy' : 'degraded',
        latency_ms: Date.now() - startTime,
        details: { operation: 'read_write_test', success: value === 'test' },
      })
    } catch (error) {
      results.push({
        check_name: 'kv_cache',
        status: 'down',
        latency_ms: Date.now() - startTime,
        error_message: error instanceof Error ? error.message : 'Unknown error',
        details: { type: 'kv_error' },
      })
    }
  }

  try {
    const supabase = getSupabaseClient(env)
    await supabase.from('healthcheck_events').insert(
      results.map((check) => ({
        ...check,
        observed_at: new Date().toISOString(),
      }))
    )
  } catch (error) {
    logger.error('Failed to save health check results', error instanceof Error ? error : undefined)
  }

  logger.info('Health check completed', { servicesChecked: results.length })
}

export async function runSupabaseKeepAlive(env: Env) {
  const logger = createJobLogger(env, 'keep-alive')
  const { getSupabaseClient } = await import('../lib/supabase')
  const startTime = Date.now()

  try {
    const supabase = getSupabaseClient(env)
    const { error } = await supabase
      .from('conversations')
      .select('id', { count: 'exact', head: true })
      .limit(1)

    const latency = Date.now() - startTime
    const ignorableCodes = ['PGRST116', 'PGRST301', '42P01']

    if (error && !ignorableCodes.includes(error.code || '')) {
      logger.warn('Supabase ping degraded', {
        code: error.code,
        message: error.message,
        latency_ms: latency,
      })
      return
    }

    logger.info('Supabase warm-up completed', {
      latency_ms: latency,
      table: 'conversations',
      status: error ? 'ok-with-limited-table' : 'ok',
    })
  } catch (error) {
    logger.error('Supabase warm-up failed', error instanceof Error ? error : undefined)
  }
}

export async function runKvCacheCleanup(env: Env, _ctx: ExecutionContext) {
  const logger = createJobLogger(env, 'cache-cleanup')

  if (!env.CACHE) {
    logger.warn('CACHE not bound, skipping cleanup')
    return
  }

  try {
    const prefix = 'deep-research:'
    const cutoffTime = Date.now() - 24 * 60 * 60 * 1000
    let cleanedCount = 0

    const list = await env.CACHE.list({ prefix })
    for (const key of list.keys) {
      if (key.expiration && key.expiration * 1000 < cutoffTime) {
        await env.CACHE.delete(key.name)
        cleanedCount++
      }
    }

    logger.info('KV cache cleanup completed', { entriesRemoved: cleanedCount })
  } catch (error) {
    logger.error('KV cache cleanup failed', error instanceof Error ? error : undefined)
  }
}

export async function runDailyQuotaReset(env: Env) {
  const logger = createJobLogger(env, 'quota-reset-daily')
  const { getSupabaseClient } = await import('../lib/supabase')
  const supabase = getSupabaseClient(env, true)

  try {
    const { error } = await supabase.rpc('reset_daily_quotas')
    if (error) {
      logger.warn('Daily quota reset RPC failed, using direct update', { error: error.message })
      await supabase
        .from('user_quotas')
        .update({
          daily_alerts_sent: 0,
          daily_deep_research: 0,
          daily_quick_chat: 0,
          daily_reset_at: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
        })
        .lte('daily_reset_at', new Date().toISOString())
    }
    logger.info('Daily quota reset completed')
  } catch (error) {
    logger.error('Daily quota reset failed', error instanceof Error ? error : undefined)
  }
}

export async function runMonthlyQuotaReset(env: Env) {
  const logger = createJobLogger(env, 'quota-reset-monthly')
  const { getSupabaseClient } = await import('../lib/supabase')
  const supabase = getSupabaseClient(env, true)

  try {
    const { error } = await supabase.rpc('reset_monthly_quotas')
    if (error) {
      logger.warn('Monthly quota reset RPC failed, using direct update', { error: error.message })
      const nextMonth = new Date()
      nextMonth.setMonth(nextMonth.getMonth() + 1)
      nextMonth.setDate(1)
      nextMonth.setHours(0, 0, 0, 0)

      await supabase
        .from('user_quotas')
        .update({
          monthly_reports: 0,
          monthly_reset_at: nextMonth.toISOString(),
        })
        .lte('monthly_reset_at', new Date().toISOString())
    }
    logger.info('Monthly quota reset completed')
  } catch (error) {
    logger.error('Monthly quota reset failed', error instanceof Error ? error : undefined)
  }
}

function calculateNextRun(taskType: string): Date {
  const now = new Date()
  const intervals: Record<string, number> = {
    price_alert: 5 * 60 * 1000,
    risk_monitor: 60 * 60 * 1000,
    news_brief: 60 * 60 * 1000,
    portfolio_health: 7 * 24 * 60 * 60 * 1000,
    opportunity_finder: 7 * 24 * 60 * 60 * 1000,
  }
  return new Date(now.getTime() + (intervals[taskType] || 60 * 60 * 1000))
}

export async function runAgentTasks(env: Env, taskType: string) {
  const logger = createJobLogger(env, `agent-tasks:${taskType}`)

  const specializedProcessors: Record<string, () => Promise<void>> = {
    price_alert: async () => {
      const { processPriceAlerts } = await import('../lib/price-alert-processor')
      await processPriceAlerts(env)
    },
    risk_monitor: async () => {
      const { processRiskMonitor } = await import('../lib/risk-monitor-processor')
      await processRiskMonitor(env)
    },
    news_brief: async () => {
      const { processNewsBrief } = await import('../lib/news-brief-processor')
      await processNewsBrief(env)
    },
    portfolio_health: async () => {
      const { processPortfolioDiagnosis } = await import('../lib/portfolio-diagnosis-processor')
      await processPortfolioDiagnosis(env)
    },
    opportunity_finder: async () => {
      const { processOpportunityDiscovery } = await import('../lib/opportunity-discovery-processor')
      await processOpportunityDiscovery(env)
    },
  }

  if (specializedProcessors[taskType]) {
    await specializedProcessors[taskType]()
    return
  }

  const { getSupabaseClient } = await import('../lib/supabase')
  const { executeAgentTask } = await import('../lib/agent-engine')
  const supabase = getSupabaseClient(env, true)

  try {
    const now = new Date()
    const { data: dueTasks, error } = await supabase
      .from('agent_tasks')
      .select('id, user_id, task_type, config')
      .eq('task_type', taskType)
      .eq('status', 'active')
      .or(`next_run_at.is.null,next_run_at.lte.${now.toISOString()}`)
      .limit(50)

    if (error) {
      logger.error(`Failed to fetch ${taskType} tasks`, undefined, { error: error.message })
      return
    }

    if (!dueTasks || dueTasks.length === 0) {
      logger.debug(`No due ${taskType} tasks`)
      return
    }

    logger.info(`Processing ${dueTasks.length} ${taskType} tasks`)

    for (const task of dueTasks) {
      try {
        await executeAgentTask(env, task.id, task.user_id, task.task_type, task.config)
        const nextRunAt = calculateNextRun(taskType)
        await supabase
          .from('agent_tasks')
          .update({ next_run_at: nextRunAt.toISOString() })
          .eq('id', task.id)
      } catch (taskError) {
        logger.error(
          `Task ${task.id} execution failed`,
          taskError instanceof Error ? taskError : undefined
        )
      }
    }

    logger.info(`Completed ${taskType} tasks`)
  } catch (error) {
    logger.error(`Error running ${taskType} tasks`, error instanceof Error ? error : undefined)
  }
}
