import React, { createContext, useContext, useState, useEffect } from 'react'

// 用户偏好设置接口
export interface UserPreferences {
  // 界面偏好
  theme: 'light' | 'dark' | 'system'
  language: 'zh-CN' | 'en-US'
  fontSize: 'small' | 'medium' | 'large'
  compactMode: boolean

  // 聊天偏好
  defaultChatMode: 'quick' | 'deep'
  autoSaveChat: boolean
  showMarkdownPreview: boolean
  enableAnimations: boolean

  // 快捷键偏好
  enableKeyboardShortcuts: boolean
  enableShortcutHints: boolean

  // 通知偏好
  enableNotifications: boolean
  enableSound: boolean
  enableDesktopNotifications: boolean

  // 数据和隐私
  enableAnalytics: boolean
  enableErrorReporting: boolean
  enablePerformanceTracking: boolean

  // 高级偏好
  autoRefreshData: boolean
  refreshInterval: number // 秒
  maxChatHistory: number
  enableOfflineMode: boolean
}

interface UserPreferencesContextType {
  preferences: UserPreferences
  updatePreference: <K extends keyof UserPreferences>(
    key: K,
    value: UserPreferences[K]
  ) => void
  updatePreferences: (updates: Partial<UserPreferences>) => void
  resetPreferences: () => void
  exportPreferences: () => string
  importPreferences: (data: string) => boolean
  isLoading: boolean
}

// 默认偏好设置
const DEFAULT_PREFERENCES: UserPreferences = {
  theme: 'system',
  language: 'zh-CN',
  fontSize: 'medium',
  compactMode: false,
  defaultChatMode: 'quick',
  autoSaveChat: true,
  showMarkdownPreview: true,
  enableAnimations: true,
  enableKeyboardShortcuts: true,
  enableShortcutHints: true,
  enableNotifications: true,
  enableSound: true,
  enableDesktopNotifications: false,
  enableAnalytics: false,
  enableErrorReporting: true,
  enablePerformanceTracking: true,
  autoRefreshData: true,
  refreshInterval: 30,
  maxChatHistory: 100,
  enableOfflineMode: false
}

const PREFERENCES_STORAGE_KEY = 'web3search:user-preferences'

const UserPreferencesContext = createContext<UserPreferencesContextType | undefined>(undefined)

interface UserPreferencesProviderProps {
  children: React.ReactNode
}

/**
 * 用户偏好设置上下文提供者
 */
export function UserPreferencesProvider({ children }: UserPreferencesProviderProps) {
  const [preferences, setPreferences] = useState<UserPreferences>(DEFAULT_PREFERENCES)
  const [isLoading, setIsLoading] = useState(true)

  // 加载偏好设置
  useEffect(() => {
    try {
      const stored = localStorage.getItem(PREFERENCES_STORAGE_KEY)
      if (stored) {
        const parsed = JSON.parse(stored)
        // 合并默认设置，确保新版本兼容性
        setPreferences({ ...DEFAULT_PREFERENCES, ...parsed })
      }
    } catch (error) {
      console.error('加载用户偏好设置失败:', error)
    } finally {
      setIsLoading(false)
    }
  }, [])

  // 保存偏好设置
  useEffect(() => {
    if (!isLoading) {
      try {
        localStorage.setItem(PREFERENCES_STORAGE_KEY, JSON.stringify(preferences))
      } catch (error) {
        console.error('保存用户偏好设置失败:', error)
      }
    }
  }, [preferences, isLoading])

  // 更新单个偏好设置
  const updatePreference = <K extends keyof UserPreferences>(
    key: K,
    value: UserPreferences[K]
  ) => {
    setPreferences(prev => ({
      ...prev,
      [key]: value
    }))

    // 特殊处理：主题变更需要应用到document
    if (key === 'theme') {
      applyTheme(value as UserPreferences['theme'])
    }
  }

  // 批量更新偏好设置
  const updatePreferences = (updates: Partial<UserPreferences>) => {
    setPreferences(prev => {
      const newPrefs = { ...prev, ...updates }
      // 特殊处理主题
      if (updates.theme) {
        applyTheme(updates.theme)
      }
      return newPrefs
    })
  }

  // 重置偏好设置
  const resetPreferences = () => {
    setPreferences(DEFAULT_PREFERENCES)
    localStorage.removeItem(PREFERENCES_STORAGE_KEY)
  }

  // 导出偏好设置
  const exportPreferences = (): string => {
    return JSON.stringify(preferences, null, 2)
  }

  // 导入偏好设置
  const importPreferences = (data: string): boolean => {
    try {
      const parsed = JSON.parse(data)
      const merged = { ...DEFAULT_PREFERENCES, ...parsed }
      setPreferences(merged)
      return true
    } catch (error) {
      console.error('导入偏好设置失败:', error)
      return false
    }
  }

  // 应用主题
  const applyTheme = (theme: UserPreferences['theme']) => {
    const root = document.documentElement
    root.classList.remove('light', 'dark')

    if (theme === 'system') {
      const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches
        ? 'dark'
        : 'light'
      root.classList.add(systemTheme)
    } else {
      root.classList.add(theme)
    }
  }

  // 监听系统主题变化
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    const handleChange = () => {
      if (preferences.theme === 'system') {
        applyTheme('system')
      }
    }

    mediaQuery.addEventListener('change', handleChange)
    return () => mediaQuery.removeEventListener('change', handleChange)
  }, [preferences.theme])

  // 初始化时应用主题
  useEffect(() => {
    applyTheme(preferences.theme)
  }, [])

  return (
    <UserPreferencesContext.Provider
      value={{
        preferences,
        updatePreference,
        updatePreferences,
        resetPreferences,
        exportPreferences,
        importPreferences,
        isLoading
      }}
    >
      {children}
    </UserPreferencesContext.Provider>
  )
}

/**
 * 使用用户偏好设置上下文
 */
export function useUserPreferences() {
  const context = useContext(UserPreferencesContext)
  if (!context) {
    throw new Error('useUserPreferences must be used within UserPreferencesProvider')
  }
  return context
}

/**
 * 便利Hook：获取特定偏好设置
 */
export function usePreference<K extends keyof UserPreferences>(key: K) {
  const { preferences, updatePreference } = useUserPreferences()
  return [preferences[key], (value: UserPreferences[K]) => updatePreference(key, value)] as const
}

/**
 * 便利Hook：检查是否为特定主题
 */
export function useIsDarkTheme() {
  const [theme] = usePreference('theme')
  const [isDark, setIsDark] = React.useState(false)

  React.useEffect(() => {
    const checkDark = () => {
      if (theme === 'system') {
        setIsDark(window.matchMedia('(prefers-color-scheme: dark)').matches)
      } else {
        setIsDark(theme === 'dark')
      }
    }

    checkDark()

    if (theme === 'system') {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
      mediaQuery.addEventListener('change', checkDark)
      return () => mediaQuery.removeEventListener('change', checkDark)
    }
  }, [theme])

  return isDark
}
