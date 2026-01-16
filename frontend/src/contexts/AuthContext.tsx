import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react'
import { useConvexAuth, useQuery } from 'convex/react'
import { useAuthActions, useAuthToken } from '@convex-dev/auth/react'
import { api } from '../../convex/_generated/api'
import type { Id } from '../../convex/_generated/dataModel'

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

interface ConvexUser {
  _id: Id<'users'>
  email?: string
  username?: string
  name?: string
  image?: string
  tokenIdentifier: string
}

interface AuthContextType {
  user: ConvexUser | null
  userId: Id<'users'> | null
  profile: UserProfile | null
  quota: UserQuota | null
  loading: boolean
  isAuthenticated: boolean
  token: string | null
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
  const { isLoading: convexLoading, isAuthenticated: convexAuthenticated } = useConvexAuth()
  const { signIn: convexSignIn, signOut: convexSignOut } = useAuthActions()
  const token = useAuthToken()

  const [user, setUser] = useState<ConvexUser | null>(null)
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [quota, setQuota] = useState<UserQuota | null>(null)
  const [loading, setLoading] = useState(true)
  const [clientSessionId] = useState(() => {
    const stored = localStorage.getItem('client_session_id')
    if (stored) return stored
    const newId = crypto.randomUUID()
    localStorage.setItem('client_session_id', newId)
    return newId
  })

  useEffect(() => {
    if (!convexLoading) {
      setLoading(false)
    }
  }, [convexLoading])

  const signUp = useCallback(async (email: string, password: string) => {
    try {
      const result = await convexSignIn('password', {
        email,
        password,
        flow: 'signUp'
      })
      if (!result.signingIn) {
        return { error: new Error('注册失败，请检查邮箱是否已被使用') }
      }
      return { error: null }
    } catch (err) {
      const error = err instanceof Error ? err : new Error('注册过程中发生错误')
      return { error }
    }
  }, [convexSignIn])

  const signIn = useCallback(async (email: string, password: string) => {
    try {
      const result = await convexSignIn('password', {
        email,
        password,
        flow: 'signIn'
      })
      if (!result.signingIn) {
        return { error: new Error('登录失败，请检查邮箱和密码') }
      }
      return { error: null }
    } catch (err) {
      const error = err instanceof Error ? err : new Error('登录过程中发生错误')
      return { error }
    }
  }, [convexSignIn])

  const signOut = useCallback(async () => {
    try {
      await convexSignOut()
    } finally {
      setUser(null)
      setProfile(null)
      setQuota(null)
      localStorage.removeItem('client_session_id')
    }
  }, [convexSignOut])

  const refreshProfile = useCallback(async () => {
    // Profile is refreshed automatically via Convex reactive queries
  }, [])

  const updateProfile = useCallback(async (_updates: Partial<UserProfile>) => {
    // TODO: Implement profile updates via Convex mutation
    return { error: new Error('Profile updates not implemented yet') }
  }, [])

  const value: AuthContextType = {
    user,
    userId: user?._id ?? null,
    profile,
    quota,
    loading,
    isAuthenticated: convexAuthenticated,
    token,
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

export const useRequireAuth = (): { user: ConvexUser | null; profile: UserProfile | null; loading: boolean } => {
  const { user, profile, loading, isAuthenticated } = useAuth()

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      window.location.href = '/auth/login'
    }
  }, [isAuthenticated, loading])

  return {
    user,
    profile,
    loading,
  }
}

export const useClientSession = () => {
  const [clientSessionId] = useState(() => {
    const stored = localStorage.getItem('client_session_id')
    if (stored) return stored
    const newId = crypto.randomUUID()
    localStorage.setItem('client_session_id', newId)
    return newId
  })

  return { clientSessionId }
}
