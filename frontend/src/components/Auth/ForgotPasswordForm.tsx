/**
 * 忘记密码表单组件
 */
import React, { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useNavigate, Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { forgotPasswordSchema, type ForgotPasswordFormData } from '@/lib/validations/auth'
import { forgotPassword } from '@/services/auth'
import { toast } from '@/components/ui/toast'
import { Loader2, CheckCircle2 } from 'lucide-react'

export const ForgotPasswordForm: React.FC = () => {
  const navigate = useNavigate()
  const [isLoading, setIsLoading] = useState(false)
  const [isSuccess, setIsSuccess] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ForgotPasswordFormData>({
    resolver: zodResolver(forgotPasswordSchema),
  })

  const onSubmit = async (data: ForgotPasswordFormData) => {
    setIsLoading(true)
    try {
      await forgotPassword(data)
      setIsSuccess(true)
      toast({
        title: '邮件已发送',
        description: '我们已向您的邮箱发送了密码重置链接，请查收。',
        variant: 'success',
      })
    } catch (error: any) {
      const errorMessage =
        error?.response?.data?.detail ||
        error?.message ||
        '发送失败，请检查您的邮箱地址'
      toast({
        title: '发送失败',
        description: errorMessage,
        variant: 'destructive',
      })
    } finally {
      setIsLoading(false)
    }
  }

  if (isSuccess) {
    return (
      <div className="space-y-4 text-center">
        <div className="flex justify-center">
          <CheckCircle2 className="h-12 w-12 text-green-500" />
        </div>
        <div className="space-y-2">
          <h3 className="text-lg font-semibold">邮件已发送</h3>
          <p className="text-sm text-muted-foreground">
            我们已向您的邮箱发送了密码重置链接，请查收邮件并按照说明操作。
          </p>
        </div>
        <Button
          type="button"
          variant="outline"
          className="w-full"
          onClick={() => navigate('/auth/login')}
        >
          返回登录
        </Button>
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="space-y-2">
        <Input
          {...register('email')}
          type="email"
          label="邮箱"
          placeholder="请输入您的邮箱"
          error={errors.email?.message}
          disabled={isLoading}
          autoComplete="email"
        />
      </div>

      <p className="text-sm text-muted-foreground">
        请输入您注册时使用的邮箱地址，我们将发送密码重置链接到您的邮箱。
      </p>

      <Button type="submit" className="w-full" disabled={isLoading}>
        {isLoading ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            发送中...
          </>
        ) : (
          '发送重置链接'
        )}
      </Button>

      <div className="text-center text-sm text-muted-foreground">
        想起密码了？{' '}
        <Link
          to="/auth/login"
          className="text-primary hover:underline"
        >
          返回登录
        </Link>
      </div>
    </form>
  )
}

