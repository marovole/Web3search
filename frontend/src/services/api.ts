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
    // 添加认证token（如果存在）
    const token = localStorage.getItem('web3search_access_token')
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
  // 构建API路径：确保不会与baseURL重复
  // 生产环境: baseURL = https://web3search-api.marovole.workers.dev, path = /api/v1/chat/quick-chat
  // 结果: https://web3search-api.marovole.workers.dev/api/v1/chat/quick-chat
  const path = '/api/v1/chat/quick-chat'
  console.log(`[API] Quick Chat Request: ${api.defaults.baseURL}${path}`)
  const response = await api.post<QuickChatResponse>(path, request)
  console.log(`[API] Quick Chat Response:`, response.data)
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

  const url = `${api.defaults.baseURL}/api/v1/chat/deep-research/stream?${queryParams}`
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
    '/api/v1/chat/deep-research',
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
  const response = await fetch(`${apiConfig.baseUrl}/api/v1/reports/generate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': localStorage.getItem('web3search_access_token')
        ? `Bearer ${localStorage.getItem('web3search_access_token')}`
        : undefined,
    },
    body: JSON.stringify(request),
  })

  if (!response.ok) {
    throw new Error(`Report generation failed: ${response.statusText}`)
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
  const response = await api.get<SearchSuggestionsResponse>('/api/v1/search/suggestions', {
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
          { id: '1', title: 'Web3技术趋势', type: 'report' },
          { id: '2', title: 'DeFi协议对比', type: 'report' },
          { id: '3', title: 'NFT市场分析', type: 'chat' },
          { id: '4', title: 'Bitcoin价格监控', type: 'watchlist' }
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
