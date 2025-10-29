import React, { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Zap, Search } from 'lucide-react'
import type { ChatMode } from '../../types'

interface ModeSwitchProps {
  mode: ChatMode
  onChange: (mode: ChatMode) => void
}

const ModeSwitch: React.FC<ModeSwitchProps> = ({ mode, onChange }) => {
  const [isTransitioning, setIsTransitioning] = useState(false)

  const handleModeChange = (newMode: ChatMode) => {
    if (newMode !== mode && !isTransitioning) {
      setIsTransitioning(true)

      // 添加短暂的延迟以确保动画完成
      setTimeout(() => {
        onChange(newMode)
        setTimeout(() => {
          setIsTransitioning(false)
        }, 100)
      }, 150)
    }
  }

  return (
    <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4">
      <div className="flex items-center gap-2">
        <span className="text-sm font-medium text-foreground">模式选择</span>
      </div>

      <div className="relative">
        {/* 背景滑动指示器 */}
        <div
          className={`
            absolute top-1 bottom-1 bg-primary rounded-md shadow-sm transition-all duration-300 ease-in-out
            ${isTransitioning ? 'scale-95' : 'scale-100'}
          `}
          style={{
            left: mode === 'quick' ? '4px' : '50%',
            width: 'calc(50% - 4px)',
            transform: mode === 'quick' ? 'translateX(0)' : 'translateX(-100%)',
          }}
        />

        <div className="flex bg-muted rounded-lg p-1 relative z-10">
          {/* Quick Chat */}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => handleModeChange('quick')}
            disabled={isTransitioning}
            className={`
              px-4 py-2 text-sm font-medium transition-all duration-200 relative z-20
              ${mode === 'quick' ? 'text-primary-foreground' : 'text-muted-foreground hover:text-foreground'}
              ${isTransitioning ? 'opacity-70' : 'opacity-100'}
            `}
          >
            <span className="flex items-center gap-2">
              <Zap className="h-4 w-4" />
              <span className="hidden sm:inline">Quick Chat</span>
              <span className="sm:hidden">快速</span>
            </span>
          </Button>

          {/* Deep Research */}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => handleModeChange('deep')}
            disabled={isTransitioning}
            className={`
              px-4 py-2 text-sm font-medium transition-all duration-200 relative z-20
              ${mode === 'deep' ? 'text-primary-foreground' : 'text-muted-foreground hover:text-foreground'}
              ${isTransitioning ? 'opacity-70' : 'opacity-100'}
            `}
          >
            <span className="flex items-center gap-2">
              <Search className="h-4 w-4" />
              <span className="hidden sm:inline">Deep Research</span>
              <span className="sm:hidden">深度</span>
            </span>
          </Button>
        </div>
      </div>

      {/* Mode Description with animation */}
      <div
        className="text-xs text-muted-foreground transition-all duration-300"
        key={mode}
      >
        <div className="flex items-center gap-1 animate-fade-in">
          {mode === 'quick' ? (
            <>
              <Zap className="h-3 w-3" />
              <span>3秒快速回答</span>
            </>
          ) : (
            <>
              <Search className="h-3 w-3" />
              <span>30秒深度报告</span>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default ModeSwitch
