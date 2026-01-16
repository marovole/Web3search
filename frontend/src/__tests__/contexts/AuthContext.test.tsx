import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import { AuthProvider, useAuth } from '../../contexts/AuthContext'

const mockUseConvexAuth = jest.fn()

jest.mock('convex/react', () => ({
  useConvexAuth: () => mockUseConvexAuth(),
  useMutation: jest.fn(),
  useQuery: jest.fn(),
}))

const TestConsumer = () => {
  const { isAuthenticated, loading, signOut } = useAuth()

  return (
    <div>
      <span data-testid="auth-status">{isAuthenticated ? 'auth' : 'guest'}</span>
      <span data-testid="loading-status">{loading ? 'loading' : 'ready'}</span>
      <button type="button" onClick={() => signOut()}>
        sign out
      </button>
    </div>
  )
}

describe('AuthProvider', () => {
  beforeEach(() => {
    mockUseConvexAuth.mockReset()
    Object.defineProperty(globalThis, 'crypto', {
      value: { randomUUID: () => 'session-123' },
      configurable: true,
    })
  })

  it('exposes loading state while convex auth is loading', () => {
    mockUseConvexAuth.mockReturnValue({ isLoading: true, isAuthenticated: false })

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    )

    expect(screen.getByTestId('loading-status')).toHaveTextContent('loading')
    expect(screen.getByTestId('auth-status')).toHaveTextContent('guest')
  })

  it('sets authenticated when convex auth is authenticated', () => {
    mockUseConvexAuth.mockReturnValue({ isLoading: false, isAuthenticated: true })

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    )

    expect(screen.getByTestId('loading-status')).toHaveTextContent('ready')
    expect(screen.getByTestId('auth-status')).toHaveTextContent('auth')
  })

  it('clears client session id on sign out', () => {
    mockUseConvexAuth.mockReturnValue({ isLoading: false, isAuthenticated: true })

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    )

    expect(localStorage.getItem('client_session_id')).toBe('session-123')

    fireEvent.click(screen.getByRole('button', { name: /sign out/i }))

    expect(localStorage.getItem('client_session_id')).toBeNull()
  })
})
