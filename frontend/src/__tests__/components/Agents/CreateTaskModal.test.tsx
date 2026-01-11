import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import '@testing-library/jest-dom'
import CreateTaskModal from '../../../components/Agents/CreateTaskModal'

const mockCreateTask = jest.fn()

jest.mock('../../../hooks/useAgentTasks', () => ({
  useAgentTasks: () => ({
    createTask: mockCreateTask,
  }),
}))

describe('CreateTaskModal', () => {
  const mockOnClose = jest.fn()
  const mockOnCreated = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns null when not open', () => {
    const { container } = render(
      <CreateTaskModal isOpen={false} onClose={mockOnClose} />
    )

    expect(container.firstChild).toBeNull()
  })

  it('renders when open', () => {
    render(<CreateTaskModal isOpen={true} onClose={mockOnClose} />)

    expect(screen.getByText('新建智能体任务')).toBeInTheDocument()
  })

  it('displays task type options', () => {
    render(<CreateTaskModal isOpen={true} onClose={mockOnClose} />)

    expect(screen.getByText('价格预警')).toBeInTheDocument()
    expect(screen.getByText('风险监控')).toBeInTheDocument()
    expect(screen.getByText('新闻速报')).toBeInTheDocument()
  })

  it('allows selecting different task types', async () => {
    render(<CreateTaskModal isOpen={true} onClose={mockOnClose} />)

    const riskMonitorOption = screen.getByText('风险监控').closest('button')
    if (riskMonitorOption) {
      fireEvent.click(riskMonitorOption)
    }

    await waitFor(() => {
      expect(screen.getByText('持续扫描代币合约风险和异常交易')).toBeInTheDocument()
    })
  })

  it('shows error when submitting without task name', async () => {
    render(<CreateTaskModal isOpen={true} onClose={mockOnClose} />)

    const form = screen.getByRole('dialog').querySelector('form')
    if (form) {
      fireEvent.submit(form)
    }

    await waitFor(() => {
      expect(screen.getByText('请输入任务名称')).toBeInTheDocument()
    })
  })

  it('calls onClose when backdrop is clicked', () => {
    render(<CreateTaskModal isOpen={true} onClose={mockOnClose} />)

    const closeButton = screen.getByRole('dialog').querySelector('button[class*="text-gray-400"]')
    if (closeButton) {
      fireEvent.click(closeButton)
    }

    expect(mockOnClose).toHaveBeenCalled()
  })

  it('has name input field', () => {
    render(<CreateTaskModal isOpen={true} onClose={mockOnClose} />)

    expect(screen.getByPlaceholderText(/BTC 价格监控/i)).toBeInTheDocument()
  })

  it('resets error when modal reopens', async () => {
    const { rerender } = render(
      <CreateTaskModal isOpen={true} onClose={mockOnClose} />
    )

    const form = screen.getByRole('dialog').querySelector('form')
    if (form) {
      fireEvent.submit(form)
    }

    await waitFor(() => {
      expect(screen.getByText('请输入任务名称')).toBeInTheDocument()
    })

    rerender(<CreateTaskModal isOpen={false} onClose={mockOnClose} />)
    rerender(<CreateTaskModal isOpen={true} onClose={mockOnClose} />)

    expect(screen.queryByText('请输入任务名称')).not.toBeInTheDocument()
  })

  it('shows price alert specific fields when price_alert is selected', () => {
    render(<CreateTaskModal isOpen={true} onClose={mockOnClose} />)

    expect(screen.getByText('监控代币')).toBeInTheDocument()
    expect(screen.getByText('触发条件')).toBeInTheDocument()
  })

  it('can type in name input field', async () => {
    render(<CreateTaskModal isOpen={true} onClose={mockOnClose} onCreated={mockOnCreated} />)

    const nameInput = screen.getByPlaceholderText(/BTC 价格监控/i)
    await userEvent.type(nameInput, 'My Price Alert')

    expect(nameInput).toHaveValue('My Price Alert')
  })
})
