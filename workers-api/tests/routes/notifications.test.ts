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

let mockNotificationsData: unknown[] = []
let mockSingleNotification: unknown = null
let mockUnreadCount = 0
let mockDbError: unknown = null

vi.mock('../../src/lib/supabase', () => ({
  getSupabaseClient: vi.fn(() => ({
    from: (_table: string) => {
      const deleteChain = {
        eq: vi.fn().mockReturnThis(),
        not: vi.fn().mockImplementation(async () => {
          if (mockDbError) return { error: mockDbError, count: 0 }
          return { error: null, count: 3 }
        }),
        then: (resolve: (value: { error: unknown }) => void) => {
          resolve({ error: mockDbError || null })
        },
      }

      const baseChain = {
        eq: vi.fn().mockReturnThis(),
        is: vi.fn().mockReturnThis(),
        order: vi.fn().mockReturnThis(),
        range: vi.fn().mockImplementation(async () => {
          if (mockDbError) return { data: null, error: mockDbError, count: 0 }
          return { data: mockNotificationsData, error: null, count: mockNotificationsData.length }
        }),
        single: vi.fn().mockImplementation(async () => {
          if (mockDbError) return { data: null, error: mockDbError }
          return { data: mockSingleNotification, error: mockSingleNotification ? null : { code: 'PGRST116' } }
        }),
        select: vi.fn().mockImplementation((cols, opts) => {
          if (opts?.count === 'exact' && opts?.head) {
            return {
              eq: vi.fn().mockReturnThis(),
              is: vi.fn().mockImplementation(async () => {
                return { count: mockUnreadCount, error: null }
              }),
            }
          }
          return baseChain
        }),
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

import notifications from '../../src/routes/notifications'

function createTestApp() {
  const app = new Hono<{ Bindings: Env }>()
  app.route('/notifications', notifications)
  return app
}

describe('Notifications Routes', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockNotificationsData = []
    mockSingleNotification = null
    mockUnreadCount = 0
    mockDbError = null
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('GET /notifications', () => {
    it('returns list of notifications with pagination', async () => {
      mockNotificationsData = [
        { id: 'notif-1', type: 'price_alert', title: 'BTC Alert', message: 'Price reached target', created_at: new Date().toISOString() },
        { id: 'notif-2', type: 'task_completed', title: 'Task Done', message: 'Research completed', created_at: new Date().toISOString() },
      ]
      mockUnreadCount = 1

      const app = createTestApp()
      const res = await app.fetch(
        new Request('http://localhost/notifications'),
        createMockEnv()
      )

      expect(res.status).toBe(200)
      const body = await res.json()
      expect(body).toHaveProperty('notifications')
      expect(body).toHaveProperty('total')
      expect(body).toHaveProperty('unread_count')
      expect(body).toHaveProperty('limit')
      expect(body).toHaveProperty('offset')
    })

    it('supports unread filter', async () => {
      mockNotificationsData = [
        { id: 'notif-1', type: 'price_alert', title: 'Unread Alert', read_at: null },
      ]
      mockUnreadCount = 1

      const app = createTestApp()
      const res = await app.fetch(
        new Request('http://localhost/notifications?unread=true'),
        createMockEnv()
      )

      expect(res.status).toBe(200)
      const body = await res.json()
      expect(body).toHaveProperty('notifications')
    })

    it('supports type filter', async () => {
      mockNotificationsData = [
        { id: 'notif-1', type: 'price_alert', title: 'Price Alert' },
      ]

      const app = createTestApp()
      const res = await app.fetch(
        new Request('http://localhost/notifications?type=price_alert'),
        createMockEnv()
      )

      expect(res.status).toBe(200)
      const body = await res.json()
      expect(body).toHaveProperty('notifications')
    })

    it('returns 500 on database error', async () => {
      mockDbError = { message: 'DB error' }

      const app = createTestApp()
      const res = await app.fetch(
        new Request('http://localhost/notifications'),
        createMockEnv()
      )

      expect(res.status).toBe(500)
      const body = await res.json()
      expect(body.error.code).toBe('DATABASE_ERROR')
    })
  })

  describe('GET /notifications/:id', () => {
    it('returns single notification', async () => {
      mockSingleNotification = {
        id: 'notif-1',
        type: 'price_alert',
        title: 'BTC Alert',
        message: 'Price reached target',
      }

      const app = createTestApp()
      const res = await app.fetch(
        new Request('http://localhost/notifications/notif-1'),
        createMockEnv()
      )

      expect(res.status).toBe(200)
      const body = await res.json()
      expect(body.notification.id).toBe('notif-1')
    })

    it('returns 404 for non-existent notification', async () => {
      mockSingleNotification = null

      const app = createTestApp()
      const res = await app.fetch(
        new Request('http://localhost/notifications/non-existent'),
        createMockEnv()
      )

      expect(res.status).toBe(404)
      const body = await res.json()
      expect(body.error.code).toBe('NOT_FOUND')
    })
  })

  describe('PATCH /notifications/:id/read', () => {
    it('marks notification as read', async () => {
      mockSingleNotification = {
        id: 'notif-1',
        type: 'price_alert',
        read_at: new Date().toISOString(),
      }

      const app = createTestApp()
      const res = await app.fetch(
        new Request('http://localhost/notifications/notif-1/read', {
          method: 'PATCH',
        }),
        createMockEnv()
      )

      expect(res.status).toBe(200)
      const body = await res.json()
      expect(body.notification).toBeDefined()
    })

    it('returns 404 for already read notification', async () => {
      mockSingleNotification = null
      mockDbError = { code: 'PGRST116' }

      const app = createTestApp()
      const res = await app.fetch(
        new Request('http://localhost/notifications/notif-1/read', {
          method: 'PATCH',
        }),
        createMockEnv()
      )

      expect(res.status).toBe(404)
    })
  })

  describe('POST /notifications/read-all', () => {
    it('marks all notifications as read', async () => {
      const app = createTestApp()
      const res = await app.fetch(
        new Request('http://localhost/notifications/read-all', {
          method: 'POST',
        }),
        createMockEnv()
      )

      expect(res.status).toBe(200)
      const body = await res.json()
      expect(body.success).toBe(true)
      expect(body).toHaveProperty('marked_count')
    })
  })

  describe('PATCH /notifications/:id/dismiss', () => {
    it('dismisses a notification', async () => {
      mockSingleNotification = {
        id: 'notif-1',
        dismissed_at: new Date().toISOString(),
      }

      const app = createTestApp()
      const res = await app.fetch(
        new Request('http://localhost/notifications/notif-1/dismiss', {
          method: 'PATCH',
        }),
        createMockEnv()
      )

      expect(res.status).toBe(200)
      const body = await res.json()
      expect(body.notification).toBeDefined()
    })

    it('returns 404 for non-existent notification', async () => {
      mockSingleNotification = null
      mockDbError = { code: 'PGRST116' }

      const app = createTestApp()
      const res = await app.fetch(
        new Request('http://localhost/notifications/non-existent/dismiss', {
          method: 'PATCH',
        }),
        createMockEnv()
      )

      expect(res.status).toBe(404)
    })
  })

  describe('DELETE /notifications/:id', () => {
    it('deletes notification successfully', async () => {
      const app = createTestApp()
      const res = await app.fetch(
        new Request('http://localhost/notifications/notif-1', {
          method: 'DELETE',
        }),
        createMockEnv()
      )

      expect(res.status).toBe(200)
      const body = await res.json()
      expect(body.success).toBe(true)
    })
  })

  describe('DELETE /notifications/dismissed/all', () => {
    it('deletes all dismissed notifications', async () => {
      const app = createTestApp()
      const res = await app.fetch(
        new Request('http://localhost/notifications/dismissed/all', {
          method: 'DELETE',
        }),
        createMockEnv()
      )

      expect(res.status).toBe(200)
      const body = await res.json()
      expect(body.success).toBe(true)
      expect(body).toHaveProperty('deleted_count')
    })
  })
})
