import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import AgentsPage from '../../pages/AgentsPage'

const mockPauseTask = jest.fn()
const mockResumeTask = jest.fn()
const mockDeleteTask = jest.fn()
const mockCreateTask = jest.fn()

jest.mock('../../contexts/AuthContext', () => ({
  useAuth: () => ({ isAuthenticated: true }),
}))

jest.mock('../../hooks/useAgentTasks', () => ({
  useAgentTasks: () => ({
    tasks: [
      {
        id: 'task-active',
        name: 'BTC Alert',
        description: 'Alert when BTC drops',
        task_type: 'price_alert',
        status: 'active',
        run_count: 1,
        success_count: 1,
        failure_count: 0,
        created_at: '',
        updated_at: '',
      },
      {
        id: 'task-paused',
        name: 'ETH Monitor',
        description: 'Risk monitor',
        task_type: 'risk_monitor',
        status: 'paused',
        run_count: 2,
        success_count: 2,
        failure_count: 0,
        created_at: '',
        updated_at: '',
      },
    ],
    loading: false,
    pauseTask: mockPauseTask,
    resumeTask: mockResumeTask,
    deleteTask: mockDeleteTask,
    createTask: mockCreateTask,
  }),
}))

jest.mock('../../components/Agents/QuickPriceAlertCard', () => ({
  __esModule: true,
  QuickPriceAlertCard: () => <div data-testid="quick-price-alert" />,
}))

describe('AgentsPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    Object.defineProperty(window, 'confirm', {
      value: jest.fn(() => true),
      writable: true,
    })
  })

  it('pauses active tasks', async () => {
    render(<AgentsPage />)

    fireEvent.click(screen.getByRole('button', { name: /暂停/i }))

    await waitFor(() => {
      expect(mockPauseTask).toHaveBeenCalledWith('task-active')
    })
  })

  it('resumes paused tasks', async () => {
    render(<AgentsPage />)

    fireEvent.click(screen.getByRole('button', { name: /恢复/i }))

    await waitFor(() => {
      expect(mockResumeTask).toHaveBeenCalledWith('task-paused')
    })
  })

  it('deletes tasks after confirmation', async () => {
    render(<AgentsPage />)

    const deleteButtons = screen.getAllByTitle('删除任务')
    fireEvent.click(deleteButtons[0])

    await waitFor(() => {
      expect(mockDeleteTask).toHaveBeenCalledWith('task-active')
    })
  })
})
