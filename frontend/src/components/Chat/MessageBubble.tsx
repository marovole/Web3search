import React, { useState, lazy, Suspense } from 'react'
import remarkGfm from 'remark-gfm'
import type { Message } from '../../types'
import CodeBlock from '../Common/CodeBlock'
import { useTypewriter } from '../../hooks/useTypewriter'
import { useTouchGestures } from '../../hooks/useTouchGestures'
import { Copy, Check, X } from 'lucide-react'

// 动态导入ReactMarkdown（按需加载）
const ReactMarkdown = lazy(() => import('react-markdown'))

interface MessageBubbleProps {
  message: Message
  /** 是否启用打字机效果（默认启用） */
  enableTypewriter?: boolean
  /** 是否显示复制按钮（移动端默认显示） */
  showCopyButton?: boolean
  /** 长按回调 */
  onLongPress?: (message: Message) => void
}

const MessageBubble: React.FC<MessageBubbleProps> = ({
  message,
  enableTypewriter = true,
  showCopyButton = true,
  onLongPress
}) => {
  const isUser = message.role === 'user'
  const [copied, setCopied] = useState(false)
  const [showActions, setShowActions] = useState(false)

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

  // 触摸手势处理
  const { handleTouchStart, handleTouchMove, handleTouchEnd } = useTouchGestures({
    onLongPress: () => {
      onLongPress?.(message)
      setShowActions(true)
    },
    onTouchEnd: () => {
      setTimeout(() => setShowActions(false), 2000) // 2秒后隐藏操作按钮
    }
  }, {
    longPressConfig: { duration: 400, moveThreshold: 15 }
  })

  // 复制功能
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.content)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy text: ', err)
    }
  }

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} group`}>
      <div
        className={`
          ${isUser ? 'message-user' : 'message-assistant'}
          max-w-[85%] md:max-w-[75%]
          transition-all duration-200
          relative
          touch-manipulation
          mobile-list-item
          ${showActions ? 'ring-2 ring-primary/20' : ''}
        `}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
      >
        {/* 操作按钮 */}
        {showActions && (
          <div className="absolute -top-2 -right-2 z-10 flex gap-1 p-1">
            <button
              onClick={handleCopy}
              className="p-2 bg-primary text-white rounded-full shadow-lg touch-manipulation touch-feedback"
              title="复制"
            >
              {copied ? (
                <Check size={16} />
              ) : (
                <Copy size={16} />
              )}
            </button>
            <button
              onClick={() => setShowActions(false)}
              className="p-2 bg-gray-600 text-white rounded-full shadow-lg touch-manipulation touch-feedback"
              title="关闭"
            >
              <X size={16} />
            </button>
          </div>
        )}

        {isUser ? (
          // User message - plain text with mobile optimization
          <p className="whitespace-pre-wrap text-base md:text-sm select-text">
            {message.content}
          </p>
        ) : (
          // Assistant message - Markdown rendering with typewriter effect
          <div
            className="prose prose-sm max-w-none cursor-pointer select-text"
            onClick={isTyping ? skipAnimation : undefined}
            title={isTyping ? '点击跳过动画' : undefined}
          >
            <Suspense fallback={<div className="text-muted-foreground">加载中...</div>}>
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  // Code block with syntax highlighting - using type-safe CodeBlock component
                  code: CodeBlock,
                  // Table styling with mobile optimization
                  table({ children }) {
                    return (
                      <div className="overflow-x-auto my-4 -mx-4 px-4 md:mx-0 md:px-0">
                        <table className="min-w-full divide-y divide-gray-200 border border-gray-300 text-sm">
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
                      <th className="px-2 py-2 text-left text-xs font-medium text-gray-700 uppercase tracking-wider border-b border-gray-300">
                        {children}
                      </th>
                    )
                  },
                  td({ children }) {
                    return (
                      <td className="px-2 py-2 text-sm text-gray-900 border-b border-gray-200">
                        {children}
                      </td>
                    )
                  },
                  // Image handling with mobile optimization
                  img({ src, alt }) {
                    return (
                      <img
                        src={src}
                        alt={alt}
                        className="max-w-full h-auto rounded-lg my-4 cursor-zoom-in"
                        loading="lazy"
                      />
                    )
                  },
                  // Links with mobile touch targets
                  a({ href, children }) {
                    return (
                      <a
                        href={href}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary hover:underline inline-block touch-target min-h-[44px] min-w-[44px] p-1 -m-1"
                      >
                        {children}
                      </a>
                    )
                  },
                }}
              >
                {contentToDisplay}
              </ReactMarkdown>
            </Suspense>

            {/* Typing indicator or Streaming indicator */}
            {(isTyping || message.isStreaming) && (
              <span className="inline-block w-2 h-4 bg-primary animate-pulse ml-1"></span>
            )}
          </div>
        )}

        {/* Timestamp and Copy Button */}
        <div className="flex items-center justify-between mt-2 text-xs text-gray-500">
          <span>
            {message.timestamp.toLocaleTimeString('zh-CN', {
              hour: '2-digit',
              minute: '2-digit',
            })}
          </span>

          {/* Copy button for desktop */}
          {showCopyButton && !isUser && (
            <button
              onClick={handleCopy}
              className="hidden md:flex items-center gap-1 px-2 py-1 rounded hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors touch-manipulation"
              title="复制消息"
            >
              {copied ? (
                <>
                  <Check size={12} />
                  <span>已复制</span>
                </>
              ) : (
                <>
                  <Copy size={12} />
                  <span>复制</span>
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

export default MessageBubble
