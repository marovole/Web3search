import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import NotificationsPage from '../../pages/NotificationsPage'

const mockFetchNotifications = jest.fn()
const mockMarkAsRead = jest.fn()
const mockMarkAllAsRead = jest.fn()
const mockDismiss = jest.fn()
const mockRefresh = jest.fn()

jest.mock('../../hooks/useNotifications', () => ({
  useNotifications: () => ({
    notifications: [
      {
        id: 'notif-1',
        type: 'price_alert',
        title: 'BTC Alert',
        body: 'BTC dropped below $50,000',
        priority: 'normal',
        created_at: new Date().toISOString(),
        read_at: null,
      },
    ],
    unreadCount: 1,
    total: 1,
    loading: false,
    error: null,
    fetchNotifications: mockFetchNotifications,
    markAsRead: mockMarkAsRead,
    markAllAsRead: mockMarkAllAsRead,
    dismissNotification: mockDismiss,
    refresh: mockRefresh,
  })
}))

describe('NotificationsPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('fetches notifications on render', () => {
    render(<NotificationsPage />)

    expect(mockFetchNotifications).toHaveBeenCalled()
  })

  it('marks a notification as read', async () => {
    render(<NotificationsPage />)

    fireEvent.click(screen.getByTitle('标记已读'))

    await waitFor(() => {
      expect(mockMarkAsRead).toHaveBeenCalledWith('notif-1')
    })
  })

  it('dismisses a notification', async () => {
    render(<NotificationsPage />)

    fireEvent.click(screen.getByTitle('删除'))

    await waitFor(() => {
      expect(mockDismiss).toHaveBeenCalledWith('notif-1')
    })
  })

  it('marks all notifications as read', async () => {
    render(<NotificationsPage />)

    fireEvent.click(screen.getByRole('button', { name: /全部已读/i }))

    await waitFor(() => {
      expect(mockMarkAllAsRead).toHaveBeenCalled()
    })
  })
})
