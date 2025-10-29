import React, { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Search,
  History,
  Clock,
  Filter,
  X,
  MessageSquare,
  FileText,
  BarChart3,
  Trash2,
  TrendingUp
} from 'lucide-react'
import { useSearchHistory } from '@/contexts/SearchHistoryContext'
import { cn } from '@/lib/utils'

// 搜索类型
type SearchType = 'all' | 'chat' | 'report' | 'watchlist'

// 搜索过滤器接口
interface SearchFilters {
  type: SearchType
  dateRange: 'all' | 'today' | 'week' | 'month'
  sortBy: 'relevance' | 'date' | 'results'
}

// 搜索结果接口
interface SearchResult {
  id: string
  title: string
  excerpt: string
  type: SearchType
  timestamp: number
  url?: string
}

interface SearchSectionProps {
  icon: React.ReactNode
  title: string
  count: number
  results: SearchResult[]
  isExpanded: boolean
  onToggle: () => void
}

function SearchSection({ icon, title, count, results, isExpanded, onToggle }: SearchSectionProps) {
  return (
    <div className="bg-card rounded-lg border border-border overflow-hidden">
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between p-4 hover:bg-muted/50 transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className="p-2 bg-primary/10 rounded-lg text-primary">
            {icon}
          </div>
          <div className="text-left">
            <h3 className="font-medium">{title}</h3>
            <p className="text-sm text-muted-foreground">{count} 条结果</p>
          </div>
        </div>
        <motion.div
          animate={{ rotate: isExpanded ? 180 : 0 }}
          transition={{ duration: 0.2 }}
        >
          <Filter size={20} className="text-muted-foreground" />
        </motion.div>
      </button>

      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="p-4 border-t border-border space-y-3">
              {results.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <Search className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p>暂无搜索结果</p>
                </div>
              ) : (
                results.map(result => (
                  <motion.div
                    key={result.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="p-3 bg-muted/50 rounded-lg hover:bg-muted transition-colors cursor-pointer"
                  >
                    <div className="flex items-start gap-3">
                      <div className="p-1.5 bg-primary/10 rounded text-primary">
                        {result.type === 'chat' && <MessageSquare size={14} />}
                        {result.type === 'report' && <FileText size={14} />}
                        {result.type === 'watchlist' && <BarChart3 size={14} />}
                      </div>
                      <div className="flex-1 min-w-0">
                        <h4 className="font-medium text-sm truncate">{result.title}</h4>
                        <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                          {result.excerpt}
                        </p>
                        <p className="text-xs text-muted-foreground mt-2">
                          {new Date(result.timestamp).toLocaleString()}
                        </p>
                      </div>
                    </div>
                  </motion.div>
                ))
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

/**
 * 搜索页面
 */
export default function SearchPage() {
  const { history, removeFromHistory, clearHistory } = useSearchHistory()
  const [query, setQuery] = useState('')
  const [filters, setFilters] = useState<SearchFilters>({
    type: 'all',
    dateRange: 'all',
    sortBy: 'relevance'
  })
  const [expandedSections, setExpandedSections] = useState<Set<SearchType>>(new Set(['chat', 'report', 'watchlist']))
  const [searchResults, setSearchResults] = useState<SearchResult[]>([])
  const [isSearching, setIsSearching] = useState(false)
  const searchInputRef = useRef<HTMLInputElement>(null)

  // 模拟搜索功能
  const performSearch = async (searchQuery: string, searchFilters: SearchFilters) => {
    setIsSearching(true)

    // 模拟异步搜索
    await new Promise(resolve => setTimeout(resolve, 500))

    // 生成模拟搜索结果
    const mockResults: SearchResult[] = [
      {
        id: '1',
        title: 'Web3技术发展趋势分析',
        excerpt: '深入分析当前Web3技术的发展现状、未来趋势和投资机会...',
        type: 'report',
        timestamp: Date.now() - 3600000,
        url: '/shared/report-1'
      },
      {
        id: '2',
        title: 'DeFi协议对比研究',
        excerpt: '对主流DeFi协议进行详细对比，包括收益率、风险评估等...',
        type: 'report',
        timestamp: Date.now() - 7200000,
        url: '/shared/report-2'
      },
      {
        id: '3',
        title: '关于NFT市场分析的讨论',
        excerpt: '用户询问NFT市场的现状和发展前景，专家进行了详细解答...',
        type: 'chat',
        timestamp: Date.now() - 10800000
      },
      {
        id: '4',
        title: 'Bitcoin价格监控',
        excerpt: '实时监控Bitcoin价格变化，设置价格提醒...',
        type: 'watchlist',
        timestamp: Date.now() - 14400000,
        url: '/watchlist'
      }
    ]

    // 根据搜索词过滤结果
    const filteredResults = searchQuery
      ? mockResults.filter(result =>
          result.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
          result.excerpt.toLowerCase().includes(searchQuery.toLowerCase())
        )
      : []

    // 根据类型过滤
    const typedResults = searchFilters.type === 'all'
      ? filteredResults
      : filteredResults.filter(result => result.type === searchFilters.type)

    setSearchResults(typedResults)

    // 添加到搜索历史
    if (searchQuery.trim()) {
      // 这里应该调用addToHistory，但为了简化演示暂时不调用
      console.log('添加搜索历史:', searchQuery)
    }

    setIsSearching(false)
  }

  // 处理搜索
  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (query.trim()) {
      performSearch(query, filters)
    }
  }

  // 处理输入变化
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value
    setQuery(value)

    // 实时搜索（防抖）
    if (value.trim()) {
      const timeoutId = setTimeout(() => {
        performSearch(value, filters)
      }, 300)
      return () => clearTimeout(timeoutId)
    } else {
      setSearchResults([])
    }
  }

  // 切换展开/折叠
  const toggleSection = (type: SearchType) => {
    setExpandedSections(prev => {
      const next = new Set(prev)
      if (next.has(type)) {
        next.delete(type)
      } else {
        next.add(type)
      }
      return next
    })
  }

  // 按类型分组搜索结果
  const resultsByType = {
    chat: searchResults.filter(r => r.type === 'chat'),
    report: searchResults.filter(r => r.type === 'report'),
    watchlist: searchResults.filter(r => r.type === 'watchlist')
  }

  // 获取最近搜索历史
  const recentHistory = history.slice(0, 5)

  return (
    <div className="container mx-auto max-w-4xl p-6 space-y-6">
      {/* 页面标题 */}
      <div className="flex items-center gap-3 mb-8">
        <div className="p-3 bg-primary/10 rounded-lg">
          <Search className="w-6 h-6 text-primary" />
        </div>
        <div>
          <h1 className="text-2xl font-bold">搜索</h1>
          <p className="text-sm text-muted-foreground">搜索聊天记录、报告和监控列表</p>
        </div>
      </div>

      {/* 搜索框 */}
      <form onSubmit={handleSearch} className="relative">
        <div className="relative">
          <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-muted-foreground" size={20} />
          <input
            ref={searchInputRef}
            type="text"
            value={query}
            onChange={handleInputChange}
            placeholder="搜索内容、关键词或话题..."
            className={cn(
              "w-full pl-12 pr-12 py-4 bg-background border border-border rounded-lg",
              "focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent",
              "text-base"
            )}
          />
          {query && (
            <button
              type="button"
              onClick={() => setQuery('')}
              className="absolute right-4 top-1/2 transform -translate-y-1/2 text-muted-foreground hover:text-foreground"
            >
              <X size={20} />
            </button>
          )}
        </div>

        {/* 搜索建议和历史 */}
        {!query && recentHistory.length > 0 && (
          <div className="mt-4 p-4 bg-card rounded-lg border border-border">
            <div className="flex items-center gap-2 mb-3">
              <Clock size={16} className="text-muted-foreground" />
              <h3 className="font-medium text-sm">最近搜索</h3>
            </div>
            <div className="flex flex-wrap gap-2">
              {recentHistory.map(item => (
                <button
                  key={item.id}
                  onClick={() => {
                    setQuery(item.query)
                    performSearch(item.query, filters)
                  }}
                  className="flex items-center gap-2 px-3 py-1.5 bg-muted hover:bg-muted/80 rounded-lg text-sm transition-colors"
                >
                  <History size={14} className="text-muted-foreground" />
                  {item.query}
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      removeFromHistory(item.id)
                    }}
                    className="text-muted-foreground hover:text-foreground"
                  >
                    <X size={14} />
                  </button>
                </button>
              ))}
            </div>
          </div>
        )}
      </form>

      {/* 搜索结果 */}
      <div className="space-y-4">
        {isSearching ? (
          <div className="flex items-center justify-center py-12">
            <div className="flex items-center gap-3">
              <div className="w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin" />
              <span className="text-muted-foreground">搜索中...</span>
            </div>
          </div>
        ) : searchResults.length > 0 ? (
          <>
            {/* 结果统计 */}
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                找到 <span className="font-medium">{searchResults.length}</span> 条结果
              </p>
              {history.length > 0 && (
                <button
                  onClick={clearHistory}
                  className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
                >
                  <Trash2 size={14} />
                  清空历史
                </button>
              )}
            </div>

            {/* 按类型分组的搜索结果 */}
            <SearchSection
              icon={<MessageSquare size={20} />}
              title="对话记录"
              count={resultsByType.chat.length}
              results={resultsByType.chat}
              isExpanded={expandedSections.has('chat')}
              onToggle={() => toggleSection('chat')}
            />

            <SearchSection
              icon={<FileText size={20} />}
              title="研究报告"
              count={resultsByType.report.length}
              results={resultsByType.report}
              isExpanded={expandedSections.has('report')}
              onToggle={() => toggleSection('report')}
            />

            <SearchSection
              icon={<BarChart3 size={20} />}
              title="监控列表"
              count={resultsByType.watchlist.length}
              results={resultsByType.watchlist}
              isExpanded={expandedSections.has('watchlist')}
              onToggle={() => toggleSection('watchlist')}
            />
          </>
        ) : query ? (
          <div className="text-center py-12">
            <Search className="w-12 h-12 mx-auto mb-4 text-muted-foreground opacity-50" />
            <h3 className="font-medium mb-2">未找到相关结果</h3>
            <p className="text-sm text-muted-foreground">
              尝试使用不同的关键词或检查拼写
            </p>
          </div>
        ) : null}
      </div>
    </div>
  )
}
