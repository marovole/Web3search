import React from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism'
import type { Message } from '../../types'

interface MessageBubbleProps {
  message: Message
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const isUser = message.role === 'user'

  return (
    <div
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4 animate-fade-in`}
    >
      <div className={isUser ? 'message-user' : 'message-assistant'}>
        {isUser ? (
          // User message - plain text
          <p className="whitespace-pre-wrap">{message.content}</p>
        ) : (
          // Assistant message - Markdown rendering
          <div className="prose prose-sm max-w-none">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                // Code block with syntax highlighting
                // @ts-ignore - react-markdown types compatibility
                code({ node, inline, className, children, ...props }) {
                  const match = /language-(\w+)/.exec(className || '')
                  return !inline && match ? (
                    // @ts-ignore - SyntaxHighlighter types compatibility
                    <SyntaxHighlighter
                      {...props}
                      style={tomorrow}
                      language={match[1]}
                      PreTag="div"
                      className="rounded-md text-sm"
                    >
                      {String(children).replace(/\n$/, '')}
                    </SyntaxHighlighter>
                  ) : (
                    <code {...props} className={`${className} bg-gray-100 px-1 py-0.5 rounded text-sm`}>
                      {children}
                    </code>
                  )
                },
                // Table styling
                table({ children }) {
                  return (
                    <div className="overflow-x-auto my-4">
                      <table className="min-w-full divide-y divide-gray-200 border border-gray-300">
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
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-700 uppercase tracking-wider border-b border-gray-300">
                      {children}
                    </th>
                  )
                },
                td({ children }) {
                  return (
                    <td className="px-4 py-2 text-sm text-gray-900 border-b border-gray-200">
                      {children}
                    </td>
                  )
                },
                // Image handling (Base64 and URLs)
                img({ src, alt }) {
                  return (
                    <img
                      src={src}
                      alt={alt}
                      className="max-w-full h-auto rounded-lg my-4"
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
              {message.content}
            </ReactMarkdown>

            {/* Streaming indicator */}
            {message.isStreaming && (
              <span className="inline-block w-2 h-4 bg-primary animate-pulse ml-1"></span>
            )}
          </div>
        )}

        {/* Timestamp */}
        <p className="text-xs text-gray-500 mt-2">
          {message.timestamp.toLocaleTimeString('zh-CN', {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </p>
      </div>
    </div>
  )
}

export default MessageBubble
