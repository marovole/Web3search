import React, { useState, useRef, useCallback } from 'react'

interface TouchPoint {
  x: number
  y: number
  timestamp: number
}

interface SwipeConfig {
  threshold?: number
  restraint?: number
  allowedTime?: number
}

interface LongPressConfig {
  duration?: number
  moveThreshold?: number
}

interface GestureCallbacks {
  onSwipeLeft?: () => void
  onSwipeRight?: () => void
  onSwipeUp?: () => void
  onSwipeDown?: () => void
  onLongPress?: () => void
  onTouchStart?: (touch: TouchPoint) => void
  onTouchEnd?: (touch: TouchPoint) => void
}

interface UseTouchGesturesOptions {
  swipeConfig?: SwipeConfig
  longPressConfig?: LongPressConfig
}

export const useTouchGestures = (
  callbacks: GestureCallbacks,
  options: UseTouchGesturesOptions = {}
) => {
  const {
    swipeConfig = { threshold: 50, restraint: 100, allowedTime: 300 },
    longPressConfig = { duration: 500, moveThreshold: 10 }
  } = options

  const {
    onSwipeLeft,
    onSwipeRight,
    onSwipeUp,
    onSwipeDown,
    onLongPress,
    onTouchStart,
    onTouchEnd
  } = callbacks

  const [isLongPressing, setIsLongPressing] = useState(false)
  const touchStartRef = useRef<TouchPoint | null>(null)
  const touchEndRef = useRef<TouchPoint | null>(null)
  const longPressTimerRef = useRef<NodeJS.Timeout | null>(null)
  const hasMovedRef = useRef(false)

  const handleTouchStart = useCallback((e: React.TouchEvent) => {
    const touch = e.touches[0]
    if (!touch) return
    const touchPoint: TouchPoint = {
      x: touch.clientX,
      y: touch.clientY,
      timestamp: Date.now()
    }

    touchStartRef.current = touchPoint
    touchEndRef.current = touchPoint
    hasMovedRef.current = false
    setIsLongPressing(false)

    // Start long press timer
    longPressTimerRef.current = setTimeout(() => {
      if (!hasMovedRef.current) {
        setIsLongPressing(true)
        onLongPress?.()
      }
    }, longPressConfig.duration)

    onTouchStart?.(touchPoint)
  }, [onLongPress, onTouchStart, longPressConfig.duration])

  const handleTouchMove = useCallback((e: React.TouchEvent) => {
    if (!touchStartRef.current) return

    const touch = e.touches[0]
    if (!touch) return
    const currentPoint: TouchPoint = {
      x: touch.clientX,
      y: touch.clientY,
      timestamp: Date.now()
    }

    touchEndRef.current = currentPoint

    // Check if movement exceeds threshold for long press
    const deltaX = Math.abs(currentPoint.x - touchStartRef.current.x)
    const deltaY = Math.abs(currentPoint.y - touchStartRef.current.y)
    const moveThreshold = longPressConfig.moveThreshold ?? 10

    if (deltaX > moveThreshold || deltaY > moveThreshold) {
      hasMovedRef.current = true

      // Clear long press timer if moved too much
      if (longPressTimerRef.current) {
        clearTimeout(longPressTimerRef.current)
        longPressTimerRef.current = null
      }
    }
  }, [longPressConfig.moveThreshold])

  const handleTouchEnd = useCallback((e: React.TouchEvent) => {
    // Clear long press timer
    if (longPressTimerRef.current) {
      clearTimeout(longPressTimerRef.current)
      longPressTimerRef.current = null
    }

    if (!touchStartRef.current || !touchEndRef.current || isLongPressing) {
      setIsLongPressing(false)
      onTouchEnd?.(touchEndRef.current!)
      return
    }

    const startX = touchStartRef.current.x
    const startY = touchStartRef.current.y
    const endX = touchEndRef.current.x
    const endY = touchEndRef.current.y
    const startTime = touchStartRef.current.timestamp
    const endTime = touchEndRef.current.timestamp

    const elapsedTime = endTime - startTime
    const deltaX = endX - startX
    const deltaY = endY - startY

    // Check if it's a valid swipe
    const allowedTime = swipeConfig.allowedTime ?? 300
    const threshold = swipeConfig.threshold ?? 50
    const restraint = swipeConfig.restraint ?? 100

    if (elapsedTime <= allowedTime) {
      if (Math.abs(deltaX) >= threshold && Math.abs(deltaY) <= restraint) {
        // Horizontal swipe
        if (deltaX > 0) {
          onSwipeRight?.()
        } else {
          onSwipeLeft?.()
        }
      } else if (Math.abs(deltaY) >= threshold && Math.abs(deltaX) <= restraint) {
        // Vertical swipe
        if (deltaY > 0) {
          onSwipeDown?.()
        } else {
          onSwipeUp?.()
        }
      }
    }

    setIsLongPressing(false)
    onTouchEnd?.(touchEndRef.current)
  }, [isLongPressing, onSwipeLeft, onSwipeRight, onSwipeUp, onSwipeDown, onTouchEnd, swipeConfig])

  // Cleanup on unmount
  const cleanup = useCallback(() => {
    if (longPressTimerRef.current) {
      clearTimeout(longPressTimerRef.current)
      longPressTimerRef.current = null
    }
  }, [])

  return {
    handleTouchStart,
    handleTouchMove,
    handleTouchEnd,
    isLongPressing,
    cleanup
  }
}

// Simplified hook for basic swipe detection
export const useSwipe = (
  onSwipeLeft?: () => void,
  onSwipeRight?: () => void,
  threshold: number = 50
) => {
  return useTouchGestures({
    onSwipeLeft,
    onSwipeRight
  }, {
    swipeConfig: { threshold, restraint: 100, allowedTime: 300 }
  })
}

// Hook for detecting keyboard visibility on mobile
export const useKeyboardDetection = () => {
  const [isKeyboardOpen, setIsKeyboardOpen] = useState(false)
  const [keyboardHeight, setKeyboardHeight] = useState(0)

  React.useEffect(() => {
    const handleResize = () => {
      const viewportHeight = window.innerHeight
      const initialHeight = window.screen.height
      const heightDiff = initialHeight - viewportHeight

      if (heightDiff > 150) { // Threshold for keyboard detection
        setIsKeyboardOpen(true)
        setKeyboardHeight(heightDiff)
      } else {
        setIsKeyboardOpen(false)
        setKeyboardHeight(0)
      }
    }

    const handleVisualViewportChange = () => {
      if (window.visualViewport) {
        const viewport = window.visualViewport
        const heightDiff = window.innerHeight - viewport.height

        if (heightDiff > 150) {
          setIsKeyboardOpen(true)
          setKeyboardHeight(heightDiff)
        } else {
          setIsKeyboardOpen(false)
          setKeyboardHeight(0)
        }
      }
    }

    window.addEventListener('resize', handleResize)

    if (window.visualViewport) {
      window.visualViewport.addEventListener('resize', handleVisualViewportChange)
    }

    return () => {
      window.removeEventListener('resize', handleResize)
      if (window.visualViewport) {
        window.visualViewport.removeEventListener('resize', handleVisualViewportChange)
      }
    }
  }, [])

  return {
    isKeyboardOpen,
    keyboardHeight
  }
}