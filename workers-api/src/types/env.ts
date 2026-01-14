export interface Env {
  ENVIRONMENT: 'development' | 'production'

  CONVEX_URL: string
  CONVEX_DEPLOY_KEY?: string

  OPENROUTER_API_KEY: string

  BRAVE_SEARCH_API_KEY?: string
  TAVILY_API_KEY?: string
  SERPER_API_KEY?: string

  GITHUB_TOKEN?: string

  CACHE?: KVNamespace

  MULTI_AGENT_TASKS?: KVNamespace

  OPENROUTER_CIRCUIT_STATE?: KVNamespace

  SENTRY_DSN?: string
  SENTRY_TRACES_SAMPLE_RATE?: string

  JWT_SECRET?: string

  STRIPE_SECRET_KEY?: string
  STRIPE_WEBHOOK_SECRET?: string
  STRIPE_PRO_PRICE_ID?: string
  STRIPE_TEAM_PRICE_ID?: string

  VAPID_PUBLIC_KEY?: string
  VAPID_PRIVATE_KEY?: string
  VAPID_SUBJECT?: string

  CRYPTOPANIC_API_KEY?: string

  CLIENT_SESSION_ID?: string

  REQUEST_SLOW_THRESHOLD_MS?: string
  REQUEST_WARN_THRESHOLD_MS?: string
}
