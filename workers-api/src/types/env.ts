/**
 * Cloudflare Workers Environment Bindings
 * Define all environment variables and bindings here
 */

export interface Env {
  // Environment
  ENVIRONMENT: 'development' | 'production'

  // Supabase
  SUPABASE_URL: string
  SUPABASE_ANON_KEY: string
  SUPABASE_SERVICE_ROLE_KEY?: string

  // OpenRouter API
  OPENROUTER_API_KEY: string

  // Search API Keys (at least one recommended)
  BRAVE_SEARCH_API_KEY?: string
  TAVILY_API_KEY?: string
  SERPER_API_KEY?: string

  // GitHub API
  GITHUB_TOKEN?: string

  // KV Namespace (Cache) - Optional for now
  CACHE?: KVNamespace

  // OpenRouter Circuit Breaker State (Optional)
  OPENROUTER_CIRCUIT_STATE?: KVNamespace

  // Sentry Error Monitoring (Optional)
  SENTRY_DSN?: string
  SENTRY_TRACES_SAMPLE_RATE?: string // Performance monitoring sample rate (0.0-1.0)

  // Supabase Auth (JWT verification)
  SUPABASE_JWT_SECRET?: string

  // Stripe (Subscription billing)
  STRIPE_SECRET_KEY?: string
  STRIPE_WEBHOOK_SECRET?: string
  STRIPE_PRO_PRICE_ID?: string
  STRIPE_TEAM_PRICE_ID?: string

  // VAPID (Web Push)
  VAPID_PUBLIC_KEY?: string
  VAPID_PRIVATE_KEY?: string
  VAPID_SUBJECT?: string

  // CryptoPanic (News)
  CRYPTOPANIC_API_KEY?: string

  // Client Session Tracking
  CLIENT_SESSION_ID?: string

  // Optional: Durable Objects (if needed in the future)
  // CHAT_CACHE?: DurableObjectNamespace

  // Performance monitoring thresholds (milliseconds)
  REQUEST_SLOW_THRESHOLD_MS?: string
  REQUEST_WARN_THRESHOLD_MS?: string
}
