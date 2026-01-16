import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import UpgradePage from '../../pages/UpgradePage'

const mockNavigate = jest.fn()
const mockUseAuth = jest.fn()
const mockCreateCheckoutSession = jest.fn()
const mockCreatePortalSession = jest.fn()
const mockToast = jest.fn()

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}))

jest.mock('../../contexts/AuthContext', () => ({
  useAuth: () => mockUseAuth(),
}))

jest.mock('../../services/api', () => ({
  createCheckoutSession: (...args: unknown[]) => mockCreateCheckoutSession(...args),
  createPortalSession: () => mockCreatePortalSession(),
}))

jest.mock('../../components/ui/toast', () => ({
  useToast: () => ({ toast: mockToast }),
}))

const renderPage = () => render(<UpgradePage />)

describe('UpgradePage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    Object.defineProperty(window, 'location', {
      value: { href: '' },
      writable: true,
    })
  })

  it('redirects to login when user is not authenticated', async () => {
    mockUseAuth.mockReturnValue({ user: null, profile: null, loading: false })

    renderPage()

    const upgradeButtons = screen.getAllByRole('button', { name: /upgrade/i })
    fireEvent.click(upgradeButtons[0])

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/auth/login?redirect=/upgrade')
    })
  })

  it('starts checkout session when authenticated', async () => {
    mockUseAuth.mockReturnValue({ user: { id: 'user-123' }, profile: { plan: 'free' }, loading: false })
    mockCreateCheckoutSession.mockResolvedValueOnce({ checkout_url: 'https://stripe.test/checkout' })

    renderPage()

    const upgradeButtons = screen.getAllByRole('button', { name: /upgrade/i })
    fireEvent.click(upgradeButtons[0])

    await waitFor(() => {
      expect(mockCreateCheckoutSession).toHaveBeenCalled()
      expect(window.location.href).toBe('https://stripe.test/checkout')
    })
  })

  it('opens billing portal when managing subscription', async () => {
    mockUseAuth.mockReturnValue({ user: { id: 'user-123' }, profile: { plan: 'pro' }, loading: false })
    mockCreatePortalSession.mockResolvedValueOnce({ portal_url: 'https://stripe.test/portal' })

    renderPage()

    const manageButton = screen.getByRole('button', { name: /manage subscription/i })
    fireEvent.click(manageButton)

    await waitFor(() => {
      expect(mockCreatePortalSession).toHaveBeenCalled()
      expect(window.location.href).toBe('https://stripe.test/portal')
    })
  })
})
