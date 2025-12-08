/**
 * Server-Sent Events (SSE) Library
 * Handles real-time streaming from backend
 * Part of Week 2 T13: Frontend SSE Integration
 */

export interface SSEOptions {
  onMessage?: (data: any) => void
  onError?: (error: Error) => void
  onOpen?: () => void
  onClose?: () => void
  timeoutMs?: number
  maxReconnectAttempts?: number
  reconnectDelayMs?: number
  headers?: Record<string, string>
}

export interface SSEState {
  connected: boolean
  error: Error | null
  reconnectAttempts: number
  lastEventId?: string
}

export interface AbortControllerWithReason {
  controller: AbortController
  reason: string
}

/**
 * Create SSE connection with AbortController
 */
export function createSSEConnection(
  url: string,
  options: SSEOptions = {}
): { eventSource: EventSource; abortController: AbortController } {
  const {
    timeoutMs = 30000,
    maxReconnectAttempts = 3,
    reconnectDelayMs = 1000,
    headers = {},
    onMessage,
    onError,
    onOpen,
    onClose,
  } = options

  // Create AbortController for timeout
  const abortController = new AbortController()
  let reconnectAttempts = 0
  let eventSource: EventSource | null = null

  // Timeout handler
  const timeoutId = setTimeout(() => {
    abortController.abort('SSE timeout')
    onError?.(new Error(`SSE connection timeout after ${timeoutMs}ms`))
  }, timeoutMs)

  // Create EventSource with URL (note: headers unsupported; signal not typed in lib yet)
  // @ts-expect-error signal is not yet in EventSourceInit typings
  eventSource = new EventSource(url, {
    signal: abortController.signal,
  })

  // Handle open
  eventSource.onopen = () => {
    reconnectAttempts = 0
    clearTimeout(timeoutId)
    onOpen?.()
    console.log('SSE connection opened')
  }

  // Handle messages
  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      onMessage?.(data)
    } catch (error) {
      console.error('Failed to parse SSE message:', error)
      onError?.(error as Error)
    }
  }

  // Handle errors
  eventSource.onerror = (error) => {
    console.error('SSE connection error:', error)

    if (abortController.signal.aborted) {
      onError?.(new Error('SSE connection aborted'))
      onClose?.()
      return
    }

    reconnectAttempts++

    if (reconnectAttempts >= maxReconnectAttempts) {
      clearTimeout(timeoutId)
      abortController.abort(`Max reconnect attempts (${maxReconnectAttempts}) reached`)
      onError?.(new Error(`SSE failed after ${reconnectAttempts} reconnect attempts`))
      onClose?.()
      return
    }

    console.log(`Reconnecting in ${reconnectDelayMs}ms (attempt ${reconnectAttempts}/${maxReconnectAttempts})`)
    setTimeout(() => {
      eventSource?.close()
      createSSEConnection(url, options)
    }, reconnectDelayMs)
  }

  return { eventSource, abortController }
}

/**
 * Parse SSE event data
 */
export function parseSSEEvent(event: MessageEvent): {
  type: string
  data: any
  id?: string
} {
  try {
    const data = JSON.parse(event.data)
    return {
      type: 'message',
      data,
      id: event.lastEventId,
    }
  } catch (error) {
    return {
      type: 'error',
      data: { error: 'Failed to parse SSE data' },
    }
  }
}

/**
 * Cancel SSE connection with reason
 */
export function cancelSSEConnection(
  connection: { eventSource: EventSource | null; abortController: AbortController }
): void {
  if (connection.eventSource) {
    connection.eventSource.close()
    connection.eventSource = null
  }
  connection.abortController.abort('Connection cancelled by user')
}

/**
 * Create debounced SSE handler
 */
export function createDebouncedSSEHandler(
  callback: (data: any) => void,
  delayMs = 100
): (data: any) => void {
  let timeoutId: NodeJS.Timeout | null = null

  return (data: any) => {
    if (timeoutId) {
      clearTimeout(timeoutId)
    }

    timeoutId = setTimeout(() => {
      callback(data)
      timeoutId = null
    }, delayMs)
  }
}

/**
 * Batch SSE messages for performance
 */
export class SSEBatchProcessor {
  private batch: any[] = []
  private maxBatchSize = 10
  private flushTimeout: NodeJS.Timeout | null = null
  private flushDelayMs = 50

  constructor(
    private onBatch: (batch: any[]) => void,
    options: { maxBatchSize?: number; flushDelayMs?: number } = {}
  ) {
    this.maxBatchSize = options.maxBatchSize ?? 10
    this.flushDelayMs = options.flushDelayMs ?? 50
  }

  add(data: any): void {
    this.batch.push(data)

    if (this.batch.length >= this.maxBatchSize) {
      this.flush()
    } else if (!this.flushTimeout) {
      this.flushTimeout = setTimeout(() => {
        this.flush()
      }, this.flushDelayMs)
    }
  }

  flush(): void {
    if (this.flushTimeout) {
      clearTimeout(this.flushTimeout)
      this.flushTimeout = null
    }

    if (this.batch.length > 0) {
      this.onBatch([...this.batch])
      this.batch = []
    }
  }
}

/**
 * Create throttled SSE handler
 */
export function createThrottledSSEHandler(
  callback: (data: any) => void,
  intervalMs = 200
): (data: any) => void {
  let lastExecution = 0

  return (data: any) => {
    const now = Date.now()
    if (now - lastExecution >= intervalMs) {
      callback(data)
      lastExecution = now
    }
  }
}

// Type definitions for common SSE events
export interface ChatSSEEvent {
  id?: string
  delta?: {
    content?: string
    role?: string
  }
  usage?: {
    prompt_tokens?: number
    completion_tokens?: number
    total_tokens?: number
  }
  finish_reason?: string
  error?: string
}

export interface ResearchSSEvent {
  event: 'research.started' | 'research.progress' | 'research.step' | 'research.completed' | 'research.failed'
  data: any
}

// Default headers for SSE requests
export const defaultSSEHeaders = {
  'Accept': 'text/event-stream',
  'Cache-Control': 'no-cache',
  'Connection': 'keep-alive',
}

// SSE State management
export class SSEManager {
  private connections = new Map<string, { eventSource: EventSource | null; abortController: AbortController }>()

  /**
   * Start SSE connection with key
   */
  connect(key: string, url: string, options: SSEOptions = {}): void {
    // Close existing connection if any
    this.disconnect(key)

    const connection = createSSEConnection(url, options)
    this.connections.set(key, connection)
  }

  /**
   * Get connection by key
   */
  get(key: string): { eventSource: EventSource | null; abortController: AbortController } | undefined {
    return this.connections.get(key)
  }

  /**
   * Disconnect by key
   */
  disconnect(key: string): void {
    const connection = this.connections.get(key)
    if (connection) {
      cancelSSEConnection(connection)
      this.connections.delete(key)
    }
  }

  /**
   * Disconnect all
   */
  disconnectAll(): void {
    for (const [key, connection] of this.connections.entries()) {
      cancelSSEConnection(connection)
    }
    this.connections.clear()
  }

  /**
   * Check if connection exists
   */
  has(key: string): boolean {
    return this.connections.has(key)
  }

  /**
   * Get all connection keys
   */
  keys(): string[] {
    return Array.from(this.connections.keys())
  }
}

// Singleton SSE manager instance
export const sseManager = new SSEManager()

// Cleanup on page unload
if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', () => {
    sseManager.disconnectAll()
  })
}

export default {
  createSSEConnection,
  cancelSSEConnection,
  parseSSEEvent,
  createDebouncedSSEHandler,
  createThrottledSSEHandler,
  SSEBatchProcessor,
  SSEManager,
  sseManager,
  defaultSSEHeaders,
}
