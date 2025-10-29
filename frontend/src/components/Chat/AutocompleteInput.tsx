/**
 * 搜索自动补全输入组件
 * 支持键盘导航、防抖搜索、点击选择、移动端触摸优化
 */

import React, { useState, useRef, useEffect, KeyboardEvent } from 'react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { searchAutocomplete } from '../../services/api'
import { Loader, Send, X } from 'lucide-react'
import { useKeyboardDetection } from '../../hooks/useTouchGestures'
import type { AutocompleteItem } from '../../types/autocomplete'

interface AutocompleteInputProps {
  value: string
  onChange: (value: string) => void
  onSend: (message: string) => void
  disabled?: boolean
  placeholder?: string
  maxLength?: number
  /** 是否启用移动端优化（默认启用） */
  mobileOptimized?: boolean
}

const AutocompleteInput: React.FC<AutocompleteInputProps> = ({
  value,
  onChange,
  onSend,
  disabled = false,
  placeholder = '输入消息...',
  maxLength = 1000,
  mobileOptimized = true,
}) => {
  const [suggestions, setSuggestions] = useState<AutocompleteItem[]>([])
  const [showDropdown, setShowDropdown] = useState(false)
  const [isSearching, setIsSearching] = useState(false)
  const [selectedIndex, setSelectedIndex] = useState(-1)
  const [isMobile, setIsMobile] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const debounceTimerRef = useRef<number>()

  // 检测移动设备
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768)
    }
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  // 键盘检测
  const { isKeyboardOpen, keyboardHeight } = useKeyboardDetection()

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
  const handleInputChange = (value: string) => {
    if (value.length <= maxLength) {
      onChange(value)

      // 触发防抖搜索
      debouncedSearch(value)
    }
  }

  // 选择建议
  const selectSuggestion = (item: AutocompleteItem) => {
    const selectedText = `${item.symbol} (${item.name})`
    onChange(selectedText)
    setSuggestions([])
    setShowDropdown(false)
    textareaRef.current?.focus()
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
    <div className={cn(
      "space-y-2",
      mobileOptimized && "safe-area-padding",
      isKeyboardOpen && isMobile && "pb-4"
    )}>
      {/* Input area with mobile optimization */}
      <div className="flex gap-2 items-end">
        <div className="flex-1 relative">
          {/* Enhanced Textarea with auto-resize */}
          <Textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => handleInputChange(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled}
            loading={isSearching}
            error={isOverLimit ? "超出字符限制" : undefined}
            helperText={isOverLimit ? `已超出 ${Math.abs(charactersRemaining)} 个字符` : undefined}
            className={cn(
              "min-h-[44px] md:min-h-[48px]",
              mobileOptimized && "mobile-input",
              "resize-none"
            )}
            autoResize={true}
            maxHeight={isMobile ? 120 : 200}
            rows={1}
          />

          {/* Enhanced dropdown for mobile */}
          {showDropdown && suggestions.length > 0 && (
            <div
              ref={dropdownRef}
              className={cn(
                "absolute bottom-full left-0 right-0 mb-2 bg-card border border-border rounded-lg shadow-lg z-50",
                "max-h-64 overflow-y-auto",
                // Mobile optimization
                isMobile && "max-h-48",
                // Smooth animations
                "animate-slide-down animate-fade-in"
              )}
              style={{ animationDuration: '200ms' }}
            >
              <div className="p-2">
                <div className="flex items-center justify-between px-2 py-1 mb-2 border-b">
                  <span className="text-xs font-medium text-muted-foreground">
                    搜索建议
                  </span>
                  <button
                    onClick={() => {
                      setShowDropdown(false)
                      setSuggestions([])
                    }}
                    className="p-1 rounded hover:bg-muted touch-manipulation"
                  >
                    <X size={14} />
                  </button>
                </div>

                <div className={cn(
                  "space-y-1",
                  isMobile && "touch-button-group"
                )}>
                  {suggestions.map((item, index) => (
                    <button
                      key={item.coingecko_id}
                      onClick={() => selectSuggestion(item)}
                      className={cn(
                        "w-full text-left hover:bg-muted border border-transparent rounded-lg transition-all duration-150",
                        "flex items-center gap-3 p-3",
                        isMobile ? "mobile-list-item touch-feedback" : "min-h-[48px]",
                        index === selectedIndex && "bg-primary/10 border-primary/20"
                      )}
                    >
                      {/* 图标 */}
                      {item.thumb && (
                        <img
                          src={item.thumb}
                          alt={item.symbol}
                          className="w-8 h-8 md:w-6 md:h-6 rounded-full flex-shrink-0"
                        />
                      )}

                      {/* 信息 */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-foreground text-sm md:text-sm">
                            {item.symbol.toUpperCase()}
                          </span>
                          {item.market_cap_rank && (
                            <span className="text-xs text-muted-foreground bg-muted px-1.5 py-0.5 rounded">
                              #{item.market_cap_rank}
                            </span>
                          )}
                        </div>
                        <div className="text-sm text-muted-foreground truncate">
                          {item.name}
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Enhanced send button with mobile optimization */}
        <Button
          onClick={handleSend}
          disabled={disabled || !value.trim() || isOverLimit}
          className={cn(
            "flex-shrink-0 transition-all duration-200",
            mobileOptimized ? "h-12 w-12 md:w-auto md:px-6" : "h-12 px-6",
            "hover:scale-105 active:scale-95 disabled:scale-100 touch-feedback"
          )}
          size={mobileOptimized && isMobile ? "icon" : "sm"}
        >
          {disabled ? (
            <Loader size={16} className="animate-spin" />
          ) : (
            <>
              <Send className="h-4 w-4" />
              {!isMobile && <span className="ml-2">发送</span>}
            </>
          )}
        </Button>
      </div>

      {/* Enhanced character count and hints with mobile optimization */}
      <div className="flex justify-between items-center text-xs">
        <div className="text-muted-foreground">
          {isMobile ? (
            <p className="flex items-center gap-2">
              {showDropdown ? (
                <>
                  <span>↑↓ 选择</span>
                  <span>•</span>
                  <span>Esc 关闭</span>
                </>
              ) : (
                <>
                  <span>Enter 发送</span>
                  <span>•</span>
                  <span>Shift+Enter 换行</span>
                </>
              )}
            </p>
          ) : (
            <p>
              提示：按 Enter 发送，Shift + Enter 换行
              {showDropdown && '，↑↓ 选择，Esc 关闭'}
            </p>
          )}
        </div>

        <p
          className={cn(
            "font-medium transition-colors",
            isOverLimit
              ? "text-destructive"
              : charactersRemaining < 100
              ? "text-warning"
              : "text-muted-foreground"
          )}
        >
          {charactersRemaining} 字符剩余
        </p>
      </div>

      {/* Mobile keyboard padding indicator */}
      {isKeyboardOpen && isMobile && (
        <div className="text-center text-xs text-muted-foreground animate-pulse">
          虚拟键盘已打开 ({Math.round(keyboardHeight)}px)
        </div>
      )}
    </div>
  )
}

export default AutocompleteInput
