/**
 * 认证上下文
 * 提供全局认证状态管理和认证相关功能
 */
import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react'
import {
  register as apiRegister,
  login as apiLogin,
  logout as apiLogout,
  getCurrentUser as apiGetCurrentUser,
  getAccessToken,
  getUser,
  setUser,
  clearAuth,
  type UserInfo,
  type RegisterRequest,
  type LoginRequest,
} from '../services/auth'

interface AuthContextType {
  // 状态
  isAuthenticated: boolean
  user: UserInfo | null
  loading: boolean

  // 方法
  register: (request: RegisterRequest) => Promise<void>
  login: (request: LoginRequest) => Promise<void>
  logout: () => Promise<void>
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

interface AuthProviderProps {
  children: ReactNode
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false)
  const [user, setUserState] = useState<UserInfo | null>(null)
  const [loading, setLoading] = useState<boolean>(true)

  // 初始化：检查是否有已保存的认证信息
  useEffect(() => {
    const initAuth = async () => {
      try {
        const token = getAccessToken()
        const savedUser = getUser()

        if (token && savedUser) {
          // 有Token和用户信息，验证Token是否有效
          try {
            const currentUser = await apiGetCurrentUser()
            setUserState(currentUser)
            setIsAuthenticated(true)
          } catch (error) {
            // Token无效，清除认证信息
            clearAuth()
            setIsAuthenticated(false)
            setUserState(null)
          }
        } else {
          setIsAuthenticated(false)
          setUserState(null)
        }
      } catch (error) {
        console.error('初始化认证失败:', error)
        clearAuth()
        setIsAuthenticated(false)
        setUserState(null)
      } finally {
        setLoading(false)
      }
    }

    initAuth()
  }, [])

  // 注册
  const handleRegister = useCallback(async (request: RegisterRequest) => {
    try {
      const response = await apiRegister(request)
      setUserState({
        id: response.user_id,
        email: response.email,
        username: response.username || null,
        email_verified: false,
        created_at: new Date().toISOString(),
      })
      setIsAuthenticated(true)
    } catch (error) {
      console.error('注册失败:', error)
      throw error
    }
  }, [])

  // 登录
  const handleLogin = useCallback(async (request: LoginRequest) => {
    try {
      const response = await apiLogin(request)
      setUserState({
        id: response.user.id,
        email: response.user.email,
        username: response.user.username,
        email_verified: response.user.email_verified,
        created_at: response.user.created_at || new Date().toISOString(),
        last_login_at: response.user.last_login_at,
      })
      setIsAuthenticated(true)
    } catch (error) {
      console.error('登录失败:', error)
      throw error
    }
  }, [])

  // 登出
  const handleLogout = useCallback(async () => {
    try {
      await apiLogout()
    } catch (error) {
      console.error('登出失败:', error)
    } finally {
      clearAuth()
      setIsAuthenticated(false)
      setUserState(null)
    }
  }, [])

  // 刷新用户信息
  const handleRefreshUser = useCallback(async () => {
    try {
      const currentUser = await apiGetCurrentUser()
      setUserState(currentUser)
    } catch (error) {
      console.error('刷新用户信息失败:', error)
      // 如果刷新失败，可能是Token过期，清除认证信息
      clearAuth()
      setIsAuthenticated(false)
      setUserState(null)
      throw error
    }
  }, [])

  const value: AuthContextType = {
    isAuthenticated,
    user,
    loading,
    register: handleRegister,
    login: handleLogin,
    logout: handleLogout,
    refreshUser: handleRefreshUser,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

/**
 * 使用认证上下文
 */
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth必须在AuthProvider内部使用')
  }
  return context
}

/**
 * 要求认证的Hook
 * 如果未登录，会重定向到登录页面
 * 返回用户信息和加载状态
 */
export const useRequireAuth = (): { user: UserInfo; loading: boolean } => {
  const { isAuthenticated, user, loading } = useAuth()

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      // 重定向到登录页面
      window.location.href = '/auth/login'
    }
  }, [isAuthenticated, loading])

  return {
    user: user!,
    loading,
  }
}

