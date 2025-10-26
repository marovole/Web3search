import React from 'react'
import type { ChatMode } from '../../types'

interface ModeSwitchProps {
  mode: ChatMode
  onChange: (mode: ChatMode) => void
}

const ModeSwitch: React.FC<ModeSwitchProps> = ({ mode, onChange }) => {
  return (
    <div className="flex items-center gap-4">
      <span className="text-sm font-medium text-gray-700">模式：</span>
      <div className="flex bg-gray-100 rounded-lg p-1">
        {/* Quick Chat */}
        <button
          onClick={() => onChange('quick')}
          className={`
            px-4 py-2 rounded-md text-sm font-medium transition-all
            ${
              mode === 'quick'
                ? 'bg-white text-primary shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }
          `}
        >
          <span className="flex items-center gap-2">
            <span>⚡</span>
            <span>Quick Chat</span>
          </span>
        </button>

        {/* Deep Research */}
        <button
          onClick={() => onChange('deep')}
          className={`
            px-4 py-2 rounded-md text-sm font-medium transition-all
            ${
              mode === 'deep'
                ? 'bg-white text-primary shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }
          `}
        >
          <span className="flex items-center gap-2">
            <span>🔬</span>
            <span>Deep Research</span>
          </span>
        </button>
      </div>

      {/* Mode Description */}
      <p className="text-xs text-gray-500 ml-2">
        {mode === 'quick' ? '3秒快速回答' : '30秒深度报告'}
      </p>
    </div>
  )
}

export default ModeSwitch
