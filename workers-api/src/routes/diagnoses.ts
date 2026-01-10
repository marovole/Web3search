import { Hono } from 'hono'
import type { Env } from '../types/env'
import { authMiddleware, getCurrentUser } from '../middlewares/auth'
import { getSupabaseClient } from '../lib/supabase'

const diagnoses = new Hono<{ Bindings: Env }>()

diagnoses.get('/', authMiddleware(), async (c) => {
  const user = getCurrentUser(c)
  if (!user) {
    return c.json({ error: { code: 'NOT_AUTHENTICATED', message: 'Not authenticated', status: 401 } }, 401)
  }

  const limit = Math.min(parseInt(c.req.query('limit') || '10'), 50)
  const supabase = getSupabaseClient(c.env)

  const { data, error } = await supabase
    .from('portfolio_diagnoses')
    .select('*')
    .eq('user_id', user.id)
    .order('diagnosis_date', { ascending: false })
    .limit(limit)

  if (error) {
    console.error('[Diagnoses] Failed to fetch:', error)
    return c.json({ error: { code: 'DATABASE_ERROR', message: 'Failed to fetch diagnoses', status: 500 } }, 500)
  }

  return c.json({ diagnoses: data })
})

diagnoses.get('/latest', authMiddleware(), async (c) => {
  const user = getCurrentUser(c)
  if (!user) {
    return c.json({ error: { code: 'NOT_AUTHENTICATED', message: 'Not authenticated', status: 401 } }, 401)
  }

  const supabase = getSupabaseClient(c.env)

  const { data, error } = await supabase
    .from('portfolio_diagnoses')
    .select('*')
    .eq('user_id', user.id)
    .order('diagnosis_date', { ascending: false })
    .limit(1)
    .single()

  if (error) {
    if (error.code === 'PGRST116') {
      return c.json({ diagnosis: null })
    }
    console.error('[Diagnoses] Failed to fetch latest:', error)
    return c.json({ error: { code: 'DATABASE_ERROR', message: 'Failed to fetch diagnosis', status: 500 } }, 500)
  }

  return c.json({ diagnosis: data })
})

diagnoses.get('/:id', authMiddleware(), async (c) => {
  const user = getCurrentUser(c)
  if (!user) {
    return c.json({ error: { code: 'NOT_AUTHENTICATED', message: 'Not authenticated', status: 401 } }, 401)
  }

  const id = c.req.param('id')
  const supabase = getSupabaseClient(c.env)

  const { data, error } = await supabase
    .from('portfolio_diagnoses')
    .select('*')
    .eq('id', id)
    .eq('user_id', user.id)
    .single()

  if (error || !data) {
    return c.json({ error: { code: 'NOT_FOUND', message: 'Diagnosis not found', status: 404 } }, 404)
  }

  return c.json({ diagnosis: data })
})

diagnoses.get('/snapshots', authMiddleware(), async (c) => {
  const user = getCurrentUser(c)
  if (!user) {
    return c.json({ error: { code: 'NOT_AUTHENTICATED', message: 'Not authenticated', status: 401 } }, 401)
  }

  const days = Math.min(parseInt(c.req.query('days') || '30'), 365)
  const supabase = getSupabaseClient(c.env)

  const startDate = new Date()
  startDate.setDate(startDate.getDate() - days)

  const { data, error } = await supabase
    .from('portfolio_snapshots')
    .select('snapshot_date, total_value_usd, total_pnl_usd, total_pnl_percent, holdings_count')
    .eq('user_id', user.id)
    .gte('snapshot_date', startDate.toISOString().split('T')[0])
    .order('snapshot_date', { ascending: true })

  if (error) {
    console.error('[Diagnoses] Failed to fetch snapshots:', error)
    return c.json({ error: { code: 'DATABASE_ERROR', message: 'Failed to fetch snapshots', status: 500 } }, 500)
  }

  return c.json({ snapshots: data })
})

export default diagnoses
