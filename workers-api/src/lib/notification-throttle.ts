/**
 * Notification Throttle
 * Prevents notification spam by implementing rate limiting and merging
 */

import type { Env } from '../types/env'
import { getSupabaseClient } from './supabase'

export interface ThrottleConfig {
  // Minimum interval between notifications of same type (in seconds)
  minInterval: number
  // Maximum notifications per hour for same type
  maxPerHour: number
  // Whether to merge similar notifications
  enableMerging: boolean
  // Time window for merging (in seconds)
  mergeWindow: number
}

export const DEFAULT_THROTTLE_CONFIG: Record<string, ThrottleConfig> = {
  price_alert: {
    minInterval: 60, // 1 minute between same alert
    maxPerHour: 10,
    enableMerging: false,
    mergeWindow: 0,
  },
  risk_monitor: {
    minInterval: 3600, // 1 hour between same risk alert
    maxPerHour: 3,
    enableMerging: true,
    mergeWindow: 1800, // Merge within 30 minutes
  },
  news_brief: {
    minInterval: 3600, // 1 hour between news briefs
    maxPerHour: 2,
    enableMerging: true,
    mergeWindow: 3600,
  },
  portfolio_health: {
    minInterval: 86400, // 1 day between portfolio health
    maxPerHour: 1,
    enableMerging: false,
    mergeWindow: 0,
  },
  recommendation: {
    minInterval: 86400, // 1 day between recommendations
    maxPerHour: 1,
    enableMerging: true,
    mergeWindow: 86400,
  },
  default: {
    minInterval: 300, // 5 minutes
    maxPerHour: 20,
    enableMerging: false,
    mergeWindow: 0,
  },
}

export interface ThrottleResult {
  allowed: boolean
  reason?: string
  shouldMerge?: boolean
  mergeWithId?: string
}

/**
 * Check if a notification should be throttled
 */
export async function shouldThrottle(
  env: Env,
  userId: string,
  notificationType: string,
  taskId?: string
): Promise<ThrottleResult> {
  const config = DEFAULT_THROTTLE_CONFIG[notificationType] || DEFAULT_THROTTLE_CONFIG.default
  const supabase = getSupabaseClient(env, true)

  try {
    // Get recent notifications of same type
    const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000).toISOString()
    
    const { data: recentNotifications, error } = await supabase
      .from('notifications')
      .select('id, created_at, data')
      .eq('user_id', userId)
      .eq('type', notificationType)
      .gte('created_at', oneHourAgo)
      .order('created_at', { ascending: false })

    if (error) {
      console.error('[Throttle] Failed to fetch recent notifications:', error)
      // Allow on error to avoid blocking legitimate notifications
      return { allowed: true }
    }

    const notifications = recentNotifications || []

    // Check max per hour
    if (notifications.length >= config.maxPerHour) {
      return {
        allowed: false,
        reason: `Exceeded ${config.maxPerHour} notifications per hour for ${notificationType}`,
      }
    }

    // Check minimum interval
    if (notifications.length > 0) {
      const lastNotification = notifications[0] as { created_at: string; id: string }
      const lastTime = new Date(lastNotification.created_at).getTime()
      const elapsed = (Date.now() - lastTime) / 1000

      if (elapsed < config.minInterval) {
        // Check if we should merge instead
        if (config.enableMerging && elapsed < config.mergeWindow) {
          return {
            allowed: false,
            shouldMerge: true,
            mergeWithId: lastNotification.id as string | undefined,
            reason: 'Merged with recent notification',
          }
        }

        return {
          allowed: false,
          reason: `Minimum interval of ${config.minInterval}s not met (${Math.round(elapsed)}s elapsed)`,
        }
      }
    }

    // If task-specific, check task-level throttling
    if (taskId) {
      const taskNotifications = notifications.filter((n) => {
        const record = n as { data?: Record<string, unknown> }
        const data = record.data as Record<string, unknown> | null
        return data?.task_id === taskId
      })

      if (taskNotifications.length > 0) {
        const lastTaskNotification = taskNotifications[0] as { created_at: string; id: string }
        const lastTime = new Date(lastTaskNotification.created_at).getTime()
        const elapsed = (Date.now() - lastTime) / 1000

        if (elapsed < config.minInterval) {
          if (config.enableMerging && elapsed < config.mergeWindow) {
            return {
              allowed: false,
              shouldMerge: true,
              mergeWithId: lastTaskNotification.id as string | undefined,
              reason: 'Merged with recent task notification',
            }
          }

          return {
            allowed: false,
            reason: `Task-level throttle: ${Math.round(elapsed)}s < ${config.minInterval}s`,
          }
        }
      }
    }

    return { allowed: true }
  } catch (error) {
    console.error('[Throttle] Error checking throttle:', error)
    return { allowed: true } // Allow on error
  }
}

/**
 * Merge notification content with existing notification
 */
export async function mergeNotification(
  env: Env,
  existingId: string,
  newContent: { title?: string; body?: string; data?: Record<string, unknown> }
): Promise<boolean> {
  const supabase = getSupabaseClient(env, true)

  try {
    // Get existing notification
    const { data: existing, error: fetchError } = await supabase
      .from('notifications')
      .select('title, body, data')
      .eq('id', existingId)
      .single()

    if (fetchError || !existing) {
      return false
    }

    // Merge content
    const existingData = (existing.data as Record<string, unknown>) || {}
    const mergedData: Record<string, unknown> = {
      ...existingData,
      ...newContent.data,
      merged_count: ((existingData.merged_count as number) || 1) + 1,
      last_merged_at: new Date().toISOString(),
    }

    // Update with merged content
    const { error: updateError } = await supabase
      .from('notifications')
      .update({
        title: newContent.title || existing.title,
        body: `${existing.body} (+ ${(mergedData.merged_count as number) - 1} more)`,
        data: mergedData,
        updated_at: new Date().toISOString(),
      })
      .eq('id', existingId)

    if (updateError) {
      console.error('[Throttle] Failed to merge notification:', updateError)
      return false
    }

    return true
  } catch (error) {
    console.error('[Throttle] Error merging notification:', error)
    return false
  }
}

/**
 * Get throttle stats for a user
 */
export async function getThrottleStats(
  env: Env,
  userId: string
): Promise<Record<string, { count: number; remaining: number }>> {
  const supabase = getSupabaseClient(env, true)
  const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000).toISOString()

  const { data: notifications } = await supabase
    .from('notifications')
    .select('type')
    .eq('user_id', userId)
    .gte('created_at', oneHourAgo)

  const stats: Record<string, { count: number; remaining: number }> = {}

  for (const [type, config] of Object.entries(DEFAULT_THROTTLE_CONFIG)) {
    if (type === 'default') continue

    const count = (notifications || []).filter((n) => n.type === type).length
    stats[type] = {
      count,
      remaining: Math.max(0, config.maxPerHour - count),
    }
  }

  return stats
}
