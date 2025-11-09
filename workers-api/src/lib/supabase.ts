/**
 * Supabase Client Configuration
 * Initialize and export Supabase client for Workers
 */

import { createClient, SupabaseClient } from '@supabase/supabase-js'
import type { Env } from '../types/env'

/**
 * Create Supabase client instance
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
 * Test database connection
 * @param env - Cloudflare Workers environment bindings
 * @returns True if connection is successful
 */
export async function testDatabaseConnection(env: Env): Promise<boolean> {
  try {
    const supabase = createSupabaseClient(env)

    // Simple query to test connection - just count any table
    const { data, error } = await supabase
      .from('conversations')
      .select('id', { count: 'exact', head: true })
      .limit(1)

    // If error code is PGRST116, it means table doesn't exist but connection works
    // Any other error or no error means connection is successful
    if (error) {
      console.log('Database query error:', JSON.stringify(error, null, 2))

      // Empty message usually means RLS is blocking access (connection OK, permissions issue)
      if (!error.message || error.message === '') {
        console.log('Database connection OK (RLS blocking access)')
        return true
      }

      // PGRST116 = table/view doesn't exist (connection OK, table missing)
      // PGRST301 = RLS prevents access (connection OK, permissions issue)
      // 42P01 = PostgreSQL: relation does not exist
      if (error.code === 'PGRST116' || error.code === 'PGRST301' || error.code === '42P01') {
        console.log('Database connection OK (table access limited)')
        return true
      }

      console.error('Database connection test failed:', error.code, error.message)
      return false
    }

    console.log('Database connection test successful')
    return true
  } catch (error) {
    console.error('Database connection test error:', error)
    return false
  }
}
