/**
 * 认证页面通用布局组件
 * 提供统一的认证页面布局和样式
 */
import React, { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { cn } from '@/lib/utils'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

interface AuthLayoutProps {
  children: ReactNode
  title: string
  description?: string
  footer?: ReactNode
  className?: string
}

export const AuthLayout: React.FC<AuthLayoutProps> = ({
  children,
  title,
  description,
  footer,
  className,
}) => {
  return (
    <div className={cn('min-h-screen flex items-center justify-center bg-background p-4', className)}>
      <div className="w-full max-w-md">
        {/* Logo/Brand */}
        <div className="text-center mb-8">
          <Link to="/" className="inline-block">
            <h1 className="text-2xl font-bold text-foreground">Web3Search</h1>
          </Link>
        </div>

        {/* Card */}
        <Card className="shadow-lg">
          <CardHeader className="space-y-1">
            <CardTitle className="text-2xl font-semibold text-center">{title}</CardTitle>
            {description && (
              <CardDescription className="text-center">{description}</CardDescription>
            )}
          </CardHeader>
          <CardContent>{children}</CardContent>
        </Card>

        {/* Footer */}
        {footer && <div className="mt-6 text-center">{footer}</div>}
      </div>
    </div>
  )
}

