/**
 * Multi-Agent API Routes
 * New API endpoints for the Multi-Agent framework (using KV storage)
 */

import { Hono } from 'hono'
import type { Env } from '../types/env'
import { authMiddleware, getCurrentUser } from '../middlewares/auth'
import { createSSEResponse, createHeartbeatInterval } from '../services/deep-research/streaming.service'
import { CentralCoordinator } from '../lib/multi-agent/coordinator'
import { getModelConfig } from '../lib/model-routing'
import { getTaskRouter } from '../lib/multi-agent/coordinator/task-router'
import { createTaskStorage } from '../lib/multi-agent/task-storage'
import type { TaskIntent, TaskConfig } from '../lib/multi-agent/types'

const multiAgent = new Hono<{ Bindings: Env }>()

/**
 * POST /api/v1/multi-agent/research
 * Start a multi-agent research task with SSE streaming
 */
multiAgent.post('/research', authMiddleware(), async (c) => {
  const user = getCurrentUser(c)
  if (!user) {
    return c.json({ error: { code: 'NOT_AUTHENTICATED', message: 'Authentication required', status: 401 } }, 401)
  }

  const body = await c.req.json<{
    query: string
    intent?: TaskIntent
    config?: Partial<TaskConfig>
  }>()

  // Validate query
  if (!body.query || body.query.trim().length < 5) {
    return c.json({
      error: { code: 'INVALID_QUERY', message: 'Query must be at least 5 characters', status: 400 },
    }, 400)
  }

  const modelConfig = getModelConfig('devstral-chat')
  if (!modelConfig) {
    return c.json({ error: { code: 'MODEL_NOT_FOUND', message: 'Model configuration not found', status: 500 } }, 500)
  }

  const taskId = crypto.randomUUID()
  const router = getTaskRouter()
  const taskStorage = createTaskStorage(c.env)

  // Detect or use provided intent
  const intent = body.intent || router.detectIntent(body.query)

  // Adjust config based on intent
  const config: TaskConfig = router.adjustConfig(intent, {
    depth: body.config?.depth || 'standard',
    outputFormat: body.config?.outputFormat || 'detailed',
    focusAreas: body.config?.focusAreas,
    maxAgents: body.config?.maxAgents,
    timeout: body.config?.timeout,
  })

  // Create task record in KV
  await taskStorage.createTask({
    id: taskId,
    userId: user.id,
    query: body.query,
    intent,
    config,
    status: 'running',
    result: null,
    error: null,
    tokensUsed: 0,
    durationMs: 0,
    startedAt: new Date().toISOString(),
    completedAt: null,
  })

  // Log routing decision
  console.log(router.createRoutingSummary(body.query, intent))

  // Return SSE response
  return createSSEResponse(async (emitter, _controller) => {
    const heartbeat = createHeartbeatInterval(emitter)

    try {
      const coordinator = new CentralCoordinator(c.env, modelConfig)

      const task = {
        id: taskId,
        userId: user.id,
        query: body.query,
        intent,
        config,
        createdAt: new Date().toISOString(),
      }

      const result = await coordinator.executeTask(task, emitter)

      // Update task record in KV
      await taskStorage.updateTask(taskId, {
        status: result.success ? 'completed' : 'failed',
        completedAt: new Date().toISOString(),
        result: result.output ? JSON.stringify(result.output) : null,
        tokensUsed: result.tokensUsed,
        durationMs: result.duration,
        error: result.error,
      })

      if (result.success) {
        emitter.emitComplete(JSON.stringify(result.output), taskId)
      } else {
        emitter.emitError(result.error || 'Task failed')
      }
    } catch (error) {
      console.error('Task execution error:', error)

      await taskStorage.updateTask(taskId, {
        status: 'failed',
        completedAt: new Date().toISOString(),
        error: error instanceof Error ? error.message : 'Unknown error',
      })

      emitter.emitError(error instanceof Error ? error.message : 'Internal error')
    } finally {
      clearInterval(heartbeat)
    }
  })
})

/**
 * GET /api/v1/multi-agent/tasks
 * Get user's task list
 */
multiAgent.get('/tasks', authMiddleware(), async (c) => {
  const user = getCurrentUser(c)
  if (!user) {
    return c.json({ error: { code: 'NOT_AUTHENTICATED', status: 401 } }, 401)
  }

  const taskStorage = createTaskStorage(c.env)
  const limit = parseInt(c.req.query('limit') || '20')
  const offset = parseInt(c.req.query('offset') || '0')

  const tasks = await taskStorage.getUserTasks(user.id, limit, offset)

  // Format tasks for response
  const formattedTasks = tasks.map((task) => ({
    id: task.id,
    query: task.query,
    intent: task.intent,
    config: task.config,
    status: task.status,
    created_at: task.createdAt,
    completed_at: task.completedAt,
    duration_ms: task.durationMs,
  }))

  return c.json({
    tasks: formattedTasks,
    pagination: {
      limit,
      offset,
      hasMore: tasks.length === limit,
    },
  })
})

/**
 * GET /api/v1/multi-agent/tasks/:id
 * Get task details
 */
multiAgent.get('/tasks/:id', authMiddleware(), async (c) => {
  const user = getCurrentUser(c)
  if (!user) {
    return c.json({ error: { code: 'NOT_AUTHENTICATED', status: 401 } }, 401)
  }

  const taskStorage = createTaskStorage(c.env)
  const taskId = c.req.param('id')

  const task = await taskStorage.getTask(taskId)

  if (!task || task.userId !== user.id) {
    return c.json({ error: { code: 'NOT_FOUND', message: 'Task not found', status: 404 } }, 404)
  }

  return c.json({ task })
})

/**
 * DELETE /api/v1/multi-agent/tasks/:id
 * Cancel or delete a task
 */
multiAgent.delete('/tasks/:id', authMiddleware(), async (c) => {
  const user = getCurrentUser(c)
  if (!user) {
    return c.json({ error: { code: 'NOT_AUTHENTICATED', status: 401 } }, 401)
  }

  const taskStorage = createTaskStorage(c.env)
  const taskId = c.req.param('id')

  const existingTask = await taskStorage.getTask(taskId)

  if (!existingTask || existingTask.userId !== user.id) {
    return c.json({ error: { code: 'NOT_FOUND', message: 'Task not found', status: 404 } }, 404)
  }

  if (existingTask.status === 'running') {
    // Mark as cancelled instead of deleting
    await taskStorage.updateTask(taskId, {
      status: 'cancelled',
      completedAt: new Date().toISOString(),
    })
  } else {
    // Delete the task
    await taskStorage.deleteTask(taskId)
  }

  return c.json({ success: true, message: 'Task cancelled' })
})

/**
 * GET /api/v1/multi-agent/intents
 * Get available intent types
 */
multiAgent.get('/intents', async (c) => {
  const router = getTaskRouter()
  const routes = router.getAllRoutes()

  return c.json({
    intents: routes.map((r) => ({
      id: r.intent,
      description: r.description,
      agents: r.agents,
    })),
  })
})

export default multiAgent
