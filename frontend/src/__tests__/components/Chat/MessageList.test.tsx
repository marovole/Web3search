import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import MessageList, { MESSAGE_LIST_VIRTUAL_THRESHOLD } from '../../../components/Chat/MessageList'
import type { Message } from '../../../types'

// Local message factory helpers to avoid ESM dependency in tests
const buildMessage = (overrides: Partial<Message> = {}): Message => ({
  id: String(Date.now() + Math.random()),
  role: 'user',
  content: 'Test message',
  timestamp: new Date(),
  isStreaming: false,
  ...overrides,
}) as Message

const buildList = (count: number, overrides: Partial<Message>[] = []): Message[] => {
  const list: Message[] = []
  for (let i = 0; i < count; i++) {
    list.push(
      buildMessage({
        id: `${Date.now()}-${i}-${Math.random()}`,
        ...(overrides[i] || {}),
      })
    )
  }
  return list
}

// Mock MessageBubble component
jest.mock('../../../components/Chat/MessageBubble', () => {
  return function MockMessageBubble({ message, enableTypewriter }: { 
    message: any, 
    enableTypewriter?: boolean 
  }) {
    return (
      <div data-testid="message-bubble" data-role={message.role}>
        <span data-testid="message-content">{message.content}</span>
        <span data-testid="message-id">{message.id}</span>
        {enableTypewriter && <span data-testid="typewriter-enabled"></span>}
      </div>
    )
  }
})

describe('MessageList', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Rendering', () => {
    it('should render empty message list', () => {
      render(<MessageList messages={[]} />)
      
      expect(screen.queryByTestId('message-bubble')).not.toBeInTheDocument()
    })

    it('should render single message', () => {
      const message = buildMessage({
        content: 'Hello world'
      })

      render(<MessageList messages={[message]} />)

      expect(screen.getByTestId('message-bubble')).toBeInTheDocument()
      expect(screen.getByText('Hello world')).toBeInTheDocument()
      expect(screen.getByTestId('message-id')).toHaveTextContent(message.id)
    })

    it('should render multiple messages in order', () => {
      const messages = buildList(3, [
        { content: 'First message' },
        { content: 'Second message' },
        { content: 'Third message' }
      ])

      render(<MessageList messages={messages} />)

      const messageBubbles = screen.getAllByTestId('message-bubble')
      expect(messageBubbles).toHaveLength(3)
      
      expect(screen.getByText('First message')).toBeInTheDocument()
      expect(screen.getByText('Second message')).toBeInTheDocument()
      expect(screen.getByText('Third message')).toBeInTheDocument()
    })

    it('should pass correct props to MessageBubble', () => {
      const message = buildMessage({
        role: 'assistant',
        content: 'Assistant message'
      })

      render(<MessageList messages={[message]} />)

      const messageBubble = screen.getByTestId('message-bubble')
      expect(messageBubble).toHaveAttribute('data-role', 'assistant')
      expect(screen.getByTestId('typewriter-enabled')).toBeInTheDocument()
    })

    it('should show scroll gradient when messages exist', () => {
      const messages = buildList(2)

      render(<MessageList messages={messages} />)

      // Check for scroll gradient indicator
      const gradient = document.querySelector('.bg-gradient-to-t')
      expect(gradient).toBeInTheDocument()
    })

    it('should not show scroll gradient when no messages', () => {
      render(<MessageList messages={[]} />)

      const gradient = document.querySelector('.bg-gradient-to-t')
      expect(gradient).not.toBeInTheDocument()
    })
  })

  describe('Message ordering and animation', () => {
    it('should render user messages with correct alignment', () => {
      const userMessage = buildMessage({ role: 'user' })

      render(<MessageList messages={[userMessage]} />)

      const messageContainer = screen.getByTestId('message-bubble').parentElement
      expect(messageContainer).toHaveClass('justify-end')
    })

    it('should render assistant messages with correct alignment', () => {
      const assistantMessage = buildMessage({ role: 'assistant' })

      render(<MessageList messages={[assistantMessage]} />)

      const messageContainer = screen.getByTestId('message-bubble').parentElement
      expect(messageContainer).toHaveClass('justify-start')
    })

    it('should apply animation classes to new messages', () => {
      const messages = buildList(2)

      render(<MessageList messages={messages} />)

      const messageContainers = screen.getAllByTestId('message-bubble').map(bubble => bubble.parentElement)
      
      // Last message should have animation classes
      expect(messageContainers[1]).toHaveClass('animate-slide-up', 'animate-fade-in')
    })

    it('should not apply animation to older messages', () => {
      const messages = buildList(3)

      render(<MessageList messages={messages} />)

      const messageContainers = screen.getAllByTestId('message-bubble').map(bubble => bubble.parentElement)
      
      // First message should not have animation classes
      expect(messageContainers[0]).not.toHaveClass('animate-slide-up')
      expect(messageContainers[0]).toHaveClass('opacity-100')
    })
  })

  describe('Scroll behavior', () => {
    beforeEach(() => {
      // Mock scrollIntoView
      window.HTMLElement.prototype.scrollIntoView = jest.fn()
    })

    it('should scroll to bottom when new message is added', async () => {
      const { rerender } = render(<MessageList messages={[]} />)
      
      // Initial state - no scroll
      expect(window.HTMLElement.prototype.scrollIntoView).not.toHaveBeenCalled()

      // Add new message
      const newMessage = buildMessage()
      rerender(<MessageList messages={[newMessage]} />)

      // Wait for the scroll timeout
      await waitFor(() => {
        expect(window.HTMLElement.prototype.scrollIntoView).toHaveBeenCalledWith({
          behavior: 'smooth',
          block: 'end',
          inline: 'nearest'
        })
      })
    })

    it('should scroll when multiple messages are added', async () => {
      const { rerender } = render(<MessageList messages={[]} />)
      
      // Add first message
      const firstMessage = buildMessage()
      rerender(<MessageList messages={[firstMessage]} />)

      // Add second message
      const secondMessage = buildMessage()
      rerender(<MessageList messages={[firstMessage, secondMessage]} />)

      await waitFor(() => {
        expect((window.HTMLElement.prototype.scrollIntoView as jest.Mock).mock.calls.length).toBeGreaterThanOrEqual(1)
      })
    })

    it('should not scroll when message list length decreases', async () => {
      const messages = buildList(2)
      const { rerender } = render(<MessageList messages={messages} />)

      // Clear scrollIntoView mock
      jest.clearAllMocks()

      // Remove a message
      rerender(<MessageList messages={messages.slice(0, 1)} />)

      // Wait a bit to ensure no scroll is triggered
      await new Promise(resolve => setTimeout(resolve, 150))

      expect(window.HTMLElement.prototype.scrollIntoView).not.toHaveBeenCalled()
    })
  })

  describe('Component structure', () => {
    it('should have proper container structure', () => {
      const messages = buildList(2)

      render(<MessageList messages={messages} />)

      // Check for relative container
      const firstBubble = screen.getAllByTestId('message-bubble')[0]
      const scrollContainer = document.querySelector('.custom-scrollbar')
      expect(scrollContainer).toBeInTheDocument()
      expect(scrollContainer?.contains(firstBubble)).toBe(true)
    })

    it('should apply correct CSS classes', () => {
      const messages = buildList(2)

      render(<MessageList messages={messages} />)

      const scrollContainer = document.querySelector('.custom-scrollbar')
      expect(scrollContainer).toHaveClass('space-y-3', 'md:space-y-2')
      expect(scrollContainer).toHaveStyle('scroll-behavior: smooth')
    })

    it('should have unique keys for each message', () => {
      const messages = buildList(3)

      render(<MessageList messages={messages} />)

      const messageIdEls = screen.getAllByTestId('message-id')
      const ids = messageIdEls.map(el => el.textContent)
      
      // All message IDs should be unique
      const uniqueIds = new Set(ids)
      expect(uniqueIds.size).toBe(3)
    })
  })

  describe('Edge cases', () => {
    it('should handle empty content messages', () => {
      const emptyMessage = buildMessage({ content: '' })

      render(<MessageList messages={[emptyMessage]} />)

      expect(screen.getByTestId('message-bubble')).toBeInTheDocument()
      expect(screen.getByTestId('message-content')).toHaveTextContent('')
    })

    it('should handle very long messages', () => {
      const longContent = 'A'.repeat(1000)
      const longMessage = buildMessage({ content: longContent })

      render(<MessageList messages={[longMessage]} />)

      expect(screen.getByTestId('message-content')).toHaveTextContent(longContent)
    })

    it('should handle messages with special characters', () => {
      const specialContent = 'Special chars: !@#$%^&*()_+-=[]{}|;:,.<>?'
      const specialMessage = buildMessage({ content: specialContent })

      render(<MessageList messages={[specialMessage]} />)

      expect(screen.getByTestId('message-content')).toHaveTextContent(specialContent)
    })

    it('should handle messages with newlines', () => {
      const multilineContent = 'Line 1\nLine 2\nLine 3'
      const multilineMessage = buildMessage({ content: multilineContent })

      render(<MessageList messages={[multilineMessage]} />)

      expect(screen.getByTestId('message-content')).toHaveTextContent(/Line 1\s*Line 2\s*Line 3/)
    })
  })

  describe('Performance', () => {
    beforeEach(() => {
      jest.spyOn(HTMLElement.prototype, 'clientHeight', 'get').mockReturnValue(480)
      jest.spyOn(HTMLElement.prototype, 'scrollHeight', 'get').mockReturnValue(50000)
      global.ResizeObserver = class {
        observe(): void {}
        unobserve(): void {}
        disconnect(): void {}
      }
      jest.spyOn(Element.prototype, 'getBoundingClientRect').mockImplementation(
        () =>
          ({
            width: 400,
            height: 88,
            top: 0,
            left: 0,
            bottom: 88,
            right: 400,
            x: 0,
            y: 0,
            toJSON: () => ({}),
          }) as DOMRect
      )
    })

    afterEach(() => {
      jest.restoreAllMocks()
    })

    it('uses tall spacer layout for long threads (virtualized path)', () => {
      const count = MESSAGE_LIST_VIRTUAL_THRESHOLD + 40
      const messages = buildList(count)

      const startTime = performance.now()
      render(<MessageList messages={messages} />)
      const endTime = performance.now()

      expect(endTime - startTime).toBeLessThan(400)

      const spacer = document.querySelector('.relative.w-full')
      expect(spacer).toBeInTheDocument()
      const heightPx = spacer?.getAttribute('style')?.match(/height:\s*(\d+)/)?.[1]
      expect(Number(heightPx ?? 0)).toBeGreaterThan(count * 80)
    })
  })
})
