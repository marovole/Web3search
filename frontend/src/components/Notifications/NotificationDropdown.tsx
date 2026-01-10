import React, { useState, useRef, useEffect } from 'react'
import { Bell, Check, CheckCheck, ExternalLink, X, AlertTriangle, TrendingUp, Newspaper, BellRing, Info } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { useNotifications, Notification } from '@/hooks/useNotifications'
import { formatDistanceToNow } from 'date-fns'
import { zhCN } from 'date-fns/locale'
import { useNavigate } from 'react-router-dom'

const NotificationIcon: React.FC<{ type: Notification['type']; size?: number }> = ({ type, size = 16 }) => {
  const iconClass = `w-${size / 4} h-${size / 4}`
  
  switch (type) {
    case 'price_alert':
      return <TrendingUp className={cn(iconClass, "text-green-500")} style={{ width: size, height: size }} />
    case 'risk_alert':
      return <AlertTriangle className={cn(iconClass, "text-red-500")} style={{ width: size, height: size }} />
    case 'news_brief':
      return <Newspaper className={cn(iconClass, "text-blue-500")} style={{ width: size, height: size }} />
    case 'portfolio_update':
      return <TrendingUp className={cn(iconClass, "text-purple-500")} style={{ width: size, height: size }} />
    case 'system':
      return <Info className={cn(iconClass, "text-muted-foreground")} style={{ width: size, height: size }} />
    case 'promo':
      return <BellRing className={cn(iconClass, "text-yellow-500")} style={{ width: size, height: size }} />
    default:
      return <Bell className={cn(iconClass, "text-muted-foreground")} style={{ width: size, height: size }} />
  }
}

interface NotificationDropdownProps {
  className?: string
}

export const NotificationDropdown: React.FC<NotificationDropdownProps> = ({ className }) => {
  const navigate = useNavigate()
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)
  
  const {
    notifications,
    unreadCount,
    loading,
    markAsRead,
    markAllAsRead,
    refresh
  } = useNotifications({ autoRefresh: true, refreshInterval: 30000, initialFetch: true })

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside)
      return () => document.removeEventListener('mousedown', handleClickOutside)
    }
    return undefined
  }, [isOpen])

  // Close on escape
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        setIsOpen(false)
      }
    }

    if (isOpen) {
      document.addEventListener('keydown', handleEscape)
      return () => document.removeEventListener('keydown', handleEscape)
    }
    return undefined
  }, [isOpen])

  const handleNotificationClick = async (notification: Notification) => {
    if (!notification.read_at) {
      await markAsRead(notification.id)
    }
    setIsOpen(false)
    // Navigate based on notification type or data
    if (notification.data?.link) {
      navigate(notification.data.link as string)
    }
  }

  const handleViewAll = () => {
    setIsOpen(false)
    navigate('/notifications')
  }

  const recentNotifications = notifications.slice(0, 5)

  return (
    <div ref={dropdownRef} className={cn("relative", className)}>
      {/* Trigger Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          "relative p-2 rounded-lg transition-all duration-200",
          "hover:bg-muted/50 active:bg-muted/70",
          "text-muted-foreground hover:text-foreground",
          isOpen && "bg-muted/50 text-foreground"
        )}
        aria-label={`通知 ${unreadCount > 0 ? `(${unreadCount} 未读)` : ''}`}
      >
        <Bell className="w-5 h-5" />
        
        {/* Unread Badge */}
        {unreadCount > 0 && (
          <span className={cn(
            "absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px]",
            "flex items-center justify-center",
            "text-[10px] font-bold text-primary-foreground",
            "bg-primary rounded-full px-1",
            "animate-in zoom-in-50 duration-200"
          )}>
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {/* Dropdown Panel */}
      {isOpen && (
        <div className={cn(
          "absolute right-0 top-full mt-2 w-80 sm:w-96",
          "bg-popover border border-border rounded-xl shadow-xl",
          "animate-in fade-in-0 zoom-in-95 slide-in-from-top-2 duration-200",
          "z-50 overflow-hidden"
        )}>
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-border/50">
            <div className="flex items-center gap-2">
              <h3 className="font-semibold text-foreground">通知</h3>
              {unreadCount > 0 && (
                <Badge variant="secondary" className="h-5 px-1.5 text-[10px]">
                  {unreadCount} 未读
                </Badge>
              )}
            </div>
            <div className="flex items-center gap-1">
              {unreadCount > 0 && (
                <Button
                  size="sm"
                  variant="ghost"
                  className="h-7 text-xs gap-1"
                  onClick={() => markAllAsRead()}
                >
                  <CheckCheck className="w-3.5 h-3.5" />
                  全部已读
                </Button>
              )}
              <button
                onClick={() => setIsOpen(false)}
                className="p-1.5 rounded-md hover:bg-muted/50 text-muted-foreground"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Notifications List */}
          <div className="max-h-[400px] overflow-y-auto">
            {loading && recentNotifications.length === 0 ? (
              <div className="p-8 text-center text-muted-foreground">
                <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-2" />
                <p className="text-sm">加载中...</p>
              </div>
            ) : recentNotifications.length === 0 ? (
              <div className="p-8 text-center">
                <div className="w-12 h-12 rounded-full bg-muted/50 flex items-center justify-center mx-auto mb-3">
                  <Bell className="w-6 h-6 text-muted-foreground/50" />
                </div>
                <p className="text-sm text-muted-foreground">暂无通知</p>
              </div>
            ) : (
              <div className="divide-y divide-border/50">
                {recentNotifications.map((notification) => {
                  const isUnread = !notification.read_at
                  const timeAgo = formatDistanceToNow(new Date(notification.created_at), {
                    addSuffix: true,
                    locale: zhCN
                  })

                  return (
                    <button
                      key={notification.id}
                      onClick={() => handleNotificationClick(notification)}
                      className={cn(
                        "w-full text-left p-4 transition-colors",
                        "hover:bg-muted/30",
                        isUnread && "bg-primary/5"
                      )}
                    >
                      <div className="flex gap-3">
                        <div className={cn(
                          "mt-0.5 p-1.5 rounded-lg shrink-0",
                          isUnread ? "bg-primary/10" : "bg-muted/50"
                        )}>
                          <NotificationIcon type={notification.type} size={16} />
                        </div>
                        
                        <div className="flex-1 min-w-0">
                          <div className="flex items-start justify-between gap-2">
                            <p className={cn(
                              "text-sm line-clamp-1",
                              isUnread ? "font-medium text-foreground" : "text-muted-foreground"
                            )}>
                              {notification.title}
                            </p>
                            {isUnread && (
                              <span className="w-2 h-2 rounded-full bg-primary shrink-0 mt-1" />
                            )}
                          </div>
                          
                          <p className="text-xs text-muted-foreground/80 line-clamp-2 mt-0.5">
                            {notification.body}
                          </p>
                          
                          <p className="text-[10px] text-muted-foreground/50 mt-1">
                            {timeAgo}
                          </p>
                        </div>
                      </div>
                    </button>
                  )
                })}
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="p-3 border-t border-border/50 bg-muted/20">
            <Button
              variant="ghost"
              className="w-full h-9 text-sm gap-2"
              onClick={handleViewAll}
            >
              查看全部通知
              <ExternalLink className="w-3.5 h-3.5" />
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}

export default NotificationDropdown
