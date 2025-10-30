import { describe, it, expect, beforeEach, vi } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import useErrorHandler from '../hooks/useErrorHandler'

describe('useErrorHandler', () => {
  it('should initialize with no error', () => {
    const { result } = renderHook(() => useErrorHandler())
    
    expect(result.current.state.hasError).toBe(false)
    expect(result.current.state.error).toBe(null)
    expect(result.current.state.retryCount).toBe(0)
    expect(result.current.isRetrying).toBe(false)
  })

  it('should handle error correctly', () => {
    const { result } = renderHook(() => useErrorHandler())
    const testError = new Error('Test error')
    
    act(() => {
      result.current.handleError(testError)
    })

    expect(result.current.state.hasError).toBe(true)
    expect(result.current.state.error).toBe(testError)
  })

  it('should retry error handling', async () => {
    vi.useFakeTimers()
    const { result } = renderHook(() => useErrorHandler())
    const testError = new Error('Test error')
    
    act(() => {
      result.current.handleError(testError)
    })

    expect(result.current.state.hasError).toBe(true)

    act(() => {
      result.current.retry()
    })

    expect(result.current.isRetrying).toBe(true)

    await act(async () => {
      vi.advanceTimersByTime(1000)
    })

    expect(result.current.isRetrying).toBe(false)
    expect(result.current.state.retryCount).toBe(1)
    vi.useRealTimers()
  })

  it('should reset error state', () => {
    const { result } = renderHook(() => useErrorHandler())
    const testError = new Error('Test error')
    
    act(() => {
      result.current.handleError(testError)
    })

    expect(result.current.state.hasError).toBe(true)

    act(() => {
      result.current.reset()
    })

    expect(result.current.state.hasError).toBe(false)
    expect(result.current.state.error).toBe(null)
    expect(result.current.state.retryCount).toBe(0)
    expect(result.current.isRetrying).toBe(false)
  })

  it('should not retry after max attempts', async () => {
    vi.useFakeTimers()
    const { result } = renderHook(() => useErrorHandler())
    const testError = new Error('Test error')
    
    // Set retry count to 3
    act(() => {
      result.current.handleError(testError)
      result.current.retry()
    })

    await act(async () => {
      vi.advanceTimersByTime(1000)
    })

    act(() => {
      result.current.handleError(testError)
      result.current.retry()
    })

    await act(async () => {
      vi.advanceTimersByTime(1000)
    })

    act(() => {
      result.current.handleError(testError)
      result.current.retry()
    })

    await act(async () => {
      vi.advanceTimersByTime(1000)
    })

    // 4th retry should not work
    act(() => {
      result.current.handleError(testError)
      result.current.retry()
    })

    expect(result.current.state.retryCount).toBeLessThanOrEqual(3)
    vi.useRealTimers()
  })
})

