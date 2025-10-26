import React from 'react'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism'

/**
 * Props for CodeBlock component
 */
interface CodeBlockProps {
  /**
   * Whether this is inline code or block code
   */
  inline?: boolean
  /**
   * CSS className - typically contains language info like "language-javascript"
   */
  className?: string
  /**
   * The code content to render
   */
  children?: React.ReactNode
}

/**
 * Type-safe code block component for use with react-markdown
 *
 * Handles both inline code (`code`) and block code (```code```)
 * with syntax highlighting via react-syntax-highlighter
 */
const CodeBlock: React.FC<CodeBlockProps> = ({ inline, className, children }) => {
  // Extract language from className (e.g., "language-javascript" -> "javascript")
  const match = /language-(\w+)/.exec(className || '')
  const language = match ? match[1] : undefined

  // Convert children to string
  const code = String(children).replace(/\n$/, '')

  // Render inline code
  if (inline) {
    return (
      <code className="bg-gray-100 text-red-600 px-1.5 py-0.5 rounded text-sm font-mono">
        {code}
      </code>
    )
  }

  // Render block code with syntax highlighting
  return (
    <SyntaxHighlighter
      style={tomorrow}
      language={language || 'text'}
      PreTag="div"
      className="rounded-lg my-2"
    >
      {code}
    </SyntaxHighlighter>
  )
}

export default CodeBlock
