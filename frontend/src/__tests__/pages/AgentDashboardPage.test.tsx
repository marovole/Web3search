import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import AgentDashboardPage from '../../pages/AgentDashboardPage'

const mockRefresh = jest.fn()
const mockLoadLogs = jest.fn()

jest.mock('../../contexts/AuthContext', () => ({
  useAuth: () => ({ isAuthenticated: true, loading: false }),
}))

jest.mock('../../hooks/useAgentActivity', () => ({
  useAgentActivity: () => ({
    dashboard: {
      stats: {
        active_tasks: 2,
        runs_today: 3,
        success_rate_7d: 95,
        notifications_sent_today: 1,
      },
      recentRuns: [],
      activeTasks: [],
    },
    logs: [],
    loading: false,
    logsLoading: false,
    refresh: mockRefresh,
    loadLogs: mockLoadLogs,
  })
}))

describe('AgentDashboardPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('loads logs when switching to logs tab', async () => {
    render(<AgentDashboardPage />)

    fireEvent.click(screen.getByRole('button', { name: /执行日志/i }))

    await waitFor(() => {
      expect(mockLoadLogs).toHaveBeenCalled()
    })
  })
})
