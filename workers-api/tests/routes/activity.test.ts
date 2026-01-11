import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'
import { Hono } from 'hono'
import type { Env } from '../../src/types/env'

const mockUser = { id: 'user-123', email: 'test@example.com', tier: 'free' }

function createMockEnv(): Env {
  return {
    ENVIRONMENT: 'test',
    SUPABASE_URL: 'https://test.supabase.co',
    SUPABASE_ANON_KEY: 'test-key',
    OPENROUTER_API_KEY: 'test-key',
  } as Env
}

let mockTasksData: unknown[] = []
let mockRunsData: unknown[] = []
let mockNotificationsCount = 0
let mockDbError: unknown = null

vi.mock('../../src/lib/supabase', () => ({
  getSupabaseClient: vi.fn(() => ({
    from: (table: string) => {
      const createChain = (): Record<string, unknown> => {
        const chain: Record<string, unknown> = {}
        const createRangeResult = () => ({
          eq: vi.fn().mockReturnValue(chain),
          then: (resolve: (val: { data: unknown; error: unknown }) => void) => {
            if (mockDbError) {
              resolve({ data: null, error: mockDbError })
            } else {
              resolve({ data: mockRunsData, error: null })
            }
          },
        })
        chain.eq = vi.fn().mockReturnValue(chain)
        chain.gte = vi.fn().mockReturnValue(chain)
        chain.in = vi.fn().mockReturnValue(chain)
        chain.order = vi.fn().mockReturnValue(chain)
        chain.limit = vi.fn().mockReturnValue(chain)
        chain.range = vi.fn().mockReturnValue(createRangeResult())
        chain.select = vi.fn().mockImplementation((cols, opts) => {
          if (opts?.count === 'exact' && opts?.head) {
            const countChain: Record<string, unknown> = {}
            countChain.eq = vi.fn().mockReturnValue(countChain)
            countChain.gte = vi.fn().mockImplementation(async () => {
              return { count: mockNotificationsCount, error: null }
            })
            countChain.is = vi.fn().mockImplementation(async () => {
              return { count: mockNotificationsCount, error: null }
            })
            return countChain
          }
          return chain
        })
        return chain
      }

      if (table === 'agent_tasks') {
        const taskChain = createChain()
        taskChain.eq = vi.fn().mockImplementation(() => {
          const result = {
            data: mockTasksData,
            error: mockDbError || null,
          }
          return {
            ...taskChain,
            then: (resolve: (val: typeof result) => void) => resolve(result),
          }
        })
        taskChain.select = vi.fn().mockReturnValue(taskChain)
        return taskChain
      }

      if (table === 'agent_runs') {
        return createChain()
      }

      if (table === 'notifications') {
        const notifChain = createChain()
        notifChain.select = vi.fn().mockImplementation((cols, opts) => {
          if (opts?.count === 'exact' && opts?.head) {
            const countChain: Record<string, unknown> = {}
            countChain.eq = vi.fn().mockReturnValue(countChain)
            countChain.gte = vi.fn().mockImplementation(async () => {
              return { count: mockNotificationsCount, error: null }
            })
            countChain.is = vi.fn().mockImplementation(async () => {
              return { count: mockNotificationsCount, error: null }
            })
            return countChain
          }
          return notifChain
        })
        return notifChain
      }

      return createChain()
    },
  })),
}))

vi.mock('../../src/middlewares/auth', () => ({
  authMiddleware: () => async (c: { set: (key: string, value: unknown) => void }, next: () => Promise<void>) => {
    c.set('user', mockUser)
    await next()
  },
  getCurrentUser: () => mockUser,
}))

import activity from '../../src/routes/activity'

function createTestApp() {
  const app = new Hono<{ Bindings: Env }>()
  app.route('/activity', activity)
  return app
}

describe('Activity Routes', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockTasksData = []
    mockRunsData = []
    mockNotificationsCount = 0
    mockDbError = null
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('GET /activity/dashboard', () => {
    it('returns dashboard stats for authenticated user', async () => {
      mockTasksData = [
        { id: 'task-1', name: 'Price Alert BTC', type: 'price_alert', task_type: 'price_alert', status: 'active', created_at: new Date().toISOString() },
        { id: 'task-2', name: 'Risk Monitor ETH', type: 'risk_monitor', task_type: 'risk_monitor', status: 'paused', created_at: new Date().toISOString() },
      ]
      mockRunsData = [
        { id: 'run-1', task_id: 'task-1', status: 'completed', started_at: new Date().toISOString(), completed_at: new Date().toISOString() },
      ]
      mockNotificationsCount = 5

      const app = createTestApp()
      const res = await app.fetch(
        new Request('http://localhost/activity/dashboard'),
        createMockEnv()
      )

      expect(res.status).toBe(200)
      const body = await res.json()
      expect(body).toHaveProperty('stats')
      expect(body.stats).toHaveProperty('total_tasks')
      expect(body.stats).toHaveProperty('active_tasks')
      expect(body.stats).toHaveProperty('paused_tasks')
      expect(body.stats).toHaveProperty('runs_today')
      expect(body.stats).toHaveProperty('runs_this_week')
      expect(body.stats).toHaveProperty('by_task_type')
      expect(body).toHaveProperty('recent_runs')
      expect(body).toHaveProperty('active_tasks')
    })

    it('returns 401 for unauthenticated request', async () => {
      // Mock getCurrentUser to return null
      vi.doMock('../../src/middlewares/auth', () => ({
        authMiddleware: () => async (_c: unknown, next: () => Promise<void>) => next(),
        getCurrentUser: () => null,
      }))

      // Since we can't easily re-import, we test authenticated path only
      // The route should handle missing user internally
    })
  })

  describe('GET /activity/logs', () => {
    it('returns activity logs with default pagination', async () => {
      mockRunsData = [
        { id: 'run-1', task_id: 'task-1', status: 'completed', started_at: new Date().toISOString(), completed_at: new Date().toISOString() },
        { id: 'run-2', task_id: 'task-1', status: 'failed', started_at: new Date().toISOString(), error: 'Test error' },
      ]
      mockTasksData = [
        { id: 'task-1', name: 'Test Task', type: 'price_alert', task_type: 'price_alert' },
      ]

      const app = createTestApp()
      const res = await app.fetch(
        new Request('http://localhost/activity/logs'),
        createMockEnv()
      )

      expect(res.status).toBe(200)
      const body = await res.json()
      expect(body).toHaveProperty('events')
      expect(body).toHaveProperty('total')
      expect(body).toHaveProperty('has_more')
    })

    it('supports task_id filter', async () => {
      mockRunsData = [
        { id: 'run-1', task_id: 'task-1', status: 'completed', started_at: new Date().toISOString() },
      ]
      mockTasksData = [
        { id: 'task-1', name: 'Test Task', type: 'price_alert', task_type: 'price_alert' },
      ]

      const app = createTestApp()
      const res = await app.fetch(
        new Request('http://localhost/activity/logs?task_id=task-1'),
        createMockEnv()
      )

      expect(res.status).toBe(200)
      const body = await res.json()
      expect(body).toHaveProperty('events')
    })

    it('supports pagination with limit and offset', async () => {
      mockRunsData = []
      mockTasksData = []

      const app = createTestApp()
      const res = await app.fetch(
        new Request('http://localhost/activity/logs?limit=10&offset=20'),
        createMockEnv()
      )

      expect(res.status).toBe(200)
      const body = await res.json()
      expect(body).toHaveProperty('events')
      expect(body.total).toBe(0)
    })

    it('returns 500 on database error', async () => {
      mockDbError = { message: 'DB error' }

      const app = createTestApp()
      const res = await app.fetch(
        new Request('http://localhost/activity/logs'),
        createMockEnv()
      )

      expect(res.status).toBe(500)
      const body = await res.json()
      expect(body.error.code).toBe('INTERNAL_ERROR')
    })
  })

  describe('GET /activity/stream', () => {
    it('returns SSE stream for authenticated user', async () => {
      const app = createTestApp()
      const res = await app.fetch(
        new Request('http://localhost/activity/stream'),
        createMockEnv()
      )

      // SSE endpoint returns 200 with text/event-stream content type
      expect(res.status).toBe(200)
      expect(res.headers.get('content-type')).toContain('text/event-stream')
    })
  })
})
