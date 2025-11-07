import React, { useState } from 'react'
import { Download, FileText, FileJson, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import {
  exportToCSV,
  exportToJSON,
  flattenGitHubResults,
  GITHUB_SEARCH_CSV_HEADERS
} from '@/utils/exportUtils'
import type { GitHubSearchResult } from '@/pages/GitHubSearchPage'

interface SearchResultsExportProps {
  results: GitHubSearchResult[]
  query: string
  className?: string
}

export function SearchResultsExport({
  results,
  query,
  className = ''
}: SearchResultsExportProps) {
  const [exporting, setExporting] = useState<'csv' | 'json' | null>(null)

  const handleExportCSV = () => {
    if (results.length === 0) return

    setExporting('csv')
    try {
      const flattened = flattenGitHubResults(results)
      const filename = `github_search_${query.replace(/[^a-zA-Z0-9]/g, '_')}_${Date.now()}`
      exportToCSV(flattened, filename, GITHUB_SEARCH_CSV_HEADERS)
      
      setTimeout(() => setExporting(null), 500)
    } catch (error) {
      console.error('CSV export failed:', error)
      setExporting(null)
    }
  }

  const handleExportJSON = () => {
    if (results.length === 0) return

    setExporting('json')
    try {
      const filename = `github_search_${query.replace(/[^a-zA-Z0-9]/g, '_')}_${Date.now()}`
      exportToJSON(results, filename, true)
      
      setTimeout(() => setExporting(null), 500)
    } catch (error) {
      console.error('JSON export failed:', error)
      setExporting(null)
    }
  }

  if (results.length === 0) {
    return null
  }

  return (
    <div className={cn('flex items-center gap-2', className)} data-export-button>
      <span className="text-sm text-muted-foreground">导出:</span>
      
      <button
        onClick={handleExportCSV}
        disabled={exporting !== null}
        className={cn(
          'flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium',
          'bg-background border hover:bg-muted transition-colors',
          'disabled:opacity-50 disabled:cursor-not-allowed'
        )}
      >
        {exporting === 'csv' ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin" />
            <span>导出中...</span>
          </>
        ) : (
          <>
            <FileText className="h-4 w-4" />
            <span>CSV</span>
          </>
        )}
      </button>

      <button
        onClick={handleExportJSON}
        disabled={exporting !== null}
        className={cn(
          'flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium',
          'bg-background border hover:bg-muted transition-colors',
          'disabled:opacity-50 disabled:cursor-not-allowed'
        )}
      >
        {exporting === 'json' ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin" />
            <span>导出中...</span>
          </>
        ) : (
          <>
            <FileJson className="h-4 w-4" />
            <span>JSON</span>
          </>
        )}
      </button>
    </div>
  )
}

export default SearchResultsExport

