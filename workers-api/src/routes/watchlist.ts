import { Hono } from 'hono'
import type { Env } from '../types/env'
import { authMiddleware, getCurrentUser } from '../middlewares/auth'
import { checkWatchlistQuota } from '../middlewares/quota'
import { getSupabaseClient } from '../lib/supabase'

const watchlist = new Hono<{ Bindings: Env }>()

watchlist.get('/', authMiddleware(), async (c) => {
  const user = getCurrentUser(c)
  if (!user) {
    return c.json({ error: { code: 'NOT_AUTHENTICATED', message: 'Not authenticated', status: 401 } }, 401)
  }

  const supabase = getSupabaseClient(c.env)

  const { data, error } = await supabase
    .from('watchlist')
    .select('*')
    .eq('user_id', user.id)
    .order('position', { ascending: true })

  if (error) {
    console.error('[Watchlist] Failed to fetch:', error)
    return c.json({ error: { code: 'DATABASE_ERROR', message: 'Failed to fetch watchlist', status: 500 } }, 500)
  }

  return c.json({ watchlist: data })
})

watchlist.post('/', authMiddleware(), checkWatchlistQuota(), async (c) => {
  const user = getCurrentUser(c)
  if (!user) {
    return c.json({ error: { code: 'NOT_AUTHENTICATED', message: 'Not authenticated', status: 401 } }, 401)
  }

  const body = await c.req.json<{
    token_id: string
    symbol: string
    name: string
    coingecko_id?: string
    logo_url?: string
    notes?: string
    tags?: string[]
    alert_settings?: Record<string, unknown>
  }>()

  if (!body.token_id || !body.symbol || !body.name) {
    return c.json(
      { error: { code: 'INVALID_INPUT', message: 'token_id, symbol, and name are required', status: 400 } },
      400
    )
  }

  const supabase = getSupabaseClient(c.env, true)

  const { data: maxPos } = await supabase
    .from('watchlist')
    .select('position')
    .eq('user_id', user.id)
    .order('position', { ascending: false })
    .limit(1)
    .single()

  const maxPosData = maxPos as { position?: number } | null
  const nextPosition = (maxPosData?.position ?? -1) + 1

  const { data, error } = await supabase
    .from('watchlist')
    .insert({
      user_id: user.id,
      token_id: body.token_id,
      symbol: body.symbol.toUpperCase(),
      name: body.name,
      coingecko_id: body.coingecko_id,
      logo_url: body.logo_url,
      notes: body.notes,
      tags: body.tags || [],
      alert_settings: body.alert_settings || {},
      position: nextPosition,
    })
    .select()
    .single()

  if (error) {
    if (error.code === '23505') {
      return c.json({ error: { code: 'ALREADY_EXISTS', message: 'Token already in watchlist', status: 409 } }, 409)
    }
    console.error('[Watchlist] Failed to insert:', error)
    return c.json({ error: { code: 'DATABASE_ERROR', message: 'Failed to add to watchlist', status: 500 } }, 500)
  }

  return c.json({ item: data }, 201)
})

watchlist.get('/:id', authMiddleware(), async (c) => {
  const user = getCurrentUser(c)
  if (!user) {
    return c.json({ error: { code: 'NOT_AUTHENTICATED', message: 'Not authenticated', status: 401 } }, 401)
  }

  const id = c.req.param('id')
  const supabase = getSupabaseClient(c.env)

  const { data, error } = await supabase
    .from('watchlist')
    .select('*')
    .eq('id', id)
    .eq('user_id', user.id)
    .single()

  if (error || !data) {
    return c.json({ error: { code: 'NOT_FOUND', message: 'Watchlist item not found', status: 404 } }, 404)
  }

  return c.json({ item: data })
})

watchlist.patch('/:id', authMiddleware(), async (c) => {
  const user = getCurrentUser(c)
  if (!user) {
    return c.json({ error: { code: 'NOT_AUTHENTICATED', message: 'Not authenticated', status: 401 } }, 401)
  }

  const id = c.req.param('id')
  const body = await c.req.json<{
    notes?: string
    tags?: string[]
    alert_settings?: Record<string, unknown>
    position?: number
  }>()

  const allowedFields = ['notes', 'tags', 'alert_settings', 'position']
  const updates: Record<string, unknown> = {}

  for (const field of allowedFields) {
    if (body[field as keyof typeof body] !== undefined) {
      updates[field] = body[field as keyof typeof body]
    }
  }

  if (Object.keys(updates).length === 0) {
    return c.json({ error: { code: 'NO_UPDATES', message: 'No valid fields to update', status: 400 } }, 400)
  }

  const supabase = getSupabaseClient(c.env, true)

  const { data, error } = await supabase
    .from('watchlist')
    .update(updates)
    .eq('id', id)
    .eq('user_id', user.id)
    .select()
    .single()

  if (error) {
    if (error.code === 'PGRST116') {
      return c.json({ error: { code: 'NOT_FOUND', message: 'Watchlist item not found', status: 404 } }, 404)
    }
    console.error('[Watchlist] Failed to update:', error)
    return c.json({ error: { code: 'DATABASE_ERROR', message: 'Failed to update watchlist item', status: 500 } }, 500)
  }

  return c.json({ item: data })
})

watchlist.delete('/:id', authMiddleware(), async (c) => {
  const user = getCurrentUser(c)
  if (!user) {
    return c.json({ error: { code: 'NOT_AUTHENTICATED', message: 'Not authenticated', status: 401 } }, 401)
  }

  const id = c.req.param('id')
  const supabase = getSupabaseClient(c.env, true)

  const { error } = await supabase.from('watchlist').delete().eq('id', id).eq('user_id', user.id)

  if (error) {
    console.error('[Watchlist] Failed to delete:', error)
    return c.json({ error: { code: 'DATABASE_ERROR', message: 'Failed to delete watchlist item', status: 500 } }, 500)
  }

  return c.json({ success: true })
})

watchlist.post('/reorder', authMiddleware(), async (c) => {
  const user = getCurrentUser(c)
  if (!user) {
    return c.json({ error: { code: 'NOT_AUTHENTICATED', message: 'Not authenticated', status: 401 } }, 401)
  }

  const body = await c.req.json<{ items: Array<{ id: string; position: number }> }>()

  if (!body.items || !Array.isArray(body.items)) {
    return c.json({ error: { code: 'INVALID_INPUT', message: 'items array is required', status: 400 } }, 400)
  }

  const supabase = getSupabaseClient(c.env, true)

  for (const item of body.items) {
    await supabase.from('watchlist').update({ position: item.position }).eq('id', item.id).eq('user_id', user.id)
  }

  return c.json({ success: true })
})

export default watchlist
