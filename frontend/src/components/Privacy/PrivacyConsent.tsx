import React, { useState, useEffect } from 'react'
import { X, AlertCircle, Shield, Eye, BarChart3 } from 'lucide-react'
import { Button } from './ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { cn } from '../lib/utils'

interface PrivacyConsentProps {
  onConsentChange?: (analytics: boolean, errorReporting: boolean) => void
}

/**
 * 隐私同意管理组件
 * 符合GDPR和CCPA要求，提供精细化的隐私控制选项
 */
export default function PrivacyConsent({ onConsentChange }: PrivacyConsentProps) {
  const [showBanner, setShowBanner] = useState(false)
  const [analyticsConsent, setAnalyticsConsent] = useState(false)
  const [errorReportingConsent, setErrorReportingConsent] = useState(false)
  const [showDetails, setShowDetails] = useState(false)

  // 检查是否已经设置过同意
  useEffect(() => {
    const consentSet = localStorage.getItem('privacy_consent_set')
    const savedAnalytics = localStorage.getItem('analytics_consent')
    const savedErrorReporting = localStorage.getItem('error_reporting_consent')

    if (!consentSet) {
      // 首次访问，显示横幅
      setShowBanner(true)
    } else {
      // 已设置过，使用保存的值
      setAnalyticsConsent(savedAnalytics === 'true')
      setErrorReportingConsent(savedErrorReporting === 'true')
    }
  }, [])

  // 保存同意状态
  const saveConsent = (analytics: boolean, errorReporting: boolean) => {
    localStorage.setItem('privacy_consent_set', 'true')
    localStorage.setItem('analytics_consent', analytics.toString())
    localStorage.setItem('error_reporting_consent', errorReporting.toString())
    
    setAnalyticsConsent(analytics)
    setErrorReportingConsent(errorReporting)
    setShowBanner(false)
    
    // 通知父组件
    if (onConsentChange) {
      onConsentChange(analytics, errorReporting)
    }
  }

  // 接受所有
  const handleAcceptAll = () => {
    saveConsent(true, true)
  }

  // 仅接受必要
  const handleAcceptNecessary = () => {
    saveConsent(false, false)
  }

  // 自定义设置
  const handleCustomSave = () => {
    saveConsent(analyticsConsent, errorReportingConsent)
  }

  // 撤回同意
  const handleRevoke = () => {
    localStorage.removeItem('privacy_consent_set')
    setShowBanner(true)
    setAnalyticsConsent(false)
    setErrorReportingConsent(false)
  }

  if (!showBanner) {
    return null
  }

  return (
    <div className={cn(
      "fixed inset-x-0 bottom-0 z-50 p-4",
      "bg-background border-t border-border shadow-lg",
      "animate-in slide-in-from-bottom duration-300"
    )}>
      <Card className="max-w-4xl mx-auto">
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <Shield className="h-6 w-6 text-primary" />
              <div>
                <CardTitle className="text-lg">隐私设置</CardTitle>
                <CardDescription>
                  我们重视您的隐私。请选择您同意的数据收集选项。
                </CardDescription>
              </div>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setShowDetails(!showDetails)}
              className="h-8 w-8"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>

        {showDetails && (
          <CardContent className="space-y-4">
            {/* 分析数据收集 */}
            <div className="flex items-start gap-4 p-4 border rounded-lg">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <BarChart3 className="h-5 w-5 text-primary" />
                  <h3 className="font-semibold">分析数据收集</h3>
                </div>
                <p className="text-sm text-muted-foreground mb-3">
                  帮助我们了解您如何使用应用，包括页面访问、点击和导航路径。
                  这些数据经过匿名化处理，不会包含个人身份信息。
                </p>
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="analytics"
                    checked={analyticsConsent}
                    onChange={(e) => setAnalyticsConsent(e.target.checked)}
                    className="h-4 w-4 rounded border-gray-300"
                  />
                  <label htmlFor="analytics" className="text-sm font-medium cursor-pointer">
                    允许分析数据收集
                  </label>
                </div>
              </div>
            </div>

            {/* 错误报告 */}
            <div className="flex items-start gap-4 p-4 border rounded-lg">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <AlertCircle className="h-5 w-5 text-primary" />
                  <h3 className="font-semibold">错误报告</h3>
                </div>
                <p className="text-sm text-muted-foreground mb-3">
                  自动收集应用错误和技术问题，帮助我们改进应用稳定性。
                  包含错误堆栈和技术信息，但不包含个人数据。
                </p>
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="errorReporting"
                    checked={errorReportingConsent}
                    onChange={(e) => setErrorReportingConsent(e.target.checked)}
                    className="h-4 w-4 rounded border-gray-300"
                  />
                  <label htmlFor="errorReporting" className="text-sm font-medium cursor-pointer">
                    允许错误报告
                  </label>
                </div>
              </div>
            </div>

            {/* 隐私政策链接 */}
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Eye className="h-4 w-4" />
              <span>
                了解更多，请查看我们的
                <a
                  href="/privacy"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary hover:underline ml-1"
                >
                  隐私政策
                </a>
              </span>
            </div>

            {/* 操作按钮 */}
            <div className="flex flex-col sm:flex-row gap-3 pt-4">
              <Button
                variant="outline"
                onClick={handleAcceptNecessary}
                className="flex-1"
              >
                仅接受必要
              </Button>
              <Button
                onClick={handleCustomSave}
                className="flex-1"
              >
                保存设置
              </Button>
              <Button
                onClick={handleAcceptAll}
                variant="default"
                className="flex-1"
              >
                接受全部
              </Button>
            </div>
          </CardContent>
        )}

        {!showDetails && (
          <CardContent>
            <div className="flex flex-col sm:flex-row gap-3">
              <Button
                variant="outline"
                onClick={handleAcceptNecessary}
                className="flex-1"
              >
                仅接受必要
              </Button>
              <Button
                onClick={() => setShowDetails(true)}
                variant="outline"
                className="flex-1"
              >
                自定义设置
              </Button>
              <Button
                onClick={handleAcceptAll}
                variant="default"
                className="flex-1"
              >
                接受全部
              </Button>
            </div>
          </CardContent>
        )}
      </Card>
    </div>
  )
}

/**
 * 隐私设置管理器Hook
 */
export function usePrivacyConsent() {
  const [analyticsConsent, setAnalyticsConsent] = useState(false)
  const [errorReportingConsent, setErrorReportingConsent] = useState(false)

  useEffect(() => {
    const savedAnalytics = localStorage.getItem('analytics_consent')
    const savedErrorReporting = localStorage.getItem('error_reporting_consent')
    
    setAnalyticsConsent(savedAnalytics === 'true')
    setErrorReportingConsent(savedErrorReporting === 'true')
  }, [])

  const revokeConsent = () => {
    localStorage.removeItem('privacy_consent_set')
    localStorage.removeItem('analytics_consent')
    localStorage.removeItem('error_reporting_consent')
    setAnalyticsConsent(false)
    setErrorReportingConsent(false)
  }

  return {
    analyticsConsent,
    errorReportingConsent,
    revokeConsent
  }
}

