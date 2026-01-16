import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import AgentChatPage from '../../pages/AgentChatPage'

const mockSendMessage = jest.fn()
const mockClearMessages = jest.fn()

jest.mock('../../contexts/AuthContext', () => ({
  useAuth: () => ({ isAuthenticated: true, loading: false }),
}))

jest.mock('../../hooks/useAgentChat', () => ({
  useAgentChat: () => ({
    messages: [],
    isLoading: false,
    isConnected: true,
    sendMessage: mockSendMessage,
    confirmIntent: jest.fn(),
    cancelIntent: jest.fn(),
    clearMessages: mockClearMessages,
    pendingConfirmation: null,
  })
}))

jest.mock('../../components/Agent', () => ({
  AgentChatMessage: () => <div data-testid="agent-message" />,
  AgentChatInput: ({ onSend }: { onSend: (message: string) => void }) => (
    <button type="button" onClick={() => onSend('hello')}>
      send
    </button>
  ),
}))

describe('AgentChatPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('sends quick action messages', async () => {
    render(<AgentChatPage />)

    fireEvent.click(screen.getByRole('button', { name: /价格提醒/i }))

    await waitFor(() => {
      expect(mockSendMessage).toHaveBeenCalledWith('当BTC跌破50000时提醒我')
    })
  })

  it('sends message from input', async () => {
    render(<AgentChatPage />)

    fireEvent.click(screen.getByRole('button', { name: /send/i }))

    await waitFor(() => {
      expect(mockSendMessage).toHaveBeenCalledWith('hello')
    })
  })
})
