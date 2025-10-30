/**
 * 认证相关类型定义
 */

// 用户信息
export interface User {
  id: string
  email: string
  username?: string | null
  email_verified: boolean
  created_at?: string
  last_login_at?: string | null
}

// 注册请求
export interface RegisterRequest {
  email: string
  password: string
  username?: string
}

// 注册响应
export interface RegisterResponse {
  user_id: string
  email: string
  username?: string | null
  access_token: string
  refresh_token: string
  token_type: string
}

// 登录请求
export interface LoginRequest {
  email: string
  password: string
}

// 登录响应
export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: User
}

// Token刷新请求
export interface RefreshTokenRequest {
  refresh_token: string
}

// Token刷新响应
export interface RefreshTokenResponse {
  access_token: string
  refresh_token: string | null
  token_type: string
}

// 忘记密码请求
export interface ForgotPasswordRequest {
  email: string
}

// 忘记密码响应
export interface ForgotPasswordResponse {
  message: string
}

// 重置密码请求
export interface ResetPasswordRequest {
  token: string
  new_password: string
}

// 重置密码响应
export interface ResetPasswordResponse {
  message: string
}

// 用户信息响应
export interface UserInfo {
  id: string
  email: string
  username?: string | null
  email_verified: boolean
  created_at: string
  last_login_at?: string | null
}

// 用户更新请求
export interface UserUpdate {
  username?: string
}

// 偏好设置响应
export interface PreferencesResponse {
  preferences: Record<string, any>
}

// 偏好设置更新请求
export interface PreferencesUpdate {
  preferences: Record<string, any>
}

// 数据导出响应
export interface DataExportResponse {
  user: {
    id: string
    email: string
    created_at: string
  }
  preferences: Record<string, any>
  conversations: Array<{
    id: number
    session_id: string
    title: string
    message_count: number
    messages: Array<{
      role: string
      content: string
      created_at: string | null
    }>
    created_at: string | null
    last_activity: string | null
  }>
  reports: Array<{
    id: number
    report_type: string
    status: string
    query: string
    title: string
    symbol: string
    created_at: string | null
    completed_at: string | null
  }>
  exported_at: string
}

// 数据迁移请求
export interface MigrationRequest {
  conversations?: Array<{
    session_id: string
    title: string
    messages: Array<{
      role: string
      content: string
      created_at?: string
    }>
    created_at?: string
  }>
  reports?: Array<{
    share_id?: string
    symbol: string
    title: string
    content: string
    query?: string
    created_at?: string
  }>
  preferences?: Record<string, any>
  watchlist?: Array<{
    symbol: string
    name: string
    added_at?: string
  }>
}

// 数据迁移响应
export interface MigrationResponse {
  success: boolean
  migrated: {
    conversations: {
      total: number
      success: number
      failed: number
      errors: Array<{
        index: number
        error: string
      }>
    }
    reports: {
      total: number
      success: number
      failed: number
      errors: Array<{
        index: number
        error: string
      }>
    }
    preferences: {
      total: number
      success: number
      failed: number
      errors: Array<{
        error: string
      }>
    }
  }
  message: string
}

// Token存储键名
export const TOKEN_STORAGE_KEY = 'web3search_access_token'
export const REFRESH_TOKEN_STORAGE_KEY = 'web3search_refresh_token'
export const USER_STORAGE_KEY = 'web3search_user'

