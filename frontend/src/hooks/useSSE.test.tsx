/**
 * SSE React Hooks Tests
 * TDD tests for useChatSSE and related hooks
 * Part of Week 2 T13: Frontend SSE Integration
 */

import { renderHook, act } from '@testing-library/react'
import { useSSE } from '../lib/sse-tool'
import { ChatSSEEvent, ResearchSSEvent } from '../lib/sse'

describe('useSSE', () => {
  let mockEventSource: any
  let mockAbortController: AbortController

  beforeEach(() => {
    mockAbortController = new AbortController()

    // Mock EventSource
    mockEventSource = {
      onopen: null,
      onmessage: null,
      onerror: null,
      close: jest.fn(),
      url: 'https://test-api.com/sse',
      readyState: 0,
      withCredentials: false
    }

    global.EventSource = jest.fn(() => mockEventSource) as any
  })

  afterEach(() => {
    jest.clearAllMocks()
  })

  describe('AbortController timeout', () => {
    it('should abort connection after timeout', () => {
      jest.useFakeTimers()

      const { result } = renderHook(() =>
        useSSE('https://test-api.com/sse', { timeoutMs: 5000 })
      )

      // Start connection
      act(() => {
        result.current.start()
      })

      // Trigger timeout
      act(() => {
        jest.advanceTimersByTime(5001)
      })

      // Should have error
      expect(result.current.error).toBeDefined()
      expect(result.current.error?.message).toMatch(/timeout/)

      jest.useRealTimers()
    })

    it('should clear timeout on successful connection', () => {
      jest.useFakeTimers()

      const { result } = renderHook(() =>
        useSSE('https://test-api.com/sse', { timeoutMs: 5000 })
      )

      // Start connection
      act(() => {
        result.current.start()
      })

      // Simulate successful connection
      act(() => {
        mockEventSource.onopen?.()
      })

      // Advance time past timeout
      act(() => {
        jest.advanceTimersByTime(6000)
      })

      // Should NOT have timeout error
      expect(result.current.error).toBeNull()
      expect(result.current.isConnected).toBe(true)

      jest.useRealTimers()
    })
  })

  describe('SSE message processing', () => {
    it('should handle chat SSE messages', () => {
      const { result } = renderHook(() =>
        useSSE<ChatSSEEvent>('https://test-api.com/chat')
      )

      // Start connection
      act(() => {
        result.current.start()
      })

      // Simulate connection open
      act(() => {
        mockEventSource.onopen?.()
      })

      // Simulate message
      const mockMessage: ChatSSEEvent = {
        delta: { content: 'Hello' },
        finish_reason: null
      }

      act(() => {
        mockEventSource.onmessage?.({
          data: JSON.stringify(mockMessage),
          lastEventId: '1',
          origin: 'https://test-api.com',
          type: 'message',
          timeStamp: Date.now()
        })
      })

      expect(result.current.data).toHaveLength(1)
      expect(result.current.current).toEqual(mockMessage)
    })

    it('should handle research SSE progress updates', () => {
      const { result } = renderHook(() =>
        useSSE<ResearchSSEvent>('https://test-api.com/research')
      )

      act(() => {
        result.current.start()
      })

      act(() => {
        mockEventSource.onopen?.()
      })

      // Simulate progress update
      const progressEvent: ResearchSSEvent = {
        event: 'research.progress',
        data: { progress_percent: 50, task_id: '123' }
      }

      act(() => {
        mockEventSource.onmessage?.({
          data: JSON.stringify(progressEvent),
          lastEventId: '2',
          origin: 'https://test-api.com',
          type: 'message',
          timeStamp: Date.now()
        })
      })

      expect(result.current.data[0].event).toBe('research.progress')
      expect(result.current.data[0].data.progress_percent).toBe(50)
    })
  })

  describe('Auto-reconnect', () => {
    it('should reconnect after connection loss', () => {
      jest.useFakeTimers()

      const { result } = renderHook(() =>
        useSSE('https://test-api.com/sse', {
          maxReconnectAttempts: 3,
          reconnectDelayMs: 1000
        })
      )

      act(() => {
        result.current.start()
      })

      // Simulate connection error
      act(() => {
        mockEventSource.onerror?.(new Error('Connection lost'))
      })

      // Should attempt reconnect
      act(() => {
        jest.advanceTimersByTime(1001)
      })

      expect(global.EventSource).toHaveBeenCalledTimes(2) // Original + 1 reconnect

      jest.useRealTimers()
    })
  })
})
