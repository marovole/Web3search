import { useState, useCallback } from 'react'
import { captureException } from '../services/sentry'

interface ErrorHandlerState {
  hasError: boolean
  error: Error | null
  errorInfo: React.ErrorInfo | null
  retryCount: number
}

interface UseErrorHandlerReturn {
  state: ErrorHandlerState
  handleError: (error: Error, errorInfo?: React.ErrorInfo) => void
  retry: () => void
  reset: () => void
  isRetrying: boolean
}

const useErrorHandler = (): UseErrorHandlerReturn => {
  const [state, setState] = useState<ErrorHandlerState>({
    hasError: false,
    error: null,
    errorInfo: null,
    retryCount: 0,
  })
  const [isRetrying, setIsRetrying] = useState(false)

  const handleError = useCallback((error: Error, errorInfo?: React.ErrorInfo) => {
    console.error('Error caught by useErrorHandler:', error, errorInfo)

    setState(prev => ({
      ...prev,
      hasError: true,
      error,
      errorInfo: errorInfo || null,
    }))

    // Capture errors in production only
    if (import.meta.env?.PROD) {
      captureException(error, { component: 'useErrorHandler', errorInfo })
    }
  }, [])

  const retry = useCallback(async () => {
    if (state.retryCount >= 3) {
      console.warn('Max retry attempts reached')
      return
    }

    setIsRetrying(true)
    setState(prev => ({
      ...prev,
      hasError: false,
      error: null,
      errorInfo: null,
      retryCount: prev.retryCount + 1,
    }))

    // Wait briefly before retrying
    await new Promise(resolve => setTimeout(resolve, 1000))

    setIsRetrying(false)
  }, [state.retryCount])

  const reset = useCallback(() => {
    setState({
      hasError: false,
      error: null,
      errorInfo: null,
      retryCount: 0,
    })
    setIsRetrying(false)
  }, [])

  return {
    state,
    handleError,
    retry,
    reset,
    isRetrying,
  }
}

export default useErrorHandler
