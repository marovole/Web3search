import React from 'react'

type CodeBlockProps = {
  inline?: boolean
  className?: string
  children?: React.ReactNode
}

const CodeBlock: React.FC<CodeBlockProps> = ({ inline, className, children }) => {
  const code = String(children ?? '')

  if (inline) {
    return <code className={className}>{code}</code>
  }

  return (
    <pre className={className ?? 'bg-muted/40 rounded-lg p-3 text-sm font-mono whitespace-pre-wrap overflow-auto'}>
      <code>{code}</code>
    </pre>
  )
}

export default CodeBlock
