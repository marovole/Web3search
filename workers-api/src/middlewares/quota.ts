import { Context, Next } from 'hono'
import type { Env } from '../types/env'
import { getCurrentUser } from './auth'
import { getSupabaseClient } from '../lib/supabase'
import { isQuotaExceeded } from '../lib/quota-limits'

export type QuotaField =
  | 'daily_deep_research'
  | 'daily_quick_chat'
  | 'daily_alerts_sent'
  | 'monthly_reports'
  | 'watchlist_count'
  | 'agent_count'

interface QuotaCheckOptions {
  field: QuotaField
  increment?: number
}

function quotaError(c: Context, field: string, used: number, limit: number) {
  return c.json(
    {
      error: {
        code: 'QUOTA_EXCEEDED',
        message: `You have exceeded your ${field.replace(/_/g, ' ')} quota`,
        status: 429,
        details: { field, used, limit, upgrade_url: '/upgrade' },
      },
    },
    429
  )
}

export function checkQuota(options: QuotaCheckOptions) {
  const { field, increment = 1 } = options

  return async (c: Context<{ Bindings: Env }>, next: Next) => {
    const user = getCurrentUser(c)

    if (!user) {
      await next()
      return
    }

    const supabase = getSupabaseClient(c.env, true)

    const { data: quota, error } = await supabase.from('user_quotas').select('*').eq('user_id', user.id).single()

    if (error || !quota) {
      console.error('[Quota] Failed to fetch quota:', error)
      await next()
      return
    }

    const fieldMap: Record<QuotaField, { used: string; limit: string }> = {
      daily_deep_research: { used: 'daily_deep_research', limit: 'daily_deep_research_limit' },
      daily_quick_chat: { used: 'daily_quick_chat', limit: 'daily_quick_chat_limit' },
      daily_alerts_sent: { used: 'daily_alerts_sent', limit: 'daily_alerts_limit' },
      monthly_reports: { used: 'monthly_reports', limit: 'monthly_reports_limit' },
      watchlist_count: { used: 'watchlist_count', limit: 'watchlist_limit' },
      agent_count: { used: 'agent_count', limit: 'agent_limit' },
    }

    const mapping = fieldMap[field]
    const used = quota[mapping.used] as number
    const limit = quota[mapping.limit] as number

    if (isQuotaExceeded(used + increment - 1, limit)) {
      return quotaError(c, field, used, limit)
    }

    await next()
  }
}

export async function incrementQuota(c: Context<{ Bindings: Env }>, field: QuotaField, amount = 1): Promise<boolean> {
  const user = getCurrentUser(c)
  if (!user) return false

  const supabase = getSupabaseClient(c.env, true)

  const fieldMap: Record<QuotaField, string> = {
    daily_deep_research: 'daily_deep_research',
    daily_quick_chat: 'daily_quick_chat',
    daily_alerts_sent: 'daily_alerts_sent',
    monthly_reports: 'monthly_reports',
    watchlist_count: 'watchlist_count',
    agent_count: 'agent_count',
  }

  const columnName = fieldMap[field]

  const { error } = await supabase.rpc('increment_quota', {
    p_user_id: user.id,
    p_field: columnName,
    p_amount: amount,
  })

  if (error) {
    console.error('[Quota] Failed to increment:', error)
    const { error: updateError } = await supabase
      .from('user_quotas')
      .update({ [columnName]: amount })
      .eq('user_id', user.id)

    if (updateError) {
      console.error('[Quota] Fallback update failed:', updateError)
      return false
    }
  }

  return true
}

export const checkDeepResearchQuota = () => checkQuota({ field: 'daily_deep_research' })
export const checkQuickChatQuota = () => checkQuota({ field: 'daily_quick_chat' })
export const checkReportsQuota = () => checkQuota({ field: 'monthly_reports' })
export const checkWatchlistQuota = () => checkQuota({ field: 'watchlist_count' })
export const checkAgentQuota = () => checkQuota({ field: 'agent_count' })
