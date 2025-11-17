/**
 * Supabase Client Configuration
 * Initialize and export Supabase client for Workers
 */

import { createClient, SupabaseClient } from '@supabase/supabase-js'
import type { Env } from '../types/env'

/**
 * Module-scoped client cache for connection reuse
 * Workers can reuse clients across multiple requests to the same edge instance
 */
interface SupabaseClientCache {
  anon?: { client: SupabaseClient; url: string; key: string }
  service?: { client: SupabaseClient; url: string; key: string }
}

declare global {
  var __supabaseClients: SupabaseClientCache | undefined
}

/**
 * Get cached Supabase client instance (recommended for production)
 * Reuses client across requests to the same Worker instance
 *
 * @param env - Cloudflare Workers environment bindings
 * @param useServiceRole - Use service role key for admin operations (default: false)
 * @returns Cached or new Supabase client instance
 */
export function getSupabaseClient(
  env: Env,
  useServiceRole: boolean = false
): SupabaseClient {
  const supabaseUrl = env.SUPABASE_URL
  const supabaseKey = useServiceRole
    ? env.SUPABASE_SERVICE_ROLE_KEY || env.SUPABASE_ANON_KEY
    : env.SUPABASE_ANON_KEY

  if (!supabaseUrl) {
    throw new Error('SUPABASE_URL environment variable is not set')
  }

  if (!supabaseKey) {
    throw new Error(
      useServiceRole
        ? 'SUPABASE_SERVICE_ROLE_KEY environment variable is not set'
        : 'SUPABASE_ANON_KEY environment variable is not set'
    )
  }

  // Initialize cache if needed
  if (!globalThis.__supabaseClients) {
    globalThis.__supabaseClients = {}
  }

  const cache = globalThis.__supabaseClients
  const cacheKey = useServiceRole ? 'service' : 'anon'
  const cached = cache[cacheKey]

  // Return cached client if credentials match
  if (cached && cached.url === supabaseUrl && cached.key === supabaseKey) {
    return cached.client
  }

  // Create new client and cache it
  const client = createClient(supabaseUrl, supabaseKey, {
    auth: {
      persistSession: false,
      autoRefreshToken: false,
    },
  })

  cache[cacheKey] = { client, url: supabaseUrl, key: supabaseKey }
  return client
}

/**
 * Create Supabase client instance (legacy, use getSupabaseClient instead)
 * Only use this when you need a fresh client instance
 *
 * @param env - Cloudflare Workers environment bindings
 * @param useServiceRole - Use service role key for admin operations (default: false)
 * @returns Supabase client instance
 */
export function createSupabaseClient(
  env: Env,
  useServiceRole: boolean = false
): SupabaseClient {
  const supabaseUrl = env.SUPABASE_URL
  const supabaseKey = useServiceRole
    ? env.SUPABASE_SERVICE_ROLE_KEY || env.SUPABASE_ANON_KEY
    : env.SUPABASE_ANON_KEY

  if (!supabaseUrl) {
    throw new Error('SUPABASE_URL environment variable is not set')
  }

  if (!supabaseKey) {
    throw new Error(
      useServiceRole
        ? 'SUPABASE_SERVICE_ROLE_KEY environment variable is not set'
        : 'SUPABASE_ANON_KEY environment variable is not set'
    )
  }

  return createClient(supabaseUrl, supabaseKey, {
    auth: {
      persistSession: false,
      autoRefreshToken: false,
    },
  })
}

/**
 * Performance threshold for slow queries (milliseconds)
 */
const SLOW_QUERY_THRESHOLD = 1000 // 1 second

/**
 * Test database connection
 * Uses cached client for better performance
 *
 * @param env - Cloudflare Workers environment bindings
 * @returns True if connection is successful
 */
export async function testDatabaseConnection(env: Env): Promise<boolean> {
  const startTime = Date.now()

  try {
    // Use cached client to avoid creating new instance on every health check
    const supabase = getSupabaseClient(env)

    // Simple query to test connection - just count any table
    const { data, error } = await supabase
      .from('conversations')
      .select('id', { count: 'exact', head: true })
      .limit(1)

    const queryDuration = Date.now() - startTime

    // Structured database query log
    const dbLog = {
      query: 'testDatabaseConnection',
      table: 'conversations',
      durationMs: queryDuration,
      slow: queryDuration > SLOW_QUERY_THRESHOLD,
    }

    if (dbLog.slow) {
      console.warn('[SLOW QUERY]', JSON.stringify(dbLog))
    } else {
      console.log('[DB QUERY]', JSON.stringify(dbLog))
    }

    // Helper to log structured database session state
    const logState = (status: string, detail?: string) =>
      console.log('[DB SESSION STATE]', JSON.stringify({
        query: 'testDatabaseConnection',
        table: 'conversations',
        status,
        detail,
      }))

    // If error code is PGRST116, it means table doesn't exist but connection works
    // Any other error or no error means connection is successful
    if (error) {
      console.log('[DB QUERY ERROR]', JSON.stringify({
        query: 'testDatabaseConnection',
        table: 'conversations',
        error: {
          code: error.code,
          message: error.message,
        },
      }))

      // Empty message usually means RLS is blocking access (connection OK, permissions issue)
      if (!error.message || error.message === '') {
        logState('rls-blocking', 'empty-message')
        return true
      }

      // PGRST116 = table/view doesn't exist (connection OK, table missing)
      // PGRST301 = RLS prevents access (connection OK, permissions issue)
      // 42P01 = PostgreSQL: relation does not exist
      if (error.code === 'PGRST116' || error.code === 'PGRST301' || error.code === '42P01') {
        logState('table-limited', error.code)
        return true
      }

      console.error('[DB CONNECTION ERROR]', JSON.stringify({
        code: error.code,
        message: error.message,
      }))
      return false
    }

    logState('ok')
    return true
  } catch (error) {
    console.error('[DB CONNECTION ERROR]', JSON.stringify({ error }))
    return false
  }
}
