import React, { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { Message } from '../../types'
import CodeBlock from '../Common/CodeBlock'
import { useTypewriter } from '../../hooks/useTypewriter'
import { useTouchGestures } from '../../hooks/useTouchGestures'
import { Copy, Check, X, Share2 } from 'lucide-react'
import { cn } from '@/lib/utils'

interface MessageBubbleProps {
  message: Message
  enableTypewriter?: boolean
  showCopyButton?: boolean
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

  const { displayedText, isTyping, skipAnimation } = useTypewriter(
    message.content,
    {
      enabled: enableTypewriter && !isUser,
      speed: 20, // Faster typing for tech feel
      isStreaming: message.isStreaming,
    }
  )

  const contentToDisplay = (enableTypewriter && !isUser) ? displayedText : message.content

  const { handleTouchStart, handleTouchMove, handleTouchEnd } = useTouchGestures({
    onLongPress: () => {
      onLongPress?.(message)
      setShowActions(true)
    },
    onTouchEnd: () => {
      setTimeout(() => setShowActions(false), 3000)
    }
  }, {
    longPressConfig: { duration: 400, moveThreshold: 15 }
  })

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
    <div className={cn(
      "flex w-full mb-6 group animate-fade-in",
      isUser ? "justify-end" : "justify-start"
    )}>
      <div
        className={cn(
          "relative max-w-[90%] md:max-w-[80%] transition-all duration-200",
          isUser ? "message-user" : "message-assistant tech-card p-6",
          showActions && "ring-2 ring-primary/50"
        )}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
      >
        {/* Mobile Actions Overlay */}
        {showActions && (
          <div className="absolute -top-3 -right-3 z-20 flex gap-2 p-1 animate-scale-in">
            {showCopyButton && (
              <button
                onClick={handleCopy}
                className="p-2 bg-primary text-primary-foreground rounded-full shadow-lg"
              >
                {copied ? <Check size={14} /> : <Copy size={14} />}
              </button>
            )}
            <button
              onClick={() => setShowActions(false)}
              className="p-2 bg-muted text-muted-foreground rounded-full shadow-lg"
            >
              <X size={14} />
            </button>
          </div>
        )}

        {isUser ? (
          // User Message: Minimal, clean text
          <div className="text-base md:text-lg font-medium leading-relaxed whitespace-pre-wrap">
            {message.content}
          </div>
        ) : (
          // Assistant Message: Rich Tech Card
          <div className="w-full">
            {/* Header with Icon */}
            <div className="flex items-center gap-2 mb-3 pb-2 border-b border-white/5">
              <div className="w-5 h-5 rounded bg-primary/20 flex items-center justify-center">
                <span className="text-xs text-primary">AI</span>
              </div>
              <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Analysis Result
              </span>
              <span className="ml-auto text-xs text-muted-foreground/70 font-mono">
                {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            </div>

            {/* Content */}
            <div
              className="prose prose-invert prose-sm md:prose-base max-w-none 
                prose-headings:text-foreground prose-headings:font-semibold prose-headings:tracking-tight
                prose-p:text-foreground/95 prose-li:text-foreground/90
                prose-a:text-secondary prose-a:no-underline hover:prose-a:underline
                prose-strong:text-foreground prose-code:text-primary prose-code:bg-primary/15 prose-code:px-1 prose-code:rounded
                prose-pre:bg-black/50 prose-pre:border prose-pre:border-white/10"
              onClick={isTyping ? skipAnimation : undefined}
            >
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  code: CodeBlock,
                  table({ children }) {
                    return (
                      <div className="overflow-x-auto my-4 border border-white/10 rounded-lg bg-black/20">
                        <table className="min-w-full divide-y divide-white/10 text-sm">
                          {children}
                        </table>
                      </div>
                    )
                  },
                  thead({ children }) {
                    return <thead className="bg-white/5">{children}</thead>
                  },
                  th({ children }) {
                    return (
                      <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                        {children}
                      </th>
                    )
                  },
                  td({ children }) {
                    return (
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-foreground/90 border-t border-white/5">
                        {children}
                      </td>
                    )
                  },
                  a({ href, children }) {
                    return (
                      <a
                        href={href}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary hover:text-primary/80 transition-colors inline-flex items-center gap-1"
                      >
                        {children}
                        <Share2 size={10} className="opacity-50" />
                      </a>
                    )
                  },
                }}
              >
                {contentToDisplay}
              </ReactMarkdown>
              
              {(isTyping || message.isStreaming) && (
                <span className="inline-block w-1.5 h-4 bg-primary animate-pulse ml-1 align-middle"></span>
              )}
            </div>

            {/* Footer Actions (Desktop) */}
            {!isTyping && !message.isStreaming && showCopyButton && (
              <div className="mt-4 pt-3 border-t border-white/5 flex justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                <button
                  onClick={handleCopy}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium text-muted-foreground hover:bg-white/5 hover:text-foreground transition-colors"
                >
                  {copied ? <Check size={14} /> : <Copy size={14} />}
                  {copied ? 'Copied' : 'Copy'}
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default MessageBubble
