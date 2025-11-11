/**
 * 安全认证服务模块
 * 提供基于httpOnly cookie的安全认证功能，包括：
 * 1. 安全的用户注册和登录
 * 2. 基于内存的access token管理
 * 3. 自动CSRF保护
 * 4. 安全的token刷新机制
 *
 * 主要安全特性：
 * - Access token仅存储在内存中
 * - Refresh token存储在httpOnly cookie中
 * - 自动CSRF token管理
 * - 安全的请求拦截器
 */

import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'
import type {
  RegisterRequest,
  RegisterResponse,
  LoginRequest,
  LoginResponse,
  UserInfo,
  UserUpdate,
  PreferencesResponse,
  PreferencesUpdate,
  DataExportResponse,
  MigrationRequest,
  MigrationResponse,
} from '../types/auth'
import { getApiConfig } from '../utils/env'

const apiConfig = getApiConfig()

// 创建独立的axios实例用于安全认证API
const secureAuthApi = axios.create({
  baseURL: apiConfig.baseUrl,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30秒超时
  withCredentials: true, // 支持cookie
})

// ================================
// 内存中的认证状态管理
// ================================

interface AuthState {
  accessToken: string | null
  csrfToken: string | null
  user: UserInfo | null
  isAuthenticated: boolean
}

// 内存中的认证状态（页面刷新时重置）
let authState: AuthState = {
  accessToken: null,
  csrfToken: null,
  user: null,
  isAuthenticated: false,
}

// 认证状态变化监听器
type AuthStateListener = (state: AuthState) => void
const authStateListeners: AuthStateListener[] = []

// 通知所有监听器
const notifyAuthStateListeners = () => {
  authStateListeners.forEach(listener => listener({ ...authState }))
}

// 更新认证状态
const updateAuthState = (updates: Partial<AuthState>) => {
  authState = { ...authState, ...updates }
  notifyAuthStateListeners()
}

// ================================
// Access Token 内存管理
// ================================

/**
 * 设置Access Token（仅存储在内存中）
 */
export const setAccessToken = (token: string): void => {
  updateAuthState({ accessToken: token, isAuthenticated: true })
}

/**
 * 获取Access Token（从内存中）
 */
export const getAccessToken = (): string | null => {
  return authState.accessToken
}

/**
 * 移除Access Token
 */
export const removeAccessToken = (): void => {
  updateAuthState({ accessToken: null, isAuthenticated: false })
}

// ================================
// CSRF Token 管理
// ================================

/**
 * 设置CSRF Token
 */
export const setCsrfToken = (token: string): void => {
  updateAuthState({ csrfToken: token })
}

/**
 * 获取CSRF Token
 */
export const getCsrfToken = (): string | null => {
  return authState.csrfToken
}

/**
 * 移除CSRF Token
 */
export const removeCsrfToken = (): void => {
  updateAuthState({ csrfToken: null })
}

// ================================
// 用户信息管理
// ================================

/**
 * 设置用户信息
 */
export const setUser = (user: UserInfo): void => {
  updateAuthState({ user })
}

/**
 * 获取用户信息
 */
export const getUser = (): UserInfo | null => {
  return authState.user
}

/**
 * 移除用户信息
 */
export const removeUser = (): void => {
  updateAuthState({ user: null })
}

/**
 * 获取当前认证状态
 */
export const getAuthState = (): AuthState => {
  return { ...authState }
}

/**
 * 认证状态变化监听
 */
export const onAuthStateChange = (listener: AuthStateListener) => {
  authStateListeners.push(listener)

  // 返回取消监听的函数
  return () => {
    const index = authStateListeners.indexOf(listener)
    if (index > -1) {
      authStateListeners.splice(index, 1)
    }
  }
}

/**
 * 清除所有认证信息
 */
export const clearAuth = (): void => {
  updateAuthState({
    accessToken: null,
    csrfToken: null,
    user: null,
    isAuthenticated: false,
  })
}

// ================================
// 请求拦截器 - 自动添加Token和CSRF保护
// ================================

secureAuthApi.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // 添加Access Token到Authorization头部
    const token = getAccessToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    // 对于需要CSRF保护的请求方法，添加CSRF token
    const csrfProtectedMethods = ['post', 'put', 'delete', 'patch']
    if (config.method && csrfProtectedMethods.includes(config.method.toLowerCase())) {
      const csrfToken = getCsrfToken()
      if (csrfToken) {
        config.headers['X-CSRF-Token'] = csrfToken
      }
    }

    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// ================================
// 响应拦截器 - 自动处理Token刷新和CSRF
// ================================

let isRefreshing = false
let refreshSubscribers: Array<(token: string, csrfToken: string) => void> = []

// 订阅Token刷新
const subscribeTokenRefresh = (cb: (token: string, csrfToken: string) => void) => {
  refreshSubscribers.push(cb)
}

// 通知所有订阅者
const onTokenRefreshed = (token: string, csrfToken: string) => {
  refreshSubscribers.forEach((cb) => cb(token, csrfToken))
  refreshSubscribers = []
}

secureAuthApi.interceptors.response.use(
  (response) => {
    // 从响应中提取新的CSRF token
    const newCsrfToken = response.data?.csrf_token
    if (newCsrfToken) {
      setCsrfToken(newCsrfToken)
    }

    return response
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as any

    // 如果是401错误且不是刷新Token的请求
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // 如果正在刷新，等待刷新完成
        return new Promise((resolve) => {
          subscribeTokenRefresh((token: string, csrfToken: string) => {
            originalRequest.headers.Authorization = `Bearer ${token}`
            originalRequest.headers['X-CSRF-Token'] = csrfToken
            resolve(secureAuthApi(originalRequest))
          })
        })
      }

      originalRequest._retry = true
      isRefreshing = true

      try {
        const refreshData = await refreshAccessToken()
        const newAccessToken = refreshData.data?.access_token
        const newCsrfToken = refreshData.data?.csrf_token

        setAccessToken(newAccessToken)
        if (newCsrfToken) {
          setCsrfToken(newCsrfToken)
        }

        isRefreshing = false
        onTokenRefreshed(newAccessToken, newCsrfToken)

        // 重试原始请求
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`
        if (newCsrfToken) {
          originalRequest.headers['X-CSRF-Token'] = newCsrfToken
        }
        return secureAuthApi(originalRequest)
      } catch (refreshError) {
        // 刷新失败，清除认证信息
        clearAuth()
        isRefreshing = false
        refreshSubscribers = []
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  }
)

// ================================
// 安全认证API方法
// ================================

/**
 * 安全用户注册
 */
export const secureRegister = async (
  request: RegisterRequest
): Promise<RegisterResponse> => {
  const response = await secureAuthApi.post<RegisterResponse>(
    '/api/v1/auth/secure-register',
    request
  )

  const data = response.data.data
  if (data && data.access_token && data.csrf_token) {
    setAccessToken(data.access_token)
    setCsrfToken(data.csrf_token)

    if (data.user) {
      setUser({
        id: data.user.user_id || data.user.id,
        email: data.user.email,
        username: data.user.username || null,
        email_verified: false,
        created_at: new Date().toISOString(),
      })
    }
  }

  return data
}

/**
 * 安全用户登录
 */
export const secureLogin = async (request: LoginRequest): Promise<LoginResponse> => {
  const response = await secureAuthApi.post<LoginResponse>(
    '/api/v1/auth/secure-login',
    request
  )

  const data = response.data.data
  if (data && data.access_token && data.csrf_token) {
    setAccessToken(data.access_token)
    setCsrfToken(data.csrf_token)

    if (data.user) {
      setUser({
        id: data.user.id,
        email: data.user.email,
        username: data.user.username,
        email_verified: data.user.email_verified,
        created_at: new Date().toISOString(),
        last_login_at: new Date().toISOString(),
      })
    }
  }

  return data
}

/**
 * 安全Token刷新
 */
export const refreshAccessToken = async () => {
  const response = await secureAuthApi.post('/api/v1/auth/secure-refresh')
  return response.data
}

/**
 * 安全用户登出
 */
export const secureLogout = async (): Promise<void> => {
  try {
    await secureAuthApi.post('/api/v1/auth/secure-logout')
  } catch (error) {
    // 即使API调用失败，也清除本地状态
    console.error('Secure logout API error:', error)
  } finally {
    clearAuth()
  }
}

/**
 * 获取CSRF Token
 */
export const getCsrfTokenFromServer = async (): Promise<string> => {
  const response = await secureAuthApi.get('/api/v1/auth/csrf-token')
  const csrfToken = response.data.data?.csrf_token
  if (csrfToken) {
    setCsrfToken(csrfToken)
  }
  return csrfToken
}

/**
 * 验证认证状态
 */
export const verifyAuthentication = async (): Promise<boolean> => {
  try {
    const response = await secureAuthApi.get('/api/v1/auth/verify-auth')
    const data = response.data.data

    if (data && data.authenticated && data.user) {
      setUser({
        id: data.user.id,
        email: data.user.email,
        username: data.user.username,
        email_verified: data.user.email_verified,
        created_at: new Date().toISOString(),
      })
      updateAuthState({ isAuthenticated: true })
      return true
    }

    return false
  } catch (error) {
    updateAuthState({ isAuthenticated: false })
    return false
  }
}

/**
 * 检查是否有有效的认证信息
 */
export const hasValidAuth = (): boolean => {
  return !!(getAccessToken() && getCsrfToken())
}

// ================================
// 初始化认证状态（页面加载时）
// ================================

/**
 * 初始化认证状态
 * 尝试从服务器验证现有的认证状态
 */
export const initializeAuth = async (): Promise<boolean> => {
  try {
    // 首先获取CSRF token
    await getCsrfTokenFromServer()

    // 然后验证认证状态
    const isValid = await verifyAuthentication()

    if (isValid) {
      console.log('认证状态初始化成功')
    } else {
      console.log('用户未认证，清除本地状态')
      clearAuth()
    }

    return isValid
  } catch (error) {
    console.warn('认证状态初始化失败:', error)
    clearAuth()
    return false
  }
}

// ================================
// 兼容性方法（用于现有代码迁移）
// ================================

/**
 * 检查用户是否已认证
 */
export const isAuthenticated = (): boolean => {
  return authState.isAuthenticated && hasValidAuth()
}

/**
 * 导出安全认证API实例
 */
export default secureAuthApi