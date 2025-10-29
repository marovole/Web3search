import React, { createContext, useContext, useState, useMemo } from 'react'
import { useKeyboardShortcuts, Shortcut, getShortcutHelp, ShortcutHelpItem } from '@/hooks/useKeyboardShortcuts'
import { ShortcutHelp } from '@/components/Shortcuts/ShortcutHelp'

interface KeyboardShortcutsContextType {
  shortcuts: Shortcut[]
  showHelp: boolean
  toggleHelp: () => void
  registerShortcut: (shortcut: Shortcut) => void
  unregisterShortcut: (key: string) => void
  helpItems: ShortcutHelpItem[]
}

const KeyboardShortcutsContext = createContext<KeyboardShortcutsContextType | undefined>(undefined)

interface KeyboardShortcutsProviderProps {
  children: React.ReactNode
  defaultShortcuts?: Shortcut[]
}

/**
 * 键盘快捷键上下文提供者
 * 管理全局快捷键和帮助面板
 */
export function KeyboardShortcutsProvider({
  children,
  defaultShortcuts = []
}: KeyboardShortcutsProviderProps) {
  const [shortcuts, setShortcuts] = useState<Shortcut[]>(defaultShortcuts)
  const [showHelp, setShowHelp] = useState(false)

  // 注册快捷键
  const registerShortcut = (shortcut: Shortcut) => {
    setShortcuts(prev => {
      // 检查是否已存在相同按键的快捷键
      const exists = prev.some(s =>
        s.key.toLowerCase() === shortcut.key.toLowerCase() &&
        !!s.ctrlKey === !!shortcut.ctrlKey &&
        !!s.shiftKey === !!shortcut.shiftKey &&
        !!s.altKey === !!shortcut.altKey &&
        !!s.metaKey === !!shortcut.metaKey
      )

      if (exists) {
        console.warn(`快捷键已存在: ${JSON.stringify(shortcut)}`)
        return prev
      }

      return [...prev, { ...shortcut, enabled: shortcut.enabled !== false }]
    })
  }

  // 注销快捷键
  const unregisterShortcut = (key: string) => {
    setShortcuts(prev => prev.filter(s => s.key !== key))
  }

  // 切换帮助面板
  const toggleHelp = () => {
    setShowHelp(prev => !prev)
  }

  // 生成帮助项
  const helpItems = useMemo(() => {
    return getShortcutHelp(shortcuts)
  }, [shortcuts])

  // 使用快捷键Hook
  useKeyboardShortcuts(shortcuts, {
    enabled: true,
    global: true
  })

  // 注册帮助快捷键（Shift + ?）
  React.useEffect(() => {
    registerShortcut({
      key: '?',
      shiftKey: true,
      handler: toggleHelp,
      description: '显示快捷键帮助',
      enabled: true
    })
  }, [])

  return (
    <KeyboardShortcutsContext.Provider value={{
      shortcuts,
      showHelp,
      toggleHelp,
      registerShortcut,
      unregisterShortcut,
      helpItems
    }}>
      {children}

      {/* 快捷键帮助面板 */}
      <ShortcutHelp
        isOpen={showHelp}
        onClose={toggleHelp}
        shortcuts={helpItems}
      />
    </KeyboardShortcutsContext.Provider>
  )
}

/**
 * 使用键盘快捷键上下文
 */
export function useKeyboardShortcutsContext() {
  const context = useContext(KeyboardShortcutsContext)
  if (!context) {
    throw new Error('useKeyboardShortcutsContext must be used within KeyboardShortcutsProvider')
  }
  return context
}

/**
 * Hook用于注册局部快捷键
 */
export function useRegisterShortcut() {
  const { registerShortcut } = useKeyboardShortcutsContext()
  return registerShortcut
}

/**
 * Hook用于注销局部快捷键
 */
export function useUnregisterShortcut() {
  const { unregisterShortcut } = useKeyboardShortcutsContext()
  return unregisterShortcut
}
