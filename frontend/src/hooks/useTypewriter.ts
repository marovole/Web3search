/**
 * 打字机效果Hook（任务 8.3）
 *
 * 功能：
 * 1. 逐字符显示文本内容
 * 2. 可配置显示速度（30-50ms/字符）
 * 3. 支持跳过动画（用户点击）
 * 4. 与流式响应配合工作
 */
import { useState, useEffect, useRef } from 'react'

interface UseTypewriterOptions {
  /**
   * 打字速度（毫秒/字符）
   * @default 40
   */
  speed?: number

  /**
   * 是否启用打字机效果
   * @default true
   */
  enabled?: boolean

  /**
   * 是否正在流式传输
   * @default false
   */
  isStreaming?: boolean

  /**
   * 完成回调
   */
  onComplete?: () => void
}

interface UseTypewriterReturn {
  /**
   * 当前显示的文本
   */
  displayedText: string

  /**
   * 是否正在打字
   */
  isTyping: boolean

  /**
   * 跳过打字动画，立即显示全部内容
   */
  skipAnimation: () => void

  /**
   * 重置打字机状态
   */
  reset: () => void
}

/**
 * 打字机效果Hook
 *
 * @example
 * ```tsx
 * const { displayedText, isTyping, skipAnimation } = useTypewriter({
 *   text: "Hello World",
 *   speed: 40,
 *   enabled: true,
 *   isStreaming: false
 * })
 * ```
 */
export function useTypewriter(
  text: string,
  options: UseTypewriterOptions = {}
): UseTypewriterReturn {
  const {
    speed = 40,
    enabled = true,
    isStreaming = false,
    onComplete
  } = options

  const [displayedText, setDisplayedText] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [shouldSkip, setShouldSkip] = useState(false)

  // 使用ref存储定时器ID，避免闭包问题
  const timerRef = useRef<NodeJS.Timeout | null>(null)
  const currentIndexRef = useRef(0)

  // 跳过动画
  const skipAnimation = () => {
    setShouldSkip(true)
  }

  // 重置状态
  const reset = () => {
    setDisplayedText('')
    setIsTyping(false)
    setShouldSkip(false)
    currentIndexRef.current = 0
    if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }
  }

  useEffect(() => {
    // 如果禁用打字机效果，直接显示全文
    if (!enabled) {
      setDisplayedText(text)
      setIsTyping(false)
      return
    }

    // 如果需要跳过动画，直接显示全文
    if (shouldSkip) {
      setDisplayedText(text)
      setIsTyping(false)
      if (onComplete && text.length > 0) {
        onComplete()
      }
      return
    }

    // 如果文本为空，重置状态
    if (text.length === 0) {
      reset()
      return
    }

    // 如果正在流式传输，不启动打字机效果，直接显示
    // 等待流式结束后再启动
    if (isStreaming) {
      setDisplayedText(text)
      return
    }

    // 如果已经显示了全部内容，不需要重新打字
    if (displayedText === text && currentIndexRef.current >= text.length) {
      setIsTyping(false)
      return
    }

    // 开始打字动画
    setIsTyping(true)
    currentIndexRef.current = displayedText.length

    // 清除之前的定时器
    if (timerRef.current) {
      clearInterval(timerRef.current)
    }

    // 创建新的打字定时器
    timerRef.current = setInterval(() => {
      currentIndexRef.current += 1

      if (currentIndexRef.current >= text.length) {
        // 打字完成
        setDisplayedText(text)
        setIsTyping(false)

        if (timerRef.current) {
          clearInterval(timerRef.current)
          timerRef.current = null
        }

        if (onComplete) {
          onComplete()
        }
      } else {
        // 逐字符显示
        setDisplayedText(text.slice(0, currentIndexRef.current))
      }
    }, speed)

    // 清理函数
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current)
        timerRef.current = null
      }
    }
  }, [text, enabled, isStreaming, shouldSkip, speed, onComplete, displayedText])

  return {
    displayedText,
    isTyping,
    skipAnimation,
    reset
  }
}
