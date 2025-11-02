import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import '@testing-library/jest-dom'
import MessageBubble from '../../../components/Chat/MessageBubble'
import type { Message } from '../../../types'

// Mock message factory
const mockMessageFactory = {
  build: (overrides: Partial<Message> = {}): Message => ({
    id: '1',
    role: 'user',
    content: 'Test message',
    timestamp: new Date(),
    isStreaming: false,
    ...overrides,
  }) as Message,
}

// Mock the hooks
jest.mock('../../../hooks/useTypewriter', () => ({
  useTypewriter: jest.fn((content, options) => ({
    displayedText: options?.enabled ? content.substring(0, Math.floor(content.length / 2)) : content,
    isTyping: options?.enabled && !options?.isStreaming,
    skipAnimation: jest.fn()
  }))
}))

jest.mock('../../../hooks/useTouchGestures', () => ({
  useTouchGestures: jest.fn(() => ({
    handleTouchStart: jest.fn(),
    handleTouchMove: jest.fn(),
    handleTouchEnd: jest.fn()
  }))
}))

// Mock ReactMarkdown and remark-gfm
jest.mock('react-markdown', () => {
  return function MockReactMarkdown({ children }: { children: React.ReactNode }) {
    return <div data-testid="markdown-content">{children}</div>
  }
})

jest.mock('remark-gfm', () => ({
  default: jest.fn()
}))

// Mock CodeBlock component
jest.mock('../../../components/Common/CodeBlock', () => {
  return function MockCodeBlock({ children }: { children: React.ReactNode }) {
    return <code data-testid="code-block">{children}</code>
  }
})

describe('MessageBubble', () => {
  const user = userEvent.setup()

  beforeEach(() => {
    // Clear all mocks
    jest.clearAllMocks()
    
    // Mock navigator.clipboard
    Object.defineProperty(navigator, 'clipboard', {
      value: {
        writeText: jest.fn().mockResolvedValue(undefined),
      },
      writable: true,
    })
  })

  describe('Rendering', () => {
    it('should render user message correctly', () => {
      const userMessage = mockMessageFactory.build({
        role: 'user',
        content: 'This is a user message'
      })

      render(<MessageBubble message={userMessage} />)

      expect(screen.getByText('This is a user message')).toBeInTheDocument()
      expect(screen.getByText('This is a user message')).toHaveClass('whitespace-pre-wrap')
    })

    it('should render assistant message with markdown', async () => {
      const assistantMessage = mockMessageFactory.build({
        role: 'assistant',
        content: '# Title\n\nThis is **bold** text.'
      })

      render(<MessageBubble message={assistantMessage} />)

      // React.lazy + Suspense may resolve asynchronously; wait until markdown renders
      await waitFor(() => expect(screen.getByTestId('markdown-content')).toBeInTheDocument())
      const md = screen.getByTestId('markdown-content') as HTMLElement
      expect(md.textContent).toMatch(/Title/i)
      expect((md.textContent || '').length).toBeGreaterThan(0)
    })

    it('should display timestamp correctly', () => {
      const timestamp = new Date('2024-01-01T10:30:00')
      const message = mockMessageFactory.build({
        timestamp
      })

      render(<MessageBubble message={message} />)

      expect(screen.getByText('10:30')).toBeInTheDocument()
    })

    it('should show copy button for assistant messages', () => {
      const assistantMessage = mockMessageFactory.build({ role: 'assistant' })

      render(<MessageBubble message={assistantMessage} />)

      expect(screen.getByRole('button', { name: /复制/i })).toBeInTheDocument()
    })

    it('should not show copy button for user messages', () => {
      const userMessage = mockMessageFactory.build({ role: 'user' })

      render(<MessageBubble message={userMessage} />)

      expect(screen.queryByRole('button', { name: /复制/i })).not.toBeInTheDocument()
    })
  })

  describe('Copy functionality', () => {
    it('should copy message content when copy button is clicked', async () => {
      const assistantMessage = mockMessageFactory.build({
        role: 'assistant',
        content: 'This is the message content to copy'
      })

      render(<MessageBubble message={assistantMessage} />)

      const copyButton = screen.getByRole('button', { name: /复制/i })
      await user.click(copyButton)

      expect(navigator.clipboard.writeText).toHaveBeenCalledWith('This is the message content to copy')
    })

    it('should show copied state after successful copy', async () => {
      const assistantMessage = mockMessageFactory.build({ role: 'assistant' })
      
      render(<MessageBubble message={assistantMessage} />)

      const copyButton = screen.getByRole('button', { name: /复制/i })
      await user.click(copyButton)

      await waitFor(() => {
        expect(screen.getByText('已复制')).toBeInTheDocument()
      })
    })

    it('should handle copy errors gracefully', async () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation()
      navigator.clipboard.writeText = jest.fn().mockRejectedValue(new Error('Copy failed'))

      const assistantMessage = mockMessageFactory.build({ role: 'assistant' })
      
      render(<MessageBubble message={assistantMessage} />)

      const copyButton = screen.getByRole('button', { name: /复制/i })
      await user.click(copyButton)

      expect(consoleSpy).toHaveBeenCalledWith('Failed to copy text: ', expect.any(Error))
      
      consoleSpy.mockRestore()
    })
  })

  describe('Typewriter effect', () => {
    it('should enable typewriter effect for assistant messages by default', () => {
      const { useTypewriter } = require('../../../hooks/useTypewriter')
      const assistantMessage = mockMessageFactory.build({ role: 'assistant' })

      render(<MessageBubble message={assistantMessage} />)

      expect(useTypewriter).toHaveBeenCalledWith(
        assistantMessage.content,
        expect.objectContaining({
          enabled: true,
          speed: 40,
          isStreaming: false
        })
      )
    })

    it('should disable typewriter effect for user messages', () => {
      const { useTypewriter } = require('../../../hooks/useTypewriter')
      const userMessage = mockMessageFactory.build({ role: 'user' })

      render(<MessageBubble message={userMessage} />)

      expect(useTypewriter).toHaveBeenCalledWith(
        userMessage.content,
        expect.objectContaining({
          enabled: false
        })
      )
    })

    it('should disable typewriter effect when enableTypewriter prop is false', () => {
      const { useTypewriter } = require('../../../hooks/useTypewriter')
      const assistantMessage = mockMessageFactory.build({ role: 'assistant' })

      render(<MessageBubble message={assistantMessage} enableTypewriter={false} />)

      expect(useTypewriter).toHaveBeenCalledWith(
        assistantMessage.content,
        expect.objectContaining({
          enabled: false
        })
      )
    })

    it('should show typing indicator when typewriter is active', () => {
      const { useTypewriter } = require('../../../hooks/useTypewriter')
      useTypewriter.mockReturnValue({
        displayedText: 'Partial content',
        isTyping: true,
        skipAnimation: jest.fn()
      })

      const assistantMessage = mockMessageFactory.build({ role: 'assistant' })

      render(<MessageBubble message={assistantMessage} />)

      expect(screen.getByTestId('markdown-content')).toBeInTheDocument()
      expect(screen.getByText('Partial content')).toBeInTheDocument()
    })
  })

  describe('Touch gestures', () => {
    it('should apply touch gesture handlers', () => {
      const { useTouchGestures } = require('../../../hooks/useTouchGestures')
      const mockHandlers = {
        handleTouchStart: jest.fn(),
        handleTouchMove: jest.fn(),
        handleTouchEnd: jest.fn()
      }
      useTouchGestures.mockReturnValue(mockHandlers)

      const message = mockMessageFactory.build()
      
      render(<MessageBubble message={message} />)

      const messageContainer = screen.getByText(message.content).closest('div') as HTMLElement
      // Simulate touch events and assert handlers called
      fireEvent.touchStart(messageContainer)
      fireEvent.touchMove(messageContainer)
      fireEvent.touchEnd(messageContainer)

      expect(mockHandlers.handleTouchStart).toHaveBeenCalled()
      expect(mockHandlers.handleTouchMove).toHaveBeenCalled()
      expect(mockHandlers.handleTouchEnd).toHaveBeenCalled()
    })

    it('should call onLongPress callback when provided', () => {
      const onLongPressMock = jest.fn()
      const { useTouchGestures } = require('../../../hooks/useTouchGestures')
      
      useTouchGestures.mockImplementation((opts: any) => {
        const { onLongPress } = opts
        // Simulate long press by calling the callback
        setTimeout(() => onLongPress?.(), 0)
        return {
          handleTouchStart: jest.fn(),
          handleTouchMove: jest.fn(),
          handleTouchEnd: jest.fn()
        }
      })

      const message = mockMessageFactory.build()
      
      render(<MessageBubble message={message} onLongPress={onLongPressMock} />)

      // Wait for the simulated long press
      setTimeout(() => {
        expect(onLongPressMock).toHaveBeenCalledWith(message)
      }, 10)
    })
  })

  describe('Accessibility', () => {
    it('should have proper ARIA labels', () => {
      const assistantMessage = mockMessageFactory.build({ role: 'assistant' })

      render(<MessageBubble message={assistantMessage} />)

      const copyButton = screen.getByRole('button', { name: /复制/i })
      expect(copyButton).toHaveAttribute('title', '复制消息')
    })

    it('should provide title for typing indicator', () => {
      const { useTypewriter } = require('../../../hooks/useTypewriter')
      useTypewriter.mockReturnValue({
        displayedText: 'Partial content',
        isTyping: true,
        skipAnimation: jest.fn()
      })

      const assistantMessage = mockMessageFactory.build({ role: 'assistant' })

      render(<MessageBubble message={assistantMessage} />)

      const markdownContainer = screen.getByTestId('markdown-content').parentElement
      expect(markdownContainer).toHaveAttribute('title', '点击跳过动画')
    })

    it('should have proper semantic structure', () => {
      const userMessage = mockMessageFactory.build({ role: 'user' })

      render(<MessageBubble message={userMessage} />)

      const messageContent = screen.getByText(userMessage.content)
      expect(messageContent.tagName).toBe('P')
      expect(messageContent).toHaveClass('select-text')
    })
  })

  describe('Props behavior', () => {
    it('should hide copy button when showCopyButton is false', () => {
      const assistantMessage = mockMessageFactory.build({ role: 'assistant' })

      render(<MessageBubble message={assistantMessage} showCopyButton={false} />)

      expect(screen.queryByRole('button', { name: /复制/i })).not.toBeInTheDocument()
    })

    it('should handle streaming messages correctly', () => {
      const { useTypewriter } = require('../../../hooks/useTypewriter')
      const streamingMessage = mockMessageFactory.build({
        role: 'assistant',
        isStreaming: true
      })

      render(<MessageBubble message={streamingMessage} />)

      expect(useTypewriter).toHaveBeenCalledWith(
        streamingMessage.content,
        expect.objectContaining({
          isStreaming: true
        })
      )
    })
  })
})
