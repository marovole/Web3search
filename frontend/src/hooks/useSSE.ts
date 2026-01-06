/**
 * React Hook for Server-Sent Events
 * Streamlines SSE usage in React components
 * Part of Week 2 T13: Frontend SSE Integration
 */

import { useState, useEffect, useRef, useCallback } from 'react'
import {
  SSEOptions,
  SSEState,
  ChatSSEEvent,
  ResearchSSEvent,
  sseManager,
  createSSEConnection,
  cancelSSEConnection,
  defaultSSEHeaders,
} from '../lib/sse'
import type { SSEManager } from '../lib/sse'
import type { ToolCallEvent, ThinkingEvent } from '../types/deep-research'

/**
 * Hook for SSE chat streaming
 */
export function useChatSSE(url: string, options: SSEOptions = {}) {
  const [messages, setMessages] = useState<ChatSSEEvent[]>([])
  const [currentMessage, setCurrentMessage] = useState<ChatSSEEvent | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  const connectionRef = useRef<{ eventSource: EventSource | null; abortController: AbortController } | null>(null)
  // Use ref to store options to avoid stale closures and unnecessary re-renders
  const optionsRef = useRef(options)
  optionsRef.current = options

  // Keep optionsRef synchronized with options prop
  useEffect(() => {
    optionsRef.current = options
  }, [options])

  const start = useCallback(() => {
    if (connectionRef.current) {
      cancelSSEConnection(connectionRef.current)
    }

    const currentOptions = optionsRef.current
    const connection = createSSEConnection(url, {
      ...currentOptions,
      onOpen: () => {
        setIsConnected(true)
        setError(null)
        currentOptions.onOpen?.()
      },
      onMessage: (data: ChatSSEEvent) => {
        if (data.error) {
          setError(new Error(data.error))
          currentOptions.onError?.(new Error(data.error))
          return
        }

        // Append to messages
        setMessages(prev => [...prev, data])
        setCurrentMessage(data)
        currentOptions.onMessage?.(data)
      },
      onError: (error) => {
        setError(error)
        setIsConnected(false)
        currentOptions.onError?.(error)
      },
      onClose: () => {
        setIsConnected(false)
        currentOptions.onClose?.()
      },
    })

    connectionRef.current = connection
  }, [url]) // Remove options from dependencies since we use optionsRef

  const stop = useCallback(() => {
    if (connectionRef.current) {
      cancelSSEConnection(connectionRef.current)
      connectionRef.current = null
      setIsConnected(false)
    }
  }, [])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stop()
    }
  }, [stop])

  const reset = useCallback(() => {
    setMessages([])
    setCurrentMessage(null)
    setError(null)
  }, [])

  return {
    messages,
    currentMessage,
    isConnected,
    error,
    start,
    stop,
    reset,
  }
}

/**
 * Hook for Deep Research SSE streaming
 * Extended with Glass Box UX event support for tool_call and thinking events
 */
export function useResearchSSE(url: string, options: SSEOptions = {}) {
  const [events, setEvents] = useState<ResearchSSEvent[]>([])
  const [currentEvent, setCurrentEvent] = useState<ResearchSSEvent | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  const [progress, setProgress] = useState(0)
  // Glass Box UX state
  const [toolCalls, setToolCalls] = useState<ToolCallEvent[]>([])
  const [thoughts, setThoughts] = useState<ThinkingEvent[]>([])
  const connectionRef = useRef<{ eventSource: EventSource | null; abortController: AbortController } | null>(null)
  // Use ref to store options to avoid stale closures and unnecessary re-renders
  const optionsRef = useRef(options)
  optionsRef.current = options

  // Keep optionsRef synchronized with options prop
  useEffect(() => {
    optionsRef.current = options
  }, [options])

  const start = useCallback(() => {
    if (connectionRef.current) {
      cancelSSEConnection(connectionRef.current)
    }

    const currentOptions = optionsRef.current
    const connection = createSSEConnection(url, {
      ...currentOptions,
      onOpen: () => {
        setIsConnected(true)
        setError(null)
        setProgress(0)
        // Clear Glass Box state on new connection
        setToolCalls([])
        setThoughts([])
        currentOptions.onOpen?.()
      },
      onMessage: (data: ResearchSSEvent) => {
        // Support both legacy event/data shape and new Glass Box type shape
        const rawData = data as Record<string, unknown>
        const eventType = rawData.type || data.event

        // Handle Glass Box tool_call events
        if (eventType === 'tool_call') {
          const toolCall: ToolCallEvent = {
            type: 'tool_call',
            tool: rawData.tool ?? 'search',
            query: rawData.query,
            provider: rawData.provider,
            latency_ms: rawData.latency_ms ?? 0,
            result_summary: rawData.result_summary ?? '',
            source_count: rawData.source_count,
            status: rawData.status ?? 'started',
            timestamp: rawData.timestamp,
          }
          setToolCalls(prev => [...prev, toolCall])
        }

        // Handle Glass Box thinking events
        if (eventType === 'thinking') {
          const thinking: ThinkingEvent = {
            type: 'thinking',
            stage: rawData.stage ?? 'planning',
            thought: rawData.thought ?? '',
            timestamp: rawData.timestamp,
          }
          setThoughts(prev => [...prev, thinking])
        }

        // Handle progress events (both legacy and new formats)
        if (data.event === 'research.progress') {
          setProgress(data.data.progress_percent || 0)
        } else if (eventType === 'progress') {
          // Support both rawData.progress_percent and payload.progress_percent
          const progressValue = rawData.progress_percent ?? rawData.data?.progress_percent ?? 0
          if (typeof progressValue === 'number') {
            setProgress(progressValue)
          }
        }

        // Handle failure events (both legacy and new formats)
        if (data.event === 'research.failed') {
          setError(new Error(data.data.error_message || 'Research failed'))
          currentOptions.onError?.(new Error(data.data.error_message || 'Research failed'))
        } else if (eventType === 'error') {
          const errorMsg = rawData.content || rawData.message || rawData.error_message || 'Research error'
          setError(new Error(errorMsg))
          currentOptions.onError?.(new Error(errorMsg))
        }

        setEvents(prev => [...prev, data])
        setCurrentEvent(data)
        currentOptions.onMessage?.(data)
      },
      onError: (error) => {
        setError(error)
        setIsConnected(false)
        currentOptions.onError?.(error)
      },
      onClose: () => {
        setIsConnected(false)
        currentOptions.onClose?.()
      },
    })

    connectionRef.current = connection
  }, [url]) // Remove options from dependencies since we use optionsRef

  const stop = useCallback(() => {
    if (connectionRef.current) {
      cancelSSEConnection(connectionRef.current)
      connectionRef.current = null
      setIsConnected(false)
    }
  }, [])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stop()
    }
  }, [stop])

  const reset = useCallback(() => {
    setEvents([])
    setCurrentEvent(null)
    setError(null)
    setProgress(0)
    setToolCalls([])
    setThoughts([])
  }, [])

  return {
    events,
    currentEvent,
    isConnected,
    error,
    progress,
    // Glass Box UX data
    toolCalls,
    thoughts,
    start,
    stop,
    reset,
  }
}

/**
 * Generic SSE hook for any SSE endpoint
 */
export function useSSE<T = any>(url: string, options: SSEOptions = {}) {
  const [data, setData] = useState<T[]>([])
  const [current, setCurrent] = useState<T | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  const [lastEventId, setLastEventId] = useState<string | undefined>(undefined)

  const start = useCallback(() => {
    const connection = sseManager.get(url)

    if (connection) {
      sseManager.disconnect(url)
    }

    sseManager.connect(url, url, {
      ...options,
      onOpen: () => {
        setIsConnected(true)
        setError(null)
        options.onOpen?.()
      },
      onMessage: (message: T) => {
        setData(prev => [...prev, message])
        setCurrent(message)
        options.onMessage?.(message)
      },
      onError: (error) => {
        setError(error)
        setIsConnected(false)
        options.onError?.(error)
      },
      onClose: () => {
        setIsConnected(false)
        options.onClose?.()
      },
    })
  }, [url, options])

  const stop = useCallback(() => {
    sseManager.disconnect(url)
    setIsConnected(false)
  }, [url])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stop()
    }
  }, [stop])

  const reset = useCallback(() => {
    setData([])
    setCurrent(null)
    setError(null)
    setLastEventId(undefined)
  }, [])

  return {
    data,
    current,
    isConnected,
    error,
    lastEventId,
    start,
    stop,
    reset,
  }
}

/**
 * Hook with auto-reconnect
 */
export function useSSEWithReconnect(url: string, options: SSEOptions & { maxReconnects?: number; reconnectDelayMs?: number } = {}) {
  const { maxReconnects = 3, reconnectDelayMs = 1000, ...sseOptions } = options
  const [reconnectAttempts, setReconnectAttempts] = useState(0)
  const { start: baseStart, stop, ...rest } = useSSE(url, sseOptions)

  const start = useCallback(() => {
    setReconnectAttempts(0)
    baseStart()
  }, [baseStart])

  // Enhanced error handler that auto-reconnects
  useEffect(() => {
    const enhancedOptions = {
      ...sseOptions,
      onError: (error: Error) => {
        if (reconnectAttempts < maxReconnects) {
          setReconnectAttempts(prev => prev + 1)
          setTimeout(() => {
            start()
          }, reconnectDelayMs)
        }
        sseOptions.onError?.(error)
      },
    }

    // Note: This is simplified. In real usage, you'd need to recreate the connection with enhanced options
  }, [reconnectAttempts, maxReconnects, reconnectDelayMs, sseOptions])

  return {
    ...rest,
    start,
    stop,
    reconnectAttempts,
  }
}

/**
 * Hook with request/response headers
 */
export function useSSEWithHeaders(url: string, options: SSEOptions & { headers?: Record<string, string> } = {}) {
  const { headers = {}, ...sseOptions } = options

  const start = useCallback(() => {
    // Append default SSE headers
    const enhancedHeaders = {
      ...defaultSSEHeaders,
      ...headers,
    }

    // Note: In real usage, you'd pass these headers in the fetch call
    // EventSource doesn't support custom headers natively
    // Would need to use fetch with ReadableStream instead
  }, [url, headers, sseOptions])

  return useSSE(url, sseOptions)
}

/**
 * Cleanup hook for SSE manager
 */
export function useSSEManager(manager: SSEManager = sseManager) {
  useEffect(() => {
    return () => {
      manager.disconnectAll()
    }
  }, [manager])
}

/**
 * Hook for batching SSE messages
 */
export function useSSEBatched<T = any>(
  url: string,
  options: SSEOptions & { batchSize?: number; flushDelayMs?: number } = {}
) {
  const { batchSize = 10, flushDelayMs = 50, ...sseOptions } = options
  const [batch, setBatch] = useState<T[]>([])
  const batchProcessorRef = useRef<any>(null)

  const { start: baseStart, stop, ...rest } = useSSE(url, sseOptions)

  const start = useCallback(() => {
    const { SSEBatchProcessor } = require('../lib/sse')
    batchProcessorRef.current = new SSEBatchProcessor(
      (batchedData: T[]) => {
        setBatch(prev => [...prev, ...batchedData])
      },
      { maxBatchSize: batchSize, flushDelayMs }
    )

    baseStart()
  }, [url, batchSize, flushDelayMs, baseStart])

  return {
    ...rest,
    batch,
    start,
    stop,
  }
}

export {
  sseManager,
  defaultSSEHeaders,
}

export default {
  useChatSSE,
  useResearchSSE,
  useSSE,
  useSSEWithReconnect,
  useSSEWithHeaders,
  useSSEManager,
  useSSEBatched,
}
