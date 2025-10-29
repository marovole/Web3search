import React, { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Search, Clock, ArrowRight } from 'lucide-react'
import { useSearchHistory } from '@/contexts/SearchHistoryContext'
import { useNavigate } from 'react-router-dom'
import { cn } from '@/lib/utils'

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

  // 获取搜索建议（这里使用模拟数据，实际应该从API获取）
  const searchSuggestions = query
    ? [
        { id: '1', title: 'Web3技术趋势', type: 'report' },
        { id: '2', title: 'DeFi协议对比', type: 'report' },
        { id: '3', title: 'NFT市场分析', type: 'chat' },
        { id: '4', title: 'Bitcoin价格监控', type: 'watchlist' }
      ].filter(item => item.title.toLowerCase().includes(query.toLowerCase()))
    : []

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
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50"
            onClick={onClose}
          />

          {/* 搜索弹窗 */}
          <div className="fixed inset-x-0 top-20 z-50 flex justify-center px-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: -20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: -20 }}
              className="w-full max-w-2xl bg-background rounded-lg shadow-xl border border-border overflow-hidden"
              onClick={(e) => e.stopPropagation()}
            >
              {/* 搜索输入框 */}
              <div className="flex items-center gap-3 p-4 border-b border-border">
                <Search className="w-5 h-5 text-muted-foreground" />
                <input
                  ref={inputRef}
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="搜索聊天记录、报告、监控..."
                  className="flex-1 bg-transparent outline-none text-lg placeholder:text-muted-foreground"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      handleSearch()
                    }
                  }}
                />
              </div>

              {/* 搜索结果 */}
              <div className="max-h-96 overflow-y-auto">
                {displayItems.length > 0 ? (
                  <div className="p-2">
                    {displayItems.map((item, index) => {
                      const isSelected = index === selectedIndex
                      const title = 'query' in item ? item.query : item.title
                      const type = 'type' in item ? item.type : 'history'

                      return (
                        <motion.button
                          key={item.id}
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          onClick={() => handleSelect(item)}
                          className={cn(
                            "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors text-left",
                            isSelected && "bg-primary/10"
                          )}
                        >
                          <div className={cn(
                            "p-1.5 rounded",
                            type === 'chat' && "bg-blue-500/10 text-blue-500",
                            type === 'report' && "bg-purple-500/10 text-purple-500",
                            type === 'watchlist' && "bg-green-500/10 text-green-500",
                            type === 'history' && "bg-muted text-muted-foreground"
                          )}>
                            {'query' in item ? (
                              <Clock size={16} />
                            ) : (
                              <Search size={16} />
                            )}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="font-medium truncate">{title}</p>
                            {'timestamp' in item && (
                              <p className="text-xs text-muted-foreground">
                                {new Date(item.timestamp).toLocaleString()}
                              </p>
                            )}
                          </div>
                          <ArrowRight size={16} className="text-muted-foreground opacity-0 group-hover:opacity-100" />
                        </motion.button>
                      )
                    })}
                  </div>
                ) : query ? (
                  <div className="p-8 text-center text-muted-foreground">
                    <Search className="w-8 h-8 mx-auto mb-2 opacity-50" />
                    <p>未找到相关结果</p>
                  </div>
                ) : (
                  <div className="p-4">
                    <h4 className="text-sm font-medium text-muted-foreground mb-3">最近搜索</h4>
                    {recentHistory.length === 0 ? (
                      <p className="text-sm text-muted-foreground text-center py-4">
                        暂无搜索历史
                      </p>
                    ) : (
                      <div className="space-y-1">
                        {recentHistory.map(item => (
                          <button
                            key={item.id}
                            onClick={() => handleSelect(item)}
                            className="w-full flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-muted transition-colors text-left"
                          >
                            <Clock size={16} className="text-muted-foreground" />
                            <span className="flex-1">{item.query}</span>
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* 底部提示 */}
              <div className="p-3 bg-muted/50 border-t border-border text-xs text-muted-foreground flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <span className="flex items-center gap-1">
                    <kbd className="px-1.5 py-0.5 bg-background rounded border">↑↓</kbd>
                    导航
                  </span>
                  <span className="flex items-center gap-1">
                    <kbd className="px-1.5 py-0.5 bg-background rounded border">Enter</kbd>
                    选择
                  </span>
                  <span className="flex items-center gap-1">
                    <kbd className="px-1.5 py-0.5 bg-background rounded border">Esc</kbd>
                    关闭
                  </span>
                </div>
              </div>
            </motion.div>
          </div>
        </>
      )}
    </AnimatePresence>
  )
}
