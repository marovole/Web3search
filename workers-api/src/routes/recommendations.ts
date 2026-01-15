import { Hono } from 'hono'
import type { Context } from 'hono'
import { z } from 'zod'

import type { Env } from '../types/env'
import { authMiddleware, getCurrentUser } from '../middlewares/auth'
import { ErrorCodes, createErrorResponse } from '../lib/errors'
import { getSupabaseClient } from '../lib/supabase'

const app = new Hono<{ Bindings: Env }>()

const RecommendationStatusSchema = z.enum([
  'active',
  'viewed',
  'liked',
  'disliked',
  'dismissed',
  'expired',
  'all',
])

const RecommendationQuerySchema = z.object({
  status: RecommendationStatusSchema.optional().default('active'),
  limit: z.preprocess(
    (value) => (value === undefined ? undefined : Number(value)),
    z.number().int().min(1).max(50).optional().default(20)
  ),
  offset: z.preprocess(
    (value) => (value === undefined ? undefined : Number(value)),
    z.number().int().min(0).optional().default(0)
  ),
})

const RecommendationIdSchema = z.string().uuid()

const PreferencesUpdateSchema = z
  .object({
    risk_tolerance: z.enum(['conservative', 'medium', 'aggressive', 'very_aggressive']).optional(),
    investment_horizon: z.enum(['short', 'medium', 'long']).optional(),
    preferred_sectors: z.array(z.string()).optional(),
    excluded_sectors: z.array(z.string()).optional(),
    preferred_chains: z.array(z.string()).optional(),
    min_market_cap: z.enum(['any', 'micro', 'small', 'medium', 'large']).optional(),
    interest_tags: z.array(z.string()).optional(),
    notification_enabled: z.boolean().optional(),
    discovery_frequency: z.enum(['daily', 'weekly', 'biweekly']).optional(),
    max_recommendations_per_batch: z.number().int().min(1).max(50).optional(),
  })
  .strict()

const FeedbackSchema = z
  .object({
    feedback: z.enum(['like', 'dislike', 'not_interested', 'already_own', 'will_research']),
    notes: z.string().max(2000).optional(),
  })
  .strict()

const errorFromZod = (error: z.ZodError): string =>
  error.issues.map((issue) => `${issue.path.join('.')}: ${issue.message}`).join(', ')

const parseJsonBody = async <T,>(
  c: Context<{ Bindings: Env }>
): Promise<{ data?: T; error?: string }> => {
  try {
    const data = await c.req.json<T>()
    return { data }
  } catch {
    return { error: 'Invalid JSON in request body' }
  }
}

app.get('/', authMiddleware(), async (c) => {
  const user = getCurrentUser(c)
  if (!user) {
    return c.json(createErrorResponse(ErrorCodes.NOT_AUTHENTICATED, 'Not authenticated'), 401)
  }

  const parsedQuery = RecommendationQuerySchema.safeParse({
    status: c.req.query('status'),
    limit: c.req.query('limit'),
    offset: c.req.query('offset'),
  })

  if (!parsedQuery.success) {
    return c.json(
      createErrorResponse(ErrorCodes.INVALID_INPUT, errorFromZod(parsedQuery.error)),
      400
    )
  }

  const supabase = getSupabaseClient(c.env, true)
  
  const { status, limit, offset } = parsedQuery.data

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
    return c.json(createErrorResponse(ErrorCodes.DATABASE_ERROR, error.message), 500)
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
    return c.json(createErrorResponse(ErrorCodes.NOT_AUTHENTICATED, 'Not authenticated'), 401)
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
    return c.json(createErrorResponse(ErrorCodes.DATABASE_ERROR, error.message), 500)
  }

  return c.json({ recommendations: data || [] })
})

app.get('/preferences', authMiddleware(), async (c) => {
  const user = getCurrentUser(c)
  if (!user) {
    return c.json(createErrorResponse(ErrorCodes.NOT_AUTHENTICATED, 'Not authenticated'), 401)
  }

  const supabase = getSupabaseClient(c.env, true)

  const { data, error } = await supabase
    .from('user_preferences')
    .select('*')
    .eq('user_id', user.id)
    .single()

  if (error && error.code !== 'PGRST116') {
    return c.json(createErrorResponse(ErrorCodes.DATABASE_ERROR, error.message), 500)
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
    return c.json(createErrorResponse(ErrorCodes.NOT_AUTHENTICATED, 'Not authenticated'), 401)
  }

  const supabase = getSupabaseClient(c.env, true)

  const parsedBody = await parseJsonBody<unknown>(c)
  if (parsedBody.error) {
    return c.json(createErrorResponse(ErrorCodes.INVALID_JSON, parsedBody.error), 400)
  }

  const validatedBody = PreferencesUpdateSchema.safeParse(parsedBody.data)
  if (!validatedBody.success) {
    return c.json(
      createErrorResponse(ErrorCodes.INVALID_INPUT, errorFromZod(validatedBody.error)),
      400
    )
  }

  const body = Object.fromEntries(
    Object.entries(validatedBody.data).filter(([, value]) => value !== undefined)
  )

  if (Object.keys(body).length === 0) {
    return c.json(createErrorResponse(ErrorCodes.NO_UPDATES, 'No valid fields to update'), 400)
  }

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
      return c.json(createErrorResponse(ErrorCodes.DATABASE_ERROR, error.message), 500)
    }
    result = data
  } else {
    const { data, error } = await supabase
      .from('user_preferences')
      .insert({ user_id: user.id, ...body })
      .select()
      .single()
    
    if (error) {
      return c.json(createErrorResponse(ErrorCodes.DATABASE_ERROR, error.message), 500)
    }
    result = data
  }

  return c.json({ preferences: result })
})

app.get('/:id', authMiddleware(), async (c) => {
  const user = getCurrentUser(c)
  if (!user) {
    return c.json(createErrorResponse(ErrorCodes.NOT_AUTHENTICATED, 'Not authenticated'), 401)
  }

  const id = c.req.param('id')
  const parsedId = RecommendationIdSchema.safeParse(id)
  if (!parsedId.success) {
    return c.json(createErrorResponse(ErrorCodes.INVALID_INPUT, 'Invalid recommendation id'), 400)
  }
  const supabase = getSupabaseClient(c.env, true)

  const { data, error } = await supabase
    .from('recommendations')
    .select('*')
    .eq('id', id)
    .eq('user_id', user.id)
    .single()

  if (error) {
    if (error.code === 'PGRST116') {
      return c.json(createErrorResponse(ErrorCodes.NOT_FOUND, 'Recommendation not found'), 404)
    }
    return c.json(createErrorResponse(ErrorCodes.DATABASE_ERROR, error.message), 500)
  }

  const recData = data as { viewed_at?: string } | null
  if (!recData?.viewed_at) {
    await supabase
      .from('recommendations')
      .update({ viewed_at: new Date().toISOString(), status: 'viewed' })
      .eq('id', id)
      .eq('user_id', user.id)
  }

  return c.json({ recommendation: data })
})

app.patch('/:id/feedback', authMiddleware(), async (c) => {
  const user = getCurrentUser(c)
  if (!user) {
    return c.json(createErrorResponse(ErrorCodes.NOT_AUTHENTICATED, 'Not authenticated'), 401)
  }

  const id = c.req.param('id')
  const parsedId = RecommendationIdSchema.safeParse(id)
  if (!parsedId.success) {
    return c.json(createErrorResponse(ErrorCodes.INVALID_INPUT, 'Invalid recommendation id'), 400)
  }
  const supabase = getSupabaseClient(c.env, true)

  const parsedBody = await parseJsonBody<unknown>(c)
  if (parsedBody.error) {
    return c.json(createErrorResponse(ErrorCodes.INVALID_JSON, parsedBody.error), 400)
  }

  const validatedBody = FeedbackSchema.safeParse(parsedBody.data)
  if (!validatedBody.success) {
    return c.json(
      createErrorResponse(ErrorCodes.INVALID_INPUT, errorFromZod(validatedBody.error)),
      400
    )
  }

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
      user_feedback: validatedBody.data.feedback,
      feedback_at: new Date().toISOString(),
      feedback_notes: validatedBody.data.notes,
      status: feedbackToStatus[validatedBody.data.feedback] || 'viewed'
    })
    .eq('id', id)
    .eq('user_id', user.id)
    .select()
    .single()

  if (error) {
    if (error.code === 'PGRST116') {
      return c.json(createErrorResponse(ErrorCodes.NOT_FOUND, 'Recommendation not found'), 404)
    }
    return c.json(createErrorResponse(ErrorCodes.DATABASE_ERROR, error.message), 500)
  }

  return c.json({ recommendation: data })
})

app.delete('/:id', authMiddleware(), async (c) => {
  const user = getCurrentUser(c)
  if (!user) {
    return c.json(createErrorResponse(ErrorCodes.NOT_AUTHENTICATED, 'Not authenticated'), 401)
  }

  const id = c.req.param('id')
  const parsedId = RecommendationIdSchema.safeParse(id)
  if (!parsedId.success) {
    return c.json(createErrorResponse(ErrorCodes.INVALID_INPUT, 'Invalid recommendation id'), 400)
  }
  const supabase = getSupabaseClient(c.env, true)

  const { error } = await supabase
    .from('recommendations')
    .update({ status: 'dismissed' })
    .eq('id', id)
    .eq('user_id', user.id)

  if (error) {
    return c.json(createErrorResponse(ErrorCodes.DATABASE_ERROR, error.message), 500)
  }

  return c.json({ success: true })
})

export default app
