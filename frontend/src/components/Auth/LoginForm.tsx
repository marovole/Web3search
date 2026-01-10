import React, { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useNavigate, useLocation, Link } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { loginSchema, type LoginFormData } from '@/lib/validations/auth'
import { toast } from '@/components/ui/toast'
import { Loader2 } from 'lucide-react'

export const LoginForm: React.FC = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const { signIn } = useAuth()
  const [isLoading, setIsLoading] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  })

  const onSubmit = async (data: LoginFormData) => {
    setIsLoading(true)
    try {
      const { error } = await signIn(data.email, data.password)
      if (error) {
        throw error
      }
      toast({
        title: '登录成功',
        description: '欢迎回来！',
        variant: 'success',
      })

      const from = (location.state as { from?: string })?.from || '/'
      navigate(from, { replace: true })
    } catch (error: unknown) {
      const err = error as Error
      const errorMessage = err?.message || '登录失败，请检查您的邮箱和密码'
      toast({
        title: '登录失败',
        description: errorMessage,
        variant: 'destructive',
      })
    } finally {
      setIsLoading(false)
    }
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

      <div className="space-y-2">
        <Input
          {...register('password')}
          type="password"
          label="密码"
          placeholder="请输入您的密码"
          error={errors.password?.message}
          disabled={isLoading}
          autoComplete="current-password"
        />
      </div>

      <div className="flex items-center justify-between text-sm">
        <Link
          to="/auth/forgot-password"
          className="text-primary hover:underline"
        >
          忘记密码？
        </Link>
      </div>

      <Button type="submit" className="w-full" disabled={isLoading}>
        {isLoading ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            登录中...
          </>
        ) : (
          '登录'
        )}
      </Button>

      <div className="text-center text-sm text-muted-foreground">
        还没有账号？{' '}
        <Link
          to="/auth/register"
          className="text-primary hover:underline"
        >
          立即注册
        </Link>
      </div>
    </form>
  )
}

