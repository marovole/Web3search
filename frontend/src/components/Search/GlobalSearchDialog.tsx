import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Search, Clock, ArrowRight, Loader2, TrendingUp } from 'lucide-react'
import { useSearchHistory } from '../../contexts/SearchHistoryContext'
import { useNavigate } from 'react-router-dom'
import { cn } from '../../lib/utils'
import { getSearchSuggestions, type SearchSuggestion } from '../../services/api'

interface GlobalSearchDialogProps {
  isOpen: boolean
  onClose: () => void
}

/**
 * 全局搜索弹窗组件
 * 支持快速搜索和搜索历史
 */
export function GlobalSearchDialog({ isOpen, onClose }: GlobalSearchDialogProps) {
  const navigate = useNavigate()
  const { getRecentHistory } = useSearchHistory()
  const [query, setQuery] = useState('')
  const [selectedIndex, setSelectedIndex] = useState(-1)
  const inputRef = useRef<HTMLInputElement>(null)

  const recentHistory = getRecentHistory(5)
  const [searchSuggestions, setSearchSuggestions] = useState<SearchSuggestion[]>([])
  const [popularSearches, setPopularSearches] = useState<string[]>([])
  const [loadingSuggestions, setLoadingSuggestions] = useState(false)

  // 防抖获取搜索建议
  useEffect(() => {
    if (!query.trim()) {
      setSearchSuggestions([])
      return
    }

    const timeoutId = setTimeout(async () => {
      setLoadingSuggestions(true)
      try {
        const response = await getSearchSuggestions(query)
        setSearchSuggestions(response.suggestions || [])
        if (response.popular) {
          setPopularSearches(response.popular)
        }
      } catch (error) {
        console.error('获取搜索建议失败:', error)
        setSearchSuggestions([])
      } finally {
        setLoadingSuggestions(false)
      }
    }, 300) // 300ms 防抖

    return () => clearTimeout(timeoutId)
  }, [query])

  // 获取显示的列表项
  const displayItems = query ? searchSuggestions : recentHistory

  // 处理键盘导航
  useEffect(() => {
    if (!isOpen) return

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'ArrowDown') {
        e.preventDefault()
        setSelectedIndex(prev => (prev + 1) % Math.max(displayItems.length, 1))
      } else if (e.key === 'ArrowUp') {
        e.preventDefault()
        setSelectedIndex(prev => (prev - 1 + Math.max(displayItems.length, 1)) % Math.max(displayItems.length, 1))
      } else if (e.key === 'Enter') {
        e.preventDefault()
        if (displayItems.length > 0 && selectedIndex >= 0) {
          handleSelect(displayItems[selectedIndex])
        } else if (query.trim()) {
          handleSearch()
        }
      } else if (e.key === 'Escape') {
        onClose()
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, displayItems, selectedIndex, query])

  // 自动聚焦输入框
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus()
    }
  }, [isOpen])

  // 重置状态
  useEffect(() => {
    if (isOpen) {
      setQuery('')
      setSelectedIndex(-1)
    }
  }, [isOpen])

  // 处理选择
  const handleSelect = (item: any) => {
    if ('query' in item) {
      // 从历史记录中选择
      setQuery(item.query)
      navigate(`/search?q=${encodeURIComponent(item.query)}`)
    } else {
      // 从建议中选择
      navigate(`/search?q=${encodeURIComponent(item.title)}`)
    }
    onClose()
  }

  // 执行搜索
  const handleSearch = () => {
    if (query.trim()) {
      navigate(`/search?q=${encodeURIComponent(query)}`)
      onClose()
    }
  }

  // 阻止背景滚动
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
    return () => {
      document.body.style.overflow = ''
    }
  }, [isOpen])

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* 背景遮罩 */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-md z-50"
            onClick={onClose}
          />

          {/* 搜索弹窗 */}
          <div className="fixed inset-x-0 top-20 z-50 flex justify-center px-4 pointer-events-none">
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: -20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: -20 }}
              className="w-full max-w-2xl glass-panel rounded-2xl overflow-hidden pointer-events-auto border border-white/10 shadow-[0_0_50px_rgba(0,0,0,0.5)]"
              onClick={(e) => e.stopPropagation()}
            >
              {/* 搜索输入框 */}
              <div className="flex items-center gap-4 p-5 border-b border-white/5 bg-white/5">
                <Search className="w-6 h-6 text-primary animate-pulse-glow" />
                <input
                  ref={inputRef}
                  data-testid="search-input"
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="搜索聊天记录、报告、监控..."
                  className="flex-1 bg-transparent outline-none text-xl placeholder:text-muted-foreground/50 text-foreground"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      handleSearch()
                    }
                  }}
                />
                <div className="hidden sm:flex items-center gap-1 text-xs text-muted-foreground border border-white/10 px-2 py-1 rounded bg-black/20">
                  <span className="text-xs">ESC</span>
                  <span>关闭</span>
                </div>
              </div>

              {/* 搜索结果 */}
              <div className="max-h-[60vh] overflow-y-auto custom-scrollbar bg-black/20">
                {loadingSuggestions && query ? (
                  <div className="p-12 text-center text-muted-foreground">
                    <Loader2 className="w-10 h-10 mx-auto mb-4 animate-spin text-primary opacity-80" />
                    <p className="animate-pulse">正在搜索全网数据...</p>
                  </div>
                ) : displayItems.length > 0 ? (
                  <div className="p-2 space-y-1">
                    {displayItems.map((item, index) => {
                      const isSelected = index === selectedIndex
                      const title = 'query' in item ? item.query : item.title

                      return (
                        <motion.button
                          key={item.id}
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          onClick={() => handleSelect(item)}
                          onMouseEnter={() => setSelectedIndex(index)}
                          className={cn(
                            "w-full flex items-center gap-4 px-4 py-3 rounded-xl transition-all duration-200 text-left group border border-transparent",
                            isSelected
                              ? "bg-primary/10 border-primary/20 shadow-[0_0_15px_rgba(0,255,255,0.1)]"
                              : "hover:bg-white/5 hover:border-white/5"
                          )}
                        >
                          <div className={cn(
                            "p-2 rounded-lg transition-colors",
                            isSelected ? "bg-primary/20 text-primary" : "bg-white/5 text-muted-foreground group-hover:text-foreground"
                          )}>
                            {'query' in item ? (
                              <Clock size={18} />
                            ) : (
                              <Search size={18} />
                            )}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className={cn(
                              "font-medium truncate text-base transition-colors",
                              isSelected ? "text-primary" : "text-foreground"
                            )}>{title}</p>
                            {'timestamp' in item && (
                              <p className="text-xs text-muted-foreground mt-0.5">
                                {new Date(item.timestamp).toLocaleString()}
                              </p>
                            )}
                            {'description' in item && item.description && (
                              <p className="text-xs text-muted-foreground mt-0.5 line-clamp-1">
                                {item.description}
                              </p>
                            )}
                          </div>
                          <ArrowRight size={18} className={cn(
                            "transition-all duration-200",
                            isSelected ? "text-primary opacity-100 translate-x-0" : "text-muted-foreground opacity-0 -translate-x-2 group-hover:opacity-50"
                          )} />
                        </motion.button>
                      )
                    })}
                  </div>
                ) : query ? (
                  <div className="p-12 text-center text-muted-foreground">
                    <Search className="w-12 h-12 mx-auto mb-4 opacity-30" />
                    <p className="text-lg font-medium mb-2">未找到相关结果</p>
                    <p className="text-sm opacity-70">尝试使用不同的关键词</p>

                    {popularSearches.length > 0 && (
                      <div className="mt-8 pt-8 border-t border-white/5">
                        <p className="text-xs mb-4 flex items-center justify-center gap-2 text-primary/80 uppercase tracking-widest">
                          <TrendingUp size={14} />
                          热门搜索
                        </p>
                        <div className="flex flex-wrap gap-2 justify-center">
                          {popularSearches.slice(0, 5).map((term, idx) => (
                            <button
                              key={idx}
                              onClick={() => {
                                setQuery(term)
                                navigate(`/search?q=${encodeURIComponent(term)}`)
                                onClose()
                              }}
                              className="px-3 py-1.5 text-sm bg-white/5 hover:bg-primary/10 hover:text-primary border border-white/5 hover:border-primary/30 rounded-lg transition-all duration-200"
                            >
                              {term}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="p-6">
                    <h4 className="text-xs font-semibold text-muted-foreground mb-4 uppercase tracking-widest px-2">最近搜索</h4>
                    {recentHistory.length === 0 ? (
                      <p className="text-sm text-muted-foreground text-center py-8 opacity-50">
                        暂无搜索历史
                      </p>
                    ) : (
                      <div className="space-y-1">
                        {recentHistory.map((item, index) => (
                          <button
                            key={item.id}
                            onClick={() => handleSelect(item)}
                            onMouseEnter={() => setSelectedIndex(index)}
                            className={cn(
                              "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors text-left group",
                              index === selectedIndex ? "bg-white/10" : "hover:bg-white/5"
                            )}
                          >
                            <Clock size={16} className="text-muted-foreground group-hover:text-primary transition-colors" />
                            <span className="flex-1 text-sm text-foreground/80 group-hover:text-foreground transition-colors">{item.query}</span>
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* 底部提示 */}
              <div className="p-3 bg-white/5 border-t border-white/5 text-xs text-muted-foreground flex items-center justify-between backdrop-blur-sm">
                <div className="flex items-center gap-4">
                  <span className="flex items-center gap-1.5">
                    <kbd className="px-1.5 py-0.5 bg-black/40 rounded border border-white/10 font-mono text-[10px]">↑↓</kbd>
                    导航
                  </span>
                  <span className="flex items-center gap-1.5">
                    <kbd className="px-1.5 py-0.5 bg-black/40 rounded border border-white/10 font-mono text-[10px]">Enter</kbd>
                    选择
                  </span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="text-primary/50">Web3Search</span>
                </div>
              </div>
            </motion.div>
          </div>
        </>
      )}
    </AnimatePresence>
  )
}
