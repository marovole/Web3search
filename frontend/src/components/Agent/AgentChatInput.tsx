/**
 * AgentChatInput Component
 * Input field for the agent chat interface with example prompts
 */

import React, { useState, useRef, useEffect } from 'react'
import { cn } from '@/lib/utils'
import { EXAMPLE_PROMPTS } from '@/types/agent-chat'

interface AgentChatInputProps {
  onSend: (message: string) => void
  disabled?: boolean
  placeholder?: string
}

const AgentChatInput: React.FC<AgentChatInputProps> = ({
  onSend,
  disabled = false,
  placeholder = '输入您的需求，例如：当BTC跌破50000时提醒我',
}) => {
  const [message, setMessage] = useState('')
  const [showExamples, setShowExamples] = useState(false)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (message.trim() && !disabled) {
      onSend(message.trim())
      setMessage('')
      setShowExamples(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  const handleExampleClick = (example: string) => {
    setMessage(example)
    setShowExamples(false)
    inputRef.current?.focus()
  }

  // Auto-resize textarea
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = 'auto'
      inputRef.current.style.height = `${Math.min(inputRef.current.scrollHeight, 120)}px`
    }
  }, [message])

  return (
    <div className="relative">
      {/* Example Prompts Dropdown */}
      {showExamples && (
        <div className="absolute bottom-full left-0 right-0 mb-2 bg-gray-800 border border-gray-700 rounded-xl shadow-xl overflow-hidden z-10">
          <div className="p-2 border-b border-gray-700">
            <span className="text-xs text-gray-400 px-2">试试这些示例</span>
          </div>
          <div className="max-h-48 overflow-y-auto">
            {EXAMPLE_PROMPTS.map((example, idx) => (
              <button
                key={idx}
                onClick={() => handleExampleClick(example)}
                className="w-full px-4 py-2.5 text-left text-sm text-gray-200 hover:bg-gray-700/50 transition-colors"
              >
                {example}
              </button>
            ))}
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="flex items-end gap-2">
        <div className="flex-1 relative">
          <textarea
            ref={inputRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            onFocus={() => message === '' && setShowExamples(true)}
            onBlur={() => setTimeout(() => setShowExamples(false), 200)}
            placeholder={placeholder}
            disabled={disabled}
            rows={1}
            className={cn(
              "w-full px-4 py-3 bg-gray-800/80 border border-gray-700/50 rounded-xl",
              "text-gray-100 placeholder-gray-500 text-sm",
              "focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50",
              "resize-none overflow-hidden transition-all",
              disabled && "opacity-50 cursor-not-allowed"
            )}
          />
          
          {/* Lightbulb Icon for Examples */}
          {message === '' && (
            <button
              type="button"
              onClick={() => setShowExamples(!showExamples)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300 transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </button>
          )}
        </div>

        <button
          type="submit"
          disabled={!message.trim() || disabled}
          className={cn(
            "px-4 py-3 rounded-xl font-medium text-sm transition-all",
            "flex items-center gap-2",
            message.trim() && !disabled
              ? "bg-blue-600 hover:bg-blue-700 text-white"
              : "bg-gray-700 text-gray-500 cursor-not-allowed"
          )}
        >
          {disabled ? (
            <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
          ) : (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          )}
        </button>
      </form>
    </div>
  )
}

export default AgentChatInput
