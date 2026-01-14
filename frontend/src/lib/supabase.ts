import { createClient, SupabaseClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env?.VITE_SUPABASE_URL ?? ''
const supabaseAnonKey = import.meta.env?.VITE_SUPABASE_ANON_KEY ?? ''

export const isSupabaseConfigured = !!(supabaseUrl && supabaseAnonKey)

if (!isSupabaseConfigured) {
  console.warn('[Supabase] Missing environment variables. Auth features are disabled.')
}

let supabaseClient: any = null

if (isSupabaseConfigured) {
  supabaseClient = createClient(supabaseUrl, supabaseAnonKey, {
    auth: {
      autoRefreshToken: true,
      persistSession: true,
      detectSessionInUrl: true,
    },
  })
}

export const supabase = supabaseClient
export default supabase
