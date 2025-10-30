import axios, { AxiosInstance } from 'axios'
import type {
  QuickChatRequest,
  QuickChatResponse,
  DeepResearchRequest,
  DeepResearchResponse,
  ShareReportRequest,
  ShareReportResponse,
  SharedReportResponse,
  Report,
} from '../types'
import type { AutocompleteResponse } from '../types/autocomplete'
import type { HotspotsResponse } from '../types/hotspot'

// Import Mock API
import * as mockApi from './api.mock'

// Load environment configuration
import { getApiConfig, isDevelopment } from '../utils/env'

// 缓存性能监控
import cachePerformanceMonitor from '../utils/cachePerformanceMonitor'

const apiConfig = getApiConfig()

if (apiConfig.useMock) {
  console.log('🎭 Mock API Mode Enabled - Using mock data instead of real backend')
} else {
  console.log('🌐 Real API Mode - Connecting to backend at', apiConfig.baseUrl)
}

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: apiConfig.baseUrl,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 120000, // 2分钟超时（Deep Research可能需要30秒）
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // 可以在这里添加认证token
    // const token = localStorage.getItem('token')
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`
    // }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => {
    // 检查是否来自缓存（Service Worker会在响应头中添加标识）
    const cached = response.headers['x-cache'] === 'HIT'
    const startTime = performance.now()
    const responseTime = performance.now() - startTime

    if (cached) {
      cachePerformanceMonitor.recordCacheHit(responseTime)
    } else {
      cachePerformanceMonitor.recordCacheMiss(responseTime)
    }

    return response
  },
  (error) => {
    // 统一错误处理
    const startTime = performance.now()
    const responseTime = performance.now() - startTime
    cachePerformanceMonitor.recordCacheMiss(responseTime)
    const message = error.response?.data?.detail || error.message || '请求失败'
    console.error('API Error:', message)
    return Promise.reject(new Error(message))
  }
)

// ================================
// Chat API - Real implementations
// ================================

/**
 * Quick Chat - Real API版本
 */
const quickChatReal = async (
  request: QuickChatRequest
): Promise<QuickChatResponse> => {
  const response = await api.post<QuickChatResponse>('/api/v1/quick-chat', request)
  return response.data
}

/**
 * Quick Chat - 快速问答（3秒内响应）
 * 根据环境配置自动选择Mock或真实API
 */
export const quickChat = apiConfig.useMock ? mockApi.quickChat : quickChatReal

/**
 * Deep Research Stream - Real API版本
 */
const deepResearchStreamReal = (request: DeepResearchRequest): EventSource => {
  const queryParams = new URLSearchParams({
    query: request.query,
    ...(request.conversation_id && { conversation_id: request.conversation_id }),
  })

  const url = `${api.defaults.baseURL}/api/v1/quick-chat/stream?${queryParams}`
  return new EventSource(url)
}

/**
 * Deep Research - 深度研究报告（流式输出）
 * 注意：这个方法返回EventSource用于SSE流式接收
 * 根据环境配置自动选择Mock或真实API
 */
export const deepResearchStream = apiConfig.useMock ? mockApi.deepResearchStream : deepResearchStreamReal

/**
 * Deep Research - Real API版本（非流式）
 */
const deepResearchReal = async (
  request: DeepResearchRequest
): Promise<DeepResearchResponse> => {
  const response = await api.post<DeepResearchResponse>(
    '/api/v1/deep-research',
    request
  )
  return response.data
}

/**
 * Deep Research - 非流式版本（等待完整响应）
 * 根据环境配置自动选择Mock或真实API
 */
export const deepResearch = apiConfig.useMock ? mockApi.deepResearch : deepResearchReal

// ================================
// Reports API - Real implementations
// ================================

/**
 * 获取报告详情 - Real API版本
 */
const getReportReal = async (reportId: number): Promise<Report> => {
  const response = await api.get<Report>(`/api/v1/reports/${reportId}`)
  return response.data
}

/**
 * 获取报告详情
 * 根据环境变量自动选择Mock或真实API
 */
export const getReport = apiConfig.useMock ? mockApi.getReport : getReportReal

/**
 * 获取报告列表 - Real API版本
 */
const getReportsReal = async (params?: {
  symbol?: string
  report_type?: string
  page?: number
  page_size?: number
}) => {
  const response = await api.get('/api/v1/reports', { params })
  return response.data
}

/**
 * 获取报告列表
 * 根据环境变量自动选择Mock或真实API
 */
export const getReports = apiConfig.useMock ? mockApi.getReports : getReportsReal

/**
 * 创建分享链接 - Real API版本
 */
const createShareLinkReal = async (
  reportId: number,
  request?: ShareReportRequest
): Promise<ShareReportResponse> => {
  const response = await api.post<ShareReportResponse>(
    `/api/v1/reports/${reportId}/share`,
    request || {}
  )
  return response.data
}

/**
 * 创建分享链接
 * 根据环境变量自动选择Mock或真实API
 */
export const createShareLink = apiConfig.useMock ? mockApi.createShareLink : createShareLinkReal

/**
 * 获取分享报告 - Real API版本
 */
const getSharedReportReal = async (
  shareToken: string
): Promise<SharedReportResponse> => {
  const response = await api.get<SharedReportResponse>(
    `/api/v1/reports/shared/${shareToken}`
  )
  return response.data
}

/**
 * 获取分享报告
 * 根据环境变量自动选择Mock或真实API
 */
export const getSharedReport = apiConfig.useMock ? mockApi.getSharedReport : getSharedReportReal

/**
 * 禁用分享链接 - Real API版本
 */
const disableShareLinkReal = async (reportId: number): Promise<void> => {
  await api.delete(`/api/v1/reports/${reportId}/share`)
}

/**
 * 禁用分享链接
 * 根据环境变量自动选择Mock或真实API
 */
export const disableShareLink = apiConfig.useMock ? mockApi.disableShareLink : disableShareLinkReal

// ================================
// Search API
// ================================

/**
 * 搜索自动补全
 */
export const searchAutocomplete = async (query: string): Promise<AutocompleteResponse> => {
  const response = await api.get<AutocompleteResponse>('/api/v1/search/autocomplete', {
    params: { q: query },
  })
  return response.data
}

/**
 * 获取市场热点
 */
export const getHotspots = async (
  limit: number = 10,
  forceRefresh: boolean = false
): Promise<HotspotsResponse> => {
  const response = await api.get<HotspotsResponse>('/api/v1/trending/hotspots', {
    params: { limit, force_refresh: forceRefresh },
  })
  return response.data
}

// ================================
// Health Check
// ================================

/**
 * 健康检查 - Real API版本
 */
const healthCheckReal = async (): Promise<{ status: string }> => {
  const response = await api.get('/health')
  return response.data
}

/**
 * 健康检查
 * 根据环境变量自动选择Mock或真实API
 */
export const healthCheck = apiConfig.useMock ? mockApi.healthCheck : healthCheckReal

export default api
