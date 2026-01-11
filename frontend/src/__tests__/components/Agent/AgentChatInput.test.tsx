import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import '@testing-library/jest-dom'
import AgentChatInput from '../../../components/Agent/AgentChatInput'

jest.mock('../../../types/agent-chat', () => ({
  EXAMPLE_PROMPTS: [
    '当BTC跌破50000时提醒我',
    '每天早上9点发送市场简报',
    '监控ETH的风险评分变化',
  ],
}))

describe('AgentChatInput', () => {
  const mockOnSend = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders input field with placeholder', () => {
    render(<AgentChatInput onSend={mockOnSend} />)

    expect(screen.getByRole('textbox')).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/输入您的需求/i)).toBeInTheDocument()
  })

  it('renders custom placeholder', () => {
    render(<AgentChatInput onSend={mockOnSend} placeholder="Custom placeholder" />)

    expect(screen.getByPlaceholderText('Custom placeholder')).toBeInTheDocument()
  })

  it('renders submit button', () => {
    render(<AgentChatInput onSend={mockOnSend} />)

    const buttons = screen.getAllByRole('button')
    expect(buttons.length).toBeGreaterThan(0)
  })

  it('calls onSend when form is submitted with message', async () => {
    render(<AgentChatInput onSend={mockOnSend} />)

    const input = screen.getByRole('textbox')
    await userEvent.type(input, 'Test message')
    
    const form = input.closest('form')!
    fireEvent.submit(form)

    await waitFor(() => {
      expect(mockOnSend).toHaveBeenCalledWith('Test message')
    })
  })

  it('does not call onSend when message is empty', async () => {
    render(<AgentChatInput onSend={mockOnSend} />)

    const input = screen.getByRole('textbox')
    const form = input.closest('form')!
    fireEvent.submit(form)

    expect(mockOnSend).not.toHaveBeenCalled()
  })

  it('does not call onSend when disabled', async () => {
    render(<AgentChatInput onSend={mockOnSend} disabled />)

    const input = screen.getByRole('textbox')
    await userEvent.type(input, 'Test message')
    
    const form = input.closest('form')!
    fireEvent.submit(form)

    expect(mockOnSend).not.toHaveBeenCalled()
  })

  it('disables input when disabled prop is true', () => {
    render(<AgentChatInput onSend={mockOnSend} disabled />)

    expect(screen.getByRole('textbox')).toBeDisabled()
  })

  it('clears input after successful submission', async () => {
    render(<AgentChatInput onSend={mockOnSend} />)

    const input = screen.getByRole('textbox')
    await userEvent.type(input, 'Test message')
    
    const form = input.closest('form')!
    fireEvent.submit(form)

    await waitFor(() => {
      expect(input).toHaveValue('')
    })
  })

  it('submits on Enter key press', async () => {
    render(<AgentChatInput onSend={mockOnSend} />)

    const input = screen.getByRole('textbox')
    await userEvent.type(input, 'Test message')
    await userEvent.keyboard('{Enter}')

    await waitFor(() => {
      expect(mockOnSend).toHaveBeenCalledWith('Test message')
    })
  })

  it('does not submit on Shift+Enter', async () => {
    render(<AgentChatInput onSend={mockOnSend} />)

    const input = screen.getByRole('textbox')
    await userEvent.type(input, 'Test message')
    await userEvent.keyboard('{Shift>}{Enter}{/Shift}')

    expect(mockOnSend).not.toHaveBeenCalled()
  })

  it('trims whitespace from message', async () => {
    render(<AgentChatInput onSend={mockOnSend} />)

    const input = screen.getByRole('textbox')
    await userEvent.type(input, '  Test message  ')
    
    const form = input.closest('form')!
    fireEvent.submit(form)

    await waitFor(() => {
      expect(mockOnSend).toHaveBeenCalledWith('Test message')
    })
  })
})
