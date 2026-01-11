import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import AgentChatMessage from '../../../components/Agent/AgentChatMessage'
import type { AgentChatMessage as AgentChatMessageType } from '../../../types/agent-chat'

jest.mock('../../../types/agent-chat', () => ({
  INTENT_DESCRIPTIONS: {
    create_price_alert: '创建价格提醒',
    delete_task: '删除任务',
    check_status: '检查状态',
  },
}))

jest.mock('react-markdown', () => {
  return function MockReactMarkdown({ children }: { children: string }) {
    return <div data-testid="markdown-content">{children}</div>
  }
})

jest.mock('remark-gfm', () => () => {})

const createMessage = (overrides: Partial<AgentChatMessageType> = {}): AgentChatMessageType => ({
  id: 'msg-1',
  role: 'assistant',
  content: 'Test message content',
  timestamp: new Date('2025-01-11T10:00:00'),
  ...overrides,
})

describe('AgentChatMessage', () => {
  it('renders user message with correct styling', () => {
    const message = createMessage({ role: 'user', content: 'User question' })
    render(<AgentChatMessage message={message} />)

    expect(screen.getByText('User question')).toBeInTheDocument()
  })

  it('renders assistant message with markdown', () => {
    const message = createMessage({ role: 'assistant', content: 'Assistant response' })
    render(<AgentChatMessage message={message} />)

    expect(screen.getByTestId('markdown-content')).toBeInTheDocument()
    expect(screen.getByText('Assistant response')).toBeInTheDocument()
  })

  it('renders system message with special styling', () => {
    const message = createMessage({ role: 'system', content: 'System notification' })
    render(<AgentChatMessage message={message} />)

    expect(screen.getByText('System notification')).toBeInTheDocument()
  })

  it('displays timestamp', () => {
    const message = createMessage()
    render(<AgentChatMessage message={message} />)

    expect(screen.getByText(/10:00/)).toBeInTheDocument()
  })

  it('shows intent badge when intent is present', () => {
    const message = createMessage({
      intent: {
        type: 'create_price_alert',
        confidence: 0.95,
        params: {},
      },
    })
    render(<AgentChatMessage message={message} />)

    expect(screen.getByText('创建价格提醒')).toBeInTheDocument()
    expect(screen.getByText(/置信度: 95%/)).toBeInTheDocument()
  })

  it('shows confirmation buttons when required', () => {
    const mockOnConfirm = jest.fn()
    const mockOnCancel = jest.fn()
    const message = createMessage({ requiresConfirmation: true })
    
    render(
      <AgentChatMessage 
        message={message} 
        showConfirmButtons 
        onConfirm={mockOnConfirm} 
        onCancel={mockOnCancel} 
      />
    )

    expect(screen.getByText('确认创建')).toBeInTheDocument()
    expect(screen.getByText('取消')).toBeInTheDocument()
  })

  it('calls onConfirm when confirm button is clicked', () => {
    const mockOnConfirm = jest.fn()
    const mockOnCancel = jest.fn()
    const message = createMessage({ requiresConfirmation: true })
    
    render(
      <AgentChatMessage 
        message={message} 
        showConfirmButtons 
        onConfirm={mockOnConfirm} 
        onCancel={mockOnCancel} 
      />
    )

    fireEvent.click(screen.getByText('确认创建'))
    expect(mockOnConfirm).toHaveBeenCalled()
  })

  it('calls onCancel when cancel button is clicked', () => {
    const mockOnConfirm = jest.fn()
    const mockOnCancel = jest.fn()
    const message = createMessage({ requiresConfirmation: true })
    
    render(
      <AgentChatMessage 
        message={message} 
        showConfirmButtons 
        onConfirm={mockOnConfirm} 
        onCancel={mockOnCancel} 
      />
    )

    fireEvent.click(screen.getByText('取消'))
    expect(mockOnCancel).toHaveBeenCalled()
  })

  it('shows task result success indicator', () => {
    const message = createMessage({
      taskResult: { success: true, message: 'Task created' },
    })
    render(<AgentChatMessage message={message} />)

    expect(screen.getByText('任务已创建')).toBeInTheDocument()
  })

  it('does not show confirmation buttons when showConfirmButtons is false', () => {
    const message = createMessage({ requiresConfirmation: true })
    
    render(<AgentChatMessage message={message} showConfirmButtons={false} />)

    expect(screen.queryByText('确认创建')).not.toBeInTheDocument()
    expect(screen.queryByText('取消')).not.toBeInTheDocument()
  })
})
