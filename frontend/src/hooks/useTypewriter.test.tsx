import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useTypewriter } from '../hooks/useTypewriter'

describe('useTypewriter', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('should initialize with empty text', () => {
    const { result } = renderHook(() => useTypewriter(''))
    
    expect(result.current.displayedText).toBe('')
    expect(result.current.isTyping).toBe(false)
  })

  it('should display text immediately when disabled', () => {
    const { result } = renderHook(() => useTypewriter('Hello', { enabled: false }))
    
    expect(result.current.displayedText).toBe('Hello')
    expect(result.current.isTyping).toBe(false)
  })

  it('should type text character by character', async () => {
    const { result } = renderHook(() => useTypewriter('Hi', { speed: 50 }))
    
    expect(result.current.displayedText).toBe('')
    expect(result.current.isTyping).toBe(true)

    act(() => {
      vi.advanceTimersByTime(50)
    })
    expect(result.current.displayedText).toBe('H')

    act(() => {
      vi.advanceTimersByTime(50)
    })
    expect(result.current.displayedText).toBe('Hi')
    expect(result.current.isTyping).toBe(false)
  })

  it('should skip animation when skipAnimation is called', () => {
    const { result } = renderHook(() => useTypewriter('Hello World', { speed: 100 }))
    
    act(() => {
      result.current.skipAnimation()
    })
    
    expect(result.current.displayedText).toBe('Hello World')
    expect(result.current.isTyping).toBe(false)
  })

  it('should reset state', async () => {
    const { result } = renderHook(() => useTypewriter('Hello', { enabled: true, speed: 50 }))
    
    act(() => {
      vi.advanceTimersByTime(300)
    })
    
    expect(result.current.displayedText).toBe('Hello')
    
    act(() => {
      result.current.reset()
    })
    
    // Wait for reset to complete
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0))
    })
    
    expect(result.current.displayedText).toBe('')
    expect(result.current.isTyping).toBe(false)
  })

  it('should call onComplete when typing finishes', () => {
    const onComplete = vi.fn()
    renderHook(() => useTypewriter('Hi', { speed: 50, onComplete }))
    
    act(() => {
      vi.advanceTimersByTime(150)
    })
    
    expect(onComplete).toHaveBeenCalled()
  })

  it('should display text immediately when streaming', () => {
    const { result } = renderHook(() => useTypewriter('Streaming text', { isStreaming: true }))
    
    expect(result.current.displayedText).toBe('Streaming text')
    expect(result.current.isTyping).toBe(false)
  })
})

