import React, { useState, useRef, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { 
  User, 
  LogOut, 
  Settings, 
  ChevronDown, 
  Crown, 
  LogIn, 
  Sparkles 
} from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { cn } from '@/lib/utils'

export const UserMenu: React.FC = () => {
  const { user, profile, isAuthenticated, signOut } = useAuth()
  const [isOpen, setIsOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)

  // Close on click outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside)
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [isOpen])

  // Close on escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        setIsOpen(false)
      }
    }

    if (isOpen) {
      document.addEventListener('keydown', handleEscape)
    }
    return () => {
      document.removeEventListener('keydown', handleEscape)
    }
  }, [isOpen])

  if (!isAuthenticated) {
    return (
      <Link
        to="/auth/login"
        className={cn(
          "w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 group relative overflow-hidden",
          "hover:bg-primary/10 text-muted-foreground hover:text-primary"
        )}
      >
        <span className="flex-shrink-0 w-5 h-5 flex items-center justify-center">
          <LogIn size={18} />
        </span>
        <span className="flex-1 text-left text-sm font-medium">
          Sign In
        </span>
      </Link>
    )
  }

  const displayName = profile?.display_name || user?.email?.split('@')[0] || 'User'
  const plan = profile?.plan || 'free'
  const initials = displayName.slice(0, 2).toUpperCase()

  const getPlanBadgeStyles = (planType: string) => {
    switch (planType) {
      case 'pro':
        return "bg-primary/10 text-primary border-primary/20"
      case 'team':
        return "bg-purple-500/10 text-purple-500 border-purple-500/20"
      default:
        return "bg-muted text-muted-foreground border-border"
    }
  }

  return (
    <div className="relative" ref={menuRef}>
      {/* Dropdown Menu */}
      <div
        className={cn(
          "absolute bottom-full left-0 w-full mb-2 p-1",
          "bg-surface-1 border border-border/50 rounded-xl shadow-xl shadow-black/5",
          "transition-all duration-200 origin-bottom",
          isOpen 
            ? "opacity-100 translate-y-0 scale-100 pointer-events-auto" 
            : "opacity-0 translate-y-2 scale-95 pointer-events-none"
        )}
      >
        <div className="flex flex-col gap-0.5">
          <Link
            to="/settings"
            onClick={() => setIsOpen(false)}
            className="flex items-center gap-2.5 px-3 py-2 text-sm text-muted-foreground hover:text-foreground hover:bg-muted/50 rounded-lg transition-colors"
          >
            <Settings size={15} />
            <span>Settings</span>
          </Link>
          
          {plan === 'free' && (
            <Link
              to="/upgrade"
              onClick={() => setIsOpen(false)}
              className="flex items-center gap-2.5 px-3 py-2 text-sm text-primary hover:bg-primary/5 rounded-lg transition-colors"
            >
              <Sparkles size={15} />
              <span>Upgrade Plan</span>
            </Link>
          )}

          <div className="h-px bg-border/40 my-1 mx-2" />

          <button
            onClick={() => {
              signOut()
              setIsOpen(false)
            }}
            className="flex items-center gap-2.5 px-3 py-2 text-sm text-red-500/80 hover:text-red-500 hover:bg-red-500/5 rounded-lg transition-colors w-full text-left"
          >
            <LogOut size={15} />
            <span>Sign Out</span>
          </button>
        </div>
      </div>

      {/* Trigger Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          "w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 group border border-transparent",
          "hover:bg-muted/40 hover:border-border/40",
          isOpen && "bg-muted/40 border-border/40"
        )}
      >
        {/* Avatar */}
        <div className="relative flex-shrink-0">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-muted to-muted/50 border border-border flex items-center justify-center overflow-hidden">
            {profile?.avatar_url ? (
              <img 
                src={profile.avatar_url} 
                alt={displayName} 
                className="w-full h-full object-cover"
              />
            ) : (
              <span className="text-xs font-medium text-muted-foreground">
                {initials}
              </span>
            )}
          </div>
          {/* Online Status Dot */}
          <span className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-green-500 border-2 border-surface-1" />
        </div>

        {/* User Info */}
        <div className="flex-1 flex flex-col items-start min-w-0">
          <span className="text-sm font-medium text-foreground truncate w-full text-left">
            {displayName}
          </span>
          <div className="flex items-center gap-1.5 w-full">
            <span className={cn(
              "text-[10px] font-mono uppercase px-1.5 py-0 rounded border leading-none flex items-center gap-1",
              getPlanBadgeStyles(plan)
            )}>
              {plan === 'pro' && <Crown size={8} className="fill-current" />}
              {plan}
            </span>
          </div>
        </div>

        {/* Chevron */}
        <ChevronDown 
          size={14} 
          className={cn(
            "text-muted-foreground/50 transition-transform duration-200",
            isOpen && "rotate-180"
          )} 
        />
      </button>
    </div>
  )
}

export default UserMenu
