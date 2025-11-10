import React, { useState, useEffect } from 'react'
import { X, Code2, Loader2, ExternalLink } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { cn } from '@/lib/utils'

// 使用 Prism Light 减少 bundle 体积，按需加载
const loadSyntaxHighlighter = async () => {
  const [PrismLight, vscDarkPlusStyle, vsStyle] = await Promise.all([
    import('react-syntax-highlighter/dist/esm/prism-light').then(m => m.default),
    import('react-syntax-highlighter/dist/esm/styles/prism').then(m => m.vscDarkPlus),
    import('react-syntax-highlighter/dist/esm/styles/prism').then(m => m.vs)
  ])
  return { PrismLight, vscDarkPlusStyle, vsStyle }
}

// 按需加载语言定义
const loadLanguage = async (lang: string, PrismLight: any) => {
  try {
    let langDefinition
    switch (lang.toLowerCase()) {
      case 'typescript':
      case 'ts':
        langDefinition = await import('react-syntax-highlighter/dist/esm/languages/prism/typescript').then(m => m.default)
        break
      case 'javascript':
      case 'js':
        langDefinition = await import('react-syntax-highlighter/dist/esm/languages/prism/javascript').then(m => m.default)
        break
      case 'python':
      case 'py':
        langDefinition = await import('react-syntax-highlighter/dist/esm/languages/prism/python').then(m => m.default)
        break
      case 'rust':
        langDefinition = await import('react-syntax-highlighter/dist/esm/languages/prism/rust').then(m => m.default)
        break
      case 'go':
        langDefinition = await import('react-syntax-highlighter/dist/esm/languages/prism/go').then(m => m.default)
        break
      case 'solidity':
        langDefinition = await import('react-syntax-highlighter/dist/esm/languages/prism/solidity').then(m => m.default)
        break
      case 'json':
        langDefinition = await import('react-syntax-highlighter/dist/esm/languages/prism/json').then(m => m.default)
        break
      case 'jsx':
        langDefinition = await import('react-syntax-highlighter/dist/esm/languages/prism/jsx').then(m => m.default)
        break
      case 'tsx':
        langDefinition = await import('react-syntax-highlighter/dist/esm/languages/prism/tsx').then(m => m.default)
        break
      default:
        return null
    }

    if (langDefinition && PrismLight.registerLanguage) {
      PrismLight.registerLanguage(lang.toLowerCase(), langDefinition)
    }
    return true
  } catch (error) {
    console.warn(`Failed to load language: ${lang}`, error)
    return null
  }
}

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
  const [SyntaxHighlighter, setSyntaxHighlighter] = useState<any>(null)
  const [darkTheme, setDarkTheme] = useState<any>(null)
  const [lightTheme, setLightTheme] = useState<any>(null)

  // 检测暗色模式
  const isDarkMode = document.documentElement.classList.contains('dark')

  // 懒加载 SyntaxHighlighter
  useEffect(() => {
    if (isOpen && !SyntaxHighlighter) {
      loadSyntaxHighlighter().then(({ PrismLight, vscDarkPlusStyle, vsStyle }) => {
        setSyntaxHighlighter(() => PrismLight)
        setDarkTheme(vscDarkPlusStyle)
        setLightTheme(vsStyle)
      })
    }
  }, [isOpen])

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

      const lang = repository.language || 'typescript'
      setCode(mockCode)
      setLanguage(lang)

      // 按需加载语言定义
      if (SyntaxHighlighter) {
        await loadLanguage(lang, SyntaxHighlighter)
      }
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

                {code && !loading && !error && SyntaxHighlighter && darkTheme && lightTheme && (
                  <div className="rounded-lg overflow-hidden border">
                    <SyntaxHighlighter
                      language={language.toLowerCase()}
                      style={isDarkMode ? darkTheme : lightTheme}
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

                {code && !loading && !error && (!SyntaxHighlighter || !darkTheme || !lightTheme) && (
                  <div className="rounded-lg overflow-hidden border p-4 bg-muted">
                    <pre className="text-sm overflow-x-auto">
                      <code>{code}</code>
                    </pre>
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

