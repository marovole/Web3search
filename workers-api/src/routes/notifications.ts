import { Hono } from 'hono'
import type { Env } from '../types/env'
import { authMiddleware, getCurrentUser } from '../middlewares/auth'
import { getSupabaseClient } from '../lib/supabase'

const notifications = new Hono<{ Bindings: Env }>()

// List notifications with pagination
notifications.get('/', authMiddleware(), async (c) => {
  const user = getCurrentUser(c)
  if (!user) {
    return c.json({ error: { code: 'NOT_AUTHENTICATED', message: 'Not authenticated', status: 401 } }, 401)
  }

  const limit = Math.min(parseInt(c.req.query('limit') || '20'), 100)
  const offset = parseInt(c.req.query('offset') || '0')
  const unreadOnly = c.req.query('unread') === 'true'
  const type = c.req.query('type')

  const supabase = getSupabaseClient(c.env)

  let query = supabase
    .from('notifications')
    .select('*', { count: 'exact' })
    .eq('user_id', user.id)

  if (unreadOnly) {
    query = query.is('read_at', null)
  }

  if (type) {
    query = query.eq('type', type)
  }

  const { data, error, count } = await query
    .order('created_at', { ascending: false })
    .range(offset, offset + limit - 1)

  if (error) {
    console.error('[Notifications] Failed to fetch notifications:', error)
    return c.json({ error: { code: 'DATABASE_ERROR', message: 'Failed to fetch notifications', status: 500 } }, 500)
  }

  // Get unread count
  const { count: unreadCount } = await supabase
    .from('notifications')
    .select('id', { count: 'exact', head: true })
    .eq('user_id', user.id)
    .is('read_at', null)

  return c.json({
    notifications: data,
    total: count,
    unread_count: unreadCount ?? 0,
    limit,
    offset
  })
})

// Get single notification
notifications.get('/:id', authMiddleware(), async (c) => {
  const user = getCurrentUser(c)
  if (!user) {
    return c.json({ error: { code: 'NOT_AUTHENTICATED', message: 'Not authenticated', status: 401 } }, 401)
  }

  const id = c.req.param('id')
  const supabase = getSupabaseClient(c.env)

  const { data, error } = await supabase
    .from('notifications')
    .select('*')
    .eq('id', id)
    .eq('user_id', user.id)
    .single()

  if (error || !data) {
    return c.json({ error: { code: 'NOT_FOUND', message: 'Notification not found', status: 404 } }, 404)
  }

  return c.json({ notification: data })
})

// Mark single notification as read
notifications.patch('/:id/read', authMiddleware(), async (c) => {
  const user = getCurrentUser(c)
  if (!user) {
    return c.json({ error: { code: 'NOT_AUTHENTICATED', message: 'Not authenticated', status: 401 } }, 401)
  }

  const id = c.req.param('id')
  const supabase = getSupabaseClient(c.env, true)

  const { data, error } = await supabase
    .from('notifications')
    .update({ read_at: new Date().toISOString() })
    .eq('id', id)
    .eq('user_id', user.id)
    .is('read_at', null)
    .select()
    .single()

  if (error) {
    if (error.code === 'PGRST116') {
      return c.json({ error: { code: 'NOT_FOUND', message: 'Notification not found or already read', status: 404 } }, 404)
    }
    console.error('[Notifications] Failed to mark as read:', error)
    return c.json({ error: { code: 'DATABASE_ERROR', message: 'Failed to mark notification as read', status: 500 } }, 500)
  }

  return c.json({ notification: data })
})

// Mark all notifications as read
notifications.post('/read-all', authMiddleware(), async (c) => {
  const user = getCurrentUser(c)
  if (!user) {
    return c.json({ error: { code: 'NOT_AUTHENTICATED', message: 'Not authenticated', status: 401 } }, 401)
  }

  const supabase = getSupabaseClient(c.env, true)

  const { error, count } = await supabase
    .from('notifications')
    .update({ read_at: new Date().toISOString() })
    .eq('user_id', user.id)
    .is('read_at', null)

  if (error) {
    console.error('[Notifications] Failed to mark all as read:', error)
    return c.json({ error: { code: 'DATABASE_ERROR', message: 'Failed to mark notifications as read', status: 500 } }, 500)
  }

  return c.json({ success: true, marked_count: count ?? 0 })
})

// Dismiss (soft delete) a notification
notifications.patch('/:id/dismiss', authMiddleware(), async (c) => {
  const user = getCurrentUser(c)
  if (!user) {
    return c.json({ error: { code: 'NOT_AUTHENTICATED', message: 'Not authenticated', status: 401 } }, 401)
  }

  const id = c.req.param('id')
  const supabase = getSupabaseClient(c.env, true)

  const { data, error } = await supabase
    .from('notifications')
    .update({ dismissed_at: new Date().toISOString() })
    .eq('id', id)
    .eq('user_id', user.id)
    .select()
    .single()

  if (error) {
    if (error.code === 'PGRST116') {
      return c.json({ error: { code: 'NOT_FOUND', message: 'Notification not found', status: 404 } }, 404)
    }
    console.error('[Notifications] Failed to dismiss:', error)
    return c.json({ error: { code: 'DATABASE_ERROR', message: 'Failed to dismiss notification', status: 500 } }, 500)
  }

  return c.json({ notification: data })
})

// Delete notification permanently
notifications.delete('/:id', authMiddleware(), async (c) => {
  const user = getCurrentUser(c)
  if (!user) {
    return c.json({ error: { code: 'NOT_AUTHENTICATED', message: 'Not authenticated', status: 401 } }, 401)
  }

  const id = c.req.param('id')
  const supabase = getSupabaseClient(c.env, true)

  const { error } = await supabase
    .from('notifications')
    .delete()
    .eq('id', id)
    .eq('user_id', user.id)

  if (error) {
    console.error('[Notifications] Failed to delete notification:', error)
    return c.json({ error: { code: 'DATABASE_ERROR', message: 'Failed to delete notification', status: 500 } }, 500)
  }

  return c.json({ success: true })
})

// Delete all dismissed notifications (cleanup)
notifications.delete('/dismissed/all', authMiddleware(), async (c) => {
  const user = getCurrentUser(c)
  if (!user) {
    return c.json({ error: { code: 'NOT_AUTHENTICATED', message: 'Not authenticated', status: 401 } }, 401)
  }

  const supabase = getSupabaseClient(c.env, true)

  const { error, count } = await supabase
    .from('notifications')
    .delete()
    .eq('user_id', user.id)
    .not('dismissed_at', 'is', null)

  if (error) {
    console.error('[Notifications] Failed to delete dismissed notifications:', error)
    return c.json({ error: { code: 'DATABASE_ERROR', message: 'Failed to delete notifications', status: 500 } }, 500)
  }

  return c.json({ success: true, deleted_count: count ?? 0 })
})

export default notifications
