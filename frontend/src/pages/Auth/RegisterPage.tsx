/**
 * 注册页面
 */
import React from 'react'
import { AuthLayout } from '@/components/Auth/AuthLayout'
import { RegisterForm } from '@/components/Auth/RegisterForm'

export const RegisterPage: React.FC = () => {
  return (
    <AuthLayout
      title="注册"
      description="创建您的 Web3Search 账户"
    >
      <RegisterForm />
    </AuthLayout>
  )
}

export default RegisterPage

