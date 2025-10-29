import { useState, useCallback, useRef } from 'react'

interface NetworkRetryOptions {
  maxRetries?: number
  retryDelay?: number
  exponentialBackoff?: boolean
}

interface NetworkRetryState {
  isLoading: boolean
  error: string | null
  retryCount: number
}

interface UseNetworkRetryReturn<T extends any[], R> {
  state: NetworkRetryState
  execute: (...args: T) => Promise<R>
  reset: () => void
}

const useNetworkRetry = <T extends any[], R>(
  fn: (...args: T) => Promise<R>,
  options: NetworkRetryOptions = {}
): UseNetworkRetryReturn<T, R> => {
  const {
    maxRetries = 3,
    retryDelay = 1000,
    exponentialBackoff = true,
  } = options

  const [state, setState] = useState<NetworkRetryState>({
    isLoading: false,
    error: null,
    retryCount: 0,
  })

  const abortControllerRef = useRef<AbortController | null>(null)

  const execute = useCallback(
    async (...args: T): Promise<R> => {
      // 取消之前的请求
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }

      abortControllerRef.current = new AbortController()

      setState(prev => ({ ...prev, isLoading: true, error: null }))

      let lastError: Error | null = null

      for (let attempt = 0; attempt <= maxRetries; attempt++) {
        try {
          const result = await fn(...args)
          setState({
            isLoading: false,
            error: null,
            retryCount: attempt,
          })
          return result
        } catch (error) {
          lastError = error instanceof Error ? error : new Error(String(error))

          // 如果是 AbortError，说明请求被取消，不重试
          if (lastError.name === 'AbortError') {
            throw lastError
          }

          console.warn(`Attempt ${attempt + 1} failed:`, lastError.message)

          // 如果是最后一次尝试，抛出错误
          if (attempt === maxRetries) {
            setState({
              isLoading: false,
              error: lastError.message,
              retryCount: attempt + 1,
            })
            throw lastError
          }

          // 计算延迟时间
          let delay = retryDelay
          if (exponentialBackoff) {
            delay = retryDelay * Math.pow(2, attempt)
          }

          // 等待后重试
          await new Promise(resolve => setTimeout(resolve, delay))
        }
      }

      // 理论上不会到达这里，但 TypeScript 需要这个返回
      throw lastError || new Error('Unknown error occurred')
    },
    [fn, maxRetries, retryDelay, exponentialBackoff]
  )

  const reset = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
    setState({
      isLoading: false,
      error: null,
      retryCount: 0,
    })
  }, [])

  return {
    state,
    execute,
    reset,
  }
}

export default useNetworkRetry