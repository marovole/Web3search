import React, { Suspense } from 'react'
import type { RouteObject } from 'react-router-dom'
import { AdaptiveSkeleton } from '../components/ui/loading'

const LoginPage = React.lazy(() => import('../pages/Auth/LoginPage'))
const RegisterPage = React.lazy(() => import('../pages/Auth/RegisterPage'))
const ForgotPasswordPage = React.lazy(() => import('../pages/Auth/ForgotPasswordPage'))
const ResetPasswordPage = React.lazy(() => import('../pages/Auth/ResetPasswordPage'))

export const authRoutes: RouteObject[] = [
  {
    path: '/auth/login',
    element: (
      <Suspense fallback={<AdaptiveSkeleton pageType="settings" />}>
        <LoginPage />
      </Suspense>
    ),
  },
  {
    path: '/auth/register',
    element: (
      <Suspense fallback={<AdaptiveSkeleton pageType="settings" />}>
        <RegisterPage />
      </Suspense>
    ),
  },
  {
    path: '/auth/forgot-password',
    element: (
      <Suspense fallback={<AdaptiveSkeleton pageType="settings" />}>
        <ForgotPasswordPage />
      </Suspense>
    ),
  },
  {
    path: '/auth/reset-password',
    element: (
      <Suspense fallback={<AdaptiveSkeleton pageType="settings" />}>
        <ResetPasswordPage />
      </Suspense>
    ),
  },
]
