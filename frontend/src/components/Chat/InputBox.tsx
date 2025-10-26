import React, { useState, useRef, KeyboardEvent } from 'react'

interface InputBoxProps {
  onSend: (message: string) => void
  disabled?: boolean
  placeholder?: string
}

const InputBox: React.FC<InputBoxProps> = ({
  onSend,
  disabled = false,
  placeholder = '输入消息...',
}) => {
  const [input, setInput] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const maxLength = 1000

  const handleSend = () => {
    if (input.trim() && !disabled) {
      onSend(input.trim())
      setInput('')
      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto'
      }
    }
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    // Enter to send, Shift+Enter to new line
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value
    if (value.length <= maxLength) {
      setInput(value)
      // Auto-resize textarea
      e.target.style.height = 'auto'
      e.target.style.height = `${e.target.scrollHeight}px`
    }
  }

  const charactersRemaining = maxLength - input.length
  const isOverLimit = charactersRemaining < 0

  return (
    <div className="space-y-2">
      {/* Input area */}
      <div className="flex gap-2 items-end">
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled}
            className="input resize-none min-h-[44px] max-h-[200px] overflow-y-auto"
            rows={1}
          />
        </div>

        <button
          onClick={handleSend}
          disabled={disabled || !input.trim() || isOverLimit}
          className="btn-primary px-6 py-3 flex-shrink-0"
        >
          {disabled ? (
            <span className="flex items-center gap-2">
              <svg
                className="animate-spin h-4 w-4"
                xmlns="http://www.w3.org/2000/svg"
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
              <span>发送中</span>
            </span>
          ) : (
            '发送'
          )}
        </button>
      </div>

      {/* Character count */}
      <div className="flex justify-between items-center text-xs">
        <p className="text-gray-500">
          提示：按 Enter 发送，Shift + Enter 换行
        </p>
        <p
          className={`font-medium ${
            isOverLimit
              ? 'text-danger'
              : charactersRemaining < 100
              ? 'text-warning'
              : 'text-gray-500'
          }`}
        >
          {charactersRemaining} 字符剩余
        </p>
      </div>
    </div>
  )
}

export default InputBox
