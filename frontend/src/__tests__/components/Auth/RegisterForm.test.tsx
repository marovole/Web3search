import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import '@testing-library/jest-dom'
import { BrowserRouter } from 'react-router-dom'
import { RegisterForm } from '../../../components/Auth/RegisterForm'

const mockNavigate = jest.fn()
const mockSignUp = jest.fn()

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}))

jest.mock('../../../contexts/AuthContext', () => ({
  useAuth: () => ({
    signUp: mockSignUp,
  }),
}))

jest.mock('../../../components/ui/toast', () => ({
  toast: jest.fn(),
}))

const renderRegisterForm = () => {
  return render(
    <BrowserRouter>
      <RegisterForm />
    </BrowserRouter>
  )
}

describe('RegisterForm', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders register form with all required fields', () => {
    renderRegisterForm()

    expect(screen.getByPlaceholderText(/邮箱/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/用户名/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/请输入密码/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/请再次输入密码/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /注册/i })).toBeInTheDocument()
  })

  it('renders login link', () => {
    renderRegisterForm()

    expect(screen.getByText(/已有账号/i)).toBeInTheDocument()
    expect(screen.getByText(/立即登录/i)).toBeInTheDocument()
  })

  it('shows validation errors for empty fields', async () => {
    renderRegisterForm()

    const submitButton = screen.getByRole('button', { name: /注册/i })
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(mockSignUp).not.toHaveBeenCalled()
    })
  })

  it('submits form with valid data', async () => {
    mockSignUp.mockResolvedValueOnce({ error: null })

    renderRegisterForm()

    const emailInput = screen.getByPlaceholderText(/邮箱/i)
    const usernameInput = screen.getByPlaceholderText(/用户名/i)
    const passwordInput = screen.getByPlaceholderText(/请输入密码/i)
    const confirmPasswordInput = screen.getByPlaceholderText(/请再次输入密码/i)
    const submitButton = screen.getByRole('button', { name: /注册/i })

    await userEvent.type(emailInput, 'test@example.com')
    await userEvent.type(usernameInput, 'testuser')
    await userEvent.type(passwordInput, 'Password123')
    await userEvent.type(confirmPasswordInput, 'Password123')
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(mockSignUp).toHaveBeenCalledWith('test@example.com', 'Password123')
    })
  })

  it('shows loading state during submission', async () => {
    mockSignUp.mockImplementation(() => new Promise(() => {}))

    renderRegisterForm()

    const emailInput = screen.getByPlaceholderText(/邮箱/i)
    const usernameInput = screen.getByPlaceholderText(/用户名/i)
    const passwordInput = screen.getByPlaceholderText(/请输入密码/i)
    const confirmPasswordInput = screen.getByPlaceholderText(/请再次输入密码/i)
    const submitButton = screen.getByRole('button', { name: /注册/i })

    await userEvent.type(emailInput, 'test@example.com')
    await userEvent.type(usernameInput, 'testuser')
    await userEvent.type(passwordInput, 'Password123')
    await userEvent.type(confirmPasswordInput, 'Password123')
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/注册中/i)).toBeInTheDocument()
    })
  })

  it('navigates to login page after successful registration', async () => {
    mockSignUp.mockResolvedValueOnce({ error: null })

    renderRegisterForm()

    const emailInput = screen.getByPlaceholderText(/邮箱/i)
    const usernameInput = screen.getByPlaceholderText(/用户名/i)
    const passwordInput = screen.getByPlaceholderText(/请输入密码/i)
    const confirmPasswordInput = screen.getByPlaceholderText(/请再次输入密码/i)
    const submitButton = screen.getByRole('button', { name: /注册/i })

    await userEvent.type(emailInput, 'test@example.com')
    await userEvent.type(usernameInput, 'testuser')
    await userEvent.type(passwordInput, 'Password123')
    await userEvent.type(confirmPasswordInput, 'Password123')
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/auth/login', { replace: true })
    })
  })

  it('handles registration error', async () => {
    mockSignUp.mockResolvedValueOnce({ error: new Error('Email already registered') })

    renderRegisterForm()

    const emailInput = screen.getByPlaceholderText(/邮箱/i)
    const usernameInput = screen.getByPlaceholderText(/用户名/i)
    const passwordInput = screen.getByPlaceholderText(/请输入密码/i)
    const confirmPasswordInput = screen.getByPlaceholderText(/请再次输入密码/i)
    const submitButton = screen.getByRole('button', { name: /注册/i })

    await userEvent.type(emailInput, 'existing@example.com')
    await userEvent.type(usernameInput, 'testuser')
    await userEvent.type(passwordInput, 'Password123')
    await userEvent.type(confirmPasswordInput, 'Password123')
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(mockNavigate).not.toHaveBeenCalled()
    })
  })

  it('has accessible form structure', () => {
    renderRegisterForm()

    expect(screen.getByPlaceholderText(/邮箱/i)).toHaveAttribute('type', 'email')
    expect(screen.getByPlaceholderText(/用户名/i)).toHaveAttribute('type', 'text')
    expect(screen.getByPlaceholderText(/请输入密码/i)).toHaveAttribute('type', 'password')
    expect(screen.getByPlaceholderText(/请再次输入密码/i)).toHaveAttribute('type', 'password')
    expect(screen.getByRole('button', { name: /注册/i })).toHaveAttribute('type', 'submit')
  })
})
