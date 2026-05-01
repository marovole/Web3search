import React, { useEffect, useRef } from 'react'
import { useVirtualizer } from '@tanstack/react-virtual'
import type { Message } from '../../types'
import MessageBubble from './MessageBubble'

/** Below this count, render all rows (simpler scroll + unit tests); above, virtualize for long threads. */
export const MESSAGE_LIST_VIRTUAL_THRESHOLD = 32

interface MessageListProps {
  messages: Message[]
  /** When set, this element must be `overflow-y: auto` and contain the list (Chat shell scroll). */
  scrollParentRef?: React.RefObject<HTMLElement | null>
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
        animationDuration: '300ms',
      }}
    >
      <MessageBubble message={message} enableTypewriter={true} />
    </div>
  )
}

const ESTIMATE_ROW_PX = 120

const scrollContainerClass =
  'overflow-y-auto space-y-3 md:space-y-2 custom-scrollbar relative'

const MessageList: React.FC<MessageListProps> = ({ messages, scrollParentRef }) => {
  const internalScrollRef = useRef<HTMLDivElement>(null)
  const scrollRef = scrollParentRef ?? internalScrollRef
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const previousMessagesLength = useRef(0)

  const useVirtual = messages.length > MESSAGE_LIST_VIRTUAL_THRESHOLD

  const rowVirtualizer = useVirtualizer({
    count: useVirtual ? messages.length : 0,
    getScrollElement: () => scrollRef.current,
    estimateSize: () => ESTIMATE_ROW_PX,
    overscan: 8,
    measureElement:
      typeof window !== 'undefined'
        ? (el) => Math.ceil(el.getBoundingClientRect().height)
        : undefined,
  })

  useEffect(() => {
    const previous = previousMessagesLength.current
    previousMessagesLength.current = messages.length

    if (messages.length <= previous || messages.length === 0) {
      return
    }

    const id = window.setTimeout(() => {
      if (useVirtual) {
        try {
          rowVirtualizer.scrollToIndex(messages.length - 1, { align: 'end', behavior: 'smooth' })
        } catch {
          scrollRef.current?.scrollTo?.({
            top: scrollRef.current.scrollHeight,
            behavior: 'smooth',
          })
        }
      } else {
        messagesEndRef.current?.scrollIntoView({
          behavior: 'smooth',
          block: 'end',
          inline: 'nearest',
        })
      }
    }, 100)

    return () => window.clearTimeout(id)
  }, [messages.length, messages, rowVirtualizer, scrollRef, useVirtual])

  const flatList = !useVirtual && messages.length > 0 && (
    <>
      {messages.map((message, index) => (
        <AnimatedMessage
          key={message.id}
          message={message}
          index={index}
          totalMessages={messages.length}
        />
      ))}
      <div ref={messagesEndRef} />
    </>
  )

  const virtualList = useVirtual && messages.length > 0 && (
    <div
      className="relative w-full"
      style={{
        height: `${rowVirtualizer.getTotalSize()}px`,
      }}
    >
      {rowVirtualizer.getVirtualItems().map((virtualRow) => {
        const message = messages[virtualRow.index]
        if (!message) return null
        return (
          <div
            key={virtualRow.key}
            data-index={virtualRow.index}
            ref={rowVirtualizer.measureElement}
            className="absolute left-0 top-0 w-full"
            style={{
              transform: `translateY(${virtualRow.start}px)`,
            }}
          >
            <AnimatedMessage
              message={message}
              index={virtualRow.index}
              totalMessages={messages.length}
            />
          </div>
        )
      })}
    </div>
  )

  const innerContent = flatList || virtualList

  return (
    <div className="relative">
      {scrollParentRef ? (
        innerContent
      ) : (
        <div
          ref={internalScrollRef}
          className={scrollContainerClass}
          style={{ scrollBehavior: 'smooth' }}
        >
          {innerContent}
        </div>
      )}

      {messages.length > 0 && (
        <div className="absolute bottom-0 left-0 right-0 h-8 bg-gradient-to-t from-background to-transparent pointer-events-none" />
      )}
    </div>
  )
}

export default MessageList
