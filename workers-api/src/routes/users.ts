/**
 * Users Routes - User profile management
 * Base path: /api/v1/users
 */

import { Hono } from 'hono'
import type { Env } from '../types/env'
import { authMiddleware, getCurrentUser } from '../middlewares/auth'
import { getSupabaseClient } from '../lib/supabase'

const users = new Hono<{ Bindings: Env }>()

users.get('/profile', authMiddleware(), async (c) => {
  const user = getCurrentUser(c)
  if (!user) {
    return c.json({ error: { code: 'NOT_AUTHENTICATED', message: 'Not authenticated', status: 401 } }, 401)
  }

  const supabase = getSupabaseClient(c.env)

  const { data: profile, error } = await supabase
    .from('user_profiles')
    .select('*')
    .eq('id', user.id)
    .single()

  if (error) {
    if (error.code === 'PGRST116') {
      return c.json({ error: { code: 'PROFILE_NOT_FOUND', message: 'Profile not found', status: 404 } }, 404)
    }
    console.error('[Users] Failed to fetch profile:', error)
    return c.json({ error: { code: 'DATABASE_ERROR', message: 'Failed to fetch profile', status: 500 } }, 500)
  }

  return c.json({ profile })
})

users.patch('/profile', authMiddleware(), async (c) => {
  const user = getCurrentUser(c)
  if (!user) {
    return c.json({ error: { code: 'NOT_AUTHENTICATED', message: 'Not authenticated', status: 401 } }, 401)
  }

  const body = await c.req.json<{
    username?: string
    display_name?: string
    avatar_url?: string
    risk_preference?: 'conservative' | 'moderate' | 'aggressive'
    notification_settings?: Record<string, boolean>
    timezone?: string
    language?: string
    theme?: 'light' | 'dark' | 'system'
    onboarding_completed?: boolean
  }>()

  const allowedFields = [
    'username',
    'display_name',
    'avatar_url',
    'risk_preference',
    'notification_settings',
    'timezone',
    'language',
    'theme',
    'onboarding_completed',
  ]

  const updates: Record<string, unknown> = {}
  for (const field of allowedFields) {
    if (body[field as keyof typeof body] !== undefined) {
      updates[field] = body[field as keyof typeof body]
    }
  }

  if (Object.keys(updates).length === 0) {
    return c.json({ error: { code: 'NO_UPDATES', message: 'No valid fields to update', status: 400 } }, 400)
  }

  if (updates.username) {
    const usernameRegex = /^[a-zA-Z0-9_]{3,30}$/
    if (!usernameRegex.test(updates.username as string)) {
      return c.json(
        {
          error: {
            code: 'INVALID_USERNAME',
            message: 'Username must be 3-30 characters, alphanumeric and underscores only',
            status: 400,
          },
        },
        400
      )
    }
  }

  if (updates.risk_preference && !['conservative', 'moderate', 'aggressive'].includes(updates.risk_preference as string)) {
    return c.json(
      {
        error: {
          code: 'INVALID_RISK_PREFERENCE',
          message: 'Risk preference must be conservative, moderate, or aggressive',
          status: 400,
        },
      },
      400
    )
  }

  if (updates.theme && !['light', 'dark', 'system'].includes(updates.theme as string)) {
    return c.json({ error: { code: 'INVALID_THEME', message: 'Theme must be light, dark, or system', status: 400 } }, 400)
  }

  const supabase = getSupabaseClient(c.env, true)

  const { data: profile, error } = await supabase
    .from('user_profiles')
    .update(updates)
    .eq('id', user.id)
    .select()
    .single()

  if (error) {
    if (error.code === '23505' && error.message.includes('username')) {
      return c.json({ error: { code: 'USERNAME_TAKEN', message: 'Username is already taken', status: 409 } }, 409)
    }
    console.error('[Users] Failed to update profile:', error)
    return c.json({ error: { code: 'DATABASE_ERROR', message: 'Failed to update profile', status: 500 } }, 500)
  }

  return c.json({ profile })
})

users.get('/quota', authMiddleware(), async (c) => {
  const user = getCurrentUser(c)
  if (!user) {
    return c.json({ error: { code: 'NOT_AUTHENTICATED', message: 'Not authenticated', status: 401 } }, 401)
  }

  const supabase = getSupabaseClient(c.env)

  const { data: quota, error } = await supabase.from('user_quotas').select('*').eq('user_id', user.id).single()

  if (error) {
    if (error.code === 'PGRST116') {
      return c.json({ error: { code: 'QUOTA_NOT_FOUND', message: 'Quota not found', status: 404 } }, 404)
    }
    console.error('[Users] Failed to fetch quota:', error)
    return c.json({ error: { code: 'DATABASE_ERROR', message: 'Failed to fetch quota', status: 500 } }, 500)
  }

  if (!quota) {
    return c.json({ error: { code: 'QUOTA_NOT_FOUND', message: 'Quota not found', status: 404 } }, 404)
  }

  const q = quota as Record<string, unknown>
  return c.json({
    quota: {
      watchlist: { used: q.watchlist_count ?? 0, limit: q.watchlist_limit ?? 10 },
      agents: { used: q.agent_count ?? 0, limit: q.agent_limit ?? 3 },
      daily: {
        alerts: { used: q.daily_alerts_sent ?? 0, limit: q.daily_alerts_limit ?? 100 },
        deep_research: { used: q.daily_deep_research ?? 0, limit: q.daily_deep_research_limit ?? 10 },
        quick_chat: { used: q.daily_quick_chat ?? 0, limit: q.daily_quick_chat_limit ?? 50 },
      },
      monthly: {
        reports: { used: q.monthly_reports ?? 0, limit: q.monthly_reports_limit ?? 30 },
      },
      resets: {
        daily: q.daily_reset_at ?? null,
        monthly: q.monthly_reset_at ?? null,
      },
    },
  })
})

export default users
