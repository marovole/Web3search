import React from 'react'
import { Bell, Check, CheckCheck, Trash2, RefreshCw, Filter, AlertTriangle, TrendingUp, Newspaper, BellRing, Info } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { useNotifications, Notification } from '@/hooks/useNotifications'
import { formatDistanceToNow } from 'date-fns'
import { zhCN } from 'date-fns/locale'

const NotificationIcon: React.FC<{ type: Notification['type'] }> = ({ type }) => {
  const iconClass = "w-5 h-5"
  
  switch (type) {
    case 'price_alert':
      return <TrendingUp className={cn(iconClass, "text-green-500")} />
    case 'risk_alert':
      return <AlertTriangle className={cn(iconClass, "text-red-500")} />
    case 'news_brief':
      return <Newspaper className={cn(iconClass, "text-blue-500")} />
    case 'portfolio_update':
      return <TrendingUp className={cn(iconClass, "text-purple-500")} />
    case 'system':
      return <Info className={cn(iconClass, "text-muted-foreground")} />
    case 'promo':
      return <BellRing className={cn(iconClass, "text-yellow-500")} />
    default:
      return <Bell className={cn(iconClass, "text-muted-foreground")} />
  }
}

const NotificationItem: React.FC<{
  notification: Notification
  onMarkRead: (id: string) => void
  onDismiss: (id: string) => void
}> = ({ notification, onMarkRead, onDismiss }) => {
  const isUnread = !notification.read_at
  
  const timeAgo = formatDistanceToNow(new Date(notification.created_at), {
    addSuffix: true,
    locale: zhCN
  })

  const priorityColors = {
    low: 'border-l-muted-foreground/30',
    normal: 'border-l-primary/50',
    high: 'border-l-yellow-500',
    urgent: 'border-l-red-500'
  }

  return (
    <div
      className={cn(
        "group relative p-4 border-l-4 rounded-r-lg transition-all duration-200",
        "hover:bg-muted/30",
        priorityColors[notification.priority],
        isUnread ? "bg-primary/5" : "bg-transparent"
      )}
    >
      <div className="flex items-start gap-3">
        <div className={cn(
          "mt-0.5 p-2 rounded-lg shrink-0",
          isUnread ? "bg-primary/10" : "bg-muted/50"
        )}>
          <NotificationIcon type={notification.type} />
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <h4 className={cn(
              "text-sm truncate",
              isUnread ? "font-semibold text-foreground" : "font-medium text-muted-foreground"
            )}>
              {notification.title}
            </h4>
            {isUnread && (
              <span className="w-2 h-2 rounded-full bg-primary shrink-0 mt-1.5" />
            )}
          </div>
          
          <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
            {notification.body}
          </p>
          
          <div className="flex items-center gap-3 mt-2">
            <span className="text-xs text-muted-foreground/60">
              {timeAgo}
            </span>
            <Badge variant="outline" className="text-[10px] h-5 px-1.5">
              {notification.type.replace('_', ' ')}
            </Badge>
          </div>
        </div>

        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
          {isUnread && (
            <Button
              size="sm"
              variant="ghost"
              className="h-8 w-8 p-0"
              onClick={() => onMarkRead(notification.id)}
              title="标记已读"
            >
              <Check className="w-4 h-4" />
            </Button>
          )}
          <Button
            size="sm"
            variant="ghost"
            className="h-8 w-8 p-0 text-muted-foreground hover:text-destructive"
            onClick={() => onDismiss(notification.id)}
            title="删除"
          >
            <Trash2 className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </div>
  )
}

const NotificationsPage: React.FC = () => {
  const {
    notifications,
    unreadCount,
    total,
    loading,
    error,
    fetchNotifications,
    markAsRead,
    markAllAsRead,
    dismissNotification,
    refresh
  } = useNotifications({ autoRefresh: true, refreshInterval: 30000 })

  const [filter, setFilter] = React.useState<'all' | 'unread'>('all')
  const [typeFilter, setTypeFilter] = React.useState<string>('')

  React.useEffect(() => {
    fetchNotifications({ unreadOnly: filter === 'unread', type: typeFilter || undefined })
  }, [filter, typeFilter, fetchNotifications])

  const handleMarkAllRead = async () => {
    await markAllAsRead()
  }

  const notificationTypes = [
    { value: '', label: '全部类型' },
    { value: 'price_alert', label: '价格预警' },
    { value: 'risk_alert', label: '风险预警' },
    { value: 'news_brief', label: '新闻速报' },
    { value: 'portfolio_update', label: '持仓更新' },
    { value: 'system', label: '系统通知' }
  ]

  return (
    <div className="min-h-screen p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-3">
              <Bell className="w-6 h-6 text-primary" />
              通知中心
              {unreadCount > 0 && (
                <Badge variant="default" className="ml-2">
                  {unreadCount} 未读
                </Badge>
              )}
            </h1>
            <p className="text-muted-foreground mt-1">
              共 {total} 条通知
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={refresh}
              disabled={loading}
              className="gap-2"
            >
              <RefreshCw className={cn("w-4 h-4", loading && "animate-spin")} />
              刷新
            </Button>
            {unreadCount > 0 && (
              <Button
                variant="outline"
                size="sm"
                onClick={handleMarkAllRead}
                className="gap-2"
              >
                <CheckCheck className="w-4 h-4" />
                全部已读
              </Button>
            )}
          </div>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-3 mb-6 p-4 rounded-xl bg-muted/30 border border-border/50">
          <Filter className="w-4 h-4 text-muted-foreground" />
          
          <div className="flex gap-2">
            <Button
              size="sm"
              variant={filter === 'all' ? 'default' : 'ghost'}
              onClick={() => setFilter('all')}
              className="h-8"
            >
              全部
            </Button>
            <Button
              size="sm"
              variant={filter === 'unread' ? 'default' : 'ghost'}
              onClick={() => setFilter('unread')}
              className="h-8"
            >
              未读
            </Button>
          </div>

          <div className="h-6 w-px bg-border mx-2" />

          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="h-8 px-3 text-sm rounded-md border border-border bg-background text-foreground"
          >
            {notificationTypes.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
        </div>

        {/* Error State */}
        {error && (
          <div className="p-4 rounded-xl bg-destructive/10 border border-destructive/30 text-destructive mb-6">
            <p className="text-sm">{error}</p>
          </div>
        )}

        {/* Notifications List */}
        <div className="space-y-2">
          {loading && notifications.length === 0 ? (
            // Loading skeleton
            Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="p-4 rounded-lg bg-muted/30 animate-pulse">
                <div className="flex gap-3">
                  <div className="w-10 h-10 rounded-lg bg-muted" />
                  <div className="flex-1 space-y-2">
                    <div className="h-4 bg-muted rounded w-1/3" />
                    <div className="h-3 bg-muted rounded w-2/3" />
                    <div className="h-3 bg-muted rounded w-1/4" />
                  </div>
                </div>
              </div>
            ))
          ) : notifications.length === 0 ? (
            // Empty state
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <div className="w-16 h-16 rounded-full bg-muted/50 flex items-center justify-center mb-4">
                <Bell className="w-8 h-8 text-muted-foreground/50" />
              </div>
              <h3 className="text-lg font-medium text-muted-foreground">暂无通知</h3>
              <p className="text-sm text-muted-foreground/60 mt-1">
                {filter === 'unread' ? '没有未读通知' : '您还没有收到任何通知'}
              </p>
            </div>
          ) : (
            notifications.map((notification) => (
              <NotificationItem
                key={notification.id}
                notification={notification}
                onMarkRead={markAsRead}
                onDismiss={dismissNotification}
              />
            ))
          )}
        </div>

        {/* Load More */}
        {notifications.length < total && (
          <div className="mt-6 text-center">
            <Button
              variant="outline"
              onClick={() => fetchNotifications({ offset: notifications.length })}
              disabled={loading}
            >
              加载更多
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}

export default NotificationsPage
