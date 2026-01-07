import React, { useState, useRef } from 'react'
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
  Sparkles
} from 'lucide-react'
import { useSearchHistory } from '@/contexts/SearchHistoryContext'

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
    <div className="glass-card overflow-hidden border border-white/5">
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between p-4 hover:bg-white/5 transition-colors group"
      >
        <div className="flex items-center gap-3">
          <div className="p-2 bg-primary/10 rounded-lg text-primary shadow-[0_0_10px_rgba(0,255,255,0.2)] group-hover:shadow-[0_0_15px_rgba(0,255,255,0.4)] transition-all duration-300">
            {icon}
          </div>
          <div className="text-left">
            <h3 className="font-medium text-foreground group-hover:text-primary transition-colors">{title}</h3>
            <p className="text-sm text-muted-foreground">{count} 条结果</p>
          </div>
        </div>
        <motion.div
          animate={{ rotate: isExpanded ? 180 : 0 }}
          transition={{ duration: 0.2 }}
        >
          <Filter size={20} className="text-muted-foreground group-hover:text-primary transition-colors" />
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
            <div className="p-4 border-t border-white/5 space-y-3 bg-black/20">
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
                    className="p-4 bg-white/5 rounded-xl hover:bg-white/10 hover:border-primary/30 border border-transparent transition-all duration-300 cursor-pointer group"
                  >
                    <div className="flex items-start gap-4">
                      <div className="p-2 bg-primary/10 rounded-lg text-primary mt-1">
                        {result.type === 'chat' && <MessageSquare size={16} />}
                        {result.type === 'report' && <FileText size={16} />}
                        {result.type === 'watchlist' && <BarChart3 size={16} />}
                      </div>
                      <div className="flex-1 min-w-0">
                        <h4 className="font-medium text-base truncate text-foreground group-hover:text-primary transition-colors">{result.title}</h4>
                        <p className="text-sm text-muted-foreground mt-1 line-clamp-2 group-hover:text-muted-foreground/80">
                          {result.excerpt}
                        </p>
                        <div className="flex items-center gap-2 mt-3">
                          <span className="text-xs px-2 py-0.5 rounded-full bg-white/5 text-muted-foreground border border-white/5">
                            {new Date(result.timestamp).toLocaleString()}
                          </span>
                        </div>
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
  const filters = {
    type: 'all' as SearchType,
    dateRange: 'all' as const,
    sortBy: 'relevance' as const
  }
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
    setQuery(e.target.value)
  }

  // 实时搜索（防抖）
  React.useEffect(() => {
    const timer = setTimeout(() => {
      if (query.trim()) {
        performSearch(query, filters)
      } else {
        setSearchResults([])
      }
    }, 300)

    return () => clearTimeout(timer)
  }, [query])

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
    <div className="container mx-auto max-w-5xl p-6 space-y-8">
      {/* 页面标题 */}
      <div className="flex items-center gap-4 mb-8 animate-fade-in">
        <div className="p-4 bg-primary/10 rounded-2xl shadow-[0_0_20px_rgba(0,255,255,0.2)] border border-primary/20">
          <Sparkles className="w-8 h-8 text-primary animate-pulse-glow" />
        </div>
        <div>
          <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-white to-white/60">搜索中心</h1>
          <p className="text-base text-muted-foreground mt-1">探索您的Web3数据、报告和对话记录</p>
        </div>
      </div>

      {/* 搜索框 */}
      <form onSubmit={handleSearch} className="relative group animate-slide-up">
        <div className="relative">
          <div className="absolute inset-0 bg-primary/20 blur-xl rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
          <Search className="absolute left-5 top-1/2 transform -translate-y-1/2 text-muted-foreground group-focus-within:text-primary transition-colors" size={24} />
          <input
            ref={searchInputRef}
            type="text"
            value={query}
            onChange={handleInputChange}
            placeholder="搜索内容、关键词或话题..."
            className="w-full pl-14 pr-14 py-5 bg-background/40 backdrop-blur-xl border border-white/10 rounded-2xl focus:outline-none focus:border-primary/50 focus:ring-2 focus:ring-primary/20 text-lg placeholder:text-muted-foreground/60 shadow-lg transition-all duration-300 relative z-10"
          />
          {query && (
            <button
              type="button"
              onClick={() => setQuery('')}
              className="absolute right-5 top-1/2 transform -translate-y-1/2 text-muted-foreground hover:text-foreground z-20"
            >
              <X size={24} />
            </button>
          )}
        </div>

        {/* 搜索建议和历史 */}
        {!query && recentHistory.length > 0 && (
          <div className="mt-6 p-6 glass-card animate-fade-in">
            <div className="flex items-center gap-2 mb-4">
              <Clock size={18} className="text-primary" />
              <h3 className="font-medium text-base">最近搜索</h3>
            </div>
            <div className="flex flex-wrap gap-3">
              {recentHistory.map(item => (
                <button
                  key={item.id}
                  onClick={() => {
                    setQuery(item.query)
                    performSearch(item.query, filters)
                  }}
                  className="flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-primary/10 hover:border-primary/30 border border-white/10 rounded-xl text-sm transition-all duration-200 group"
                >
                  <History size={14} className="text-muted-foreground group-hover:text-primary" />
                  <span className="group-hover:text-primary transition-colors">{item.query}</span>
                  <div
                    onClick={(e) => {
                      e.stopPropagation()
                      removeFromHistory(item.id)
                    }}
                    className="ml-1 p-0.5 rounded-full hover:bg-white/10 text-muted-foreground hover:text-destructive transition-colors"
                  >
                    <X size={14} />
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}
      </form>

      {/* 搜索结果 */}
      <div className="space-y-6 animate-slide-up" style={{ animationDelay: '0.1s' }}>
        {isSearching ? (
          <div className="flex flex-col items-center justify-center py-20">
            <div className="relative">
              <div className="w-16 h-16 border-4 border-primary/30 border-t-primary rounded-full animate-spin" />
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="w-8 h-8 bg-primary/20 rounded-full animate-pulse" />
              </div>
            </div>
            <span className="mt-4 text-muted-foreground animate-pulse">正在搜索全网数据...</span>
          </div>
        ) : searchResults.length > 0 ? (
          <>
            {/* 结果统计 */}
            <div className="flex items-center justify-between px-2">
              <p className="text-sm text-muted-foreground">
                找到 <span className="font-bold text-primary">{searchResults.length}</span> 条结果
              </p>
              {history.length > 0 && (
                <button
                  onClick={clearHistory}
                  className="flex items-center gap-2 text-sm text-muted-foreground hover:text-destructive transition-colors px-3 py-1.5 rounded-lg hover:bg-white/5"
                >
                  <Trash2 size={14} />
                  清空历史
                </button>
              )}
            </div>

            {/* 按类型分组的搜索结果 */}
            <div className="grid gap-6">
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
            </div>
          </>
        ) : query ? (
          <div className="text-center py-20 glass-card">
            <div className="w-20 h-20 mx-auto mb-6 bg-white/5 rounded-full flex items-center justify-center">
              <Search className="w-10 h-10 text-muted-foreground opacity-50" />
            </div>
            <h3 className="text-xl font-medium mb-2">未找到相关结果</h3>
            <p className="text-muted-foreground">
              尝试使用不同的关键词或检查拼写
            </p>
          </div>
        ) : null}
      </div>
    </div>
  )
}
