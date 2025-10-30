/**
 * 重置密码页面
 */
import React from 'react'
import { AuthLayout } from '@/components/Auth/AuthLayout'
import { ResetPasswordForm } from '@/components/Auth/ResetPasswordForm'

export const ResetPasswordPage: React.FC = () => {
  return (
    <AuthLayout
      title="重置密码"
      description="请输入您的新密码"
    >
      <ResetPasswordForm />
    </AuthLayout>
  )
}

export default ResetPasswordPage

