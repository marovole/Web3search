import React, { createContext, useContext, useState, useEffect } from 'react'

// 搜索历史记录接口
export interface SearchHistoryItem {
  id: string
  query: string
  timestamp: number
  resultsCount: number
  type: 'chat' | 'report' | 'watchlist'
  filters?: Record<string, any>
}

// 搜索历史上下文类型
interface SearchHistoryContextType {
  history: SearchHistoryItem[]
  addToHistory: (item: Omit<SearchHistoryItem, 'id' | 'timestamp'>) => void
  removeFromHistory: (id: string) => void
  clearHistory: () => void
  searchHistory: (query: string) => SearchHistoryItem[]
  getRecentHistory: (limit?: number) => SearchHistoryItem[]
}

// 搜索历史存储键
const SEARCH_HISTORY_STORAGE_KEY = 'web3search:search-history'
const MAX_HISTORY_ITEMS = 100

const SearchHistoryContext = createContext<SearchHistoryContextType | undefined>(undefined)

interface SearchHistoryProviderProps {
  children: React.ReactNode
}

/**
 * 搜索历史记录上下文提供者
 */
export function SearchHistoryProvider({ children }: SearchHistoryProviderProps) {
  const [history, setHistory] = useState<SearchHistoryItem[]>([])

  // 加载搜索历史
  useEffect(() => {
    try {
      const stored = localStorage.getItem(SEARCH_HISTORY_STORAGE_KEY)
      if (stored) {
        const parsed = JSON.parse(stored)
        setHistory(parsed)
      }
    } catch (error) {
      console.error('加载搜索历史失败:', error)
    }
  }, [])

  // 保存搜索历史
  useEffect(() => {
    try {
      localStorage.setItem(SEARCH_HISTORY_STORAGE_KEY, JSON.stringify(history))
    } catch (error) {
      console.error('保存搜索历史失败:', error)
    }
  }, [history])

  // 添加搜索记录
  const addToHistory = (item: Omit<SearchHistoryItem, 'id' | 'timestamp'>) => {
    const newItem: SearchHistoryItem = {
      ...item,
      id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
      timestamp: Date.now()
    }

    setHistory(prev => {
      // 避免重复搜索
      const filtered = prev.filter(h => h.query !== item.query || h.type !== item.type)
      const newHistory = [newItem, ...filtered]

      // 限制历史记录数量
      return newHistory.slice(0, MAX_HISTORY_ITEMS)
    })
  }

  // 删除搜索记录
  const removeFromHistory = (id: string) => {
    setHistory(prev => prev.filter(item => item.id !== id))
  }

  // 清空搜索历史
  const clearHistory = () => {
    setHistory([])
    localStorage.removeItem(SEARCH_HISTORY_STORAGE_KEY)
  }

  // 搜索历史记录
  const searchHistory = (query: string): SearchHistoryItem[] => {
    if (!query.trim()) return []

    const lowercaseQuery = query.toLowerCase()
    return history.filter(item =>
      item.query.toLowerCase().includes(lowercaseQuery)
    )
  }

  // 获取最近的历史记录
  const getRecentHistory = (limit = 10): SearchHistoryItem[] => {
    return history.slice(0, limit)
  }

  return (
    <SearchHistoryContext.Provider
      value={{
        history,
        addToHistory,
        removeFromHistory,
        clearHistory,
        searchHistory,
        getRecentHistory
      }}
    >
      {children}
    </SearchHistoryContext.Provider>
  )
}

/**
 * 使用搜索历史上下文
 */
export function useSearchHistory() {
  const context = useContext(SearchHistoryContext)
  if (!context) {
    throw new Error('useSearchHistory must be used within SearchHistoryProvider')
  }
  return context
}

/**
 * 便利Hook：按类型获取搜索历史
 */
export function useSearchHistoryByType(type: SearchHistoryItem['type']) {
  const { history } = useSearchHistory()
  return React.useMemo(() => {
    return history.filter(item => item.type === type)
  }, [history, type])
}
