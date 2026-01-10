import { Hono } from 'hono'
import type { Env } from '../types/env'
import { authMiddleware, getCurrentUser } from '../middlewares/auth'
import { getSupabaseClient } from '../lib/supabase'

const app = new Hono<{ Bindings: Env }>()

app.get('/', authMiddleware(), async (c) => {
  const user = getCurrentUser(c)
  if (!user) {
    return c.json({ error: { code: 'NOT_AUTHENTICATED', message: 'Not authenticated', status: 401 } }, 401)
  }

  const supabase = getSupabaseClient(c.env, true)
  
  const status = c.req.query('status') || 'active'
  const limit = Math.min(parseInt(c.req.query('limit') || '20'), 50)
  const offset = parseInt(c.req.query('offset') || '0')

  let query = supabase
    .from('recommendations')
    .select('*', { count: 'exact' })
    .eq('user_id', user.id)
    .order('created_at', { ascending: false })
    .range(offset, offset + limit - 1)

  if (status !== 'all') {
    query = query.eq('status', status)
  }

  const { data, error, count } = await query

  if (error) {
    return c.json({ error: { code: 'DB_ERROR', message: error.message, status: 500 } }, 500)
  }

  return c.json({
    recommendations: data || [],
    total: count || 0,
    limit,
    offset
  })
})

app.get('/latest', authMiddleware(), async (c) => {
  const user = getCurrentUser(c)
  if (!user) {
    return c.json({ error: { code: 'NOT_AUTHENTICATED', message: 'Not authenticated', status: 401 } }, 401)
  }

  const supabase = getSupabaseClient(c.env, true)

  const { data, error } = await supabase
    .from('recommendations')
    .select('*')
    .eq('user_id', user.id)
    .eq('status', 'active')
    .order('created_at', { ascending: false })
    .limit(10)

  if (error) {
    return c.json({ error: { code: 'DB_ERROR', message: error.message, status: 500 } }, 500)
  }

  return c.json({ recommendations: data || [] })
})

app.get('/preferences', authMiddleware(), async (c) => {
  const user = getCurrentUser(c)
  if (!user) {
    return c.json({ error: { code: 'NOT_AUTHENTICATED', message: 'Not authenticated', status: 401 } }, 401)
  }

  const supabase = getSupabaseClient(c.env, true)

  const { data, error } = await supabase
    .from('user_preferences')
    .select('*')
    .eq('user_id', user.id)
    .single()

  if (error && error.code !== 'PGRST116') {
    return c.json({ error: { code: 'DB_ERROR', message: error.message, status: 500 } }, 500)
  }

  const defaultPreferences = {
    user_id: user.id,
    risk_tolerance: 'medium',
    investment_horizon: 'medium',
    preferred_sectors: [],
    excluded_sectors: [],
    preferred_chains: [],
    min_market_cap: 'any',
    interest_tags: [],
    notification_enabled: true,
    discovery_frequency: 'weekly',
    max_recommendations_per_batch: 5
  }

  return c.json({ preferences: data || defaultPreferences })
})

app.put('/preferences', authMiddleware(), async (c) => {
  const user = getCurrentUser(c)
  if (!user) {
    return c.json({ error: { code: 'NOT_AUTHENTICATED', message: 'Not authenticated', status: 401 } }, 401)
  }

  const supabase = getSupabaseClient(c.env, true)

  const body = await c.req.json<{
    risk_tolerance?: string
    investment_horizon?: string
    preferred_sectors?: string[]
    excluded_sectors?: string[]
    preferred_chains?: string[]
    min_market_cap?: string
    interest_tags?: string[]
    notification_enabled?: boolean
    discovery_frequency?: string
    max_recommendations_per_batch?: number
  }>()

  const { data: existing } = await supabase
    .from('user_preferences')
    .select('id')
    .eq('user_id', user.id)
    .single()

  let result
  if (existing) {
    const { data, error } = await supabase
      .from('user_preferences')
      .update(body)
      .eq('user_id', user.id)
      .select()
      .single()
    
    if (error) {
      return c.json({ error: { code: 'DB_ERROR', message: error.message, status: 500 } }, 500)
    }
    result = data
  } else {
    const { data, error } = await supabase
      .from('user_preferences')
      .insert({ user_id: user.id, ...body })
      .select()
      .single()
    
    if (error) {
      return c.json({ error: { code: 'DB_ERROR', message: error.message, status: 500 } }, 500)
    }
    result = data
  }

  return c.json({ preferences: result })
})

app.get('/:id', authMiddleware(), async (c) => {
  const user = getCurrentUser(c)
  if (!user) {
    return c.json({ error: { code: 'NOT_AUTHENTICATED', message: 'Not authenticated', status: 401 } }, 401)
  }

  const id = c.req.param('id')
  const supabase = getSupabaseClient(c.env, true)

  const { data, error } = await supabase
    .from('recommendations')
    .select('*')
    .eq('id', id)
    .eq('user_id', user.id)
    .single()

  if (error) {
    if (error.code === 'PGRST116') {
      return c.json({ error: { code: 'NOT_FOUND', message: 'Recommendation not found', status: 404 } }, 404)
    }
    return c.json({ error: { code: 'DB_ERROR', message: error.message, status: 500 } }, 500)
  }

  if (!data.viewed_at) {
    await supabase
      .from('recommendations')
      .update({ viewed_at: new Date().toISOString(), status: 'viewed' })
      .eq('id', id)
  }

  return c.json({ recommendation: data })
})

app.patch('/:id/feedback', authMiddleware(), async (c) => {
  const user = getCurrentUser(c)
  if (!user) {
    return c.json({ error: { code: 'NOT_AUTHENTICATED', message: 'Not authenticated', status: 401 } }, 401)
  }

  const id = c.req.param('id')
  const supabase = getSupabaseClient(c.env, true)

  const body = await c.req.json<{
    feedback: 'like' | 'dislike' | 'not_interested' | 'already_own' | 'will_research'
    notes?: string
  }>()

  const feedbackToStatus: Record<string, string> = {
    like: 'liked',
    dislike: 'disliked',
    not_interested: 'dismissed',
    already_own: 'dismissed',
    will_research: 'viewed'
  }

  const { data, error } = await supabase
    .from('recommendations')
    .update({
      user_feedback: body.feedback,
      feedback_at: new Date().toISOString(),
      feedback_notes: body.notes,
      status: feedbackToStatus[body.feedback] || 'viewed'
    })
    .eq('id', id)
    .eq('user_id', user.id)
    .select()
    .single()

  if (error) {
    if (error.code === 'PGRST116') {
      return c.json({ error: { code: 'NOT_FOUND', message: 'Recommendation not found', status: 404 } }, 404)
    }
    return c.json({ error: { code: 'DB_ERROR', message: error.message, status: 500 } }, 500)
  }

  return c.json({ recommendation: data })
})

app.delete('/:id', authMiddleware(), async (c) => {
  const user = getCurrentUser(c)
  if (!user) {
    return c.json({ error: { code: 'NOT_AUTHENTICATED', message: 'Not authenticated', status: 401 } }, 401)
  }

  const id = c.req.param('id')
  const supabase = getSupabaseClient(c.env, true)

  const { error } = await supabase
    .from('recommendations')
    .update({ status: 'dismissed' })
    .eq('id', id)
    .eq('user_id', user.id)

  if (error) {
    return c.json({ error: { code: 'DB_ERROR', message: error.message, status: 500 } }, 500)
  }

  return c.json({ success: true })
})

export default app
