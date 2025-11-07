import React, { useState, useEffect } from 'react'
import { Search, Code, GitBranch, GitPullRequest, Loader2, Star, GitFork, Eye, Calendar } from 'lucide-react'
import { cn } from '@/lib/utils'
import { motion, AnimatePresence } from 'framer-motion'

// 类型定义
interface GitHubSearchResult {
  id: number
  name: string
  full_name: string
  description: string
  html_url: string
  language: string
  stargazers_count: number
  forks_count: number
  watchers_count: number
  created_at: string
  updated_at: string
  pushed_at: string
  owner: {
    login: string
    avatar_url: string
  }
}

interface AIGeneratedSummary {
  total_results: number
  result_types: Record<string, number>
  key_insights: string[]
  top_repositories: string[]
  languages: Array<{ name: string; count: number }>
}

interface GitHubSearchResponse {
  success: boolean
  data: {
    total_count: number
    items: GitHubSearchResult[]
    page: number
    per_page: number
  }
  summary: AIGeneratedSummary
  query: string
  search_type: string
  execution_time_ms: number
}

const GitHubSearchPage: React.FC = () => {
  const [query, setQuery] = useState('')
  const [searchType, setSearchType] = useState<'repositories' | 'commits' | 'issues'>('repositories')
  const [page, setPage] = useState(1)
  const [perPage, setPerPage] = useState(10)
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState<GitHubSearchResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  // 执行搜索
  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault()

    if (!query.trim()) {
      setError('请输入搜索关键词')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const apiUrl = import.meta.env.VITE_API_BASE_URL || 'https://web3search-api.onrender.com'
      const apiKey = import.meta.env.VITE_API_KEY || 'test123'

      const url = new URL(`${apiUrl}/api/v1/github/search`)
      url.searchParams.append('query', query)
      url.searchParams.append('search_type', searchType)
      url.searchParams.append('page', page.toString())
      url.searchParams.append('per_page', perPage.toString())

      const response = await fetch(url.toString(), {
        headers: {
          'x-api-key': apiKey,
          'Accept': 'application/json'
        }
      })

      if (!response.ok) {
        throw new Error(`搜索失败: ${response.statusText}`)
      }

      const data: GitHubSearchResponse = await response.json()

      if (!data.success) {
        throw new Error('搜索请求失败')
      }

      setResults(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : '搜索失败，请稍后重试')
      console.error('GitHub search error:', err)
    } finally {
      setLoading(false)
    }
  }

  // 当页码变化时重新搜索
  useEffect(() => {
    if (query && results) {
      handleSearch()
    }
  }, [page, perPage])

  // 格式化日期
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }

  // 格式化数字
  const formatNumber = (num: number) => {
    if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'k'
    }
    return num.toString()
  }

  return (
    <div className="min-h-screen bg-background p-6 md:p-8">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* 页面标题 */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-2"
        >
          <h1 className="text-4xl font-bold flex items-center gap-3">
            <Code className="h-10 w-10 text-primary" />
            GitHub 代码搜索
          </h1>
          <p className="text-muted-foreground text-lg">
            搜索 GitHub 上的代码仓库、提交记录和议题，并获取 AI 智能摘要
          </p>
        </motion.div>

        {/* 搜索表单 */}
        <motion.form
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          onSubmit={handleSearch}
          className="bg-card rounded-lg border p-6 shadow-sm space-y-4"
        >
          {/* 搜索输入框 */}
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="输入搜索关键词，如: blockchain, ethereum, web3..."
                className="w-full pl-10 pr-4 py-3 bg-background border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className={cn(
                "px-6 py-3 bg-primary text-primary-foreground rounded-lg font-medium",
                "hover:bg-primary/90 transition-colors",
                "disabled:opacity-50 disabled:cursor-not-allowed",
                "flex items-center gap-2"
              )}
            >
              {loading ? (
                <>
                  <Loader2 className="h-5 w-5 animate-spin" />
                  搜索中...
                </>
              ) : (
                <>
                  <Search className="h-5 w-5" />
                  搜索
                </>
              )}
            </button>
          </div>

          {/* 搜索选项 */}
          <div className="flex flex-wrap items-center gap-4">
            {/* 搜索类型 */}
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-muted-foreground">类型:</span>
              <div className="flex gap-2">
                {[
                  { value: 'repositories', label: '仓库', icon: <Code className="h-4 w-4" /> },
                  { value: 'commits', label: '提交', icon: <GitBranch className="h-4 w-4" /> },
                  { value: 'issues', label: '议题', icon: <GitPullRequest className="h-4 w-4" /> }
                ].map(({ value, label, icon }) => (
                  <button
                    key={value}
                    type="button"
                    onClick={() => {
                      setSearchType(value as any)
                      setPage(1)
                    }}
                    className={cn(
                      "px-3 py-1.5 rounded-md text-sm font-medium transition-colors",
                      "flex items-center gap-1.5",
                      searchType === value
                        ? "bg-primary text-primary-foreground"
                        : "bg-muted hover:bg-muted/80"
                    )}
                  >
                    {icon}
                    {label}
                  </button>
                ))}
              </div>
            </div>

            {/* 每页数量 */}
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-muted-foreground">每页:</span>
              <select
                value={perPage}
                onChange={(e) => {
                  setPerPage(Number(e.target.value))
                  setPage(1)
                }}
                className="px-3 py-1.5 bg-background border rounded-md text-sm"
              >
                <option value={5}>5</option>
                <option value={10}>10</option>
                <option value={20}>20</option>
                <option value={50}>50</option>
              </select>
            </div>
          </div>
        </motion.form>

        {/* 错误信息 */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="bg-destructive/10 border border-destructive/20 text-destructive rounded-lg p-4"
            >
              <p className="font-medium">⚠️ {error}</p>
            </motion.div>
          )}
        </AnimatePresence>

        {/* 搜索结果 */}
        <AnimatePresence mode="wait">
          {results && (
            <motion.div
              key="results"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="space-y-6"
            >
              {/* AI 摘要 */}
              {results.summary && results.summary.key_insights.length > 0 && (
                <div className="bg-gradient-to-br from-primary/10 to-primary/5 rounded-lg border p-6 space-y-4">
                  <h2 className="text-2xl font-bold flex items-center gap-2">
                    🤖 AI 智能摘要
                  </h2>
                  <div className="space-y-3">
                    {results.summary.key_insights.map((insight, index) => (
                      <div key={index} className="flex gap-2">
                        <span className="text-primary font-bold">•</span>
                        <p className="text-sm leading-relaxed">{insight}</p>
                      </div>
                    ))}
                  </div>

                  {/* 语言分布 */}
                  {results.summary.languages.length > 0 && (
                    <div className="pt-4 border-t">
                      <h3 className="text-sm font-medium text-muted-foreground mb-2">编程语言分布</h3>
                      <div className="flex flex-wrap gap-2">
                        {results.summary.languages.map((lang) => (
                          <span
                            key={lang.name}
                            className="px-3 py-1 bg-background rounded-full text-xs font-medium border"
                          >
                            {lang.name} ({lang.count})
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* 结果统计 */}
              <div className="flex items-center justify-between">
                <p className="text-sm text-muted-foreground">
                  找到 <span className="font-bold text-foreground">{results.data.total_count.toLocaleString()}</span> 个结果
                  <span className="mx-2">•</span>
                  耗时 <span className="font-medium">{(results.execution_time_ms / 1000).toFixed(2)}s</span>
                </p>
              </div>

              {/* 仓库列表 */}
              <div className="space-y-4">
                {results.data.items.map((item, index) => (
                  <motion.a
                    key={item.id}
                    href={item.html_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05 }}
                    className="block bg-card rounded-lg border p-5 hover:border-primary/50 hover:shadow-md transition-all"
                  >
                    <div className="space-y-3">
                      {/* 仓库信息 */}
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1 space-y-2">
                          <h3 className="text-xl font-bold text-primary hover:underline flex items-center gap-2">
                            {item.full_name}
                          </h3>
                          {item.description && (
                            <p className="text-sm text-muted-foreground line-clamp-2">
                              {item.description}
                            </p>
                          )}
                        </div>
                        {item.owner.avatar_url && (
                          <img
                            src={item.owner.avatar_url}
                            alt={item.owner.login}
                            className="w-12 h-12 rounded-full border-2"
                          />
                        )}
                      </div>

                      {/* 统计信息 */}
                      <div className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground">
                        {item.language && (
                          <span className="flex items-center gap-1.5">
                            <span className="w-3 h-3 rounded-full bg-primary" />
                            {item.language}
                          </span>
                        )}
                        <span className="flex items-center gap-1.5">
                          <Star className="h-4 w-4" />
                          {formatNumber(item.stargazers_count)}
                        </span>
                        <span className="flex items-center gap-1.5">
                          <GitFork className="h-4 w-4" />
                          {formatNumber(item.forks_count)}
                        </span>
                        <span className="flex items-center gap-1.5">
                          <Eye className="h-4 w-4" />
                          {formatNumber(item.watchers_count)}
                        </span>
                        <span className="flex items-center gap-1.5">
                          <Calendar className="h-4 w-4" />
                          更新于 {formatDate(item.updated_at)}
                        </span>
                      </div>
                    </div>
                  </motion.a>
                ))}
              </div>

              {/* 分页控制 */}
              {results.data.total_count > perPage && (
                <div className="flex items-center justify-center gap-2 pt-4">
                  <button
                    onClick={() => setPage(Math.max(1, page - 1))}
                    disabled={page === 1 || loading}
                    className={cn(
                      "px-4 py-2 rounded-lg border font-medium transition-colors",
                      "disabled:opacity-50 disabled:cursor-not-allowed",
                      "hover:bg-muted"
                    )}
                  >
                    上一页
                  </button>
                  <span className="px-4 py-2 text-sm text-muted-foreground">
                    第 {page} 页 / 共 {Math.ceil(results.data.total_count / perPage)} 页
                  </span>
                  <button
                    onClick={() => setPage(page + 1)}
                    disabled={page >= Math.ceil(results.data.total_count / perPage) || loading}
                    className={cn(
                      "px-4 py-2 rounded-lg border font-medium transition-colors",
                      "disabled:opacity-50 disabled:cursor-not-allowed",
                      "hover:bg-muted"
                    )}
                  >
                    下一页
                  </button>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>

        {/* 空状态 */}
        {!loading && !results && !error && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center py-20 space-y-4"
          >
            <Code className="h-20 w-20 text-muted-foreground/30 mx-auto" />
            <div className="space-y-2">
              <h3 className="text-xl font-medium text-muted-foreground">
                开始搜索 GitHub 代码仓库
              </h3>
              <p className="text-sm text-muted-foreground">
                输入关键词如 "blockchain"、"ethereum" 或 "web3" 来发现相关项目
              </p>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  )
}

export default GitHubSearchPage
