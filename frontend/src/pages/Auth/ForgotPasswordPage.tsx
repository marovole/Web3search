/**
 * 忘记密码页面
 */
import React from 'react'
import { AuthLayout } from '@/components/Auth/AuthLayout'
import { ForgotPasswordForm } from '@/components/Auth/ForgotPasswordForm'

export const ForgotPasswordPage: React.FC = () => {
  return (
    <AuthLayout
      title="忘记密码"
      description="我们将向您的邮箱发送密码重置链接"
    >
      <ForgotPasswordForm />
    </AuthLayout>
  )
}

export default ForgotPasswordPage

