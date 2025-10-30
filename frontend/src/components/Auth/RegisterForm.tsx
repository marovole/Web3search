/**
 * 注册表单组件
 */
import React, { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { registerSchema, type RegisterFormData } from '@/lib/validations/auth'
import { toast } from '@/components/ui/toast'
import { Loader2 } from 'lucide-react'

export const RegisterForm: React.FC = () => {
  const navigate = useNavigate()
  const { register: registerUser } = useAuth()
  const [isLoading, setIsLoading] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
  })

  const onSubmit = async (data: RegisterFormData) => {
    setIsLoading(true)
    try {
      await registerUser({
        email: data.email,
        password: data.password,
        username: data.username,
      })
      toast({
        title: '注册成功',
        description: '欢迎加入 Web3Search！',
        variant: 'success',
      })

      // 注册成功后自动登录，重定向到首页
      navigate('/', { replace: true })
    } catch (error: any) {
      const errorMessage =
        error?.response?.data?.detail ||
        error?.message ||
        '注册失败，请检查您的输入信息'
      toast({
        title: '注册失败',
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
          {...register('username')}
          type="text"
          label="用户名（可选）"
          placeholder="请输入用户名（3-20个字符）"
          error={errors.username?.message}
          disabled={isLoading}
          autoComplete="username"
        />
      </div>

      <div className="space-y-2">
        <Input
          {...register('password')}
          type="password"
          label="密码"
          placeholder="请输入密码（至少8个字符，包含字母和数字）"
          error={errors.password?.message}
          disabled={isLoading}
          autoComplete="new-password"
        />
      </div>

      <div className="space-y-2">
        <Input
          {...register('confirmPassword')}
          type="password"
          label="确认密码"
          placeholder="请再次输入密码"
          error={errors.confirmPassword?.message}
          disabled={isLoading}
          autoComplete="new-password"
        />
      </div>

      <Button type="submit" className="w-full" disabled={isLoading}>
        {isLoading ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            注册中...
          </>
        ) : (
          '注册'
        )}
      </Button>

      <div className="text-center text-sm text-muted-foreground">
        已有账号？{' '}
        <Link
          to="/auth/login"
          className="text-primary hover:underline"
        >
          立即登录
        </Link>
      </div>
    </form>
  )
}

