import React, { useEffect, useRef } from 'react'
import type { Message } from '../../types'
import MessageBubble from './MessageBubble'

interface MessageListProps {
  messages: Message[]
}

interface AnimatedMessageProps {
  message: Message
  index: number
  totalMessages: number
}

const AnimatedMessage: React.FC<AnimatedMessageProps> = ({ message, index, totalMessages }) => {
  const isNew = index === totalMessages - 1
  const isUser = message.role === 'user'

  return (
    <div
      className={`
        flex ${isUser ? 'justify-end' : 'justify-start'} mb-3 md:mb-4
        ${isNew ? 'animate-slide-up animate-fade-in' : ''}
        ${!isNew ? 'opacity-100' : ''}
      `}
      style={{
        animationDelay: isNew ? '0ms' : '0ms',
        animationDuration: '300ms'
      }}
    >
      <MessageBubble
        key={message.id}
        message={message}
        enableTypewriter={true}
      />
    </div>
  )
}

const MessageList: React.FC<MessageListProps> = ({ messages }) => {
  const listRef = useRef<HTMLDivElement>(null)
  const previousMessagesLength = useRef(messages.length)

  // 检测新消息并滚动到底部
  useEffect(() => {
    const hasNewMessage = messages.length > previousMessagesLength.current
    previousMessagesLength.current = messages.length

    if (hasNewMessage && listRef.current) {
      // 平滑滚动到最新消息
      const timer = setTimeout(() => {
        listRef.current?.scrollIntoView({
          behavior: 'smooth',
          block: 'end',
          inline: 'nearest'
        })
      }, 100) // 短暂延迟确保DOM已更新

      return () => clearTimeout(timer)
    }
  }, [messages])

  return (
    <div className="relative">
      <div
        ref={listRef}
        className="space-y-3 md:space-y-2 custom-scrollbar"
        style={{ scrollBehavior: 'smooth' }}
      >
        {messages.map((message, index) => (
          <AnimatedMessage
            key={message.id}
            message={message}
            index={index}
            totalMessages={messages.length}
          />
        ))}
      </div>

      {/* 滚动指示器 */}
      {messages.length > 0 && (
        <div className="absolute bottom-0 left-0 right-0 h-8 bg-gradient-to-t from-background to-transparent pointer-events-none" />
      )}
    </div>
  )
}

export default MessageList
