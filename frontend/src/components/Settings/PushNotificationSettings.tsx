import React, { useState, useEffect } from 'react'
import { Bell, BellOff, CheckCircle, XCircle, Loader2, Send, AlertTriangle } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { useAuth } from '@/contexts/AuthContext'
import {
  isPushSupported,
  getPushSubscriptionStatus,
  subscribeToPush,
  unsubscribeFromPush,
  testPushNotification
} from '@/lib/push'

interface PushNotificationSettingsProps {
  className?: string
}

export const PushNotificationSettings: React.FC<PushNotificationSettingsProps> = ({
  className
}) => {
  const { session } = useAuth()
  const [status, setStatus] = useState<{
    supported: boolean
    permission: NotificationPermission
    subscribed: boolean
  }>({ supported: false, permission: 'default', subscribed: false })
  
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)
  const [testLoading, setTestLoading] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  useEffect(() => {
    checkStatus()
  }, [])

  const checkStatus = async () => {
    setLoading(true)
    const result = await getPushSubscriptionStatus()
    setStatus(result)
    setLoading(false)
  }

  const handleSubscribe = async () => {
    if (!session?.access_token) {
      setMessage({ type: 'error', text: '请先登录' })
      return
    }

    setActionLoading(true)
    setMessage(null)

    const result = await subscribeToPush(session.access_token)
    
    if (result.success) {
      setMessage({ type: 'success', text: '推送通知已开启' })
      await checkStatus()
    } else {
      setMessage({ type: 'error', text: result.error || '开启失败' })
    }

    setActionLoading(false)
  }

  const handleUnsubscribe = async () => {
    if (!session?.access_token) {
      setMessage({ type: 'error', text: '请先登录' })
      return
    }

    setActionLoading(true)
    setMessage(null)

    const result = await unsubscribeFromPush(session.access_token)
    
    if (result.success) {
      setMessage({ type: 'success', text: '推送通知已关闭' })
      await checkStatus()
    } else {
      setMessage({ type: 'error', text: result.error || '关闭失败' })
    }

    setActionLoading(false)
  }

  const handleTest = async () => {
    if (!session?.access_token) {
      setMessage({ type: 'error', text: '请先登录' })
      return
    }

    setTestLoading(true)
    setMessage(null)

    const result = await testPushNotification(session.access_token)
    
    if (result.success) {
      setMessage({ type: 'success', text: result.message || '测试通知已发送' })
    } else {
      setMessage({ type: 'error', text: result.error || '发送失败' })
    }

    setTestLoading(false)
  }

  if (loading) {
    return (
      <div className={cn("p-6 rounded-xl border bg-card", className)}>
        <div className="flex items-center justify-center py-8">
          <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
        </div>
      </div>
    )
  }

  if (!status.supported) {
    return (
      <div className={cn("p-6 rounded-xl border bg-card", className)}>
        <div className="flex items-start gap-4">
          <div className="p-3 rounded-xl bg-muted">
            <BellOff className="w-6 h-6 text-muted-foreground" />
          </div>
          <div>
            <h3 className="font-semibold text-lg">推送通知</h3>
            <p className="text-sm text-muted-foreground mt-1">
              您的浏览器不支持推送通知功能
            </p>
            <Badge variant="outline" className="mt-3">不支持</Badge>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className={cn("p-6 rounded-xl border bg-card", className)}>
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-4">
          <div className={cn(
            "p-3 rounded-xl",
            status.subscribed ? "bg-primary/10" : "bg-muted"
          )}>
            {status.subscribed ? (
              <Bell className="w-6 h-6 text-primary" />
            ) : (
              <BellOff className="w-6 h-6 text-muted-foreground" />
            )}
          </div>
          <div>
            <h3 className="font-semibold text-lg">推送通知</h3>
            <p className="text-sm text-muted-foreground mt-1">
              接收价格预警、风险提醒和新闻速报
            </p>
            
            <div className="flex items-center gap-2 mt-3">
              {status.subscribed ? (
                <Badge className="bg-primary/10 text-primary border-primary/30">
                  <CheckCircle className="w-3 h-3 mr-1" />
                  已开启
                </Badge>
              ) : status.permission === 'denied' ? (
                <Badge variant="destructive">
                  <XCircle className="w-3 h-3 mr-1" />
                  已被浏览器阻止
                </Badge>
              ) : (
                <Badge variant="outline">未开启</Badge>
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          {status.subscribed && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleTest}
              disabled={testLoading}
              className="gap-2"
            >
              {testLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
              测试
            </Button>
          )}
          
          {status.subscribed ? (
            <Button
              variant="outline"
              size="sm"
              onClick={handleUnsubscribe}
              disabled={actionLoading}
              className="gap-2"
            >
              {actionLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <BellOff className="w-4 h-4" />
              )}
              关闭
            </Button>
          ) : status.permission === 'denied' ? (
            <Button variant="outline" size="sm" disabled className="gap-2">
              <AlertTriangle className="w-4 h-4" />
              请在浏览器设置中解除阻止
            </Button>
          ) : (
            <Button
              size="sm"
              onClick={handleSubscribe}
              disabled={actionLoading}
              className="gap-2"
            >
              {actionLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Bell className="w-4 h-4" />
              )}
              开启推送
            </Button>
          )}
        </div>
      </div>

      {message && (
        <div className={cn(
          "mt-4 p-3 rounded-lg text-sm flex items-center gap-2",
          message.type === 'success' 
            ? "bg-green-500/10 text-green-500 border border-green-500/20"
            : "bg-red-500/10 text-red-500 border border-red-500/20"
        )}>
          {message.type === 'success' ? (
            <CheckCircle className="w-4 h-4 shrink-0" />
          ) : (
            <XCircle className="w-4 h-4 shrink-0" />
          )}
          {message.text}
        </div>
      )}

      {status.permission === 'denied' && (
        <div className="mt-4 p-4 rounded-lg bg-yellow-500/10 border border-yellow-500/20">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-yellow-500 shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-yellow-500">通知权限被阻止</p>
              <p className="text-xs text-yellow-500/80 mt-1">
                请点击浏览器地址栏左侧的锁图标，找到"通知"设置并选择"允许"，然后刷新页面。
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default PushNotificationSettings
