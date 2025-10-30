/**
 * 认证服务模块
 * 提供用户注册、登录、Token管理和自动刷新功能
 */
import axios, { AxiosError } from 'axios'
import type {
  RegisterRequest,
  RegisterResponse,
  LoginRequest,
  LoginResponse,
  RefreshTokenRequest,
  RefreshTokenResponse,
  ForgotPasswordRequest,
  ForgotPasswordResponse,
  ResetPasswordRequest,
  ResetPasswordResponse,
  UserInfo,
  UserUpdate,
  PreferencesResponse,
  PreferencesUpdate,
  DataExportResponse,
  MigrationRequest,
  MigrationResponse,
} from '../types/auth'
import { TOKEN_STORAGE_KEY, REFRESH_TOKEN_STORAGE_KEY, USER_STORAGE_KEY } from '../types/auth'
import { getApiConfig } from '../utils/env'

const apiConfig = getApiConfig()

// 创建独立的axios实例用于认证API
const authApi = axios.create({
  baseURL: apiConfig.baseUrl,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30秒超时
})

// Token刷新状态标志，防止并发刷新
let isRefreshing = false
let refreshSubscribers: Array<(token: string) => void> = []

// 订阅Token刷新
const subscribeTokenRefresh = (cb: (token: string) => void) => {
  refreshSubscribers.push(cb)
}

// 通知所有订阅者
const onTokenRefreshed = (token: string) => {
  refreshSubscribers.forEach((cb) => cb(token))
  refreshSubscribers = []
}

// ================================
// Token存储管理
// ================================

/**
 * 存储Access Token
 */
export const setAccessToken = (token: string): void => {
  localStorage.setItem(TOKEN_STORAGE_KEY, token)
}

/**
 * 获取Access Token
 */
export const getAccessToken = (): string | null => {
  return localStorage.getItem(TOKEN_STORAGE_KEY)
}

/**
 * 移除Access Token
 */
export const removeAccessToken = (): void => {
  localStorage.removeItem(TOKEN_STORAGE_KEY)
}

/**
 * 存储Refresh Token
 */
export const setRefreshToken = (token: string): void => {
  localStorage.setItem(REFRESH_TOKEN_STORAGE_KEY, token)
}

/**
 * 获取Refresh Token
 */
export const getRefreshToken = (): string | null => {
  return localStorage.getItem(REFRESH_TOKEN_STORAGE_KEY)
}

/**
 * 移除Refresh Token
 */
export const removeRefreshToken = (): void => {
  localStorage.removeItem(REFRESH_TOKEN_STORAGE_KEY)
}

/**
 * 存储用户信息
 */
export const setUser = (user: UserInfo): void => {
  localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user))
}

/**
 * 获取用户信息
 */
export const getUser = (): UserInfo | null => {
  const userStr = localStorage.getItem(USER_STORAGE_KEY)
  if (!userStr) return null
  try {
    return JSON.parse(userStr)
  } catch {
    return null
  }
}

/**
 * 移除用户信息
 */
export const removeUser = (): void => {
  localStorage.removeItem(USER_STORAGE_KEY)
}

/**
 * 清除所有认证信息
 */
export const clearAuth = (): void => {
  removeAccessToken()
  removeRefreshToken()
  removeUser()
}

// ================================
// 请求拦截器 - 自动添加Token
// ================================

authApi.interceptors.request.use(
  (config) => {
    const token = getAccessToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// ================================
// 响应拦截器 - 自动刷新Token
// ================================

authApi.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as any

    // 如果是401错误且不是刷新Token的请求
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // 如果正在刷新，等待刷新完成
        return new Promise((resolve) => {
          subscribeTokenRefresh((token: string) => {
            originalRequest.headers.Authorization = `Bearer ${token}`
            resolve(authApi(originalRequest))
          })
        })
      }

      originalRequest._retry = true
      isRefreshing = true

      const refreshToken = getRefreshToken()
      if (!refreshToken) {
        clearAuth()
        return Promise.reject(error)
      }

      try {
        const response = await refreshAccessToken(refreshToken)
        const newAccessToken = response.access_token

        setAccessToken(newAccessToken)
        if (response.refresh_token) {
          setRefreshToken(response.refresh_token)
        }

        isRefreshing = false
        onTokenRefreshed(newAccessToken)

        // 重试原始请求
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`
        return authApi(originalRequest)
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
// 认证API方法
// ================================

/**
 * 用户注册
 */
export const register = async (
  request: RegisterRequest
): Promise<RegisterResponse> => {
  const response = await authApi.post<RegisterResponse>(
    '/api/v1/auth/register',
    request
  )

  // 存储Token和用户信息
  setAccessToken(response.data.access_token)
  setRefreshToken(response.data.refresh_token)
  setUser({
    id: response.data.user_id,
    email: response.data.email,
    username: response.data.username || null,
    email_verified: false,
    created_at: new Date().toISOString(),
  })

  return response.data
}

/**
 * 用户登录
 */
export const login = async (request: LoginRequest): Promise<LoginResponse> => {
  const response = await authApi.post<LoginResponse>(
    '/api/v1/auth/login',
    request
  )

  // 存储Token和用户信息
  setAccessToken(response.data.access_token)
  setRefreshToken(response.data.refresh_token)
  setUser({
    id: response.data.user.id,
    email: response.data.user.email,
    username: response.data.user.username,
    email_verified: response.data.user.email_verified,
    created_at: response.data.user.created_at || new Date().toISOString(),
    last_login_at: response.data.user.last_login_at,
  })

  return response.data
}

/**
 * 刷新Access Token
 */
export const refreshAccessToken = async (
  refreshToken: string
): Promise<RefreshTokenResponse> => {
  const response = await authApi.post<RefreshTokenResponse>(
    '/api/v1/auth/refresh',
    { refresh_token: refreshToken } as RefreshTokenRequest
  )
  return response.data
}

/**
 * 用户登出
 */
export const logout = async (): Promise<void> => {
  try {
    await authApi.post('/api/v1/auth/logout')
  } catch (error) {
    // 即使API调用失败，也清除本地存储
    console.error('Logout API error:', error)
  } finally {
    clearAuth()
  }
}

/**
 * 忘记密码
 */
export const forgotPassword = async (
  request: ForgotPasswordRequest
): Promise<ForgotPasswordResponse> => {
  const response = await authApi.post<ForgotPasswordResponse>(
    '/api/v1/auth/forgot-password',
    request
  )
  return response.data
}

/**
 * 重置密码
 */
export const resetPassword = async (
  request: ResetPasswordRequest
): Promise<ResetPasswordResponse> => {
  const response = await authApi.post<ResetPasswordResponse>(
    '/api/v1/auth/reset-password',
    request
  )
  return response.data
}

// ================================
// 用户管理API方法
// ================================

/**
 * 获取当前用户信息
 */
export const getCurrentUser = async (): Promise<UserInfo> => {
  const response = await authApi.get<UserInfo>('/api/v1/users/me')
  setUser(response.data)
  return response.data
}

/**
 * 更新用户信息
 */
export const updateUser = async (
  update: UserUpdate
): Promise<UserInfo> => {
  const response = await authApi.put<UserInfo>('/api/v1/users/me', update)
  setUser(response.data)
  return response.data
}

/**
 * 删除账户
 */
export const deleteAccount = async (password: string): Promise<void> => {
  await authApi.delete('/api/v1/users/me', {
    data: { password },
  })
  clearAuth()
}

/**
 * 获取用户偏好设置
 */
export const getUserPreferences = async (): Promise<PreferencesResponse> => {
  const response = await authApi.get<PreferencesResponse>(
    '/api/v1/users/me/preferences'
  )
  return response.data
}

/**
 * 更新用户偏好设置
 */
export const updateUserPreferences = async (
  preferences: Record<string, any>
): Promise<PreferencesResponse> => {
  const response = await authApi.put<PreferencesResponse>(
    '/api/v1/users/me/preferences',
    { preferences } as PreferencesUpdate
  )
  return response.data
}

/**
 * 导出用户数据
 */
export const exportUserData = async (): Promise<DataExportResponse> => {
  const response = await authApi.post<DataExportResponse>(
    '/api/v1/users/me/export-data'
  )
  return response.data
}

/**
 * 迁移localStorage数据
 */
export const migrateUserData = async (
  request: MigrationRequest
): Promise<MigrationResponse> => {
  const response = await authApi.post<MigrationResponse>(
    '/api/v1/users/me/migrate-data',
    request
  )
  return response.data
}

// ================================
// 类型导出
// ================================

export type {
  User,
  RegisterRequest,
  RegisterResponse,
  LoginRequest,
  LoginResponse,
  RefreshTokenRequest,
  RefreshTokenResponse,
  ForgotPasswordRequest,
  ForgotPasswordResponse,
  ResetPasswordRequest,
  ResetPasswordResponse,
  UserInfo,
  UserUpdate,
  PreferencesResponse,
  PreferencesUpdate,
  DataExportResponse,
  MigrationRequest,
  MigrationResponse,
} from '../types/auth'

export default authApi

