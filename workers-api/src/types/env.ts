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

  // KV Namespace (Cache) - Optional for now
  CACHE?: KVNamespace

  // Client Session Tracking
  CLIENT_SESSION_ID?: string

  // Optional: Durable Objects (if needed in the future)
  // CHAT_CACHE?: DurableObjectNamespace
}
