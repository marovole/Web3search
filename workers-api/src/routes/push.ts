import { Hono } from 'hono'
import type { Env } from '../types/env'
import { authMiddleware, getCurrentUser } from '../middlewares/auth'
import { getSupabaseClient } from '../lib/supabase'
import { sendPushToUser, createNotificationPayload } from '../lib/push'

const push = new Hono<{ Bindings: Env }>()

push.post('/subscribe', authMiddleware(), async (c) => {
  const user = getCurrentUser(c)
  if (!user) {
    return c.json({ error: { code: 'NOT_AUTHENTICATED', message: 'Not authenticated', status: 401 } }, 401)
  }

  const body = await c.req.json<{
    endpoint: string
    keys: {
      p256dh: string
      auth: string
    }
    userAgent?: string
  }>()

  if (!body.endpoint || !body.keys?.p256dh || !body.keys?.auth) {
    return c.json(
      { error: { code: 'INVALID_INPUT', message: 'endpoint, keys.p256dh, and keys.auth are required', status: 400 } },
      400
    )
  }

  const supabase = getSupabaseClient(c.env, true)

  const { data: existing } = await supabase
    .from('push_subscriptions')
    .select('id, user_id')
    .eq('endpoint', body.endpoint)
    .single()

  if (existing) {
    if (existing.user_id === user.id) {
      const { data, error } = await supabase
        .from('push_subscriptions')
        .update({
          p256dh: body.keys.p256dh,
          auth: body.keys.auth,
          user_agent: body.userAgent,
          is_active: true,
          failure_count: 0,
          updated_at: new Date().toISOString()
        })
        .eq('id', existing.id)
        .select()
        .single()

      if (error) {
        console.error('[Push] Failed to update subscription:', error)
        return c.json({ error: { code: 'DATABASE_ERROR', message: 'Failed to update subscription', status: 500 } }, 500)
      }

      return c.json({ subscription: data, updated: true })
    } else {
      return c.json(
        { error: { code: 'ENDPOINT_IN_USE', message: 'This endpoint is already registered to another user', status: 409 } },
        409
      )
    }
  }

  const { data, error } = await supabase
    .from('push_subscriptions')
    .insert({
      user_id: user.id,
      endpoint: body.endpoint,
      p256dh: body.keys.p256dh,
      auth: body.keys.auth,
      user_agent: body.userAgent,
      is_active: true
    })
    .select()
    .single()

  if (error) {
    console.error('[Push] Failed to create subscription:', error)
    return c.json({ error: { code: 'DATABASE_ERROR', message: 'Failed to create subscription', status: 500 } }, 500)
  }

  return c.json({ subscription: data, created: true }, 201)
})

push.delete('/unsubscribe', authMiddleware(), async (c) => {
  const user = getCurrentUser(c)
  if (!user) {
    return c.json({ error: { code: 'NOT_AUTHENTICATED', message: 'Not authenticated', status: 401 } }, 401)
  }

  const body = await c.req.json<{ endpoint: string }>()

  if (!body.endpoint) {
    return c.json({ error: { code: 'INVALID_INPUT', message: 'endpoint is required', status: 400 } }, 400)
  }

  const supabase = getSupabaseClient(c.env, true)

  const { error } = await supabase
    .from('push_subscriptions')
    .delete()
    .eq('user_id', user.id)
    .eq('endpoint', body.endpoint)

  if (error) {
    console.error('[Push] Failed to delete subscription:', error)
    return c.json({ error: { code: 'DATABASE_ERROR', message: 'Failed to delete subscription', status: 500 } }, 500)
  }

  return c.json({ success: true })
})

push.get('/subscriptions', authMiddleware(), async (c) => {
  const user = getCurrentUser(c)
  if (!user) {
    return c.json({ error: { code: 'NOT_AUTHENTICATED', message: 'Not authenticated', status: 401 } }, 401)
  }

  const supabase = getSupabaseClient(c.env)

  const { data, error, count } = await supabase
    .from('push_subscriptions')
    .select('id, endpoint, user_agent, is_active, last_used_at, created_at', { count: 'exact' })
    .eq('user_id', user.id)
    .order('created_at', { ascending: false })

  if (error) {
    console.error('[Push] Failed to fetch subscriptions:', error)
    return c.json({ error: { code: 'DATABASE_ERROR', message: 'Failed to fetch subscriptions', status: 500 } }, 500)
  }

  return c.json({ subscriptions: data, total: count })
})

push.post('/test', authMiddleware(), async (c) => {
  const user = getCurrentUser(c)
  if (!user) {
    return c.json({ error: { code: 'NOT_AUTHENTICATED', message: 'Not authenticated', status: 401 } }, 401)
  }

  const payload = createNotificationPayload(
    'system',
    '测试通知',
    '这是一条测试推送通知，用于验证您的浏览器推送功能是否正常。',
    { test: true }
  )

  const result = await sendPushToUser(c.env, user.id, payload)

  if (result.sent === 0) {
    return c.json({
      success: false,
      message: '没有找到活跃的推送订阅',
      details: result
    })
  }

  return c.json({
    success: true,
    message: `成功发送 ${result.sent} 条测试通知`,
    details: result
  })
})

push.get('/vapid-public-key', async (c) => {
  const publicKey = c.env.VAPID_PUBLIC_KEY

  if (!publicKey) {
    return c.json({ error: { code: 'NOT_CONFIGURED', message: 'VAPID not configured', status: 500 } }, 500)
  }

  return c.json({ publicKey })
})

export default push
