import React from 'react'

interface NetworkErrorRetryProps {
  onRetry: () => void
  error?: string
  isRetrying?: boolean
  retryCount?: number
}

const NetworkErrorRetry: React.FC<NetworkErrorRetryProps> = ({
  onRetry,
  error,
  isRetrying = false,
  retryCount = 0,
}) => {
  const getErrorSuggestion = (errorMessage: string): string => {
    if (errorMessage.includes('Network Error') || errorMessage.includes('fetch')) {
      return '网络连接失败，请检查网络连接后重试'
    }
    if (errorMessage.includes('timeout')) {
      return '请求超时，请稍后重试'
    }
    if (errorMessage.includes('500')) {
      return '服务器暂时不可用，请稍后重试'
    }
    if (errorMessage.includes('401') || errorMessage.includes('403')) {
      return '认证失败，请刷新页面后重试'
    }
    if (errorMessage.includes('429')) {
      return '请求过于频繁，请稍等片刻后重试'
    }
    return '发生未知错误，请重试'
  }

  const suggestion = error ? getErrorSuggestion(error) : '发生错误，请重试'

  return (
    <div className="flex items-center justify-center p-4">
      <div className="text-center max-w-sm">
        <div className="text-orange-500 mb-3">
          <svg
            className="w-8 h-8 mx-auto"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        </div>

        <p className="text-sm text-gray-600 mb-4">
          {suggestion}
        </p>

        <div className="flex items-center justify-center gap-3">
          <button
            onClick={onRetry}
            disabled={isRetrying || retryCount >= 3}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-primary bg-primary/10 border border-primary/200 rounded-lg hover:bg-primary/20 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isRetrying ? (
              <>
                <svg
                  className="animate-spin h-4 w-4"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  ></circle>
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  ></path>
                </svg>
                重试中...
              </>
            ) : (
              <>
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                  />
                </svg>
                重试
              </>
            )}
          </button>

          {retryCount >= 3 && (
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
            >
              刷新页面
            </button>
          )}
        </div>

        {retryCount > 0 && retryCount < 3 && (
          <p className="text-xs text-gray-500 mt-2">
            已重试 {retryCount} 次，最多重试 3 次
          </p>
        )}

        {retryCount >= 3 && (
          <p className="text-xs text-orange-600 mt-2">
            已达到最大重试次数，如果问题持续存在，请刷新页面
          </p>
        )}
      </div>
    </div>
  )
}

export default NetworkErrorRetry