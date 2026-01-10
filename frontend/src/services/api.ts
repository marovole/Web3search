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
  CheckoutResponse,
  PortalResponse,
} from '../types'
import type { AutocompleteResponse } from '../types/autocomplete'
import type { HotspotsResponse } from '../types/hotspot'

// Import Mock API
import * as mockApi from './api.mock'

// Load environment configuration
import { getApiConfig, isDevelopment } from '../utils/env'
import tokenManager from '../utils/tokenManager'
import logger from '../utils/logger'

const apiConfig = getApiConfig()
const isDevMode = isDevelopment()

// 在开发环境输出 API 模式信息
if (isDevMode) {
  if (apiConfig.useMock) {
    logger.info('Mock API Mode - Using mock data')
  } else {
    logger.info('Real API Mode - Backend:', apiConfig.baseUrl)
  }
}

// Normalize API path to prevent URL duplication
// Ensures baseURL and path are combined correctly without duplicate /api/v1
function normalizeApiPath(baseUrl: string, path: string): string {
  // Remove trailing slash and /api/v1 from baseUrl if present
  const normalizedBase = baseUrl.replace(/\/api\/v1\/?$/, '').replace(/\/$/, '')
  // Remove leading slash and /api/v1 (with or without trailing slash) from path if present
  const normalizedPath = path.replace(/^\/?api\/v1\/?/, '').replace(/^\//, '')
  return `${normalizedBase}/api/v1/${normalizedPath}`.replace(/\/+$/, '')
}

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: normalizeApiPath(apiConfig.baseUrl, '/api/v1'),
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 120000, // 2分钟超时（Deep Research可能需要30秒）
})

type SSEClient = {
  onmessage: ((ev: MessageEvent) => any) | null
  onerror: ((ev: any) => any) | null
  onopen?: ((ev: any) => any) | null
  close: () => void
}

function createAuthenticatedSSE(url: string, init?: RequestInit): SSEClient {
  const controller = new AbortController()
  let onmessage: ((ev: MessageEvent) => any) | null = null
  let onerror: ((ev: any) => any) | null = null
  let onopen: ((ev: any) => any) | null = null

  const start = async () => {
    try {
      const response = await fetch(url, { ...init, signal: controller.signal })
      if (!response.body) throw new Error('Stream not supported')
      onopen?.(new Event('open'))

      const reader = response.body.getReader()
      const decoder = new TextDecoder('utf-8')
      let buffer = ''

      let isDone = false
      while (!isDone) {
        const { done, value } = await reader.read()
        if (done) {
          isDone = true
          break
        }
        buffer += decoder.decode(value, { stream: true })
        const parts = buffer.split('\n\n')
        buffer = parts.pop() ?? ''

        for (const part of parts) {
          if (!part.trim()) continue
          const lines = part.split('\n')
          let data = ''
          for (const line of lines) {
            if (line.startsWith('data:')) data += `${line.slice(5).trim()}\n`
          }
          onmessage?.(new MessageEvent('message', { data: data.trimEnd() }))
        }
      }
    } catch (err: any) {
      onerror?.(err)
    }
  }

  void start()

  return {
    get onmessage() {
      return onmessage
    },
    set onmessage(fn) {
      onmessage = fn
    },
    get onerror() {
      return onerror
    },
    set onerror(fn) {
      onerror = fn
    },
    get onopen() {
      return onopen
    },
    set onopen(fn) {
      onopen = fn
    },
    close: () => controller.abort(),
  }
}

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // 使用安全的令牌管理器获取token
    const token = tokenManager.getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // 统一错误处理
    const message = error.response?.data?.detail || error.message || '请求失败'
    logger.error('API Error:', message)
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
  // Path relative to normalized baseURL (/api/v1)
  const path = 'chat/quick-chat'

  // 仅在开发环境输出请求和响应日志
  if (isDevMode) {
    logger.info('Quick Chat Request:', `${api.defaults.baseURL}/${path}`)
  }

  // Explicitly disable streaming for axios requests (axios cannot parse SSE streams)
  const response = await api.post<QuickChatResponse>(path, { ...request, stream: false })

  if (isDevMode) {
    logger.debug('Quick Chat Response:', response.data)
  }

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
const deepResearchStreamReal = (request: DeepResearchRequest): SSEClient => {
  const queryParams = new URLSearchParams({
    query: request.query,
    ...(request.conversation_id && { conversation_id: request.conversation_id }),
  })

  const url = `${api.defaults.baseURL}/deep-research/stream?${queryParams}`
  const token = tokenManager.getToken()

  if (!token) {
    return new EventSource(url)
  }

  return createAuthenticatedSSE(url, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
    method: 'GET',
  })
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
    'deep-research',
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
  const response = await api.get<Report>(`reports/${reportId}`)
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
  const response = await api.get('reports', { params })
  return response.data
}

/**
 * 获取报告列表
 * 根据环境变量自动选择Mock或真实API
 */
export const getReports = apiConfig.useMock ? mockApi.getReports : getReportsReal

// ================================
// Report Generation API
// ================================

export interface ReportSection {
  id: string
  title: string
  description?: string
  focus_points?: string[]
}

export interface ReportGenerationRequest {
  topic: string
  sections: ReportSection[]
  format?: 'markdown' | 'json'
  save_to_database?: boolean
}

export interface ReportStreamChunk {
  type: string
  section_id?: string
  section_title?: string
  delta?: string
  is_complete?: boolean
  current_section?: number
  total_sections?: number
  completed_sections?: string[]
  progress_percent?: number
  report_id?: string
  content?: Record<string, string>
  generation_time_ms?: number
  error?: string
}

/**
 * 生成研究报告 - Real API版本（流式响应）
 */
const generateReportReal = async (request: ReportGenerationRequest) => {
  const token = tokenManager.getToken()
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const response = await fetch(`${apiConfig.baseUrl}/reports/generate`, {
    method: 'POST',
    headers,
    body: JSON.stringify(request),
  })

  if (!response.ok) {
    // Validate Content-Type before parsing error
    const contentType = response.headers.get('content-type')
    if (!contentType?.includes('application/json')) {
      throw new Error(`Unexpected response type: ${contentType || 'unknown'}`)
    }
    const errorData = await response.json().catch(() => ({}))
    throw new Error(errorData.detail || `Report generation failed: ${response.statusText}`)
  }

  // Validate Content-Type for streaming response
  const responseContentType = response.headers.get('content-type')
  if (!responseContentType?.includes('text/event-stream')) {
    console.warn(`Unexpected Content-Type: ${responseContentType}, expected text/event-stream`)
  }

  return response
}

/**
 * Mock Report Generation
 */
const generateReportMock = async (request: ReportGenerationRequest) => {
  // 模拟流式响应
  return new Response(
    new ReadableStream({
      async start(controller) {
        const encoder = new TextEncoder()

        // 发送开始事件
        const startEvent = {
          type: 'report_start',
          topic: request.topic,
          sections: request.sections,
          total_sections: request.sections.length
        }
        controller.enqueue(encoder.encode(`data: ${JSON.stringify(startEvent)}\n\n`))

        // 模拟生成每个部分
        for (let i = 0; i < request.sections.length; i++) {
        const section = request.sections[i]
        if (!section) continue

          // 发送进度
          const progress = {
            type: 'progress_update',
            current_section: i + 1,
            total_sections: request.sections.length,
            progress_percent: Math.round(((i + 1) / request.sections.length) * 100)
          }
          controller.enqueue(encoder.encode(`data: ${JSON.stringify(progress)}\n\n`))

          // 发送内容
          const content = {
            type: 'section_complete',
            section_id: section.id,
            section_title: section.title,
            delta: `Mock content for ${section.title}...`,
            is_complete: true
          }
          controller.enqueue(encoder.encode(`data: ${JSON.stringify(content)}\n\n`))

          // 模拟延迟
          await new Promise(resolve => setTimeout(resolve, 1000))
        }

        // 发送完成事件
        const completeEvent = {
          type: 'report_complete',
          topic: request.topic,
          content: Object.fromEntries(request.sections.map(s => [s.id, `Mock content for ${s.title}`]))
        }
        controller.enqueue(encoder.encode(`data: ${JSON.stringify(completeEvent)}\n\n`))
        controller.enqueue(encoder.encode('event: done\ndata: {"status":"completed"}\n\n'))

        controller.close()
      }
    }),
    {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      }
    }
  )
}

/**
 * 生成研究报告
 * 根据环境变量自动选择Mock或真实API
 */
export const generateReport = apiConfig.useMock ? generateReportMock : generateReportReal

// ================================
// Search Suggestions API
// ================================

export interface SearchSuggestion {
  id: string
  title: string
  type: 'report' | 'chat' | 'watchlist' | 'repository'
  description?: string
  url?: string
}

export interface SearchSuggestionsResponse {
  suggestions: SearchSuggestion[]
  popular?: string[]
}

/**
 * 获取搜索建议 - Real API版本
 */
const getSearchSuggestionsReal = async (query: string): Promise<SearchSuggestionsResponse> => {
  const response = await api.get<SearchSuggestionsResponse>('search/suggestions', {
    params: { q: query }
  })
  return response.data
}

/**
 * 获取搜索建议
 * 根据环境配置自动选择Mock或真实API
 */
export const getSearchSuggestions = apiConfig.useMock
  ? async (query: string): Promise<SearchSuggestionsResponse> => {
      // Mock 实现：返回模拟建议
      await new Promise(resolve => setTimeout(resolve, 200))
      return {
        suggestions: [
          { id: '1', title: 'Web3技术趋势', type: 'report' as const },
          { id: '2', title: 'DeFi协议对比', type: 'report' as const },
          { id: '3', title: 'NFT市场分析', type: 'chat' as const },
          { id: '4', title: 'Bitcoin价格监控', type: 'watchlist' as const }
        ].filter(item => item.title.toLowerCase().includes(query.toLowerCase())),
        popular: ['blockchain', 'ethereum', 'web3', 'defi']
      }
    }
  : getSearchSuggestionsReal

/**
 * 创建分享链接 - Real API版本
 */
const createShareLinkReal = async (
  reportId: number,
  request?: ShareReportRequest
): Promise<ShareReportResponse> => {
  const response = await api.post<ShareReportResponse>(
    `reports/${reportId}/share`,
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
    `reports/shared/${shareToken}`
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
  await api.delete(`reports/${reportId}/share`)
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
  const response = await api.get<AutocompleteResponse>('search/autocomplete', {
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
  const response = await api.get<HotspotsResponse>('trending/hotspots', {
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


// ================================
// Billing API
// ================================

/**
 * Create checkout session
 */
export const createCheckoutSession = async (
  plan: 'pro' | 'team',
  interval: 'monthly' | 'yearly'
): Promise<CheckoutResponse> => {
  const response = await api.post<CheckoutResponse>('billing/checkout', {
    plan,
    interval,
  })
  return response.data
}

/**
 * Create billing portal session
 */
export const createPortalSession = async (): Promise<PortalResponse> => {
  const response = await api.post<PortalResponse>('billing/portal')
  return response.data
}

export default api
