import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'
import { Hono } from 'hono'
import type { Env } from '../../src/types/env'

let mockUser: { id: string; email: string } | null = { id: 'user-123', email: 'test@example.com' }
let mockProfile: Record<string, unknown> | null = null
let mockQuota: Record<string, unknown> | null = null
let mockProfileError: { code?: string } | null = null
let mockQuotaError: { code?: string } | null = null

function createMockEnv(): Env {
  return {
    ENVIRONMENT: 'test',
    SUPABASE_URL: 'https://test.supabase.co',
    SUPABASE_ANON_KEY: 'test-key',
    OPENROUTER_API_KEY: 'test-key',
    JWT_SECRET: 'jwt-secret',
  } as Env
}

vi.mock('../../src/lib/supabase', () => ({
  getSupabaseClient: vi.fn(() => ({
    from: (table: string) => {
      const baseChain = {
        select: vi.fn().mockReturnThis(),
        eq: vi.fn().mockReturnThis(),
        single: vi.fn().mockImplementation(async () => {
          if (table === 'user_profiles') {
            return { data: mockProfile, error: mockProfileError }
          }
          if (table === 'user_quotas') {
            return { data: mockQuota, error: mockQuotaError }
          }
          return { data: null, error: null }
        })
      }
      return baseChain
    },
    auth: {
      getUser: vi.fn().mockResolvedValue({ data: { user: mockUser }, error: null })
    }
  }))
}))

vi.mock('../../src/middlewares/auth', () => ({
  authMiddleware: () => async (c: { set: (key: string, value: unknown) => void }, next: () => Promise<void>) => {
    if (mockUser) {
      c.set('currentUser', mockUser)
    }
    await next()
  },
  getCurrentUser: () => mockUser,
}))

import auth from '../../src/routes/auth'

function createTestApp() {
  const app = new Hono<{ Bindings: Env }>()
  app.route('/auth', auth)
  return app
}

describe('Auth Routes', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockUser = { id: 'user-123', email: 'test@example.com' }
    mockProfileError = null
    mockQuotaError = null
    mockProfile = {
      id: 'user-123',
      username: 'satoshi',
      display_name: 'Satoshi',
      avatar_url: null,
      plan: 'free',
      risk_preference: 'moderate',
      notification_settings: {},
      timezone: 'UTC',
      language: 'en',
      theme: 'system',
      onboarding_completed: false,
      created_at: '2025-01-01T00:00:00Z'
    }
    mockQuota = {
      watchlist_count: 1,
      watchlist_limit: 5,
      agent_count: 0,
      agent_limit: 3,
      daily_alerts_sent: 0,
      daily_alerts_limit: 10,
      daily_deep_research: 1,
      daily_deep_research_limit: 3,
      daily_quick_chat: 2,
      daily_quick_chat_limit: 20,
      monthly_reports: 0,
      monthly_reports_limit: 5,
      daily_reset_at: '2025-01-02T00:00:00Z',
      monthly_reset_at: '2025-02-01T00:00:00Z'
    }
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('returns user profile and quota for authenticated user', async () => {
    const app = createTestApp()
    const res = await app.fetch(new Request('http://localhost/auth/me'), createMockEnv())

    expect(res.status).toBe(200)
    const body = await res.json()

    expect(body.user.id).toBe('user-123')
    expect(body.user.username).toBe('satoshi')
    expect(body.user.plan).toBe('free')
    expect(body.quota.watchlist.used).toBe(1)
    expect(body.quota.daily.deep_research.used).toBe(1)
  })

  it('returns 401 when user is not authenticated', async () => {
    mockUser = null
    const app = createTestApp()
    const res = await app.fetch(new Request('http://localhost/auth/me'), createMockEnv())

    expect(res.status).toBe(401)
    const body = await res.json()
    expect(body.error.code).toBe('NOT_AUTHENTICATED')
  })

  it('refreshes auth token for authenticated user', async () => {
    const app = createTestApp()
    const res = await app.fetch(new Request('http://localhost/auth/refresh', { method: 'POST' }), createMockEnv())

    expect(res.status).toBe(200)
    const body = await res.json()
    expect(body.user.id).toBe('user-123')
  })
})
