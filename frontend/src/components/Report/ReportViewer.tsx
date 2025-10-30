import React, { useState, useEffect, lazy, Suspense } from 'react'
import remarkGfm from 'remark-gfm'
import type { SharedReportResponse } from '../../types'
import ExportButton from './ExportButton'
import AddButton from '../Watchlist/AddButton'
import CodeBlock from '../Common/CodeBlock'

// 动态导入ReactMarkdown（按需加载）
const ReactMarkdown = lazy(() => import('react-markdown'))

interface ReportViewerProps {
  report: SharedReportResponse
}

interface TOCItem {
  id: string
  text: string
  level: number
}

const ReportViewer: React.FC<ReportViewerProps> = ({ report }) => {
  const [toc, setToc] = useState<TOCItem[]>([])
  const [activeId, setActiveId] = useState<string>('')

  // Generate TOC from markdown
  useEffect(() => {
    const headings: TOCItem[] = []
    const lines = report.markdown_content.split('\n')

    lines.forEach((line) => {
      const match = line.match(/^(#{2,4})\s+(.+)$/)
      if (match) {
        const level = match[1].length
        const text = match[2].trim()
        const id = text
          .toLowerCase()
          .replace(/[^a-z0-9\u4e00-\u9fa5]+/g, '-')
          .replace(/^-|-$/g, '')
        headings.push({ id, text, level })
      }
    })

    setToc(headings)
  }, [report.markdown_content])

  // Scroll spy for active section
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setActiveId(entry.target.id)
          }
        })
      },
      { rootMargin: '-20% 0% -35% 0%' }
    )

    // Observe all headings
    toc.forEach((item) => {
      const element = document.getElementById(item.id)
      if (element) {
        observer.observe(element)
      }
    })

    return () => observer.disconnect()
  }, [toc])

  const scrollToSection = (id: string) => {
    const element = document.getElementById(id)
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }

  return (
    <div className="flex gap-6">
      {/* Table of Contents (Desktop only) */}
      {toc.length > 0 && (
        <aside className="hidden lg:block w-64 flex-shrink-0 sticky top-6 self-start no-print">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
            <h3 className="text-sm font-semibold text-gray-900 mb-3">目录</h3>
            <nav className="space-y-1">
              {toc.map((item) => (
                <button
                  key={item.id}
                  onClick={() => scrollToSection(item.id)}
                  className={`
                    block w-full text-left text-sm py-1 px-2 rounded transition-colors
                    ${activeId === item.id ? 'text-primary font-medium bg-blue-50' : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'}
                    ${item.level === 3 ? 'pl-4' : ''}
                    ${item.level === 4 ? 'pl-6' : ''}
                  `}
                >
                  {item.text}
                </button>
              ))}
            </nav>
          </div>
        </aside>
      )}

      {/* Report Content */}
      <div className="flex-1 min-w-0">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 print-full-width">
          {/* Report Header */}
          <div className="mb-8 pb-6 border-b border-gray-200">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              {report.title}
            </h1>
            <div className="flex flex-wrap items-center gap-4 text-sm text-gray-600">
              <span className="flex items-center gap-1">
                <span>📊</span>
                <span>{report.symbol}</span>
              </span>
              <span className="flex items-center gap-1">
                <span>📅</span>
                <span>{new Date(report.created_at).toLocaleDateString('zh-CN')}</span>
              </span>
              {report.quality_score && (
                <span className="flex items-center gap-1">
                  <span>⭐</span>
                  <span>质量分数: {report.quality_score}/100</span>
                </span>
              )}
              <span className="flex items-center gap-1">
                <span>🏷️</span>
                <span className="capitalize">{report.report_type.replace('_', ' ')}</span>
              </span>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="mb-6 no-print flex flex-wrap gap-3">
            <ExportButton
              markdownContent={report.markdown_content}
              reportTitle={report.title}
              symbol={report.symbol}
            />
            <AddButton symbol={report.symbol} name={report.title} />
          </div>

          {/* Markdown Content */}
          <article className="prose prose-lg max-w-none">
            <Suspense fallback={<div className="text-muted-foreground">加载中...</div>}>
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  // Add IDs to headings for TOC
                  h2: ({ children }) => {
                    const text = String(children)
                    const id = text
                      .toLowerCase()
                      .replace(/[^a-z0-9\u4e00-\u9fa5]+/g, '-')
                      .replace(/^-|-$/g, '')
                    return <h2 id={id}>{children}</h2>
                  },
                  h3: ({ children }) => {
                    const text = String(children)
                    const id = text
                      .toLowerCase()
                      .replace(/[^a-z0-9\u4e00-\u9fa5]+/g, '-')
                      .replace(/^-|-$/g, '')
                    return <h3 id={id}>{children}</h3>
                  },
                  h4: ({ children }) => {
                    const text = String(children)
                    const id = text
                      .toLowerCase()
                      .replace(/[^a-z0-9\u4e00-\u9fa5]+/g, '-')
                      .replace(/^-|-$/g, '')
                    return <h4 id={id}>{children}</h4>
                  },
                  // Code blocks - using type-safe CodeBlock component
                  code: CodeBlock,
                  // Tables
                  table({ children }) {
                    return (
                      <div className="overflow-x-auto my-6">
                        <table className="min-w-full divide-y divide-gray-300 border border-gray-300">
                          {children}
                        </table>
                      </div>
                    )
                  },
                  thead({ children }) {
                    return <thead className="bg-gray-50">{children}</thead>
                  },
                  th({ children }) {
                    return (
                      <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900 border-b border-gray-300">
                        {children}
                      </th>
                    )
                  },
                  td({ children }) {
                    return (
                      <td className="px-4 py-3 text-sm text-gray-700 border-b border-gray-200">
                        {children}
                      </td>
                    )
                  },
                  // Images (Base64 or URLs)
                  img({ src, alt }) {
                    return (
                      <img
                        src={src}
                        alt={alt}
                        className="max-w-full h-auto rounded-lg shadow-sm my-6"
                        loading="lazy"
                      />
                    )
                  },
                  // Links
                  a({ href, children }) {
                    return (
                      <a
                        href={href}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary hover:underline"
                      >
                        {children}
                      </a>
                    )
                  },
                }}
              >
                {report.markdown_content}
              </ReactMarkdown>
            </Suspense>
          </article>

          {/* Footer */}
          <div className="mt-12 pt-6 border-t border-gray-200">
            <div className="flex flex-wrap gap-2 text-xs text-gray-500">
              <span>数据来源:</span>
              {report.data_sources?.map((source, i) => (
                <span key={i} className="bg-gray-100 px-2 py-1 rounded">
                  {source}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ReportViewer
