import React, { useState } from 'react'
import { Filter, X, Calendar, Star, Code, ChevronDown } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { cn } from '@/lib/utils'

export interface FilterOptions {
  languages: string[]
  starsMin: number | null
  starsMax: number | null
  updatedAfter: string | null
  sortBy: 'stars' | 'updated' | 'created' | 'relevance'
}

interface AdvancedFiltersProps {
  filters: FilterOptions
  onFiltersChange: (filters: FilterOptions) => void
  availableLanguages?: string[]
  className?: string
}

const SORT_OPTIONS = [
  { value: 'stars', label: 'Stars 数' },
  { value: 'updated', label: '更新时间' },
  { value: 'created', label: '创建时间' },
  { value: 'relevance', label: '相关性' }
] as const

const DATE_RANGES = [
  { value: null, label: '全部时间' },
  { value: '7d', label: '最近 7 天' },
  { value: '30d', label: '最近 30 天' },
  { value: '1y', label: '最近 1 年' }
] as const

export function AdvancedFilters({
  filters,
  onFiltersChange,
  availableLanguages = [],
  className = ''
}: AdvancedFiltersProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [languageInput, setLanguageInput] = useState('')

  const updateFilter = <K extends keyof FilterOptions>(
    key: K,
    value: FilterOptions[K]
  ) => {
    onFiltersChange({ ...filters, [key]: value })
  }

  const addLanguage = (lang: string) => {
    if (lang && !filters.languages.includes(lang)) {
      updateFilter('languages', [...filters.languages, lang])
      setLanguageInput('')
    }
  }

  const removeLanguage = (lang: string) => {
    updateFilter(
      'languages',
      filters.languages.filter(l => l !== lang)
    )
  }

  const clearFilters = () => {
    onFiltersChange({
      languages: [],
      starsMin: null,
      starsMax: null,
      updatedAfter: null,
      sortBy: 'relevance'
    })
  }

  const hasActiveFilters =
    filters.languages.length > 0 ||
    filters.starsMin !== null ||
    filters.starsMax !== null ||
    filters.updatedAfter !== null ||
    filters.sortBy !== 'relevance'

  // 过滤可用语言（排除已选择的）
  const filteredLanguages = availableLanguages.filter(
    lang =>
      lang.toLowerCase().includes(languageInput.toLowerCase()) &&
      !filters.languages.includes(lang)
  )

  return (
    <div className={cn('relative', className)}>
      {/* 过滤器按钮 */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          'flex items-center gap-2 px-4 py-2 rounded-lg border transition-colors',
          hasActiveFilters
            ? 'bg-primary/10 border-primary text-primary'
            : 'bg-background border-border hover:bg-muted',
          'text-sm font-medium'
        )}
      >
        <Filter size={16} />
        <span>高级过滤</span>
        {hasActiveFilters && (
          <span className="px-1.5 py-0.5 bg-primary text-primary-foreground rounded-full text-xs">
            {filters.languages.length +
              (filters.starsMin !== null ? 1 : 0) +
              (filters.starsMax !== null ? 1 : 0) +
              (filters.updatedAfter !== null ? 1 : 0)}
          </span>
        )}
        <ChevronDown
          size={16}
          className={cn('transition-transform', isOpen && 'rotate-180')}
        />
      </button>

      {/* 过滤器面板 */}
      <AnimatePresence>
        {isOpen && (
          <>
            {/* 背景遮罩 */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-40"
              onClick={() => setIsOpen(false)}
            />

            {/* 过滤器内容 */}
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="absolute top-full left-0 mt-2 w-96 bg-card border rounded-lg shadow-lg p-4 z-50 space-y-4"
            >
              {/* 语言过滤 */}
              <div>
                <label className="flex items-center gap-2 text-sm font-medium mb-2">
                  <Code size={16} />
                  编程语言
                </label>
                <div className="space-y-2">
                  {/* 已选语言 */}
                  {filters.languages.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                      {filters.languages.map(lang => (
                        <span
                          key={lang}
                          className="inline-flex items-center gap-1 px-2 py-1 bg-primary/10 text-primary rounded-md text-xs"
                        >
                          {lang}
                          <button
                            onClick={() => removeLanguage(lang)}
                            className="hover:text-primary/70"
                          >
                            <X size={12} />
                          </button>
                        </span>
                      ))}
                    </div>
                  )}

                  {/* 语言输入 */}
                  <div className="relative">
                    <input
                      type="text"
                      value={languageInput}
                      onChange={e => setLanguageInput(e.target.value)}
                      onKeyDown={e => {
                        if (e.key === 'Enter' && languageInput) {
                          e.preventDefault()
                          addLanguage(languageInput)
                        }
                      }}
                      placeholder="输入语言名称..."
                      className="w-full px-3 py-2 bg-background border rounded-md text-sm"
                    />
                    {filteredLanguages.length > 0 && (
                      <div className="absolute z-10 w-full mt-1 bg-card border rounded-md shadow-lg max-h-40 overflow-y-auto">
                        {filteredLanguages.slice(0, 10).map(lang => (
                          <button
                            key={lang}
                            onClick={() => addLanguage(lang)}
                            className="w-full px-3 py-2 text-left text-sm hover:bg-muted transition-colors"
                          >
                            {lang}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Stars 范围 */}
              <div>
                <label className="flex items-center gap-2 text-sm font-medium mb-2">
                  <Star size={16} />
                  Stars 数量
                </label>
                <div className="flex items-center gap-2">
                  <input
                    type="number"
                    value={filters.starsMin || ''}
                    onChange={e =>
                      updateFilter(
                        'starsMin',
                        e.target.value ? parseInt(e.target.value) : null
                      )
                    }
                    placeholder="最小值"
                    className="flex-1 px-3 py-2 bg-background border rounded-md text-sm"
                  />
                  <span className="text-muted-foreground">-</span>
                  <input
                    type="number"
                    value={filters.starsMax || ''}
                    onChange={e =>
                      updateFilter(
                        'starsMax',
                        e.target.value ? parseInt(e.target.value) : null
                      )
                    }
                    placeholder="最大值"
                    className="flex-1 px-3 py-2 bg-background border rounded-md text-sm"
                  />
                </div>
              </div>

              {/* 更新时间 */}
              <div>
                <label className="flex items-center gap-2 text-sm font-medium mb-2">
                  <Calendar size={16} />
                  更新时间
                </label>
                <select
                  value={filters.updatedAfter || ''}
                  onChange={e =>
                    updateFilter('updatedAfter', e.target.value || null)
                  }
                  className="w-full px-3 py-2 bg-background border rounded-md text-sm"
                >
                  {DATE_RANGES.map(range => (
                    <option key={range.value || 'all'} value={range.value || ''}>
                      {range.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* 排序 */}
              <div>
                <label className="flex items-center gap-2 text-sm font-medium mb-2">
                  <Filter size={16} />
                  排序方式
                </label>
                <div className="grid grid-cols-2 gap-2">
                  {SORT_OPTIONS.map(option => (
                    <button
                      key={option.value}
                      onClick={() => updateFilter('sortBy', option.value)}
                      className={cn(
                        'px-3 py-2 rounded-md text-sm font-medium transition-colors',
                        filters.sortBy === option.value
                          ? 'bg-primary text-primary-foreground'
                          : 'bg-muted hover:bg-muted/80'
                      )}
                    >
                      {option.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* 操作按钮 */}
              <div className="flex items-center justify-between pt-2 border-t">
                <button
                  onClick={clearFilters}
                  disabled={!hasActiveFilters}
                  className={cn(
                    'px-3 py-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors',
                    'disabled:opacity-50 disabled:cursor-not-allowed'
                  )}
                >
                  清除所有
                </button>
                <button
                  onClick={() => setIsOpen(false)}
                  className="px-4 py-1.5 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:bg-primary/90 transition-colors"
                >
                  应用
                </button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  )
}

export default AdvancedFilters

