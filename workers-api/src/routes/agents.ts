import { Hono } from 'hono'
import type { Env } from '../types/env'
import { authMiddleware, getCurrentUser } from '../middlewares/auth'
import { checkAgentQuota } from '../middlewares/quota'
import { getSupabaseClient } from '../lib/supabase'

const agents = new Hono<{ Bindings: Env }>()

agents.get('/tasks', authMiddleware(), async (c) => {
  const user = getCurrentUser(c)
  if (!user) {
    return c.json({ error: { code: 'NOT_AUTHENTICATED', message: 'Not authenticated', status: 401 } }, 401)
  }

  const status = c.req.query('status')
  const type = c.req.query('type')
  const limit = parseInt(c.req.query('limit') || '50')
  const offset = parseInt(c.req.query('offset') || '0')

  const supabase = getSupabaseClient(c.env)

  let query = supabase.from('agent_tasks').select('*', { count: 'exact' }).eq('user_id', user.id)

  if (status) {
    query = query.eq('status', status)
  }
  if (type) {
    query = query.eq('type', type)
  }

  const { data, error, count } = await query
    .order('created_at', { ascending: false })
    .range(offset, offset + limit - 1)

  if (error) {
    console.error('[Agents] Failed to fetch tasks:', error)
    return c.json({ error: { code: 'DATABASE_ERROR', message: 'Failed to fetch tasks', status: 500 } }, 500)
  }

  return c.json({ tasks: data, total: count, limit, offset })
})

agents.post('/tasks', authMiddleware(), checkAgentQuota(), async (c) => {
  const user = getCurrentUser(c)
  if (!user) {
    return c.json({ error: { code: 'NOT_AUTHENTICATED', message: 'Not authenticated', status: 401 } }, 401)
  }

  const body = await c.req.json<{
    name: string
    description?: string
    type: 'price_alert' | 'risk_monitor' | 'news_brief' | 'portfolio_health' | 'opportunity_finder' | 'custom'
    config: Record<string, unknown>
    schedule?: string
  }>()

  if (!body.name || !body.type || !body.config) {
    return c.json(
      { error: { code: 'INVALID_INPUT', message: 'name, type, and config are required', status: 400 } },
      400
    )
  }

  const validTypes = ['price_alert', 'risk_monitor', 'news_brief', 'portfolio_health', 'opportunity_finder', 'custom']
  if (!validTypes.includes(body.type)) {
    return c.json({ error: { code: 'INVALID_TYPE', message: `type must be one of: ${validTypes.join(', ')}`, status: 400 } }, 400)
  }

  const supabase = getSupabaseClient(c.env, true)

  const nextRunAt = body.schedule ? calculateNextRun(body.schedule) : null

  const { data, error } = await supabase
    .from('agent_tasks')
    .insert({
      user_id: user.id,
      name: body.name,
      description: body.description,
      type: body.type,
      config: body.config,
      schedule: body.schedule,
      next_run_at: nextRunAt,
      status: 'active',
    })
    .select()
    .single()

  if (error) {
    console.error('[Agents] Failed to create task:', error)
    return c.json({ error: { code: 'DATABASE_ERROR', message: 'Failed to create task', status: 500 } }, 500)
  }

  return c.json({ task: data }, 201)
})

agents.get('/tasks/:id', authMiddleware(), async (c) => {
  const user = getCurrentUser(c)
  if (!user) {
    return c.json({ error: { code: 'NOT_AUTHENTICATED', message: 'Not authenticated', status: 401 } }, 401)
  }

  const id = c.req.param('id')
  const supabase = getSupabaseClient(c.env)

  const { data, error } = await supabase.from('agent_tasks').select('*').eq('id', id).eq('user_id', user.id).single()

  if (error || !data) {
    return c.json({ error: { code: 'NOT_FOUND', message: 'Task not found', status: 404 } }, 404)
  }

  return c.json({ task: data })
})

agents.patch('/tasks/:id', authMiddleware(), async (c) => {
  const user = getCurrentUser(c)
  if (!user) {
    return c.json({ error: { code: 'NOT_AUTHENTICATED', message: 'Not authenticated', status: 401 } }, 401)
  }

  const id = c.req.param('id')
  const body = await c.req.json<{
    name?: string
    description?: string
    config?: Record<string, unknown>
    schedule?: string
    status?: 'active' | 'paused' | 'completed' | 'cancelled'
  }>()

  const allowedFields = ['name', 'description', 'config', 'schedule', 'status']
  const updates: Record<string, unknown> = {}

  for (const field of allowedFields) {
    if (body[field as keyof typeof body] !== undefined) {
      updates[field] = body[field as keyof typeof body]
    }
  }

  if (updates.schedule) {
    updates.next_run_at = calculateNextRun(updates.schedule as string)
  }

  if (Object.keys(updates).length === 0) {
    return c.json({ error: { code: 'NO_UPDATES', message: 'No valid fields to update', status: 400 } }, 400)
  }

  const supabase = getSupabaseClient(c.env, true)

  const { data, error } = await supabase
    .from('agent_tasks')
    .update(updates)
    .eq('id', id)
    .eq('user_id', user.id)
    .select()
    .single()

  if (error) {
    if (error.code === 'PGRST116') {
      return c.json({ error: { code: 'NOT_FOUND', message: 'Task not found', status: 404 } }, 404)
    }
    console.error('[Agents] Failed to update task:', error)
    return c.json({ error: { code: 'DATABASE_ERROR', message: 'Failed to update task', status: 500 } }, 500)
  }

  return c.json({ task: data })
})

agents.delete('/tasks/:id', authMiddleware(), async (c) => {
  const user = getCurrentUser(c)
  if (!user) {
    return c.json({ error: { code: 'NOT_AUTHENTICATED', message: 'Not authenticated', status: 401 } }, 401)
  }

  const id = c.req.param('id')
  const supabase = getSupabaseClient(c.env, true)

  const { error } = await supabase.from('agent_tasks').delete().eq('id', id).eq('user_id', user.id)

  if (error) {
    console.error('[Agents] Failed to delete task:', error)
    return c.json({ error: { code: 'DATABASE_ERROR', message: 'Failed to delete task', status: 500 } }, 500)
  }

  return c.json({ success: true })
})

agents.post('/tasks/:id/pause', authMiddleware(), async (c) => {
  const user = getCurrentUser(c)
  if (!user) {
    return c.json({ error: { code: 'NOT_AUTHENTICATED', message: 'Not authenticated', status: 401 } }, 401)
  }

  const id = c.req.param('id')
  const supabase = getSupabaseClient(c.env, true)

  const { data, error } = await supabase
    .from('agent_tasks')
    .update({ status: 'paused' })
    .eq('id', id)
    .eq('user_id', user.id)
    .eq('status', 'active')
    .select()
    .single()

  if (error || !data) {
    return c.json({ error: { code: 'NOT_FOUND', message: 'Active task not found', status: 404 } }, 404)
  }

  return c.json({ task: data })
})

agents.post('/tasks/:id/resume', authMiddleware(), async (c) => {
  const user = getCurrentUser(c)
  if (!user) {
    return c.json({ error: { code: 'NOT_AUTHENTICATED', message: 'Not authenticated', status: 401 } }, 401)
  }

  const id = c.req.param('id')
  const supabase = getSupabaseClient(c.env, true)

  const { data: task } = await supabase.from('agent_tasks').select('schedule').eq('id', id).eq('user_id', user.id).single()

  const nextRunAt = task?.schedule ? calculateNextRun(task.schedule) : null

  const { data, error } = await supabase
    .from('agent_tasks')
    .update({ status: 'active', next_run_at: nextRunAt })
    .eq('id', id)
    .eq('user_id', user.id)
    .eq('status', 'paused')
    .select()
    .single()

  if (error || !data) {
    return c.json({ error: { code: 'NOT_FOUND', message: 'Paused task not found', status: 404 } }, 404)
  }

  return c.json({ task: data })
})

agents.get('/tasks/:id/runs', authMiddleware(), async (c) => {
  const user = getCurrentUser(c)
  if (!user) {
    return c.json({ error: { code: 'NOT_AUTHENTICATED', message: 'Not authenticated', status: 401 } }, 401)
  }

  const id = c.req.param('id')
  const limit = parseInt(c.req.query('limit') || '20')
  const offset = parseInt(c.req.query('offset') || '0')

  const supabase = getSupabaseClient(c.env)

  const { data: task } = await supabase.from('agent_tasks').select('id').eq('id', id).eq('user_id', user.id).single()

  if (!task) {
    return c.json({ error: { code: 'NOT_FOUND', message: 'Task not found', status: 404 } }, 404)
  }

  const { data, error, count } = await supabase
    .from('agent_runs')
    .select('*', { count: 'exact' })
    .eq('task_id', id)
    .order('started_at', { ascending: false })
    .range(offset, offset + limit - 1)

  if (error) {
    console.error('[Agents] Failed to fetch runs:', error)
    return c.json({ error: { code: 'DATABASE_ERROR', message: 'Failed to fetch runs', status: 500 } }, 500)
  }

  return c.json({ runs: data, total: count, limit, offset })
})

function calculateNextRun(schedule: string): string | null {
  const now = new Date()

  if (schedule === 'hourly') {
    now.setHours(now.getHours() + 1, 0, 0, 0)
  } else if (schedule === 'daily') {
    now.setDate(now.getDate() + 1)
    now.setHours(9, 0, 0, 0)
  } else if (schedule === 'weekly') {
    now.setDate(now.getDate() + 7)
    now.setHours(9, 0, 0, 0)
  } else if (schedule.startsWith('every_')) {
    const minutes = parseInt(schedule.replace('every_', '').replace('m', ''))
    if (!isNaN(minutes)) {
      now.setMinutes(now.getMinutes() + minutes, 0, 0)
    }
  } else {
    return null
  }

  return now.toISOString()
}

export default agents
