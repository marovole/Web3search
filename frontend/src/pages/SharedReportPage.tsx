import React, { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getSharedReport } from '../services/api'
import type { SharedReportResponse } from '../types'
import ReportViewer from '../components/Report/ReportViewer'

const SharedReportPage: React.FC = () => {
  const { shareToken } = useParams<{ shareToken: string }>()
  const [report, setReport] = useState<SharedReportResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadReport = async () => {
      if (!shareToken) {
        setError('分享链接无效')
        setLoading(false)
        return
      }

      try {
        const data = await getSharedReport(shareToken)
        setReport(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : '加载报告失败')
      } finally {
        setLoading(false)
      }
    }

    loadReport()
  }, [shareToken])

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-gray-600">正在加载报告...</p>
        </div>
      </div>
    )
  }

  if (error || !report) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-800 mb-4">⚠️</h1>
          <p className="text-lg text-gray-600 mb-6">{error || '报告不存在或已过期'}</p>
          <Link
            to="/"
            className="btn-primary inline-block"
          >
            返回首页
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4 no-print">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <Link to="/" className="text-2xl font-bold text-primary hover:text-blue-600">
            Web3 AI Search Engine
          </Link>
          <p className="text-sm text-gray-600">
            分享报告
          </p>
        </div>
      </header>

      {/* Report Content */}
      <main className="max-w-5xl mx-auto px-4 py-8">
        <ReportViewer report={report} />
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 px-6 py-4 mt-12 no-print">
        <div className="max-w-5xl mx-auto text-center text-sm text-gray-500">
          <p>
            本报告由 AI 自动生成，仅供参考 ·
            <Link to="/" className="text-primary hover:underline ml-2">
              生成你自己的报告
            </Link>
          </p>
        </div>
      </footer>
    </div>
  )
}

export default SharedReportPage
