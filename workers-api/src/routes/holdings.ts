import { Hono } from 'hono'
import type { Env } from '../types/env'
import { authMiddleware, getCurrentUser } from '../middlewares/auth'
import { getSupabaseClient } from '../lib/supabase'

const holdings = new Hono<{ Bindings: Env }>()

holdings.get('/', authMiddleware(), async (c) => {
  const user = getCurrentUser(c)
  if (!user) {
    return c.json({ error: { code: 'NOT_AUTHENTICATED', message: 'Not authenticated', status: 401 } }, 401)
  }

  const supabase = getSupabaseClient(c.env)

  const { data, error } = await supabase
    .from('holdings')
    .select('*')
    .eq('user_id', user.id)
    .order('created_at', { ascending: false })

  if (error) {
    console.error('[Holdings] Failed to fetch:', error)
    return c.json({ error: { code: 'DATABASE_ERROR', message: 'Failed to fetch holdings', status: 500 } }, 500)
  }

  return c.json({ holdings: data })
})

holdings.post('/', authMiddleware(), async (c) => {
  const user = getCurrentUser(c)
  if (!user) {
    return c.json({ error: { code: 'NOT_AUTHENTICATED', message: 'Not authenticated', status: 401 } }, 401)
  }

  const body = await c.req.json<{
    token_id: string
    symbol: string
    name: string
    quantity: number
    coingecko_id?: string
    logo_url?: string
    avg_buy_price?: number
    total_cost_basis?: number
    notes?: string
    tags?: string[]
    acquisition_date?: string
    is_staked?: boolean
    staking_platform?: string
    staking_apy?: number
  }>()

  if (!body.token_id || !body.symbol || !body.name) {
    return c.json(
      { error: { code: 'INVALID_INPUT', message: 'token_id, symbol, and name are required', status: 400 } },
      400
    )
  }

  if (body.quantity === undefined || body.quantity < 0) {
    return c.json(
      { error: { code: 'INVALID_INPUT', message: 'quantity must be a non-negative number', status: 400 } },
      400
    )
  }

  const supabase = getSupabaseClient(c.env, true)

  const { data, error } = await supabase
    .from('holdings')
    .insert({
      user_id: user.id,
      token_id: body.token_id,
      symbol: body.symbol.toUpperCase(),
      name: body.name,
      quantity: body.quantity,
      coingecko_id: body.coingecko_id,
      logo_url: body.logo_url,
      avg_buy_price: body.avg_buy_price,
      total_cost_basis: body.total_cost_basis,
      notes: body.notes,
      tags: body.tags || [],
      acquisition_date: body.acquisition_date,
      is_staked: body.is_staked || false,
      staking_platform: body.staking_platform,
      staking_apy: body.staking_apy,
    })
    .select()
    .single()

  if (error) {
    if (error.code === '23505') {
      return c.json({ error: { code: 'ALREADY_EXISTS', message: 'Token already in holdings', status: 409 } }, 409)
    }
    console.error('[Holdings] Failed to insert:', error)
    return c.json({ error: { code: 'DATABASE_ERROR', message: 'Failed to add holding', status: 500 } }, 500)
  }

  return c.json({ holding: data }, 201)
})

holdings.get('/:id', authMiddleware(), async (c) => {
  const user = getCurrentUser(c)
  if (!user) {
    return c.json({ error: { code: 'NOT_AUTHENTICATED', message: 'Not authenticated', status: 401 } }, 401)
  }

  const id = c.req.param('id')
  const supabase = getSupabaseClient(c.env)

  const { data, error } = await supabase
    .from('holdings')
    .select('*')
    .eq('id', id)
    .eq('user_id', user.id)
    .single()

  if (error || !data) {
    return c.json({ error: { code: 'NOT_FOUND', message: 'Holding not found', status: 404 } }, 404)
  }

  return c.json({ holding: data })
})

holdings.patch('/:id', authMiddleware(), async (c) => {
  const user = getCurrentUser(c)
  if (!user) {
    return c.json({ error: { code: 'NOT_AUTHENTICATED', message: 'Not authenticated', status: 401 } }, 401)
  }

  const id = c.req.param('id')
  const body = await c.req.json<{
    quantity?: number
    avg_buy_price?: number
    total_cost_basis?: number
    notes?: string
    tags?: string[]
    acquisition_date?: string
    is_staked?: boolean
    staking_platform?: string
    staking_apy?: number
  }>()

  const allowedFields = [
    'quantity', 'avg_buy_price', 'total_cost_basis', 'notes', 'tags',
    'acquisition_date', 'is_staked', 'staking_platform', 'staking_apy'
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

  const supabase = getSupabaseClient(c.env, true)

  const { data, error } = await supabase
    .from('holdings')
    .update(updates)
    .eq('id', id)
    .eq('user_id', user.id)
    .select()
    .single()

  if (error || !data) {
    console.error('[Holdings] Failed to update:', error)
    return c.json({ error: { code: 'NOT_FOUND', message: 'Holding not found or update failed', status: 404 } }, 404)
  }

  return c.json({ holding: data })
})

holdings.delete('/:id', authMiddleware(), async (c) => {
  const user = getCurrentUser(c)
  if (!user) {
    return c.json({ error: { code: 'NOT_AUTHENTICATED', message: 'Not authenticated', status: 401 } }, 401)
  }

  const id = c.req.param('id')
  const supabase = getSupabaseClient(c.env, true)

  const { error } = await supabase
    .from('holdings')
    .delete()
    .eq('id', id)
    .eq('user_id', user.id)

  if (error) {
    console.error('[Holdings] Failed to delete:', error)
    return c.json({ error: { code: 'DATABASE_ERROR', message: 'Failed to delete holding', status: 500 } }, 500)
  }

  return c.json({ success: true })
})

holdings.get('/summary', authMiddleware(), async (c) => {
  const user = getCurrentUser(c)
  if (!user) {
    return c.json({ error: { code: 'NOT_AUTHENTICATED', message: 'Not authenticated', status: 401 } }, 401)
  }

  const supabase = getSupabaseClient(c.env)

  const { data: holdingsData, error } = await supabase
    .from('holdings')
    .select('symbol, name, quantity, coingecko_id')
    .eq('user_id', user.id)

  if (error) {
    console.error('[Holdings] Failed to fetch summary:', error)
    return c.json({ error: { code: 'DATABASE_ERROR', message: 'Failed to fetch holdings', status: 500 } }, 500)
  }

  const coingeckoIds = (holdingsData as unknown as Array<{ coingecko_id?: string }>)
    ?.filter(h => h.coingecko_id)
    .map(h => h.coingecko_id as string)
    .join(',')

  let prices: Record<string, { usd: number; usd_24h_change?: number }> = {}
  
  if (coingeckoIds) {
    try {
      const priceRes = await fetch(
        `https://api.coingecko.com/api/v3/simple/price?ids=${coingeckoIds}&vs_currencies=usd&include_24hr_change=true`
      )
      if (priceRes.ok) {
        prices = await priceRes.json()
      }
    } catch (priceError) {
      console.error('[Holdings] Failed to fetch prices:', priceError)
    }
  }

  let totalValue = 0
  const holdingsTyped = holdingsData as unknown as Array<{ coingecko_id?: string; symbol: string; name: string; quantity: string }> | null
  const holdingsWithValue = holdingsTyped?.map(h => {
    const price = h.coingecko_id ? prices[h.coingecko_id]?.usd : undefined
    const value = price ? Number(h.quantity) * price : undefined
    if (value) totalValue += value
    
    return {
      symbol: h.symbol,
      name: h.name,
      quantity: Number(h.quantity),
      price_usd: price,
      value_usd: value,
      change_24h: h.coingecko_id ? prices[h.coingecko_id]?.usd_24h_change : undefined
    }
  }) || []

  return c.json({
    total_value_usd: totalValue,
    holdings_count: holdingsData?.length || 0,
    holdings: holdingsWithValue.sort((a, b) => (b.value_usd || 0) - (a.value_usd || 0))
  })
})

export default holdings
