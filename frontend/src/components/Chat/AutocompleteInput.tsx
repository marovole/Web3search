import React, { useState, useRef, useEffect, KeyboardEvent } from 'react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { searchAutocomplete } from '../../services/api'
import { Loader, ArrowRight, Terminal } from 'lucide-react'
import { useKeyboardDetection } from '../../hooks/useTouchGestures'
import type { AutocompleteItem } from '../../types/autocomplete'

interface AutocompleteInputProps {
  value: string
  onChange: (value: string) => void
  onSend: (message: string) => void
  disabled?: boolean
  placeholder?: string
  maxLength?: number
  mobileOptimized?: boolean
}

const AutocompleteInput: React.FC<AutocompleteInputProps> = ({
  value,
  onChange,
  onSend,
  disabled = false,
  placeholder = 'Ask anything...',
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

  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 768)
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  const { isKeyboardOpen } = useKeyboardDetection()

  const debouncedSearch = (query: string) => {
    if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current)
    if (query.trim().length < 2) {
      setSuggestions([])
      setShowDropdown(false)
      return
    }
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

  const handleInputChange = (value: string) => {
    if (value.length <= maxLength) {
      onChange(value)
      debouncedSearch(value)
    }
  }

  const selectSuggestion = (item: AutocompleteItem) => {
    const selectedText = `${item.symbol} (${item.name})`
    onChange(selectedText)
    setSuggestions([])
    setShowDropdown(false)
    textareaRef.current?.focus()
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (showDropdown && suggestions.length > 0) {
      if (e.key === 'ArrowDown') {
        e.preventDefault()
        setSelectedIndex((prev) => (prev < suggestions.length - 1 ? prev + 1 : 0))
      } else if (e.key === 'ArrowUp') {
        e.preventDefault()
        setSelectedIndex((prev) => (prev > 0 ? prev - 1 : suggestions.length - 1))
      } else if (e.key === 'Enter' && !e.shiftKey && selectedIndex >= 0) {
        e.preventDefault()
        const selected = suggestions[selectedIndex]
        if (selected) selectSuggestion(selected)
        return
      } else if (e.key === 'Escape') {
        e.preventDefault()
        setShowDropdown(false)
        setSelectedIndex(-1)
        return
      }
    }

    if (e.key === 'Enter' && !e.shiftKey && !showDropdown) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleSend = () => {
    if (value.trim() && !disabled) {
      onSend(value.trim())
      onChange('')
      setSuggestions([])
      setShowDropdown(false)
    }
  }

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

  useEffect(() => {
    return () => {
      if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current)
    }
  }, [])

  const charactersRemaining = maxLength - value.length
  const isOverLimit = charactersRemaining < 0

  return (
    <div className={cn("relative", isKeyboardOpen && isMobile && "pb-2")}>
      {/* Terminal-style Input Container */}
      <div className={cn(
        "flex items-end gap-3 p-3 rounded-xl transition-all duration-250",
        "bg-surface-2/40 backdrop-blur-md",
        "focus-within:bg-surface-2/60"
      )}>
        {/* Terminal Prompt */}
        <div className="flex items-center gap-2 pb-2.5 pl-1 shrink-0">
          <Terminal className="w-4 h-4 text-primary/70" />
          <span className="font-mono text-sm text-muted-foreground/50">{">"}</span>
        </div>
        
        {/* Textarea */}
        <Textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => handleInputChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          className={cn(
            "flex-1 min-h-[40px] max-h-[120px] py-2 px-0",
            "bg-transparent border-none shadow-none resize-none focus-visible:ring-0",
            "font-mono text-base text-foreground placeholder:text-muted-foreground/35",
            "custom-scrollbar"
          )}
          autoResize={true}
          rows={1}
        />

        {/* Keyboard Hint */}
        {!value.trim() && !isMobile && (
          <div className="hidden md:flex items-center gap-1.5 pb-2.5 shrink-0">
            <kbd className="kbd-hint">↵</kbd>
            <span className="text-[10px] text-muted-foreground/40 font-mono">send</span>
          </div>
        )}

        {/* Send Button */}
        <Button
          onClick={handleSend}
          disabled={disabled || !value.trim() || isOverLimit}
          className={cn(
            "h-9 px-4 rounded-lg shrink-0 mb-0.5 transition-all duration-200",
            "font-mono text-sm font-medium",
            value.trim() 
              ? "bg-primary text-primary-foreground hover:bg-primary/90 shadow-glow-sm active:scale-[0.97]" 
              : "bg-muted/40 text-muted-foreground/60 hover:bg-muted/60"
          )}
        >
          {disabled ? (
            <Loader size={15} className="animate-spin" />
          ) : (
            <>
              RUN
              <ArrowRight size={13} className="ml-1.5" />
            </>
          )}
        </Button>
      </div>

      {/* Dropdown Suggestions - Terminal Style */}
      {showDropdown && suggestions.length > 0 && (
        <div
          ref={dropdownRef}
          className={cn(
            "absolute bottom-full left-0 right-0 mb-2",
            "terminal-panel overflow-hidden",
            "animate-slide-up z-50"
          )}
        >
          {/* Suggestions Header */}
          <div className="px-4 py-2 border-b border-border/30 bg-surface-2/50 flex items-center justify-between">
            <span className="font-mono text-[9px] uppercase tracking-[0.15em] text-muted-foreground/50">
              SUGGESTIONS
            </span>
            <div className="flex items-center gap-2">
              <kbd className="kbd-hint text-[8px]">↑↓</kbd>
              <span className="text-[9px] text-muted-foreground/40 font-mono">navigate</span>
            </div>
          </div>
          <div className="max-h-60 overflow-y-auto custom-scrollbar">
            {suggestions.map((item, index) => (
              <button
                key={item.coingecko_id}
                onClick={() => selectSuggestion(item)}
                className={cn(
                  "w-full text-left px-4 py-3 transition-all duration-150 flex items-center gap-3",
                  "border-b border-border/15 last:border-0 relative",
                  index === selectedIndex 
                    ? "bg-primary/[0.08] text-foreground" 
                    : "hover:bg-primary/[0.04] text-foreground"
                )}
              >
                {/* Selection indicator */}
                {index === selectedIndex && (
                  <span className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-1/2 bg-primary rounded-r" />
                )}
                {item.thumb ? (
                  <img src={item.thumb} alt={item.symbol} className="w-6 h-6 rounded-md" />
                ) : (
                  <div className="w-6 h-6 rounded-md bg-muted/50 flex items-center justify-center text-[10px] font-mono text-muted-foreground">?</div>
                )}
                <div className="flex-1 min-w-0 flex items-center gap-2">
                  <span className={cn(
                    "font-mono font-semibold text-sm",
                    index === selectedIndex && "text-primary"
                  )}>{item.symbol.toUpperCase()}</span>
                  <span className="text-xs text-muted-foreground/50 truncate">{item.name}</span>
                </div>
                {item.market_cap_rank && (
                  <span className={cn(
                    "rank-badge text-[10px]",
                    item.market_cap_rank <= 10 && "rank-badge-top"
                  )}>
                    #{item.market_cap_rank}
                  </span>
                )}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Character Count */}
      {charactersRemaining < 100 && (
        <div className={cn(
          "absolute -top-6 right-2 text-xs font-mono animate-fade-in",
          charactersRemaining < 20 ? "text-destructive" : "text-secondary"
        )}>
          {charactersRemaining}
        </div>
      )}
    </div>
  )
}

export default AutocompleteInput
