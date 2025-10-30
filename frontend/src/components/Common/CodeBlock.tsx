import React, { Suspense, lazy } from 'react'

/**
 * Props for CodeBlock component compatible with react-markdown
 */
interface CodeBlockProps {
  inline?: boolean
  className?: string
  children?: React.ReactNode
  [key: string]: any
}

/**
 * Type-safe code block component for use with react-markdown
 *
 * Handles both inline code (`code`) and block code (```code```)
 * with syntax highlighting via react-syntax-highlighter (lazy loaded)
 */
const CodeBlock: React.FC<CodeBlockProps> = ({ inline, className, children, ...props }) => {
  // Extract language from className (e.g., "language-javascript" -> "javascript")
  const match = /language-(\w+)/.exec(className || '')
  const language = match ? match[1] : undefined

  // Convert children to string
  const code = String(children).replace(/\n$/, '')

  // Render inline code (no lazy loading needed)
  if (inline) {
    return (
      <code className="bg-gray-100 text-red-600 px-1.5 py-0.5 rounded text-sm font-mono" {...props}>
        {code}
      </code>
    )
  }

  // Render block code with syntax highlighting (lazy loaded)
  return (
    <Suspense fallback={
      <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg my-2 overflow-x-auto">
        <code>{code}</code>
      </pre>
    }>
      <LazySyntaxHighlighter language={language || 'text'} {...props}>
        {code}
      </LazySyntaxHighlighter>
    </Suspense>
  )
}

// 内部组件：处理动态导入的语法高亮
const LazySyntaxHighlighter: React.FC<{
  language: string
  children: string
  [key: string]: any
}> = ({ language, children, ...props }) => {
  const [Component, setComponent] = React.useState<any>(null)
  const [theme, setTheme] = React.useState<any>(null)

  React.useEffect(() => {
    Promise.all([
      import('react-syntax-highlighter').then(m => m.Prism),
      import('react-syntax-highlighter/dist/esm/styles/prism').then(m => m.tomorrow)
    ]).then(([SyntaxHighlighterComp, tomorrowTheme]) => {
      setComponent(() => SyntaxHighlighterComp)
      setTheme(tomorrowTheme)
    })
  }, [])

  if (!Component || !theme) {
    return (
      <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg my-2 overflow-x-auto">
        <code>{children}</code>
      </pre>
    )
  }

  return (
    <Component
      style={theme}
      language={language}
      PreTag="div"
      className="rounded-lg my-2"
      {...props}
    >
      {children}
    </Component>
  )
}

export default CodeBlock
