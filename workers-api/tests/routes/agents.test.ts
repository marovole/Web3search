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
let mockSingleTask: unknown = null
let mockDbError: unknown = null

vi.mock('../../src/lib/supabase', () => ({
  getSupabaseClient: vi.fn(() => ({
    from: (_table: string) => {
      const deleteChain = {
        eq: vi.fn().mockReturnThis(),
        then: (resolve: (value: { error: unknown }) => void) => {
          resolve({ error: mockDbError || null })
        },
      }
      const baseChain = {
        eq: vi.fn().mockReturnThis(),
        order: vi.fn().mockReturnThis(),
        range: vi.fn().mockImplementation(async () => {
          if (mockDbError) return { data: null, error: mockDbError }
          return { data: _table === 'agent_runs' ? mockRunsData : mockTasksData, count: mockTasksData.length, error: null }
        }),
        single: vi.fn().mockImplementation(async () => {
          if (mockDbError) return { data: null, error: mockDbError }
          return { data: mockSingleTask, error: mockSingleTask ? null : { code: 'PGRST116' } }
        }),
        select: vi.fn().mockReturnThis(),
        insert: vi.fn().mockReturnThis(),
        update: vi.fn().mockReturnThis(),
        delete: vi.fn().mockReturnValue(deleteChain),
      }
      return baseChain
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

vi.mock('../../src/middlewares/quota', () => ({
  checkAgentQuota: () => async (_c: unknown, next: () => Promise<void>) => next(),
}))

import agents from '../../src/routes/agents'

function createTestApp() {
  const app = new Hono<{ Bindings: Env }>()
  app.route('/agents', agents)
  return app
}

describe('Agents Routes', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockTasksData = []
    mockRunsData = []
    mockSingleTask = null
    mockDbError = null
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('GET /agents/tasks', () => {
    it('returns list of tasks for authenticated user', async () => {
      mockTasksData = [
        { id: 'task-1', name: 'Price Alert BTC', type: 'price_alert', status: 'active' },
        { id: 'task-2', name: 'Risk Monitor ETH', type: 'risk_monitor', status: 'paused' },
      ]

      const app = createTestApp()
      const res = await app.fetch(
        new Request('http://localhost/agents/tasks'),
        createMockEnv()
      )

      expect(res.status).toBe(200)
      const body = await res.json()
      expect(body.tasks).toHaveLength(2)
    })

    it('returns 500 on database error', async () => {
      mockDbError = { message: 'DB error' }

      const app = createTestApp()
      const res = await app.fetch(
        new Request('http://localhost/agents/tasks'),
        createMockEnv()
      )

      expect(res.status).toBe(500)
      const body = await res.json()
      expect(body.error.code).toBe('DATABASE_ERROR')
    })
  })

  describe('POST /agents/tasks', () => {
    it('creates a new task with valid input', async () => {
      mockSingleTask = {
        id: 'task-new',
        name: 'New Alert',
        type: 'price_alert',
        status: 'active',
        config: { token: 'BTC', threshold: 100000 },
      }

      const app = createTestApp()
      const res = await app.fetch(
        new Request('http://localhost/agents/tasks', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            name: 'New Alert',
            type: 'price_alert',
            config: { token: 'BTC', threshold: 100000 },
          }),
        }),
        createMockEnv()
      )

      expect(res.status).toBe(201)
      const body = await res.json()
      expect(body.task.name).toBe('New Alert')
    })

    it('returns 400 for missing required fields', async () => {
      const app = createTestApp()
      const res = await app.fetch(
        new Request('http://localhost/agents/tasks', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name: 'Test' }),
        }),
        createMockEnv()
      )

      expect(res.status).toBe(400)
      const body = await res.json()
      expect(body.error.code).toBe('INVALID_INPUT')
    })

    it('returns 400 for invalid task type', async () => {
      const app = createTestApp()
      const res = await app.fetch(
        new Request('http://localhost/agents/tasks', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            name: 'Test',
            type: 'invalid_type',
            config: {},
          }),
        }),
        createMockEnv()
      )

      expect(res.status).toBe(400)
      const body = await res.json()
      expect(body.error.code).toBe('INVALID_TYPE')
    })
  })

  describe('GET /agents/tasks/:id', () => {
    it('returns task details for valid id', async () => {
      mockSingleTask = {
        id: 'task-1',
        name: 'BTC Alert',
        type: 'price_alert',
        status: 'active',
      }

      const app = createTestApp()
      const res = await app.fetch(
        new Request('http://localhost/agents/tasks/task-1'),
        createMockEnv()
      )

      expect(res.status).toBe(200)
      const body = await res.json()
      expect(body.task.id).toBe('task-1')
    })

    it('returns 404 for non-existent task', async () => {
      mockSingleTask = null

      const app = createTestApp()
      const res = await app.fetch(
        new Request('http://localhost/agents/tasks/non-existent'),
        createMockEnv()
      )

      expect(res.status).toBe(404)
    })
  })

  describe('PATCH /agents/tasks/:id', () => {
    it('updates task with valid fields', async () => {
      mockSingleTask = {
        id: 'task-1',
        name: 'Updated Name',
        status: 'paused',
      }

      const app = createTestApp()
      const res = await app.fetch(
        new Request('http://localhost/agents/tasks/task-1', {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name: 'Updated Name' }),
        }),
        createMockEnv()
      )

      expect(res.status).toBe(200)
      const body = await res.json()
      expect(body.task.name).toBe('Updated Name')
    })

    it('returns 400 when no valid fields provided', async () => {
      const app = createTestApp()
      const res = await app.fetch(
        new Request('http://localhost/agents/tasks/task-1', {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ invalid_field: 'value' }),
        }),
        createMockEnv()
      )

      expect(res.status).toBe(400)
      const body = await res.json()
      expect(body.error.code).toBe('NO_UPDATES')
    })
  })

  describe('DELETE /agents/tasks/:id', () => {
    it('deletes task successfully', async () => {
      const app = createTestApp()
      const res = await app.fetch(
        new Request('http://localhost/agents/tasks/task-1', {
          method: 'DELETE',
        }),
        createMockEnv()
      )

      expect(res.status).toBe(200)
      const body = await res.json()
      expect(body.success).toBe(true)
    })
  })

  describe('POST /agents/tasks/:id/pause', () => {
    it('pauses an active task', async () => {
      mockSingleTask = {
        id: 'task-1',
        status: 'paused',
      }

      const app = createTestApp()
      const res = await app.fetch(
        new Request('http://localhost/agents/tasks/task-1/pause', {
          method: 'POST',
        }),
        createMockEnv()
      )

      expect(res.status).toBe(200)
      const body = await res.json()
      expect(body.task.status).toBe('paused')
    })

    it('returns 404 when task is not active', async () => {
      mockSingleTask = null

      const app = createTestApp()
      const res = await app.fetch(
        new Request('http://localhost/agents/tasks/task-1/pause', {
          method: 'POST',
        }),
        createMockEnv()
      )

      expect(res.status).toBe(404)
    })
  })

  describe('POST /agents/tasks/:id/resume', () => {
    it('resumes a paused task', async () => {
      mockSingleTask = {
        id: 'task-1',
        status: 'active',
        schedule: 'hourly',
      }

      const app = createTestApp()
      const res = await app.fetch(
        new Request('http://localhost/agents/tasks/task-1/resume', {
          method: 'POST',
        }),
        createMockEnv()
      )

      expect(res.status).toBe(200)
      const body = await res.json()
      expect(body.task.status).toBe('active')
    })
  })

  describe('GET /agents/tasks/:id/runs', () => {
    it('returns run history for task', async () => {
      mockSingleTask = { id: 'task-1' }
      mockRunsData = [
        { id: 'run-1', task_id: 'task-1', status: 'completed' },
        { id: 'run-2', task_id: 'task-1', status: 'completed' },
      ]

      const app = createTestApp()
      const res = await app.fetch(
        new Request('http://localhost/agents/tasks/task-1/runs'),
        createMockEnv()
      )

      expect(res.status).toBe(200)
      const body = await res.json()
      expect(body.runs).toHaveLength(2)
    })

    it('returns 404 for non-existent task', async () => {
      mockSingleTask = null

      const app = createTestApp()
      const res = await app.fetch(
        new Request('http://localhost/agents/tasks/non-existent/runs'),
        createMockEnv()
      )

      expect(res.status).toBe(404)
    })
  })
})
