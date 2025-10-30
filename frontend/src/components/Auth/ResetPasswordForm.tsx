/**
 * 重置密码表单组件
 */
import React, { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useNavigate, useSearchParams, Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { resetPasswordSchema, type ResetPasswordFormData } from '@/lib/validations/auth'
import { resetPassword } from '@/services/auth'
import { toast } from '@/components/ui/toast'
import { Loader2, CheckCircle2, AlertCircle } from 'lucide-react'

export const ResetPasswordForm: React.FC = () => {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [isLoading, setIsLoading] = useState(false)
  const [isSuccess, setIsSuccess] = useState(false)
  const [tokenError, setTokenError] = useState<string | null>(null)

  const token = searchParams.get('token')

  useEffect(() => {
    if (!token) {
      setTokenError('重置链接无效：缺少令牌参数')
    }
  }, [token])

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ResetPasswordFormData>({
    resolver: zodResolver(resetPasswordSchema),
  })

  const onSubmit = async (data: ResetPasswordFormData) => {
    if (!token) {
      toast({
        title: '重置失败',
        description: '重置链接无效，请重新申请密码重置。',
        variant: 'destructive',
      })
      return
    }

    setIsLoading(true)
    try {
      await resetPassword({
        token,
        new_password: data.password,
      })
      setIsSuccess(true)
      toast({
        title: '密码重置成功',
        description: '您的密码已成功重置，请使用新密码登录。',
        variant: 'success',
      })
    } catch (error: any) {
      const errorMessage =
        error?.response?.data?.detail ||
        error?.message ||
        '密码重置失败，令牌可能已过期，请重新申请'
      toast({
        title: '重置失败',
        description: errorMessage,
        variant: 'destructive',
      })
    } finally {
      setIsLoading(false)
    }
  }

  if (tokenError) {
    return (
      <div className="space-y-4 text-center">
        <div className="flex justify-center">
          <AlertCircle className="h-12 w-12 text-destructive" />
        </div>
        <div className="space-y-2">
          <h3 className="text-lg font-semibold">链接无效</h3>
          <p className="text-sm text-muted-foreground">{tokenError}</p>
        </div>
        <Button
          type="button"
          variant="outline"
          className="w-full"
          onClick={() => navigate('/auth/forgot-password')}
        >
          重新申请重置
        </Button>
      </div>
    )
  }

  if (isSuccess) {
    return (
      <div className="space-y-4 text-center">
        <div className="flex justify-center">
          <CheckCircle2 className="h-12 w-12 text-green-500" />
        </div>
        <div className="space-y-2">
          <h3 className="text-lg font-semibold">密码重置成功</h3>
          <p className="text-sm text-muted-foreground">
            您的密码已成功重置，请使用新密码登录。
          </p>
        </div>
        <Button
          type="button"
          className="w-full"
          onClick={() => navigate('/auth/login')}
        >
          前往登录
        </Button>
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="space-y-2">
        <Input
          {...register('password')}
          type="password"
          label="新密码"
          placeholder="请输入新密码（至少8个字符，包含字母和数字）"
          error={errors.password?.message}
          disabled={isLoading}
          autoComplete="new-password"
        />
      </div>

      <div className="space-y-2">
        <Input
          {...register('confirmPassword')}
          type="password"
          label="确认新密码"
          placeholder="请再次输入新密码"
          error={errors.confirmPassword?.message}
          disabled={isLoading}
          autoComplete="new-password"
        />
      </div>

      <Button type="submit" className="w-full" disabled={isLoading}>
        {isLoading ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            重置中...
          </>
        ) : (
          '重置密码'
        )}
      </Button>

      <div className="text-center text-sm text-muted-foreground">
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

