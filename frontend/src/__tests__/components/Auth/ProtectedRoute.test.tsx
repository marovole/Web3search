import React from 'react'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import { BrowserRouter, Routes, Route, MemoryRouter } from 'react-router-dom'
import { ProtectedRoute } from '../../../components/Auth/ProtectedRoute'

const mockProfile = {
  id: 'user-123',
  plan: 'free' as const,
}

const mockUseAuth = jest.fn()

jest.mock('../../../contexts/AuthContext', () => ({
  useAuth: () => mockUseAuth(),
}))

const TestChild = () => <div data-testid="protected-content">Protected Content</div>

describe('ProtectedRoute', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('shows loading spinner when loading', () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: false,
      loading: true,
      profile: null,
    })

    render(
      <BrowserRouter>
        <ProtectedRoute>
          <TestChild />
        </ProtectedRoute>
      </BrowserRouter>
    )

    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument()
  })

  it('renders children when authenticated', () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      loading: false,
      profile: mockProfile,
    })

    render(
      <BrowserRouter>
        <ProtectedRoute>
          <TestChild />
        </ProtectedRoute>
      </BrowserRouter>
    )

    expect(screen.getByTestId('protected-content')).toBeInTheDocument()
  })

  it('redirects to login when not authenticated', () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: false,
      loading: false,
      profile: null,
    })

    render(
      <MemoryRouter initialEntries={['/protected']}>
        <Routes>
          <Route
            path="/protected"
            element={
              <ProtectedRoute>
                <TestChild />
              </ProtectedRoute>
            }
          />
          <Route path="/auth/login" element={<div data-testid="login-page">Login Page</div>} />
        </Routes>
      </MemoryRouter>
    )

    expect(screen.getByTestId('login-page')).toBeInTheDocument()
    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument()
  })

  it('allows access when user has required plan', () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      loading: false,
      profile: { ...mockProfile, plan: 'pro' },
    })

    render(
      <BrowserRouter>
        <ProtectedRoute requiredPlan="pro">
          <TestChild />
        </ProtectedRoute>
      </BrowserRouter>
    )

    expect(screen.getByTestId('protected-content')).toBeInTheDocument()
  })

  it('redirects to upgrade when user plan is insufficient', () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      loading: false,
      profile: { ...mockProfile, plan: 'free' },
    })

    render(
      <MemoryRouter initialEntries={['/pro-feature']}>
        <Routes>
          <Route
            path="/pro-feature"
            element={
              <ProtectedRoute requiredPlan="pro">
                <TestChild />
              </ProtectedRoute>
            }
          />
          <Route path="/upgrade" element={<div data-testid="upgrade-page">Upgrade Page</div>} />
        </Routes>
      </MemoryRouter>
    )

    expect(screen.getByTestId('upgrade-page')).toBeInTheDocument()
    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument()
  })

  it('allows higher plan users to access lower tier content', () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      loading: false,
      profile: { ...mockProfile, plan: 'team' },
    })

    render(
      <BrowserRouter>
        <ProtectedRoute requiredPlan="pro">
          <TestChild />
        </ProtectedRoute>
      </BrowserRouter>
    )

    expect(screen.getByTestId('protected-content')).toBeInTheDocument()
  })

  it('handles null profile gracefully', () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      loading: false,
      profile: null,
    })

    render(
      <MemoryRouter initialEntries={['/pro-feature']}>
        <Routes>
          <Route
            path="/pro-feature"
            element={
              <ProtectedRoute requiredPlan="pro">
                <TestChild />
              </ProtectedRoute>
            }
          />
          <Route path="/upgrade" element={<div data-testid="upgrade-page">Upgrade Page</div>} />
        </Routes>
      </MemoryRouter>
    )

    expect(screen.getByTestId('upgrade-page')).toBeInTheDocument()
  })
})
