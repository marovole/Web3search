import React from 'react'
import { Bell } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useNotifications } from '@/hooks/useNotifications'

interface NotificationBadgeProps {
  className?: string
  onClick?: () => void
  showZero?: boolean
}

export const NotificationBadge: React.FC<NotificationBadgeProps> = ({
  className,
  onClick,
  showZero = false
}) => {
  const { unreadCount } = useNotifications({ autoRefresh: true, refreshInterval: 30000, initialFetch: true })

  if (unreadCount === 0 && !showZero) {
    return (
      <button
        onClick={onClick}
        className={cn(
          "relative p-2 rounded-lg transition-all duration-200",
          "hover:bg-muted/50 active:bg-muted/70",
          "text-muted-foreground hover:text-foreground",
          className
        )}
        aria-label="通知"
      >
        <Bell className="w-5 h-5" />
      </button>
    )
  }

  return (
    <button
      onClick={onClick}
      className={cn(
        "relative p-2 rounded-lg transition-all duration-200",
        "hover:bg-muted/50 active:bg-muted/70",
        "text-muted-foreground hover:text-foreground",
        className
      )}
      aria-label={`通知 (${unreadCount} 未读)`}
    >
      <Bell className="w-5 h-5" />
      
      {/* Badge */}
      <span className={cn(
        "absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px]",
        "flex items-center justify-center",
        "text-[10px] font-bold text-primary-foreground",
        "bg-primary rounded-full px-1",
        "animate-in zoom-in-50 duration-200"
      )}>
        {unreadCount > 99 ? '99+' : unreadCount}
      </span>
    </button>
  )
}

export default NotificationBadge
