/**
 * Mock API Service - 用于前端UI测试（不连接真实后端）
 *
 * 使用方式：
 * 1. 在.env.local中设置 VITE_USE_MOCK_API=true
 * 2. 重启开发服务器
 * 3. 所有API请求将使用Mock数据
 */

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

import {
  mockQuickChatResponse,
  mockDeepResearchResponse,
  mockReport,
  mockShareReportResponse,
  mockSharedReportResponse,
  generateSSEEvents,
} from '../mocks/mockData'

// ================================
// Mock Utilities
// ================================

/**
 * 模拟网络延迟
 */
const delay = (ms: number): Promise<void> => {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

/**
 * 自定义EventSource模拟器（用于SSE流式推送）
 */
class MockEventSource implements EventSource {
  readonly CONNECTING = 0
  readonly OPEN = 1
  readonly CLOSED = 2

  url: string
  readyState: number = this.CONNECTING
  withCredentials = false

  onopen: ((this: EventSource, ev: Event) => unknown) | null = null
  onmessage: ((this: EventSource, ev: MessageEvent) => unknown) | null = null
  onerror: ((this: EventSource, ev: Event) => unknown) | null = null

  private timeouts: number[] = []

  constructor(url: string) {
    this.url = url
    this.startStreaming()
  }

  /**
   * 开始模拟流式推送
   */
  private startStreaming(): void {
    // 延迟500ms后触发onopen
    const openTimeout = window.setTimeout(() => {
      this.readyState = this.OPEN
      if (this.onopen) {
        this.onopen(new Event('open'))
      }

      // 开始推送消息
      this.pushMessages()
    }, 500)

    this.timeouts.push(openTimeout)
  }

  /**
   * 推送SSE消息
   */
  private pushMessages(): void {
    const events = generateSSEEvents()
    let accumulatedDelay = 0

    events.forEach((event) => {
      accumulatedDelay += event.delay
      const timeout = window.setTimeout(() => {
        if (this.readyState === this.OPEN && this.onmessage) {
          const messageEvent = new MessageEvent('message', {
            data: event.data,
          })
          this.onmessage(messageEvent)
        }
      }, accumulatedDelay)

      this.timeouts.push(timeout)
    })

    // 最后一条消息后发送完成事件
    const finalTimeout = window.setTimeout(() => {
      if (this.readyState === this.OPEN) {
        const doneEvent = new MessageEvent('message', {
          data: JSON.stringify({ content: '[DONE]', stage: 'completed', progress: 100 }),
        })
        if (this.onmessage) {
          this.onmessage(doneEvent)
        }
        this.close()
      }
    }, accumulatedDelay + 1000)

    this.timeouts.push(finalTimeout)
  }

  /**
   * 关闭连接
   */
  close(): void {
    this.readyState = this.CLOSED
    this.timeouts.forEach((timeout) => clearTimeout(timeout))
    this.timeouts = []
  }

  addEventListener(): void {
    // Mock implementation
  }

  removeEventListener(): void {
    // Mock implementation
  }

  dispatchEvent(): boolean {
    return true
  }
}

// ================================
// Mock API Methods
// ================================

/**
 * Quick Chat - Mock版本
 * 延迟1秒返回Mock响应
 */
export const quickChat = async (
  request: QuickChatRequest
): Promise<QuickChatResponse> => {
  console.log('[Mock API] Quick Chat request:', request)
  await delay(1000) // 模拟1秒网络延迟

  return {
    ...mockQuickChatResponse,
    conversation_id: request.conversation_id || `mock-conv-${Date.now()}`,
  }
}

/**
 * Deep Research - Mock流式版本
 * 返回自定义EventSource模拟器
 */
export const deepResearchStream = (request: DeepResearchRequest): EventSource => {
  console.log('[Mock API] Deep Research Stream request:', request)
  const url = `mock://deep-research/stream?query=${request.query}`
  return new MockEventSource(url) as EventSource
}

/**
 * Deep Research - Mock非流式版本
 * 延迟30秒返回完整报告（模拟真实生成时间）
 */
export const deepResearch = async (
  request: DeepResearchRequest
): Promise<DeepResearchResponse> => {
  console.log('[Mock API] Deep Research request:', request)
  await delay(30000) // 模拟30秒生成时间

  return mockDeepResearchResponse
}

/**
 * 获取报告详情 - Mock版本
 */
export const getReport = async (reportId: number): Promise<Report> => {
  console.log('[Mock API] Get Report:', reportId)
  await delay(500)

  return {
    ...mockReport,
    id: reportId,
  }
}

/**
 * 获取报告列表 - Mock版本
 */
export const getReports = async (params?: {
  symbol?: string
  report_type?: string
  page?: number
  page_size?: number
}) => {
  console.log('[Mock API] Get Reports:', params)
  await delay(800)

  // 返回3个Mock报告
  return {
    items: [
      { ...mockReport, id: 1001, symbol: 'BTC', created_at: '2025-10-26T15:30:00Z' },
      { ...mockReport, id: 1002, symbol: 'ETH', created_at: '2025-10-26T14:20:00Z', title: 'Ethereum (ETH) 深度研究报告' },
      { ...mockReport, id: 1003, symbol: 'SOL', created_at: '2025-10-26T13:10:00Z', title: 'Solana (SOL) 深度研究报告' },
    ],
    total: 3,
    page: params?.page || 1,
    page_size: params?.page_size || 10,
  }
}

/**
 * 创建分享链接 - Mock版本
 */
export const createShareLink = async (
  reportId: number,
  request?: ShareReportRequest
): Promise<ShareReportResponse> => {
  console.log('[Mock API] Create Share Link:', reportId, request)
  await delay(500)

  const token = `mock-token-${reportId}-${Date.now()}`
  return {
    share_token: token,
    share_url: `http://localhost:3000/shared/${token}`,
    expires_at: request?.expires_in_days
      ? new Date(Date.now() + request.expires_in_days * 24 * 60 * 60 * 1000).toISOString()
      : undefined,
  }
}

/**
 * 获取分享报告 - Mock版本
 */
export const getSharedReport = async (
  shareToken: string
): Promise<SharedReportResponse> => {
  console.log('[Mock API] Get Shared Report:', shareToken)
  await delay(800)

  return mockSharedReportResponse
}

/**
 * 禁用分享链接 - Mock版本
 */
export const disableShareLink = async (reportId: number): Promise<void> => {
  console.log('[Mock API] Disable Share Link:', reportId)
  await delay(500)
  // 无返回值
}

/**
 * 健康检查 - Mock版本
 */
export const healthCheck = async (): Promise<{ status: string }> => {
  console.log('[Mock API] Health Check')
  await delay(200)

  return {
    status: 'healthy (mock)',
  }
}

// ================================
// Export all methods
// ================================

export default {
  quickChat,
  deepResearchStream,
  deepResearch,
  getReport,
  getReports,
  createShareLink,
  getSharedReport,
  disableShareLink,
  healthCheck,
}
