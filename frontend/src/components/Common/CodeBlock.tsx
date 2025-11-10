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

// 内部组件：处理动态导入的语法高亮（使用 Prism Light 减少 bundle 体积）
const LazySyntaxHighlighter: React.FC<{
  language: string
  children: string
  [key: string]: any
}> = ({ language, children, ...props }) => {
  const [Component, setComponent] = React.useState<any>(null)
  const [theme, setTheme] = React.useState<any>(null)
  const [languageLoaded, setLanguageLoaded] = React.useState(false)

  // 动态加载语言定义
  const loadLanguage = async (lang: string) => {
    try {
      switch (lang.toLowerCase()) {
        case 'typescript':
        case 'ts':
          const ts = await import('react-syntax-highlighter/dist/esm/languages/prism/typescript')
          return ts.default
        case 'javascript':
        case 'js':
          const js = await import('react-syntax-highlighter/dist/esm/languages/prism/javascript')
          return js.default
        case 'json':
          const json = await import('react-syntax-highlighter/dist/esm/languages/prism/json')
          return json.default
        case 'bash':
        case 'sh':
          const bash = await import('react-syntax-highlighter/dist/esm/languages/prism/bash')
          return bash.default
        case 'sql':
          const sql = await import('react-syntax-highlighter/dist/esm/languages/prism/sql')
          return sql.default
        case 'solidity':
          const solidity = await import('react-syntax-highlighter/dist/esm/languages/prism/solidity')
          return solidity.default
        case 'python':
        case 'py':
          const python = await import('react-syntax-highlighter/dist/esm/languages/prism/python')
          return python.default
        case 'rust':
          const rust = await import('react-syntax-highlighter/dist/esm/languages/prism/rust')
          return rust.default
        case 'go':
          const go = await import('react-syntax-highlighter/dist/esm/languages/prism/go')
          return go.default
        case 'jsx':
          const jsx = await import('react-syntax-highlighter/dist/esm/languages/prism/jsx')
          return jsx.default
        case 'tsx':
          const tsx = await import('react-syntax-highlighter/dist/esm/languages/prism/tsx')
          return tsx.default
        default:
          return null
      }
    } catch (error) {
      console.warn(`Failed to load language: ${lang}`, error)
      return null
    }
  }

  React.useEffect(() => {
    // 使用 Prism Light 并按需加载语言
    Promise.all([
      import('react-syntax-highlighter/dist/esm/prism-light').then(m => m.default),
      import('react-syntax-highlighter/dist/esm/styles/prism').then(m => m.vscDarkPlus),
      loadLanguage(language)
    ]).then(([PrismLight, vscDarkPlusTheme, langDefinition]) => {
      // 如果成功加载了语言定义，注册它
      if (langDefinition && PrismLight.registerLanguage) {
        PrismLight.registerLanguage(language.toLowerCase(), langDefinition)
      }
      setComponent(() => PrismLight)
      setTheme(vscDarkPlusTheme)
      setLanguageLoaded(true)
    })
  }, [language])

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
