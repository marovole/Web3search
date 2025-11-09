/**
 * Streaming Chat Component
 * Real-time chat with SSE streaming responses
 * Part of Week 2 T13: Frontend SSE Integration
 */

import { useState, useEffect, useRef } from 'react'
import { useChatSSE } from '../../hooks/useSSE'
import type { ChatSSEEvent } from '../../lib/sse'

export interface StreamingChatProps {
  apiUrl: string
  conversationId?: string
  onMessageComplete?: (message: string) => void
  onError?: (error: Error) => void
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  isStreaming?: boolean
}

export function StreamingChat({
  apiUrl,
  conversationId,
  onMessageComplete,
  onError,
}: StreamingChatProps) {
  const [query, setQuery] = useState('')
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const {
    messages: sseMessages,
    currentMessage,
    isConnected,
    error,
    start,
    stop,
    reset,
  } = useChatSSE(apiUrl, {
    onMessage: (data: ChatSSEEvent) => {
      if (data.error) {
        onError?.(new Error(data.error))
        return
      }

      // Check if this is the final message
      if (data.finish_reason === 'stop') {
        setIsStreaming(false)
        setMessages(prev => {
          const updated = [...prev]
          const lastMessage = updated[updated.length - 1]
          if (lastMessage && lastMessage.isStreaming) {
            lastMessage.isStreaming = false
            onMessageComplete?.(lastMessage.content)
          }
          return updated
        })
      }
    },
    onError: (err) => {
      setIsStreaming(false)
      onError?.(err)
    },
  })

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, currentMessage])

  // Build message from SSE chunks
  useEffect(() => {
    if (currentMessage && isStreaming) {
      setMessages(prev => {
        const lastIndex = prev.length - 1
        const lastMessage = prev[lastIndex]

        if (lastMessage && lastMessage.role === 'assistant' && lastMessage.isStreaming) {
          // Update the streaming message
          const updated = [...prev]
          updated[lastIndex] = {
            ...lastMessage,
            content: lastMessage.content + (currentMessage.delta?.content || ''),
          }
          return updated
        } else if (currentMessage.delta?.content) {
          // Start a new assistant message
          return [
            ...prev,
            {
              id: `assistant-${Date.now()}`,
              role: 'assistant',
              content: currentMessage.delta.content,
              timestamp: new Date(),
              isStreaming: true,
            },
          ]
        }

        return prev
      })
    }
  }, [currentMessage, isStreaming])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!query.trim()) return

    // Add user message
    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: query,
      timestamp: new Date(),
    }

    setMessages(prev => [...prev, userMessage])
    setQuery('')
    setIsStreaming(true)

    // Start SSE connection
    try {
      const body = {
        query,
        stream: true,
        conversation_id: conversationId,
      }

      // Connect to SSE endpoint
      // Note: In real implementation, this would be part of start() call
      // For demo purposes, we'll simulate the streaming
      console.log('Starting SSE connection to:', apiUrl)
      start()
    } catch (error) {
      setIsStreaming(false)
      onError?.(error as Error)
    }
  }

  const handleCancel = () => {
    stop()
    setIsStreaming(false)
    setMessages(prev => {
      const updated = [...prev]
      const lastMessage = updated[updated.length - 1]
      if (lastMessage && lastMessage.isStreaming) {
        lastMessage.isStreaming = false
      }
      return updated
    })
  }

  const formatMessageContent = (content: string) => {
    return content.split('\n').map((line, i) => (
      <p key={i} className="mb-2">
        {line}
      </p>
    ))
  }

  return (
    <div className="flex flex-col h-full bg-gray-50 dark:bg-gray-900">
      {/* Connection status */}
      <div className="px-4 py-2 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center space-x-2">
          <div
            className={`w-2 h-2 rounded-full ${
              isConnected ? 'bg-green-500' : 'bg-gray-400'
            }`}
          />
          <span className="text-sm text-gray-600 dark:text-gray-400">
            {isConnected ? 'Connected' : 'Disconnected'}
          </span>
          {isStreaming && (
            <span className="ml-2 text-xs text-blue-600 dark:text-blue-400">
              Streaming...
            </span>
          )}
          {error && (
            <span className="ml-2 text-xs text-red-600 dark:text-red-400">
              Error: {error.message}
            </span>
          )}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-500 dark:text-gray-400">
            <p>Start a conversation</p>
            <p className="text-sm mt-2">Type your message below</p>
          </div>
        ) : (
          messages.map(message => (
            <div
              key={message.id}
              className={`flex ${
                message.role === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              <div
                className={`max-w-3xl px-4 py-3 rounded-lg ${
                  message.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100'
                } ${message.isStreaming ? 'animate-pulse' : ''}`}
              >
                <div className="whitespace-pre-wrap">
                  {formatMessageContent(message.content)}
                </div>
                {message.isStreaming && (
                  <div className="mt-2">
                    <div className="h-1 bg-gray-300 dark:bg-gray-600 rounded overflow-hidden">
                      <div className="h-full bg-blue-500 animate-pulse" style={{ width: '100%' }} />
                    </div>
                  </div>
                )}
                <div className={`text-xs mt-1 ${
                  message.role === 'user'
                    ? 'text-blue-100'
                    : 'text-gray-500 dark:text-gray-400'
                }`}>
                  {message.timestamp.toLocaleTimeString()}
                </div>
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input form */}
      <div className="px-4 py-4 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700">
        <form onSubmit={handleSubmit} className="flex space-x-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type your message..."
            disabled={isStreaming}
            className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={!query.trim() || isStreaming}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            {isStreaming ? 'Streaming...' : 'Send'}
          </button>
          {isStreaming && (
            <button
              type="button"
              onClick={handleCancel}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
            >
              Cancel
            </button>
          )}
        </form>
      </div>
    </div>
  )
}

export default StreamingChat
