import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react'
import type { User, Session } from '@supabase/supabase-js'
import { supabase } from '@/lib/supabase'

interface UserProfile {
  id: string
  username: string | null
  display_name: string | null
  avatar_url: string | null
  plan: 'free' | 'pro' | 'team'
  risk_preference: 'conservative' | 'moderate' | 'aggressive'
  notification_settings: Record<string, boolean>
  timezone: string
  language: string
  theme: 'light' | 'dark' | 'system'
  onboarding_completed: boolean
  created_at?: string
}

interface UserQuota {
  watchlist: { used: number; limit: number }
  agents: { used: number; limit: number }
  daily: {
    alerts: { used: number; limit: number }
    deep_research: { used: number; limit: number }
    quick_chat: { used: number; limit: number }
  }
  monthly: {
    reports: { used: number; limit: number }
  }
  resets?: {
    daily: string
    monthly: string
  }
}

interface AuthContextType {
  user: User | null
  session: Session | null
  profile: UserProfile | null
  quota: UserQuota | null
  loading: boolean
  isAuthenticated: boolean
  signUp: (email: string, password: string) => Promise<{ error: Error | null }>
  signIn: (email: string, password: string) => Promise<{ error: Error | null }>
  signOut: () => Promise<void>
  refreshProfile: () => Promise<void>
  updateProfile: (updates: Partial<UserProfile>) => Promise<{ error: Error | null }>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

interface AuthProviderProps {
  children: ReactNode
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [session, setSession] = useState<Session | null>(null)
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [quota, setQuota] = useState<UserQuota | null>(null)
  const [loading, setLoading] = useState(true)

  const fetchUserData = useCallback(async (accessToken: string) => {
    try {
      const apiUrl = import.meta.env.VITE_API_BASE_URL || ''
      const response = await fetch(`${apiUrl}/api/v1/auth/me`, {
        headers: { Authorization: `Bearer ${accessToken}` },
      })

      if (response.ok) {
        const data = await response.json()
        setProfile(data.user)
        setQuota(data.quota)
      }
    } catch (error) {
      console.error('[Auth] Failed to fetch user data:', error)
    }
  }, [])

  useEffect(() => {
    if (!supabase) {
      setLoading(false)
      return
    }

    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session)
      setUser(session?.user ?? null)
      if (session?.access_token) {
        fetchUserData(session.access_token)
      }
      setLoading(false)
    })

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(async (event, session) => {
      setSession(session)
      setUser(session?.user ?? null)

      if (event === 'SIGNED_IN' && session?.access_token) {
        await fetchUserData(session.access_token)
      } else if (event === 'SIGNED_OUT') {
        setProfile(null)
        setQuota(null)
      }
    })

    return () => subscription.unsubscribe()
  }, [fetchUserData])

  const signUp = useCallback(async (email: string, password: string) => {
    if (!supabase) return { error: new Error('Auth service unavailable') }
    const { error } = await supabase.auth.signUp({ email, password })
    return { error: error as Error | null }
  }, [])

  const signIn = useCallback(async (email: string, password: string) => {
    if (!supabase) return { error: new Error('Auth service unavailable') }
    const { error } = await supabase.auth.signInWithPassword({ email, password })
    return { error: error as Error | null }
  }, [])

  const signOut = useCallback(async () => {
    if (supabase) {
      await supabase.auth.signOut()
    }
    setProfile(null)
    setQuota(null)
  }, [])

  const refreshProfile = useCallback(async () => {
    if (session?.access_token) {
      await fetchUserData(session.access_token)
    }
  }, [session?.access_token, fetchUserData])

  const updateProfile = useCallback(
    async (updates: Partial<UserProfile>) => {
      if (!session?.access_token) {
        return { error: new Error('Not authenticated') }
      }

      try {
        const apiUrl = import.meta.env.VITE_API_BASE_URL || ''
        const response = await fetch(`${apiUrl}/api/v1/users/profile`, {
          method: 'PATCH',
          headers: {
            Authorization: `Bearer ${session.access_token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(updates),
        })

        if (!response.ok) {
          const data = await response.json()
          return { error: new Error(data.error?.message || 'Failed to update profile') }
        }

        const data = await response.json()
        setProfile(data.profile)
        return { error: null }
      } catch (error) {
        return { error: error as Error }
      }
    },
    [session?.access_token]
  )

  const value: AuthContextType = {
    user,
    session,
    profile,
    quota,
    loading,
    isAuthenticated: !!user,
    signUp,
    signIn,
    signOut,
    refreshProfile,
    updateProfile,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export const useRequireAuth = (): { user: User; profile: UserProfile | null; loading: boolean } => {
  const { user, profile, loading, isAuthenticated } = useAuth()

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      window.location.href = '/auth/login'
    }
  }, [isAuthenticated, loading])

  return {
    user: user!,
    profile,
    loading,
  }
}
