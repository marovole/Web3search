/**
 * Agent Activity Routes
 * API endpoints for agent execution logs and dashboard stats
 */

import { Hono } from 'hono'
import { streamSSE } from 'hono/streaming'
import type { Env } from '../types/env'
import { authMiddleware, getCurrentUser } from '../middlewares/auth'
import { getSupabaseClient } from '../lib/supabase'

const app = new Hono<{ Bindings: Env }>()

// ============================================================================
// GET /dashboard - Get dashboard stats and recent activity
// ============================================================================
app.get('/dashboard', authMiddleware(), async (c) => {
  const user = getCurrentUser(c)
  if (!user) {
    return c.json({ error: { code: 'NOT_AUTHENTICATED', message: 'Not authenticated', status: 401 } }, 401)
  }

  const supabase = getSupabaseClient(c.env, true)

  try {
    // Get task counts by status
    const { data: tasks } = await supabase
      .from('agent_tasks')
      .select('id, name, type, task_type, status, created_at')
      .eq('user_id', user.id)

    const totalTasks = tasks?.length || 0
    const activeTasks = tasks?.filter(t => t.status === 'active').length || 0
    const pausedTasks = tasks?.filter(t => t.status === 'paused').length || 0

    // Get runs from last 7 days
    const sevenDaysAgo = new Date()
    sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7)

    const { data: runs } = await supabase
      .from('agent_runs')
      .select('id, task_id, status, started_at, completed_at, result')
      .eq('user_id', user.id)
      .gte('started_at', sevenDaysAgo.toISOString())
      .order('started_at', { ascending: false })
      .limit(100)

    const today = new Date()
    today.setHours(0, 0, 0, 0)
    const runsData = runs as unknown as Array<{ started_at: string; status: string; task_id: string; id: string }> | null
    const runsToday = runsData?.filter(r => new Date(r.started_at) >= today).length || 0
    const runsThisWeek = runsData?.length || 0

    const successfulRuns = runsData?.filter(r => r.status === 'completed').length || 0
    const successRate = runsThisWeek > 0 ? Math.round((successfulRuns / runsThisWeek) * 100) : 100

    // Get notifications sent today
    const { count: notificationsToday } = await supabase
      .from('notifications')
      .select('id', { count: 'exact', head: true })
      .eq('user_id', user.id)
      .gte('created_at', today.toISOString())

    // Build task type stats
    const byTaskType: Record<string, { count: number; active: number; last_run?: string }> = {}
    const taskTypes = ['price_alert', 'risk_monitor', 'news_brief', 'portfolio_health', 'opportunity_finder']
    const tasksData = tasks as unknown as Array<{ id: string; task_type?: string; type?: string; status: string }> | null
    
    for (const type of taskTypes) {
      const typeTasks = tasksData?.filter(t => t.task_type === type || t.type === type) || []
      const typeRuns = runsData?.filter(r => {
        const task = tasksData?.find(t => t.id === r.task_id)
        return task && (task.task_type === type || task.type === type)
      }) || []

      byTaskType[type] = {
        count: typeTasks.length,
        active: typeTasks.filter(t => t.status === 'active').length,
        last_run: typeRuns[0]?.started_at as string | undefined
      }
    }

    // Recent runs with task info
    const recentRuns = (runs || []).slice(0, 10).map(run => {
      const task = tasks?.find(t => t.id === run.task_id)
      return {
        id: run.id,
        task_id: run.task_id,
        task_type: task?.task_type || task?.type || 'unknown',
        task_name: task?.name || 'Unknown Task',
        started_at: run.started_at,
        completed_at: run.completed_at,
        status: run.status,
        trigger: 'scheduled',
        result_summary: typeof run.result === 'object' && run.result 
          ? (run.result as Record<string, unknown>).summary as string 
          : undefined
      }
    })

    // Active tasks with status
    const activeTskList = (tasks || [])
      .filter(t => t.status === 'active')
      .slice(0, 10)
      .map(task => {
        const taskRuns = runs?.filter(r => r.task_id === task.id) || []
        const lastRun = taskRuns[0]
        return {
          id: task.id,
          name: task.name,
          type: task.task_type || task.type,
          status: task.status,
          last_run_at: lastRun?.started_at,
          last_run_status: lastRun?.status === 'completed' ? 'success' : lastRun?.status === 'failed' ? 'error' : undefined,
          run_count: taskRuns.length,
          trigger_count: taskRuns.filter(r => r.status === 'completed').length,
          created_at: task.created_at
        }
      })

    return c.json({
      stats: {
        total_tasks: totalTasks,
        active_tasks: activeTasks,
        paused_tasks: pausedTasks,
        runs_today: runsToday,
        runs_this_week: runsThisWeek,
        notifications_sent_today: notificationsToday || 0,
        alerts_triggered_today: 0, // TODO: Track separately
        success_rate_7d: successRate,
        by_task_type: byTaskType
      },
      recent_runs: recentRuns,
      active_tasks: activeTskList
    })
  } catch (error) {
    console.error('[Activity] Dashboard error:', error)
    return c.json({ error: { code: 'INTERNAL_ERROR', message: 'Failed to load dashboard', status: 500 } }, 500)
  }
})

// ============================================================================
// GET /logs - Get activity logs with filtering
// ============================================================================
app.get('/logs', authMiddleware(), async (c) => {
  const user = getCurrentUser(c)
  if (!user) {
    return c.json({ error: { code: 'NOT_AUTHENTICATED', message: 'Not authenticated', status: 401 } }, 401)
  }

  const supabase = getSupabaseClient(c.env, true)

  const taskType = c.req.query('task_type')
  const taskId = c.req.query('task_id')
  const limit = Math.min(parseInt(c.req.query('limit') || '50'), 100)
  const offset = parseInt(c.req.query('offset') || '0')

  try {
    // Get runs with filters
    let query = supabase
      .from('agent_runs')
      .select('id, task_id, status, started_at, completed_at, result, error')
      .eq('user_id', user.id)
      .order('started_at', { ascending: false })
      .range(offset, offset + limit - 1)

    if (taskId) {
      query = query.eq('task_id', taskId)
    }

    const { data: runs, error } = await query

    if (error) {
      throw error
    }

    // Get associated tasks
    const taskIds = [...new Set((runs || []).map(r => r.task_id))]
    const { data: tasks } = await supabase
      .from('agent_tasks')
      .select('id, name, type, task_type')
      .in('id', taskIds.length > 0 ? taskIds : ['none'])

    // Filter by task type if specified
    let filteredRuns = runs || []
    if (taskType && tasks) {
      const matchingTaskIds = tasks
        .filter(t => t.task_type === taskType || t.type === taskType)
        .map(t => t.id)
      filteredRuns = filteredRuns.filter(r => matchingTaskIds.includes(r.task_id))
    }

    // Transform to activity events
    const events = filteredRuns.map(run => {
      const task = tasks?.find(t => t.id === run.task_id)
      const hasError = run.status === 'failed' || run.error
      
      return {
        id: run.id,
        task_id: run.task_id,
        task_type: task?.task_type || task?.type || 'unknown',
        task_name: task?.name || 'Unknown Task',
        event_type: hasError ? 'task_failed' : 'task_completed',
        status: hasError ? 'error' : 'success',
        message: hasError 
          ? `任务执行失败: ${run.error || 'Unknown error'}`
          : `任务执行成功`,
        details: typeof run.result === 'object' ? run.result as Record<string, unknown> : undefined,
        created_at: run.completed_at || run.started_at
      }
    })

    return c.json({
      events,
      total: events.length,
      has_more: events.length === limit
    })
  } catch (error) {
    console.error('[Activity] Logs error:', error)
    return c.json({ error: { code: 'INTERNAL_ERROR', message: 'Failed to load logs', status: 500 } }, 500)
  }
})

// ============================================================================
// GET /stream - SSE stream for real-time activity updates
// ============================================================================
app.get('/stream', authMiddleware(), async (c) => {
  const user = getCurrentUser(c)
  if (!user) {
    return c.json({ error: { code: 'NOT_AUTHENTICATED', message: 'Not authenticated', status: 401 } }, 401)
  }

  return streamSSE(c, async (stream) => {
    const supabase = getSupabaseClient(c.env, true)
    let lastCheckTime = new Date()

    // Send initial connection event
    await stream.writeSSE({ event: 'connected', data: JSON.stringify({ userId: user.id }) })

    // Poll for new activity every 5 seconds
    const pollInterval = setInterval(async () => {
      try {
        const { data: newRuns } = await supabase
          .from('agent_runs')
          .select('id, task_id, status, started_at, completed_at, result')
          .eq('user_id', user.id)
          .gte('started_at', lastCheckTime.toISOString())
          .order('started_at', { ascending: false })
          .limit(10)

        if (newRuns && newRuns.length > 0) {
          // Get task info
          const taskIds = [...new Set(newRuns.map(r => r.task_id))]
          const { data: tasks } = await supabase
            .from('agent_tasks')
            .select('id, name, type, task_type')
            .in('id', taskIds)

          for (const run of newRuns) {
            const task = tasks?.find(t => t.id === run.task_id)
            await stream.writeSSE({
              event: 'activity',
              data: JSON.stringify({
                id: run.id,
                task_id: run.task_id,
                task_type: task?.task_type || task?.type || 'unknown',
                task_name: task?.name || 'Unknown Task',
                event_type: run.status === 'completed' ? 'task_completed' : 'task_started',
                status: run.status === 'completed' ? 'success' : 'info',
                message: run.status === 'completed' ? '任务执行完成' : '任务开始执行',
                created_at: run.started_at
              })
            })
          }

          lastCheckTime = new Date()
        }

        // Send heartbeat
        await stream.writeSSE({ event: 'heartbeat', data: new Date().toISOString() })
      } catch (error) {
        console.error('[Activity Stream] Poll error:', error)
      }
    }, 5000)

    // Cleanup on disconnect
    stream.onAbort(() => {
      clearInterval(pollInterval)
    })

    // Keep connection alive for up to 30 seconds
    await new Promise(resolve => setTimeout(resolve, 30000))
    clearInterval(pollInterval)
  })
})

export default app
