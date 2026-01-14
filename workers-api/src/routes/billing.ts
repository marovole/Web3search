import { Hono } from 'hono'
import Stripe from 'stripe'
import type { Env } from '../types/env'
import { authMiddleware, getCurrentUser } from '../middlewares/auth'
import { getSupabaseClient } from '../lib/supabase'

const billing = new Hono<{ Bindings: Env }>()

function getStripe(env: Env): Stripe {
  if (!env.STRIPE_SECRET_KEY) {
    throw new Error('STRIPE_SECRET_KEY is not configured')
  }
  return new Stripe(env.STRIPE_SECRET_KEY)
}

billing.post('/checkout', authMiddleware(), async (c) => {
  const user = getCurrentUser(c)
  if (!user) {
    return c.json({ error: { code: 'NOT_AUTHENTICATED', message: 'Not authenticated', status: 401 } }, 401)
  }

  const body = await c.req.json<{
    plan: 'pro' | 'team'
    interval?: 'month' | 'year'
    success_url?: string
    cancel_url?: string
  }>()

  if (!body.plan || !['pro', 'team'].includes(body.plan)) {
    return c.json({ error: { code: 'INVALID_PLAN', message: 'Plan must be "pro" or "team"', status: 400 } }, 400)
  }

  const stripe = getStripe(c.env)
  const supabase = getSupabaseClient(c.env, true)

  const { data: profile } = await supabase.from('user_profiles').select('stripe_customer_id').eq('id', user.id).single()

  let customerId = profile?.stripe_customer_id

  if (!customerId) {
    const customer = await stripe.customers.create({
      email: user.email,
      metadata: { user_id: user.id },
    })
    customerId = customer.id

    await supabase.from('user_profiles').update({ stripe_customer_id: customerId }).eq('id', user.id)
  }

  const priceId = body.plan === 'pro' ? c.env.STRIPE_PRO_PRICE_ID : c.env.STRIPE_TEAM_PRICE_ID

  if (!priceId) {
    return c.json(
      { error: { code: 'PRICE_NOT_CONFIGURED', message: `Price for ${body.plan} plan is not configured`, status: 500 } },
      500
    )
  }

  const baseUrl = c.req.header('origin') || 'https://web3search.pages.dev'

  const session = await stripe.checkout.sessions.create({
    customer: customerId as string,
    mode: 'subscription',
    line_items: [{ price: priceId, quantity: 1 }],
    success_url: body.success_url || `${baseUrl}/settings/billing?success=true`,
    cancel_url: body.cancel_url || `${baseUrl}/settings/billing?canceled=true`,
    metadata: { user_id: user.id, plan: body.plan },
    subscription_data: { metadata: { user_id: user.id, plan: body.plan } },
  })

  return c.json({ checkout_url: session.url, session_id: session.id })
})

billing.post('/portal', authMiddleware(), async (c) => {
  const user = getCurrentUser(c)
  if (!user) {
    return c.json({ error: { code: 'NOT_AUTHENTICATED', message: 'Not authenticated', status: 401 } }, 401)
  }

  const supabase = getSupabaseClient(c.env)
  const { data: profile } = await supabase.from('user_profiles').select('stripe_customer_id').eq('id', user.id).single()

  const profileData = profile as { stripe_customer_id?: string } | null
  if (!profileData?.stripe_customer_id) {
    return c.json({ error: { code: 'NO_SUBSCRIPTION', message: 'No active subscription found', status: 404 } }, 404)
  }

  const stripe = getStripe(c.env)
  const baseUrl = c.req.header('origin') || 'https://web3search.pages.dev'

  const session = await stripe.billingPortal.sessions.create({
    customer: profileData.stripe_customer_id,
    return_url: `${baseUrl}/settings/billing`,
  })

  return c.json({ portal_url: session.url })
})

billing.post('/webhook', async (c) => {
  const stripe = getStripe(c.env)
  const signature = c.req.header('stripe-signature')

  if (!signature) {
    return c.json({ error: { code: 'MISSING_SIGNATURE', message: 'Stripe signature required', status: 400 } }, 400)
  }

  if (!c.env.STRIPE_WEBHOOK_SECRET) {
    console.error('[Billing] STRIPE_WEBHOOK_SECRET not configured')
    return c.json({ error: { code: 'WEBHOOK_NOT_CONFIGURED', message: 'Webhook not configured', status: 500 } }, 500)
  }

  const body = await c.req.text()

  let event: Stripe.Event
  try {
    event = stripe.webhooks.constructEvent(body, signature, c.env.STRIPE_WEBHOOK_SECRET)
  } catch (err) {
    console.error('[Billing] Webhook signature verification failed:', err)
    return c.json({ error: { code: 'INVALID_SIGNATURE', message: 'Invalid webhook signature', status: 400 } }, 400)
  }

  const supabase = getSupabaseClient(c.env, true)

  try {
    switch (event.type) {
      case 'checkout.session.completed': {
        const session = event.data.object as Stripe.Checkout.Session
        await handleCheckoutCompleted(supabase, stripe, session)
        break
      }

      case 'customer.subscription.updated': {
        const subscription = event.data.object as Stripe.Subscription
        await handleSubscriptionUpdated(supabase, subscription)
        break
      }

      case 'customer.subscription.deleted': {
        const subscription = event.data.object as Stripe.Subscription
        await handleSubscriptionDeleted(supabase, subscription)
        break
      }

      case 'invoice.paid': {
        const invoice = event.data.object as Stripe.Invoice
        console.log('[Billing] Invoice paid:', invoice.id)
        break
      }

      case 'invoice.payment_failed': {
        const invoice = event.data.object as Stripe.Invoice
        console.warn('[Billing] Invoice payment failed:', invoice.id)
        break
      }

      default:
        console.log('[Billing] Unhandled event type:', event.type)
    }
  } catch (err) {
    console.error('[Billing] Error processing webhook:', err)
    return c.json({ error: { code: 'PROCESSING_ERROR', message: 'Error processing webhook', status: 500 } }, 500)
  }

  return c.json({ received: true })
})

async function handleCheckoutCompleted(
  supabase: ReturnType<typeof getSupabaseClient>,
  stripe: Stripe,
  session: Stripe.Checkout.Session
) {
  const userId = session.metadata?.user_id
  const plan = session.metadata?.plan as 'pro' | 'team' | undefined

  if (!userId || !plan) {
    console.error('[Billing] Missing metadata in checkout session:', session.id)
    return
  }

  const subscriptionId = session.subscription as string
  const subscriptionResponse = await stripe.subscriptions.retrieve(subscriptionId)
  const subscription = subscriptionResponse as unknown as {
    status: string
    items: { data: Array<{ price: { id: string; product: string } }> }
    current_period_start: number
    current_period_end: number
    cancel_at_period_end: boolean
  }

  await supabase
    .from('user_profiles')
    .update({
      plan,
      stripe_customer_id: session.customer as string,
    })
    .eq('id', userId)

  await supabase.from('subscriptions').upsert({
    id: subscriptionId,
    user_id: userId,
    status: subscription.status,
    price_id: subscription.items.data[0]?.price.id,
    product_id: subscription.items.data[0]?.price.product as string,
    current_period_start: new Date(subscription.current_period_start * 1000).toISOString(),
    current_period_end: new Date(subscription.current_period_end * 1000).toISOString(),
    cancel_at_period_end: subscription.cancel_at_period_end,
  })

  console.log('[Billing] Checkout completed for user:', userId, 'plan:', plan)
}

async function handleSubscriptionUpdated(supabase: ReturnType<typeof getSupabaseClient>, subscription: Stripe.Subscription) {
  const userId = subscription.metadata?.user_id
  if (!userId) {
    console.error('[Billing] Missing user_id in subscription metadata:', subscription.id)
    return
  }

  const sub = subscription as unknown as {
    current_period_start: number
    current_period_end: number
    cancel_at_period_end: boolean
    canceled_at: number | null
    status: string
    id: string
    metadata: { plan?: string; user_id?: string }
  }

  await supabase
    .from('subscriptions')
    .update({
      status: sub.status,
      current_period_start: new Date(sub.current_period_start * 1000).toISOString(),
      current_period_end: new Date(sub.current_period_end * 1000).toISOString(),
      cancel_at_period_end: sub.cancel_at_period_end,
      canceled_at: sub.canceled_at ? new Date(sub.canceled_at * 1000).toISOString() : null,
    })
    .eq('id', sub.id)

  if (sub.status === 'active') {
    const plan = sub.metadata?.plan as 'pro' | 'team' | undefined
    if (plan) {
      await supabase.from('user_profiles').update({ plan }).eq('id', userId)
    }
  }

  console.log('[Billing] Subscription updated:', sub.id, 'status:', sub.status)
}

async function handleSubscriptionDeleted(supabase: ReturnType<typeof getSupabaseClient>, subscription: Stripe.Subscription) {
  const userId = subscription.metadata?.user_id
  if (!userId) {
    console.error('[Billing] Missing user_id in subscription metadata:', subscription.id)
    return
  }

  await supabase
    .from('subscriptions')
    .update({
      status: 'canceled',
      canceled_at: new Date().toISOString(),
    })
    .eq('id', subscription.id)

  await supabase.from('user_profiles').update({ plan: 'free' }).eq('id', userId)

  console.log('[Billing] Subscription deleted, user downgraded to free:', userId)
}

billing.get('/subscription', authMiddleware(), async (c) => {
  const user = getCurrentUser(c)
  if (!user) {
    return c.json({ error: { code: 'NOT_AUTHENTICATED', message: 'Not authenticated', status: 401 } }, 401)
  }

  const supabase = getSupabaseClient(c.env)

  const { data: subscription } = await supabase
    .from('subscriptions')
    .select('*')
    .eq('user_id', user.id)
    .in('status', ['active', 'trialing', 'past_due'])
    .order('created_at', { ascending: false })
    .limit(1)
    .single()

  if (!subscription) {
    return c.json({ subscription: null, plan: 'free' })
  }

  return c.json({
    subscription: {
      id: subscription.id,
      status: subscription.status,
      current_period_end: subscription.current_period_end,
      cancel_at_period_end: subscription.cancel_at_period_end,
    },
    plan: user.plan || 'free',
  })
})

export default billing
