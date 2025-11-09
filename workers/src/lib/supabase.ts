import { createClient, type SupabaseClient } from '@supabase/supabase-js'
import type { Env } from '../types/env'

type ClientRole = 'anon' | 'service'
type ClientCacheKey = `${ClientRole}:${string}`

// 模块级别的客户端缓存，避免重复创建
const clientCache = new Map<ClientCacheKey, SupabaseClient>()

/**
 * Supabase 健康检查结果
 */
export interface SupabaseHealth {
  status: 'ok' | 'error'
  latencyMs: number
  message?: string
}

/**
 * 获取 Supabase 客户端实例
 * 使用缓存避免重复创建连接
 *
 * @param env - Worker 环境变量
 * @param role - 使用的密钥角色 ('anon' 或 'service')
 * @returns Supabase 客户端实例
 */
export function getSupabaseClient(env: Env, role: ClientRole = 'anon'): SupabaseClient {
  const url = env.SUPABASE_URL
  if (!url) {
    throw new Error('SUPABASE_URL is not configured')
  }

  // 根据角色选择对应的 API 密钥 - 显式检查而不是静默回退
  let apiKey: string
  if (role === 'service') {
    if (!env.SUPABASE_SERVICE_ROLE_KEY) {
      throw new Error('SUPABASE_SERVICE_ROLE_KEY not configured but service role requested')
    }
    apiKey = env.SUPABASE_SERVICE_ROLE_KEY
  } else {
    if (!env.SUPABASE_ANON_KEY) {
      throw new Error('SUPABASE_ANON_KEY not configured')
    }
    apiKey = env.SUPABASE_ANON_KEY
  }

  // 构建缓存键
  const cacheKey: ClientCacheKey = `${role}:${url}`
  let client = clientCache.get(cacheKey)

  if (!client) {
    client = createClient(url, apiKey, {
      global: {
        fetch, // 使用 Workers 原生的 fetch
        headers: { 'X-Client-Info': 'web3search-worker' },
      },
    })
    clientCache.set(cacheKey, client)
  }

  return client
}

/**
 * 检查 Supabase 数据库连接健康状况
 *
 * @param env - Worker 环境变量
 * @returns 健康检查结果（包含状态、延迟、错误信息）
 */
export async function checkSupabaseHealth(env: Env): Promise<SupabaseHealth> {
  const client = getSupabaseClient(env)
  const targetTable = env.SUPABASE_HEALTH_TABLE ?? 'projects'
  const started = performance.now()

  try {
    // 执行轻量级查询验证连接 (不使用 count 以避免 O(n) 性能问题)
    const { error } = await client
      .from(targetTable)
      .select('id', { head: true })
      .limit(1)

    const latencyMs = Math.round(performance.now() - started)

    if (error) {
      return {
        status: 'error',
        latencyMs,
        message: error.message
      }
    }

    return { status: 'ok', latencyMs }
  } catch (error) {
    const latencyMs = Math.round(performance.now() - started)
    const message = error instanceof Error
      ? error.message
      : 'Unknown Supabase error'

    return { status: 'error', latencyMs, message }
  }
}
