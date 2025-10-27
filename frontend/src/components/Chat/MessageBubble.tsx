import React from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { Message } from '../../types'
import CodeBlock from '../Common/CodeBlock'
import { useTypewriter } from '../../hooks/useTypewriter'

interface MessageBubbleProps {
  message: Message
  /** 是否启用打字机效果（默认启用） */
  enableTypewriter?: boolean
}

const MessageBubble: React.FC<MessageBubbleProps> = ({
  message,
  enableTypewriter = true
}) => {
  const isUser = message.role === 'user'

  // 为助手消息启用打字机效果
  const { displayedText, isTyping, skipAnimation } = useTypewriter(
    message.content,
    {
      enabled: enableTypewriter && !isUser,
      speed: 40, // 40ms/字符
      isStreaming: message.isStreaming,
    }
  )

  // 使用打字机文本（如果启用），否则使用原始内容
  const contentToDisplay = (enableTypewriter && !isUser) ? displayedText : message.content

  return (
    <div
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4 animate-fade-in`}
    >
      <div className={isUser ? 'message-user' : 'message-assistant'}>
        {isUser ? (
          // User message - plain text
          <p className="whitespace-pre-wrap">{message.content}</p>
        ) : (
          // Assistant message - Markdown rendering with typewriter effect
          <div
            className="prose prose-sm max-w-none cursor-pointer"
            onClick={isTyping ? skipAnimation : undefined}
            title={isTyping ? '点击跳过动画' : undefined}
          >
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                // Code block with syntax highlighting - using type-safe CodeBlock component
                code: CodeBlock,
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
              {contentToDisplay}
            </ReactMarkdown>

            {/* Typing indicator or Streaming indicator */}
            {(isTyping || message.isStreaming) && (
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
