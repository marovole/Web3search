/**
 * 搜索自动补全输入组件
 * 支持键盘导航、防抖搜索、点击选择
 */

import React, { useState, useRef, useEffect, KeyboardEvent } from 'react'
import { searchAutocomplete } from '../../services/api'
import type { AutocompleteItem } from '../../types/autocomplete'

interface AutocompleteInputProps {
  value: string
  onChange: (value: string) => void
  onSend: (message: string) => void
  disabled?: boolean
  placeholder?: string
  maxLength?: number
}

const AutocompleteInput: React.FC<AutocompleteInputProps> = ({
  value,
  onChange,
  onSend,
  disabled = false,
  placeholder = '输入消息...',
  maxLength = 1000,
}) => {
  const [suggestions, setSuggestions] = useState<AutocompleteItem[]>([])
  const [showDropdown, setShowDropdown] = useState(false)
  const [isSearching, setIsSearching] = useState(false)
  const [selectedIndex, setSelectedIndex] = useState(-1)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const debounceTimerRef = useRef<number>()

  // 防抖搜索
  const debouncedSearch = (query: string) => {
    // 清除之前的定时器
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current)
    }

    // 如果查询为空或太短，不搜索
    if (query.trim().length < 2) {
      setSuggestions([])
      setShowDropdown(false)
      return
    }

    // 设置新的定时器（300ms延迟）
    debounceTimerRef.current = window.setTimeout(async () => {
      try {
        setIsSearching(true)
        const response = await searchAutocomplete(query)
        setSuggestions(response.results)
        setShowDropdown(response.results.length > 0)
        setSelectedIndex(-1)
      } catch (error) {
        console.error('Autocomplete search failed:', error)
        setSuggestions([])
        setShowDropdown(false)
      } finally {
        setIsSearching(false)
      }
    }, 300)
  }

  // 处理输入变化
  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newValue = e.target.value
    if (newValue.length <= maxLength) {
      onChange(newValue)
      // Auto-resize textarea
      e.target.style.height = 'auto'
      e.target.style.height = `${e.target.scrollHeight}px`

      // 触发防抖搜索
      debouncedSearch(newValue)
    }
  }

  // 选择建议
  const selectSuggestion = (item: AutocompleteItem) => {
    const selectedText = `${item.symbol} (${item.name})`
    onChange(selectedText)
    setSuggestions([])
    setShowDropdown(false)
    textareaRef.current?.focus()

    // 调整textarea高度
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`
    }
  }

  // 键盘导航
  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    // 如果下拉框显示，处理方向键和Enter
    if (showDropdown && suggestions.length > 0) {
      if (e.key === 'ArrowDown') {
        e.preventDefault()
        setSelectedIndex((prev) => (prev < suggestions.length - 1 ? prev + 1 : 0))
      } else if (e.key === 'ArrowUp') {
        e.preventDefault()
        setSelectedIndex((prev) => (prev > 0 ? prev - 1 : suggestions.length - 1))
      } else if (e.key === 'Enter' && !e.shiftKey && selectedIndex >= 0) {
        e.preventDefault()
        selectSuggestion(suggestions[selectedIndex])
        return
      } else if (e.key === 'Escape') {
        e.preventDefault()
        setShowDropdown(false)
        setSelectedIndex(-1)
        return
      }
    }

    // 正常的Enter发送逻辑
    if (e.key === 'Enter' && !e.shiftKey && !showDropdown) {
      e.preventDefault()
      handleSend()
    }
  }

  // 发送消息
  const handleSend = () => {
    if (value.trim() && !disabled) {
      onSend(value.trim())
      onChange('')
      setSuggestions([])
      setShowDropdown(false)
      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto'
      }
    }
  }

  // 点击外部关闭下拉框
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node) &&
        textareaRef.current &&
        !textareaRef.current.contains(event.target as Node)
      ) {
        setShowDropdown(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // 清理定时器
  useEffect(() => {
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current)
      }
    }
  }, [])

  const charactersRemaining = maxLength - value.length
  const isOverLimit = charactersRemaining < 0

  return (
    <div className="space-y-2">
      {/* Input area */}
      <div className="flex gap-2 items-end">
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={value}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled}
            className="input resize-none min-h-[44px] max-h-[200px] overflow-y-auto"
            rows={1}
          />

          {/* 下拉建议框 */}
          {showDropdown && suggestions.length > 0 && (
            <div
              ref={dropdownRef}
              className="absolute bottom-full left-0 right-0 mb-2 bg-white border border-gray-300 rounded-lg shadow-lg max-h-64 overflow-y-auto z-50"
            >
              {suggestions.map((item, index) => (
                <button
                  key={item.coingecko_id}
                  onClick={() => selectSuggestion(item)}
                  className={`w-full px-4 py-3 text-left hover:bg-gray-50 border-b border-gray-100 last:border-b-0 flex items-center gap-3 transition-colors ${
                    index === selectedIndex ? 'bg-blue-50' : ''
                  }`}
                >
                  {/* 图标 */}
                  {item.thumb && (
                    <img
                      src={item.thumb}
                      alt={item.symbol}
                      className="w-6 h-6 rounded-full"
                    />
                  )}

                  {/* 信息 */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-gray-900">
                        {item.symbol.toUpperCase()}
                      </span>
                      {item.market_cap_rank && (
                        <span className="text-xs text-gray-500">
                          #{item.market_cap_rank}
                        </span>
                      )}
                    </div>
                    <div className="text-sm text-gray-600 truncate">
                      {item.name}
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}

          {/* 加载指示器 */}
          {isSearching && (
            <div className="absolute right-3 top-3">
              <svg
                className="animate-spin h-4 w-4 text-gray-400"
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
            </div>
          )}
        </div>

        <button
          onClick={handleSend}
          disabled={disabled || !value.trim() || isOverLimit}
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

      {/* Character count and hints */}
      <div className="flex justify-between items-center text-xs">
        <p className="text-gray-500">
          提示：按 Enter 发送，Shift + Enter 换行{showDropdown && '，↑↓ 选择，Esc 关闭'}
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

export default AutocompleteInput
