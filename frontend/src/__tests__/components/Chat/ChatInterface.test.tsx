import React from 'react'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import '@testing-library/jest-dom'
import ChatInterface from '../../../components/Chat/ChatInterface'

// Mock API services
jest.mock('../../../services/api', () => ({
  quickChat: jest.fn(),
  deepResearchStream: jest.fn(() => ({
    onmessage: jest.fn(),
    onerror: jest.fn(),
    close: jest.fn()
  }))
}))

// Mock hooks
jest.mock('../../../hooks/useNetworkRetry', () => {
  const fn = jest.fn()
  return { __esModule: true, default: fn }
})

// Mock Sentry
jest.mock('../../../services/sentry', () => ({
  startTransaction: jest.fn(),
  addBreadcrumb: jest.fn(),
  captureException: jest.fn()
}))

// Mock child components
jest.mock('../../../components/Chat/ModeSwitch', () => {
  return function MockModeSwitch({ mode, onChange }: { mode: string, onChange: Function }) {
    return (
      <div data-testid="mode-switch">
        <button 
          data-testid="mode-quick" 
          onClick={() => onChange('quick')}
          className={mode === 'quick' ? 'active' : ''}
        >
          Quick
        </button>
        <button 
          data-testid="mode-deep" 
          onClick={() => onChange('deep')}
          className={mode === 'deep' ? 'active' : ''}
        >
          Deep
        </button>
      </div>
    )
  }
})

jest.mock('../../../components/Chat/MessageList', () => {
  return function MockMessageList({ messages }: { messages: any[] }) {
    return (
      <div data-testid="message-list">
        {messages.map((message) => (
          <div key={message.id} data-testid="message" data-role={message.role}>
            {message.content}
          </div>
        ))}
      </div>
    )
  }
})

jest.mock('../../../components/Chat/AutocompleteInput', () => {
  return function MockAutocompleteInput({ 
    value, 
    onChange, 
    onSend, 
    disabled, 
    placeholder 
  }: {
    value: string
    onChange: (v: string) => void
    onSend: (v: string) => void
    disabled: boolean
    placeholder: string
  }) {
    return (
      <div data-testid="autocomplete-input">
        <input
          data-testid="chat-input"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          disabled={disabled}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && value.trim()) {
              onSend(value)
            }
          }}
        />
        <button 
          data-testid="send-button"
          onClick={() => onSend(value)}
          disabled={disabled}
        >
          Send
        </button>
      </div>
    )
  }
})

jest.mock('../../../components/Hotspot/HotspotPanel', () => {
  return function MockHotspotPanel({ onSelectHotspot }: { onSelectHotspot: Function }) {
    return (
      <div data-testid="hotspot-panel">
        <button 
          data-testid="hotspot-btc"
          onClick={() => (onSelectHotspot as (s: string, n: string) => void)('BTC', 'Bitcoin')}
        >
          BTC (Bitcoin)
        </button>
      </div>
    )
  }
})

jest.mock('../../../components/Error/NetworkErrorRetry', () => {
  return function MockNetworkErrorRetry({ onRetry }: { onRetry: () => void }) {
    return (
      <div data-testid="network-error-retry">
        <button data-testid="retry-button" onClick={() => onRetry()}>
          Retry
        </button>
      </div>
    )
  }
})

jest.mock('../../../components/Shared/LoadingAnimation', () => {
  return function MockLoadingAnimation({ stage, mode }: { stage: number, mode: string }) {
    return (
      <div data-testid="loading-animation">
        Loading stage {stage} for {mode} mode
      </div>
    )
  }
})

describe('ChatInterface', () => {
  const user = userEvent.setup()

  beforeEach(() => {
    jest.clearAllMocks()
    localStorage.clear()
  })

  describe('Initial rendering', () => {
    it('should render chat interface with welcome screen', () => {
      render(<ChatInterface />)

      expect(screen.getByTestId('mode-switch')).toBeInTheDocument()
      expect(screen.getByTestId('hotspot-panel')).toBeInTheDocument()
      expect(screen.getByText(/Quick Start/i)).toBeInTheDocument()
      expect(screen.getByTestId('autocomplete-input')).toBeInTheDocument()
    })

    it('should default to quick mode', () => {
      render(<ChatInterface />)

      const quickButton = screen.getByTestId('mode-quick')
      expect(quickButton).toHaveClass('active')
    })

    it('should load saved mode from localStorage', () => {
      localStorage.setItem('chatMode', 'deep')
      render(<ChatInterface />)

      const deepButton = screen.getByTestId('mode-deep')
      expect(deepButton).toHaveClass('active')
    })

    it('should show correct placeholder based on mode', () => {
      render(<ChatInterface />)
      
      const input = screen.getByTestId('chat-input')
      expect(input).toHaveAttribute('placeholder', 'Ask anything about crypto...')

      // Switch to deep mode
      fireEvent.click(screen.getByTestId('mode-deep'))
      expect(input).toHaveAttribute('placeholder', 'Enter project name for deep research...')
    })
  })

  describe('Mode switching', () => {
    it('should switch between quick and deep mode', async () => {
      render(<ChatInterface />)

      // Initially in quick mode
      expect(screen.getByTestId('mode-quick')).toHaveClass('active')

      // Switch to deep mode
      await user.click(screen.getByTestId('mode-deep'))
      expect(screen.getByTestId('mode-deep')).toHaveClass('active')
      expect(screen.getByTestId('mode-quick')).not.toHaveClass('active')

      // Switch back to quick mode
      await user.click(screen.getByTestId('mode-quick'))
      expect(screen.getByTestId('mode-quick')).toHaveClass('active')
      expect(screen.getByTestId('mode-deep')).not.toHaveClass('active')
    })

    it('should save mode to localStorage', async () => {
      render(<ChatInterface />)

      await user.click(screen.getByTestId('mode-deep'))
      expect(localStorage.getItem('chatMode')).toBe('deep')

      await user.click(screen.getByTestId('mode-quick'))
      expect(localStorage.getItem('chatMode')).toBe('quick')
    })
  })

  describe('Message sending', () => {
    it('should send message in quick mode', async () => {
      const { quickChat } = require('../../../services/api')
      const mockResponse = {
        content: 'This is a response',
        session_id: 'session-123'
      }
      quickChat.mockResolvedValue(mockResponse)

      const useNetworkRetry = require('../../../hooks/useNetworkRetry').default
      const mockExecute = jest.fn().mockResolvedValue(mockResponse)
      useNetworkRetry.mockReturnValue({
        execute: mockExecute,
        state: { isLoading: false, error: null, retryCount: 0 },
        reset: jest.fn()
      })

      render(<ChatInterface />)

      const input = screen.getByTestId('chat-input')
      const sendButton = screen.getByTestId('send-button')

      await user.type(input, 'What is Bitcoin?')
      await user.click(sendButton)

      expect(mockExecute).toHaveBeenCalledWith({
        query: 'What is Bitcoin?',
        conversation_id: undefined
      })

      // Check that messages are displayed
      await waitFor(() => {
        const messages = screen.getAllByTestId('message')
        expect(messages).toHaveLength(2) // User message + assistant response
        expect(messages[0]).toHaveAttribute('data-role', 'user')
        expect(messages[1]).toHaveAttribute('data-role', 'assistant')
      })
    })

    it('should not send empty messages', async () => {
      const { quickChat } = require('../../../services/api')
      const useNetworkRetry = require('../../../hooks/useNetworkRetry').default
      const mockExecute = jest.fn()
      useNetworkRetry.mockReturnValue({
        execute: mockExecute,
        state: { isLoading: false, error: null, retryCount: 0 },
        reset: jest.fn()
      })

      render(<ChatInterface />)

      const sendButton = screen.getByTestId('send-button')
      await user.click(sendButton)

      expect(mockExecute).not.toHaveBeenCalled()
    })

    it('should clear input after sending message', async () => {
      const useNetworkRetry = require('../../../hooks/useNetworkRetry').default
      useNetworkRetry.mockReturnValue({
        execute: jest.fn().mockResolvedValue({ content: 'Response', session_id: '123' }),
        state: { isLoading: false, error: null, retryCount: 0 },
        reset: jest.fn()
      })

      render(<ChatInterface />)

      const input = screen.getByTestId('chat-input')
      await user.type(input, 'Test message')
      await user.click(screen.getByTestId('send-button'))

      expect(input).toHaveValue('')
    })

    it('should show welcome screen when no messages', () => {
      render(<ChatInterface />)

      expect(screen.getByText(/Quick Start/i)).toBeInTheDocument()
      expect(screen.getByTestId('hotspot-panel')).toBeInTheDocument()
      expect(screen.queryByTestId('message-list')).not.toBeInTheDocument()
    })

    it('should show message list when messages exist', async () => {
      const useNetworkRetry = require('../../../hooks/useNetworkRetry').default
      useNetworkRetry.mockReturnValue({
        execute: jest.fn().mockResolvedValue({ content: 'Response', session_id: '123' }),
        state: { isLoading: false, error: null, retryCount: 0 },
        reset: jest.fn()
      })

      render(<ChatInterface />)

      const input = screen.getByTestId('chat-input')
      await user.type(input, 'Test')
      await user.click(screen.getByTestId('send-button'))

      await waitFor(() => {
        expect(screen.getByTestId('message-list')).toBeInTheDocument()
        expect(screen.queryByText(/Quick Start/i)).not.toBeInTheDocument()
      })
    })
  })

  describe('Hotspot selection', () => {
    it('should fill input with hotspot data', async () => {
      render(<ChatInterface />)

      await user.click(screen.getByTestId('hotspot-btc'))
      
      const input = screen.getByTestId('chat-input')
      expect(input).toHaveValue('BTC (Bitcoin)')
    })
  })

  describe('Error handling', () => {
    it('should handle API errors gracefully', async () => {
      const useNetworkRetry = require('../../../hooks/useNetworkRetry').default
      const error = new Error('Network error')
      useNetworkRetry.mockReturnValue({
        execute: jest.fn().mockRejectedValue(error),
        state: { isLoading: false, error, retryCount: 1 },
        reset: jest.fn()
      })

      render(<ChatInterface />)

      const input = screen.getByTestId('chat-input')
      await user.type(input, 'Test message')
      await user.click(screen.getByTestId('send-button'))

      await waitFor(() => {
        const messages = screen.getAllByTestId('message')
        expect(messages).toHaveLength(2)
        expect(messages[1]).toHaveTextContent('❌ 抱歉，发生错误：Network error')
      })
    })

    it('should show retry button on error', async () => {
      const useNetworkRetry = require('../../../hooks/useNetworkRetry').default
      const error = new Error('Network error')
      useNetworkRetry.mockReturnValue({
        execute: jest.fn().mockRejectedValue(error),
        state: { isLoading: false, error, retryCount: 1 },
        reset: jest.fn()
      })

      render(<ChatInterface />)

      const input = screen.getByTestId('chat-input')
      await user.type(input, 'Test message')
      await user.click(screen.getByTestId('send-button'))

      await waitFor(() => {
        expect(screen.getByTestId('network-error-retry')).toBeInTheDocument()
        expect(screen.getByTestId('retry-button')).toBeInTheDocument()
      })
    })

  })

  describe('Deep research mode', () => {
    it('should handle deep research streaming', async () => {
      const { deepResearchStream } = require('../../../services/api')
      const mockEventSource: any = {
        onmessage: undefined,
        onerror: undefined,
        close: jest.fn(),
      };
      deepResearchStream.mockReturnValue(mockEventSource);

      render(<ChatInterface />);

      // Switch to deep mode
      await user.click(screen.getByTestId('mode-deep'));

      const input = screen.getByTestId('chat-input');
      await user.type(input, 'Bitcoin');
      await user.click(screen.getByTestId('send-button'));

      expect(deepResearchStream).toHaveBeenCalledWith({
        query: 'Bitcoin',
        conversation_id: undefined,
      });

      // Simulate streaming response
      act(() => {
        ;(mockEventSource.onmessage as any)?.({
          data: JSON.stringify({
            type: 'progress',
            stage: 'data_collection',
            content: '正在采集市场数据...',
          }),
        })
      });

      await waitFor(() => {
        expect(screen.getByTestId('loading-animation')).toBeInTheDocument();
      });
    });
  });

  describe('Loading states', () => {
    it('should disable input during loading', async () => {
      const useNetworkRetry = require('../../../hooks/useNetworkRetry').default
      useNetworkRetry.mockReturnValue({
        execute: jest.fn().mockImplementation(() => new Promise(() => {})), // Never resolves
        state: { isLoading: true, error: null, retryCount: 0 },
        reset: jest.fn()
      })

      render(<ChatInterface />)

      const input = screen.getByTestId('chat-input')
      const sendButton = screen.getByTestId('send-button')

      await user.type(input, 'Test message')
      await user.click(sendButton)

      expect(input).toBeDisabled()
      expect(sendButton).toBeDisabled()
    })
  })

  describe('Accessibility', () => {
    it('should have proper ARIA labels', () => {
      render(<ChatInterface />)

      const input = screen.getByTestId('chat-input')
      expect(input).toHaveAttribute('placeholder')

      const sendButton = screen.getByTestId('send-button')
      expect(sendButton).toBeInTheDocument()
    })

    it('should support keyboard navigation', async () => {
      const useNetworkRetry = require('../../../hooks/useNetworkRetry').default
      const mockExecute = jest.fn().mockResolvedValue({ content: 'Response', session_id: '123' })
      useNetworkRetry.mockReturnValue({
        execute: mockExecute,
        state: { isLoading: false, error: null, retryCount: 0 },
        reset: jest.fn()
      })

      render(<ChatInterface />)

      const input = screen.getByTestId('chat-input') as HTMLInputElement
      input.focus()
      await user.clear(input)
      await user.keyboard('Test message{Enter}')

      expect(mockExecute).toHaveBeenCalledWith({
        query: 'Test message',
        conversation_id: undefined
      })

      await waitFor(() => {
        const messages = screen.getAllByTestId('message')
        expect(messages).toHaveLength(2)
      })
    })
  })

  describe('Component lifecycle', () => {
    it('should cleanup EventSource on unmount', () => {
      const { deepResearchStream } = require('../../../services/api')
      const mockEventSource = {
        onmessage: jest.fn(),
        onerror: jest.fn(),
        close: jest.fn()
      }
      deepResearchStream.mockReturnValue(mockEventSource)

      const { unmount } = render(<ChatInterface />)

      // Trigger deep research to create EventSource
      fireEvent.click(screen.getByTestId('mode-deep'))
      const input = screen.getByTestId('chat-input') as HTMLInputElement
      fireEvent.change(input, { target: { value: 'Test' } })
      fireEvent.click(screen.getByTestId('send-button'))

      unmount()

      expect(mockEventSource.close).toHaveBeenCalled()
    })
  })
})
