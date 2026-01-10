/**
 * Web Push Notification Service for Cloudflare Workers
 * Uses Web Crypto API for VAPID authentication
 */

import type { Env } from '../types/env'
import { getSupabaseClient } from './supabase'

export interface PushSubscription {
  endpoint: string
  keys: {
    p256dh: string
    auth: string
  }
}

export interface PushPayload {
  title: string
  body: string
  icon?: string
  badge?: string
  tag?: string
  data?: Record<string, unknown>
  actions?: Array<{
    action: string
    title: string
    icon?: string
  }>
}

interface PushSubscriptionRecord {
  id: string
  user_id: string
  endpoint: string
  p256dh: string
  auth: string
  is_active: boolean
}

function base64UrlEncode(buffer: ArrayBuffer | Uint8Array): string {
  const bytes = buffer instanceof Uint8Array ? buffer : new Uint8Array(buffer)
  let binary = ''
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i])
  }
  return btoa(binary)
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/, '')
}

function base64UrlDecode(str: string): Uint8Array {
  str = str.replace(/-/g, '+').replace(/_/g, '/')
  while (str.length % 4) {
    str += '='
  }
  const binary = atob(str)
  const bytes = new Uint8Array(binary.length)
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i)
  }
  return bytes
}

async function generateVapidHeaders(
  audience: string,
  subject: string,
  publicKey: string,
  privateKey: string
): Promise<{ authorization: string; cryptoKey: string }> {
  const header = { typ: 'JWT', alg: 'ES256' }
  const now = Math.floor(Date.now() / 1000)
  const payload = {
    aud: audience,
    exp: now + 12 * 60 * 60,
    sub: subject
  }

  const headerB64 = base64UrlEncode(new TextEncoder().encode(JSON.stringify(header)))
  const payloadB64 = base64UrlEncode(new TextEncoder().encode(JSON.stringify(payload)))
  const unsignedToken = `${headerB64}.${payloadB64}`

  const privateKeyBytes = base64UrlDecode(privateKey)
  const cryptoKey = await crypto.subtle.importKey(
    'pkcs8',
    privateKeyBytes,
    { name: 'ECDSA', namedCurve: 'P-256' },
    false,
    ['sign']
  )

  const signature = await crypto.subtle.sign(
    { name: 'ECDSA', hash: 'SHA-256' },
    cryptoKey,
    new TextEncoder().encode(unsignedToken)
  )

  const signatureB64 = base64UrlEncode(signature)
  const jwt = `${unsignedToken}.${signatureB64}`

  return {
    authorization: `vapid t=${jwt}, k=${publicKey}`,
    cryptoKey: publicKey
  }
}

export async function sendPushNotification(
  env: Env,
  subscription: PushSubscription,
  payload: PushPayload
): Promise<{ success: boolean; error?: string }> {
  try {
    const vapidPublicKey = env.VAPID_PUBLIC_KEY
    const vapidPrivateKey = env.VAPID_PRIVATE_KEY
    const vapidSubject = env.VAPID_SUBJECT || 'mailto:admin@web3search.app'

    if (!vapidPublicKey || !vapidPrivateKey) {
      return { success: false, error: 'VAPID keys not configured' }
    }

    const url = new URL(subscription.endpoint)
    const audience = `${url.protocol}//${url.host}`

    const { authorization, cryptoKey } = await generateVapidHeaders(
      audience,
      vapidSubject,
      vapidPublicKey,
      vapidPrivateKey
    )

    const payloadString = JSON.stringify(payload)

    const response = await fetch(subscription.endpoint, {
      method: 'POST',
      headers: {
        'Authorization': authorization,
        'Crypto-Key': `p256ecdsa=${cryptoKey}`,
        'Content-Type': 'application/json',
        'Content-Encoding': 'aes128gcm',
        'TTL': '86400'
      },
      body: payloadString
    })

    if (response.status === 201 || response.status === 200) {
      return { success: true }
    }

    if (response.status === 410 || response.status === 404) {
      return { success: false, error: 'subscription_expired' }
    }

    const errorText = await response.text()
    return { success: false, error: `Push failed: ${response.status} - ${errorText}` }
  } catch (error) {
    console.error('[Push] Send failed:', error)
    return { success: false, error: error instanceof Error ? error.message : 'Unknown error' }
  }
}

export async function sendPushToUser(
  env: Env,
  userId: string,
  payload: PushPayload
): Promise<{ sent: number; failed: number; expired: string[] }> {
  const supabase = getSupabaseClient(env, true)
  
  const { data: subscriptions, error } = await supabase
    .from('push_subscriptions')
    .select('id, endpoint, p256dh, auth')
    .eq('user_id', userId)
    .eq('is_active', true)

  if (error || !subscriptions || subscriptions.length === 0) {
    return { sent: 0, failed: 0, expired: [] }
  }

  let sent = 0
  let failed = 0
  const expired: string[] = []

  for (const sub of subscriptions as PushSubscriptionRecord[]) {
    const result = await sendPushNotification(env, {
      endpoint: sub.endpoint,
      keys: { p256dh: sub.p256dh, auth: sub.auth }
    }, payload)

    if (result.success) {
      sent++
      await supabase
        .from('push_subscriptions')
        .update({ last_used_at: new Date().toISOString(), failure_count: 0 })
        .eq('id', sub.id)
    } else {
      failed++
      
      if (result.error === 'subscription_expired') {
        expired.push(sub.id)
        await supabase
          .from('push_subscriptions')
          .update({ is_active: false })
          .eq('id', sub.id)
      } else {
        await supabase
          .from('push_subscriptions')
          .update({ failure_count: (sub as PushSubscriptionRecord & { failure_count?: number }).failure_count || 0 + 1 })
          .eq('id', sub.id)
      }
    }
  }

  return { sent, failed, expired }
}

export async function sendPushToAllUsers(
  env: Env,
  userIds: string[],
  payload: PushPayload
): Promise<{ totalSent: number; totalFailed: number }> {
  let totalSent = 0
  let totalFailed = 0

  for (const userId of userIds) {
    const result = await sendPushToUser(env, userId, payload)
    totalSent += result.sent
    totalFailed += result.failed
  }

  return { totalSent, totalFailed }
}

export function createNotificationPayload(
  type: 'price_alert' | 'risk_alert' | 'news_brief' | 'portfolio_update' | 'recommendation' | 'system',
  title: string,
  body: string,
  data?: Record<string, unknown>
): PushPayload {
  const icons: Record<string, string> = {
    price_alert: '/icons/price-alert.png',
    risk_alert: '/icons/risk-alert.png',
    news_brief: '/icons/news.png',
    portfolio_update: '/icons/portfolio.png',
    recommendation: '/icons/recommendation.png',
    system: '/icons/system.png'
  }

  return {
    title,
    body,
    icon: icons[type] || '/icons/default.png',
    badge: '/icons/badge.png',
    tag: type,
    data: {
      type,
      timestamp: Date.now(),
      ...data
    },
    actions: type === 'price_alert' ? [
      { action: 'view', title: '查看详情' },
      { action: 'dismiss', title: '忽略' }
    ] : undefined
  }
}
