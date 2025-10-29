import React from 'react'

interface SkeletonLoaderProps {
  type?: 'message' | 'input' | 'card' | 'list'
  count?: number
  className?: string
}

const SkeletonLoader: React.FC<SkeletonLoaderProps> = ({
  type = 'message',
  count = 1,
  className = '',
}) => {
  const renderSkeleton = () => {
    switch (type) {
      case 'message':
        return (
          <div className="flex gap-3 animate-pulse">
            <div className="w-8 h-8 bg-gray-200 rounded-full flex-shrink-0"></div>
            <div className="flex-1 space-y-2">
              <div className="h-4 bg-gray-200 rounded w-3/4"></div>
              <div className="h-4 bg-gray-200 rounded w-1/2"></div>
              <div className="h-4 bg-gray-200 rounded w-2/3"></div>
            </div>
          </div>
        )

      case 'input':
        return (
          <div className="animate-pulse">
            <div className="h-12 bg-gray-200 rounded-lg"></div>
            <div className="h-4 bg-gray-200 rounded w-1/4 mt-2"></div>
          </div>
        )

      case 'card':
        return (
          <div className="bg-white p-4 rounded-lg border border-gray-200 animate-pulse">
            <div className="h-6 bg-gray-200 rounded w-1/3 mb-3"></div>
            <div className="space-y-2">
              <div className="h-4 bg-gray-200 rounded"></div>
              <div className="h-4 bg-gray-200 rounded w-5/6"></div>
              <div className="h-4 bg-gray-200 rounded w-4/6"></div>
            </div>
          </div>
        )

      case 'list':
        return (
          <div className="space-y-3 animate-pulse">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex items-center gap-3">
                <div className="w-12 h-12 bg-gray-200 rounded-lg"></div>
                <div className="flex-1 space-y-2">
                  <div className="h-4 bg-gray-200 rounded w-1/3"></div>
                  <div className="h-3 bg-gray-200 rounded w-2/3"></div>
                </div>
              </div>
            ))}
          </div>
        )

      default:
        return (
          <div className="h-4 bg-gray-200 rounded animate-pulse"></div>
        )
    }
  }

  return (
    <div className={className}>
      {Array.from({ length: count }, (_, i) => (
        <div key={i} className={count > 1 ? 'mb-4 last:mb-0' : ''}>
          {renderSkeleton()}
        </div>
      ))}
    </div>
  )
}

export default SkeletonLoader