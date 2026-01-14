import React, { useState } from 'react'
import secureAuthApi from '../../services/secureAuth'
import { useToast } from '../ui/toast'

interface ExportButtonProps {
  markdownContent: string
  reportTitle: string
  symbol: string
  reportId?: number
  isCompleted?: boolean
}

const ExportButton: React.FC<ExportButtonProps> = ({
  markdownContent,
  reportTitle,
  symbol,
  reportId,
  isCompleted = false,
}) => {
  const [copying, setCopying] = useState(false)
  const [exportingPdf, setExportingPdf] = useState(false)
  const [showSuccess, setShowSuccess] = useState(false)
  const { toast } = useToast()

  // Download Markdown file
  const handleDownloadMarkdown = () => {
    const blob = new Blob([markdownContent], { type: 'text/markdown;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    // Use reportTitle for better filename, fallback to symbol
    const filename = reportTitle
      ? `${reportTitle.replace(/[^a-zA-Z0-9_\u4e00-\u9fa5]/g, '_')}_${Date.now()}.md`
      : `${symbol}_report_${Date.now()}.md`
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    showSuccessMessage()
  }

  // Download PDF from backend
  const handleDownloadPDF = async () => {
    if (!reportId || !isCompleted) {
      toast({
        title: '无法导出PDF',
        description: 'PDF导出仅支持已完成的报告',
        variant: 'destructive',
      })
      return
    }

    try {
      setExportingPdf(true)

      // 使用配置好的API客户端（支持httpOnly cookie认证）
      const response = await secureAuthApi.get(
        `/api/v1/reports/reports/${reportId}/export/pdf`,
        {
          responseType: 'blob',
        }
      )

      if (!response.data) {
        throw new Error('PDF导出失败: 无响应数据')
      }

      // 获取文件名（从响应头中提取）
      const contentDisposition = response.headers['content-disposition']
      let filename = `${symbol}_深度研究报告_${new Date().toISOString().split('T')[0]}.pdf`

      if (contentDisposition) {
        const matches = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/)
        if (matches && matches[1]) {
          filename = matches[1].replace(/['"]/g, '')
        }
      }

      // 下载文件
      const blob = response.data as Blob
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)

      showSuccessMessage()
    } catch (error) {
      console.error('PDF导出失败:', error)
      toast({
        title: 'PDF导出失败',
        description: error instanceof Error ? error.message : '未知错误',
        variant: 'destructive',
      })
    } finally {
      setExportingPdf(false)
    }
  }

  // Print as PDF (browser print dialog)
  const handlePrintPDF = () => {
    window.print()
  }

  // Copy share link to clipboard
  const handleCopyShareLink = async () => {
    setCopying(true)
    try {
      if (reportId) {
        // If we have reportId, generate share link via API
        // For now, just copy current URL
        const shareUrl = window.location.href
        await navigator.clipboard.writeText(shareUrl)
      } else {
        // For shared reports, copy current URL
        await navigator.clipboard.writeText(window.location.href)
      }
      showSuccessMessage()
    } catch (error) {
      console.error('Failed to copy:', error)
    } finally {
      setCopying(false)
    }
  }

  const showSuccessMessage = () => {
    setShowSuccess(true)
    setTimeout(() => setShowSuccess(false), 2000)
  }

  return (
    <div className="flex flex-wrap gap-2">
      {/* Download Markdown */}
      <button
        onClick={handleDownloadMarkdown}
        className="btn-secondary flex items-center gap-2"
      >
        <svg
          className="w-4 h-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
          />
        </svg>
        <span>下载 Markdown</span>
      </button>

      {/* Download PDF */}
      {reportId && isCompleted && (
        <button
          onClick={handleDownloadPDF}
          disabled={exportingPdf}
          className="btn-secondary flex items-center gap-2"
        >
          {exportingPdf ? (
            <>
              <svg
                className="animate-spin w-4 h-4"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                ></circle>
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                ></path>
              </svg>
              <span>导出PDF中...</span>
            </>
          ) : (
            <>
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
              <span>下载 PDF</span>
            </>
          )}
        </button>
      )}

      {/* Print as PDF */}
      <button
        onClick={handlePrintPDF}
        className="btn-secondary flex items-center gap-2"
      >
        <svg
          className="w-4 h-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z"
          />
        </svg>
        <span>打印 PDF</span>
      </button>

      {/* Copy Share Link */}
      <button
        onClick={handleCopyShareLink}
        disabled={copying}
        className="btn-secondary flex items-center gap-2"
      >
        <svg
          className="w-4 h-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z"
          />
        </svg>
        <span>{copying ? '复制中...' : '复制链接'}</span>
      </button>

      {/* Success Message */}
      {showSuccess && (
        <div className="fixed bottom-4 right-4 bg-success text-white px-4 py-2 rounded-lg shadow-lg animate-slide-up z-50">
          <div className="flex items-center gap-2">
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M5 13l4 4L19 7"
              />
            </svg>
            <span>操作成功</span>
          </div>
        </div>
      )}
    </div>
  )
}

export default ExportButton
