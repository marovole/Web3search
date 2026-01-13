import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import '@testing-library/jest-dom'
import { BrowserRouter } from 'react-router-dom'
import { LoginForm } from '../../../components/Auth/LoginForm'

const routerFutureConfig = {
  v7_startTransition: true,
  v7_relativeSplatPath: true,
} as const

const mockNavigate = jest.fn()
const mockSignIn = jest.fn()

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
  useLocation: () => ({ state: { from: '/dashboard' } }),
}))

jest.mock('../../../contexts/AuthContext', () => ({
  useAuth: () => ({
    signIn: mockSignIn,
  }),
}))

jest.mock('../../../components/ui/toast', () => ({
  toast: jest.fn(),
}))

const renderLoginForm = () => {
  return render(
    <BrowserRouter future={routerFutureConfig}>
      <LoginForm />
    </BrowserRouter>
  )
}

describe('LoginForm', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders login form with email and password fields', () => {
    renderLoginForm()

    expect(screen.getByPlaceholderText(/邮箱/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/密码/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /登录/i })).toBeInTheDocument()
  })

  it('renders forgot password and register links', () => {
    renderLoginForm()

    expect(screen.getByText(/忘记密码/i)).toBeInTheDocument()
    expect(screen.getByText(/立即注册/i)).toBeInTheDocument()
  })

  it('shows validation errors for empty fields', async () => {
    renderLoginForm()

    const submitButton = screen.getByRole('button', { name: /登录/i })
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(mockSignIn).not.toHaveBeenCalled()
    })
  })

  it('submits form with valid credentials', async () => {
    mockSignIn.mockResolvedValueOnce({ error: null })

    renderLoginForm()

    const emailInput = screen.getByPlaceholderText(/邮箱/i)
    const passwordInput = screen.getByPlaceholderText(/密码/i)
    const submitButton = screen.getByRole('button', { name: /登录/i })

    await userEvent.type(emailInput, 'test@example.com')
    await userEvent.type(passwordInput, 'password123')
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(mockSignIn).toHaveBeenCalledWith('test@example.com', 'password123')
    })
  })

  it('shows loading state during submission', async () => {
    mockSignIn.mockImplementation(() => new Promise(() => {}))

    renderLoginForm()

    const emailInput = screen.getByPlaceholderText(/邮箱/i)
    const passwordInput = screen.getByPlaceholderText(/密码/i)
    const submitButton = screen.getByRole('button', { name: /登录/i })

    await userEvent.type(emailInput, 'test@example.com')
    await userEvent.type(passwordInput, 'password123')
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/登录中/i)).toBeInTheDocument()
    })
  })

  it('navigates to previous location after successful login', async () => {
    mockSignIn.mockResolvedValueOnce({ error: null })

    renderLoginForm()

    const emailInput = screen.getByPlaceholderText(/邮箱/i)
    const passwordInput = screen.getByPlaceholderText(/密码/i)
    const submitButton = screen.getByRole('button', { name: /登录/i })

    await userEvent.type(emailInput, 'test@example.com')
    await userEvent.type(passwordInput, 'password123')
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard', { replace: true })
    })
  })

  it('handles login error', async () => {
    mockSignIn.mockResolvedValueOnce({ error: new Error('Invalid credentials') })

    renderLoginForm()

    const emailInput = screen.getByPlaceholderText(/邮箱/i)
    const passwordInput = screen.getByPlaceholderText(/密码/i)
    const submitButton = screen.getByRole('button', { name: /登录/i })

    await userEvent.type(emailInput, 'test@example.com')
    await userEvent.type(passwordInput, 'wrongpassword')
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(mockNavigate).not.toHaveBeenCalled()
    })
  })

  it('has accessible form structure', () => {
    renderLoginForm()

    expect(screen.getByPlaceholderText(/邮箱/i)).toHaveAttribute('type', 'email')
    expect(screen.getByPlaceholderText(/密码/i)).toHaveAttribute('type', 'password')
    expect(screen.getByRole('button', { name: /登录/i })).toHaveAttribute('type', 'submit')
  })
})
