import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'
import { Hono } from 'hono'
import type { Env } from '../../src/types/env'

const mockStripe = {
  customers: { create: vi.fn().mockResolvedValue({ id: 'cus_123' }) },
  checkout: { sessions: { create: vi.fn().mockResolvedValue({ id: 'cs_123', url: 'https://stripe.test/checkout' }) } },
  billingPortal: { sessions: { create: vi.fn().mockResolvedValue({ url: 'https://stripe.test/portal' }) } },
  webhooks: { constructEvent: vi.fn() },
  subscriptions: { retrieve: vi.fn().mockResolvedValue({
    status: 'active',
    items: { data: [{ price: { id: 'price_123', product: 'prod_123' } }] },
    current_period_start: 1700000000,
    current_period_end: 1705000000,
    cancel_at_period_end: false,
  }) },
}

let mockUser: { id: string; email: string } | null = { id: 'user-123', email: 'test@example.com' }
let mockProfile: { stripe_customer_id?: string | null } | null = null
let mockProfileError: unknown = null
let mockUpdateError: unknown = null

function createMockEnv(overrides: Partial<Env> = {}): Env {
  return {
    ENVIRONMENT: 'test',
    SUPABASE_URL: 'https://test.supabase.co',
    SUPABASE_ANON_KEY: 'test-key',
    OPENROUTER_API_KEY: 'test-key',
    JWT_SECRET: 'jwt-secret',
    STRIPE_SECRET_KEY: 'sk_test',
    STRIPE_PRO_PRICE_ID: 'price_pro',
    STRIPE_TEAM_PRICE_ID: 'price_team',
    STRIPE_WEBHOOK_SECRET: 'whsec_test',
    ...overrides,
  } as Env
}

vi.mock('stripe', () => ({
  default: class Stripe {
    customers = mockStripe.customers
    checkout = mockStripe.checkout
    billingPortal = mockStripe.billingPortal
    webhooks = mockStripe.webhooks
    subscriptions = mockStripe.subscriptions
    constructor() {}
  },
}))

vi.mock('../../src/lib/supabase', () => ({
  getSupabaseClient: vi.fn(() => ({
    from: (_table: string) => {
      const updateChain = {
        eq: vi.fn().mockImplementation(async () => ({ error: mockUpdateError })),
      }
      return {
        select: vi.fn().mockReturnThis(),
        eq: vi.fn().mockReturnThis(),
        single: vi.fn().mockResolvedValue({ data: mockProfile, error: mockProfileError }),
        update: vi.fn().mockReturnValue(updateChain),
        upsert: vi.fn().mockResolvedValue({ error: null }),
      }
    },
    auth: {
      getUser: vi.fn().mockResolvedValue({ data: { user: mockUser }, error: null })
    }
  })),
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

import billing from '../../src/routes/billing'

function createTestApp() {
  const app = new Hono<{ Bindings: Env }>()
  app.route('/billing', billing)
  return app
}

describe('Billing Routes', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockUser = { id: 'user-123', email: 'test@example.com' }
    mockProfile = { stripe_customer_id: null }
    mockProfileError = null
    mockUpdateError = null
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('returns 400 for invalid plan', async () => {
    const app = createTestApp()
    const res = await app.fetch(
      new Request('http://localhost/billing/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ plan: 'invalid' }),
      }),
      createMockEnv()
    )

    expect(res.status).toBe(400)
    const body = await res.json()
    expect(body.error.code).toBe('INVALID_PLAN')
  })

  it('creates checkout session for valid plan', async () => {
    const app = createTestApp()
    const res = await app.fetch(
      new Request('http://localhost/billing/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ plan: 'pro', interval: 'month' }),
      }),
      createMockEnv()
    )

    expect(res.status).toBe(200)
    const body = await res.json()
    expect(body.checkout_url).toBe('https://stripe.test/checkout')
  })

  it('returns 404 when no subscription for portal', async () => {
    mockProfile = { stripe_customer_id: null }

    const app = createTestApp()
    const res = await app.fetch(
      new Request('http://localhost/billing/portal', { method: 'POST' }),
      createMockEnv()
    )

    expect(res.status).toBe(404)
    const body = await res.json()
    expect(body.error.code).toBe('NO_SUBSCRIPTION')
  })

  it('creates billing portal session when customer exists', async () => {
    mockProfile = { stripe_customer_id: 'cus_123' }

    const app = createTestApp()
    const res = await app.fetch(
      new Request('http://localhost/billing/portal', { method: 'POST' }),
      createMockEnv()
    )

    expect(res.status).toBe(200)
    const body = await res.json()
    expect(body.portal_url).toBe('https://stripe.test/portal')
  })

  it('returns 400 for invalid webhook signature', async () => {
    mockStripe.webhooks.constructEvent.mockImplementation(() => {
      throw new Error('Invalid signature')
    })

    const app = createTestApp()
    const res = await app.fetch(
      new Request('http://localhost/billing/webhook', {
        method: 'POST',
        headers: { 'stripe-signature': 'sig_test' },
        body: JSON.stringify({ type: 'checkout.session.completed' }),
      }),
      createMockEnv()
    )

    expect(res.status).toBe(400)
    const body = await res.json()
    expect(body.error.code).toBe('INVALID_SIGNATURE')
  })
})
