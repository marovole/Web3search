/**
 * 登录页面
 */
import React from 'react'
import { AuthLayout } from '@/components/Auth/AuthLayout'
import { LoginForm } from '@/components/Auth/LoginForm'

export const LoginPage: React.FC = () => {
  return (
    <AuthLayout
      title="登录"
      description="登录您的账户以继续使用 Web3Search"
    >
      <LoginForm />
    </AuthLayout>
  )
}

export default LoginPage

