import React from 'react'
import type { ChatMode } from '../../types'

interface LoadingAnimationProps {
  stage: number
  mode: ChatMode
}

const LoadingAnimation: React.FC<LoadingAnimationProps> = ({ stage, mode }) => {
  // Loading stages for Deep Research
  const deepResearchStages = [
    { emoji: '📊', text: '正在采集市场数据...' },
    { emoji: '🔗', text: '正在分析链上活动...' },
    { emoji: '💬', text: '正在评估社交情绪...' },
    { emoji: '📈', text: '正在生成技术面分析...' },
    { emoji: '📝', text: '正在组装报告...' },
  ]

  const currentStage = deepResearchStages[Math.min(stage, deepResearchStages.length - 1)]

  return (
    <div className="flex flex-col items-start mb-4 animate-fade-in">
      <div className="message-assistant">
        {mode === 'quick' ? (
          // Quick Chat loading
          <div className="flex items-center gap-3">
            <div className="flex gap-1">
              <span className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
              <span className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
              <span className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
            </div>
            <span className="text-sm text-gray-600">正在思考...</span>
          </div>
        ) : (
          // Deep Research loading with stages
          <div className="space-y-4">
            {/* Current stage */}
            <div className="flex items-center gap-3">
              <span className="text-2xl">{currentStage.emoji}</span>
              <span className="text-sm font-medium text-gray-700">
                {currentStage.text}
              </span>
            </div>

            {/* Progress bar */}
            <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
              <div
                className="bg-primary h-full transition-all duration-500 ease-out"
                style={{
                  width: `${((stage + 1) / deepResearchStages.length) * 100}%`,
                }}
              ></div>
            </div>

            {/* Stage indicators */}
            <div className="flex justify-between text-xs text-gray-500">
              {deepResearchStages.map((s, i) => (
                <span
                  key={i}
                  className={`transition-colors ${
                    i <= stage ? 'text-primary font-medium' : ''
                  }`}
                >
                  {s.emoji}
                </span>
              ))}
            </div>

            {/* Skeleton loader for report preview */}
            <div className="mt-6 space-y-2 animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-3/4"></div>
              <div className="h-4 bg-gray-200 rounded w-full"></div>
              <div className="h-4 bg-gray-200 rounded w-5/6"></div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default LoadingAnimation
