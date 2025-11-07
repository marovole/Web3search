import React, { useState, useEffect } from 'react'
import { X, Code2, Loader2, ExternalLink } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { vs } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { cn } from '@/lib/utils'

interface CodePreviewProps {
  repository: {
    full_name: string
    html_url: string
    language?: string
  }
  isOpen: boolean
  onClose: () => void
  className?: string
}

/**
 * 代码预览组件
 * 显示仓库的代码片段预览
 */
export function CodePreview({
  repository,
  isOpen,
  onClose,
  className = ''
}: CodePreviewProps) {
  const [code, setCode] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [language, setLanguage] = useState<string>('')

  // 检测暗色模式
  const isDarkMode = document.documentElement.classList.contains('dark')

  useEffect(() => {
    if (isOpen && repository) {
      loadCodePreview()
    } else {
      setCode(null)
      setError(null)
    }
  }, [isOpen, repository])

  const loadCodePreview = async () => {
    setLoading(true)
    setError(null)

    try {
      // 尝试从 GitHub API 获取 README 或主要代码文件
      // 注意：这需要 GitHub token，这里使用模拟数据作为示例
      // 实际实现应该调用后端 API
      
      // 模拟代码预览
      await new Promise(resolve => setTimeout(resolve, 500))
      
      const mockCode = `// ${repository.full_name}
// 这是一个代码预览示例

export function example() {
  console.log('Hello, World!')
  return {
    message: '代码预览功能'
  }
}

// 更多代码...
const data = {
  repository: '${repository.full_name}',
  language: '${repository.language || 'TypeScript'}'
}`

      setCode(mockCode)
      setLanguage(repository.language || 'typescript')
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载代码预览失败')
    } finally {
      setLoading(false)
    }
  }

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

          {/* 预览面板 */}
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className={cn(
                'w-full max-w-4xl max-h-[90vh] bg-card dark:bg-card/95 border border-border dark:border-border/80 rounded-lg shadow-xl dark:shadow-2xl',
                'flex flex-col overflow-hidden',
                className
              )}
              onClick={(e) => e.stopPropagation()}
            >
              {/* 头部 */}
              <div className="flex items-center justify-between p-4 border-b">
                <div className="flex items-center gap-3">
                  <Code2 className="h-5 w-5 text-primary" />
                  <div>
                    <h3 className="font-semibold">{repository.full_name}</h3>
                    <p className="text-sm text-muted-foreground">代码预览</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <a
                    href={repository.html_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="p-2 hover:bg-muted rounded-md transition-colors"
                    title="在 GitHub 上查看"
                  >
                    <ExternalLink size={18} className="text-muted-foreground" />
                  </a>
                  <button
                    onClick={onClose}
                    className="p-2 hover:bg-muted rounded-md transition-colors"
                  >
                    <X size={18} className="text-muted-foreground" />
                  </button>
                </div>
              </div>

              {/* 内容 */}
              <div className="flex-1 overflow-auto p-4">
                {loading && (
                  <div className="flex items-center justify-center py-12">
                    <div className="flex items-center gap-3">
                      <Loader2 className="h-5 w-5 animate-spin text-primary" />
                      <span className="text-muted-foreground">加载代码预览...</span>
                    </div>
                  </div>
                )}

                {error && (
                  <div className="text-center py-12">
                    <p className="text-destructive mb-2">{error}</p>
                    <a
                      href={repository.html_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary hover:underline"
                    >
                      在 GitHub 上查看
                    </a>
                  </div>
                )}

                {code && !loading && !error && (
                  <div className="rounded-lg overflow-hidden border">
                    <SyntaxHighlighter
                      language={language.toLowerCase()}
                      style={isDarkMode ? vscDarkPlus : vs}
                      customStyle={{
                        margin: 0,
                        borderRadius: 0,
                        fontSize: '14px',
                        lineHeight: '1.6'
                      }}
                      showLineNumbers
                    >
                      {code}
                    </SyntaxHighlighter>
                  </div>
                )}
              </div>

              {/* 底部提示 */}
              <div className="p-3 bg-muted/50 border-t text-xs text-muted-foreground text-center">
                提示：这是代码预览示例。实际实现需要集成 GitHub API 获取真实代码内容。
              </div>
            </motion.div>
          </div>
        </>
      )}
    </AnimatePresence>
  )
}

export default CodePreview

