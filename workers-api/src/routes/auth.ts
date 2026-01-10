/**
 * Auth Routes - User authentication endpoints
 * Base path: /api/v1/auth
 */

import { Hono } from 'hono'
import type { Env } from '../types/env'
import { authMiddleware, getCurrentUser } from '../middlewares/auth'
import { getSupabaseClient } from '../lib/supabase'

const auth = new Hono<{ Bindings: Env }>()

auth.get('/me', authMiddleware(), async (c) => {
  const user = getCurrentUser(c)
  if (!user) {
    return c.json({ error: { code: 'NOT_AUTHENTICATED', message: 'Not authenticated', status: 401 } }, 401)
  }

  const supabase = getSupabaseClient(c.env)

  const { data: profile, error: profileError } = await supabase
    .from('user_profiles')
    .select('*')
    .eq('id', user.id)
    .single()

  if (profileError && profileError.code !== 'PGRST116') {
    console.error('[Auth] Failed to fetch profile:', profileError)
  }

  const { data: quota, error: quotaError } = await supabase
    .from('user_quotas')
    .select('*')
    .eq('user_id', user.id)
    .single()

  if (quotaError && quotaError.code !== 'PGRST116') {
    console.error('[Auth] Failed to fetch quota:', quotaError)
  }

  return c.json({
    user: {
      id: user.id,
      email: user.email,
      username: profile?.username || null,
      display_name: profile?.display_name || null,
      avatar_url: profile?.avatar_url || null,
      plan: profile?.plan || 'free',
      risk_preference: profile?.risk_preference || 'moderate',
      notification_settings: profile?.notification_settings || {},
      timezone: profile?.timezone || 'UTC',
      language: profile?.language || 'en',
      theme: profile?.theme || 'system',
      onboarding_completed: profile?.onboarding_completed || false,
      created_at: profile?.created_at,
    },
    quota: quota
      ? {
          watchlist: { used: quota.watchlist_count, limit: quota.watchlist_limit },
          agents: { used: quota.agent_count, limit: quota.agent_limit },
          daily: {
            alerts: { used: quota.daily_alerts_sent, limit: quota.daily_alerts_limit },
            deep_research: { used: quota.daily_deep_research, limit: quota.daily_deep_research_limit },
            quick_chat: { used: quota.daily_quick_chat, limit: quota.daily_quick_chat_limit },
          },
          monthly: {
            reports: { used: quota.monthly_reports, limit: quota.monthly_reports_limit },
          },
          resets: {
            daily: quota.daily_reset_at,
            monthly: quota.monthly_reset_at,
          },
        }
      : null,
  })
})

auth.post('/refresh', authMiddleware({ verifyWithSupabase: true }), async (c) => {
  const user = getCurrentUser(c)
  if (!user) {
    return c.json({ error: { code: 'NOT_AUTHENTICATED', message: 'Not authenticated', status: 401 } }, 401)
  }

  return c.json({
    message: 'Token is valid',
    user: { id: user.id, email: user.email },
  })
})

export default auth
