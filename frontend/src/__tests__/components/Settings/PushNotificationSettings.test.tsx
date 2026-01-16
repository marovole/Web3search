import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import { PushNotificationSettings } from '../../../components/Settings/PushNotificationSettings'

const mockGetStatus = jest.fn()
const mockSubscribe = jest.fn()
const mockUnsubscribe = jest.fn()
const mockTest = jest.fn()

jest.mock('../../../contexts/AuthContext', () => ({
  useAuth: () => ({ session: { access_token: 'token' } }),
}))

jest.mock('../../../lib/push', () => ({
  isPushSupported: () => true,
  getPushSubscriptionStatus: () => mockGetStatus(),
  subscribeToPush: (token: string) => mockSubscribe(token),
  unsubscribeFromPush: (token: string) => mockUnsubscribe(token),
  testPushNotification: (token: string) => mockTest(token),
}))

describe('PushNotificationSettings', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('subscribes to push notifications', async () => {
    mockGetStatus.mockResolvedValueOnce({ supported: true, permission: 'default', subscribed: false })
    mockSubscribe.mockResolvedValueOnce({ success: true })

    render(<PushNotificationSettings />)

    const enableButton = await screen.findByRole('button', { name: /开启推送/i })
    fireEvent.click(enableButton)

    await waitFor(() => {
      expect(mockSubscribe).toHaveBeenCalledWith('token')
    })
  })

  it('unsubscribes from push notifications', async () => {
    mockGetStatus.mockResolvedValueOnce({ supported: true, permission: 'granted', subscribed: true })
    mockUnsubscribe.mockResolvedValueOnce({ success: true })

    render(<PushNotificationSettings />)

    const disableButton = await screen.findByRole('button', { name: /关闭/i })
    fireEvent.click(disableButton)

    await waitFor(() => {
      expect(mockUnsubscribe).toHaveBeenCalledWith('token')
    })
  })

  it('sends test notification when subscribed', async () => {
    mockGetStatus.mockResolvedValueOnce({ supported: true, permission: 'granted', subscribed: true })
    mockTest.mockResolvedValueOnce({ success: true, message: 'ok' })

    render(<PushNotificationSettings />)

    const testButton = await screen.findByRole('button', { name: /测试/i })
    fireEvent.click(testButton)

    await waitFor(() => {
      expect(mockTest).toHaveBeenCalledWith('token')
    })
  })
})
