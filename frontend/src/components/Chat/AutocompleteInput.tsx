import React, { useState, useRef, useEffect, KeyboardEvent } from 'react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { searchAutocomplete } from '../../services/api'
import { Loader, Send, X, Sparkles } from 'lucide-react'
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
        selectSuggestion(suggestions[selectedIndex])
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
      {/* Glass Capsule Container */}
      <div className={cn(
        "flex items-end gap-2 p-2 rounded-3xl transition-all duration-300",
        "bg-background/40 backdrop-blur-md border border-white/10",
        "focus-within:border-primary/50 focus-within:ring-1 focus-within:ring-primary/50 focus-within:bg-background/60"
      )}>
        
        {/* Textarea */}
        <Textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => handleInputChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          className={cn(
            "flex-1 min-h-[44px] max-h-[120px] py-3 px-4",
            "bg-transparent border-none shadow-none resize-none focus-visible:ring-0",
            "text-base placeholder:text-muted-foreground/70",
            "custom-scrollbar"
          )}
          autoResize={true}
          rows={1}
        />

        {/* Send Button */}
        <Button
          onClick={handleSend}
          disabled={disabled || !value.trim() || isOverLimit}
          className={cn(
            "h-10 w-10 rounded-full shrink-0 mb-1 mr-1 transition-all duration-300",
            value.trim() 
              ? "bg-primary text-primary-foreground hover:bg-primary/90 shadow-[0_0_15px_rgba(0,242,255,0.3)]" 
              : "bg-muted text-muted-foreground hover:bg-muted/80"
          )}
          size="icon"
        >
          {disabled ? (
            <Loader size={18} className="animate-spin" />
          ) : (
            <Send size={18} className={cn(value.trim() && "ml-0.5")} />
          )}
        </Button>
      </div>

      {/* Dropdown Suggestions */}
      {showDropdown && suggestions.length > 0 && (
        <div
          ref={dropdownRef}
          className={cn(
            "absolute bottom-full left-0 right-0 mb-2 mx-2",
            "bg-card/90 backdrop-blur-xl border border-white/10 rounded-xl shadow-2xl overflow-hidden",
            "animate-slide-up z-50"
          )}
        >
          <div className="max-h-60 overflow-y-auto custom-scrollbar p-1">
            {suggestions.map((item, index) => (
              <button
                key={item.coingecko_id}
                onClick={() => selectSuggestion(item)}
                className={cn(
                  "w-full text-left px-4 py-3 rounded-lg transition-colors flex items-center gap-3",
                  index === selectedIndex ? "bg-primary/10 text-primary" : "hover:bg-white/5 text-foreground"
                )}
              >
                {item.thumb ? (
                  <img src={item.thumb} alt={item.symbol} className="w-6 h-6 rounded-full" />
                ) : (
                  <div className="w-6 h-6 rounded-full bg-muted flex items-center justify-center text-xs">?</div>
                )}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-bold">{item.symbol.toUpperCase()}</span>
                    <span className="text-xs opacity-50 truncate">{item.name}</span>
                  </div>
                </div>
                {item.market_cap_rank && (
                  <span className="text-xs px-1.5 py-0.5 rounded bg-white/5 text-muted-foreground">
                    #{item.market_cap_rank}
                  </span>
                )}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Character Count (Only show when close to limit) */}
      {charactersRemaining < 100 && (
        <div className="absolute -top-6 right-2 text-xs font-medium text-warning animate-fade-in">
          {charactersRemaining}
        </div>
      )}
    </div>
  )
}

export default AutocompleteInput
