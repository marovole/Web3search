import { useEffect, useRef } from 'react'

export interface ShortcutHandler {
  (event: KeyboardEvent): void
}

export interface Shortcut {
  key: string
  ctrlKey?: boolean
  shiftKey?: boolean
  altKey?: boolean
  metaKey?: boolean
  handler: ShortcutHandler
  description?: string
  enabled?: boolean
}

interface UseKeyboardShortcutsOptions {
  enabled?: boolean
  global?: boolean
  element?: HTMLElement | null
}

/**
 * 键盘快捷键管理Hook
 * 支持全局和局部快捷键，提供优雅的用户体验
 */
export function useKeyboardShortcuts(
  shortcuts: Shortcut[],
  options: UseKeyboardShortcutsOptions = {}
) {
  const { enabled = true, global = true, element = null } = options
  const shortcutsRef = useRef(shortcuts)
  const elementRef = useRef(element)

  useEffect(() => {
    shortcutsRef.current = shortcuts
  }, [shortcuts])

  useEffect(() => {
    elementRef.current = element
  }, [element])

  useEffect(() => {
    if (!enabled) return

    const handleKeyDown = (event: KeyboardEvent) => {
      // 如果正在输入，不触发快捷键
      const target = event.target as HTMLElement
      const isInput = target.tagName === 'INPUT' ||
                      target.tagName === 'TEXTAREA' ||
                      target.getAttribute('contenteditable') === 'true' ||
                      target.isContentEditable

      // 如果是输入框或编辑器，且快捷键不强制在输入框中生效，则跳过
      if (isInput && !global) return

      // 检查匹配的快捷键
      for (const shortcut of shortcutsRef.current) {
        if (shortcut.enabled === false) continue

        const matches = shortcut.key.toLowerCase() === event.key.toLowerCase() &&
                       !!shortcut.ctrlKey === event.ctrlKey &&
                       !!shortcut.shiftKey === event.shiftKey &&
                       !!shortcut.altKey === event.altKey &&
                       !!shortcut.metaKey === event.metaKey

        if (matches) {
          // 阻止默认行为
          event.preventDefault()
          event.stopPropagation()

          // 执行处理器
          try {
            shortcut.handler(event)
          } catch (error) {
            console.error('快捷键处理器执行错误:', error)
          }

          break
        }
      }
    }

    // 确定监听的目标元素
    const targetElement = elementRef.current || (global ? document : null)
    if (!targetElement) return

    targetElement.addEventListener('keydown', handleKeyDown as EventListener)

    return () => {
      targetElement.removeEventListener('keydown', handleKeyDown as EventListener)
    }
  }, [enabled, global])

  // 提供一个禁用/启用特定快捷键的函数
  const setShortcutEnabled = (key: string, enabled: boolean) => {
    shortcutsRef.current.forEach(shortcut => {
      if (shortcut.key.toLowerCase() === key.toLowerCase()) {
        shortcut.enabled = enabled
      }
    })
  }

  return {
    setShortcutEnabled
  }
}

/**
 * 预定义的常用快捷键配置
 */
export const DEFAULT_SHORTCUTS = {
  // 导航快捷键
  GO_TO_HOME: {
    key: 'g',
    shiftKey: true,
    handler: () => {
      window.location.href = '/'
    },
    description: '跳转到首页'
  },

  GO_TO_HISTORY: {
    key: 'g',
    altKey: true,
    handler: () => {
      window.location.href = '/history'
    },
    description: '跳转到历史记录'
  },

  GO_TO_WATCHLIST: {
    key: 'g',
    metaKey: true,
    handler: () => {
      window.location.href = '/watchlist'
    },
    description: '跳转到监控列表'
  },

  // 搜索快捷键
  TOGGLE_SEARCH: {
    key: '/',
    handler: (event: KeyboardEvent) => {
      const target = event.target as HTMLElement
      // 只有在非输入框中才激活搜索
      const isInput = target.tagName === 'INPUT' ||
                      target.tagName === 'TEXTAREA' ||
                      target.getAttribute('contenteditable') === 'true'
      if (!isInput) {
        // 触发搜索输入框（需要结合具体UI实现）
        console.log('激活搜索')
      }
    },
    description: '激活搜索'
  },

  // 动作快捷键
  NEW_CHAT: {
    key: 'n',
    ctrlKey: true,
    handler: () => {
      // 创建新聊天（需要结合具体UI实现）
      console.log('创建新聊天')
    },
    description: '创建新聊天'
  },

  // 帮助快捷键
  SHOW_HELP: {
    key: '?',
    shiftKey: true,
    handler: () => {
      // 显示帮助面板（需要结合具体UI实现）
      console.log('显示快捷键帮助')
    },
    description: '显示快捷键帮助'
  },

  // 通用快捷键
  ESCAPE: {
    key: 'Escape',
    handler: () => {
      // 关闭模态框、取消选择等
      console.log('取消当前操作')
    },
    description: '取消/关闭'
  }
}

/**
 * 快捷键帮助组件使用的数据结构
 */
export interface ShortcutHelpItem {
  key: string
  description: string
  category: string
}

export function getShortcutHelp(shortcuts: Shortcut[]): ShortcutHelpItem[] {
  return shortcuts
    .filter(s => s.description && s.enabled !== false)
    .map(s => ({
      key: formatShortcutKey(s),
      description: s.description || '',
      category: getShortcutCategory(s)
    }))
    .sort((a, b) => a.category.localeCompare(b.category))
}

/**
 * 格式化快捷键显示文本
 */
function formatShortcutKey(shortcut: Shortcut): string {
  const parts: string[] = []

  if (shortcut.ctrlKey) parts.push('Ctrl')
  if (shortcut.metaKey) parts.push('Cmd')
  if (shortcut.altKey) parts.push('Alt')
  if (shortcut.shiftKey) parts.push('Shift')

  parts.push(shortcut.key.toUpperCase())

  return parts.join(' + ')
}

/**
 * 获取快捷键分类
 */
function getShortcutCategory(shortcut: Shortcut): string {
  if (shortcut.key.toLowerCase() === 'g') return '导航'
  if (['/', 'n', 'ctrlKey'].some(k => shortcut[k as keyof Shortcut])) return '操作'
  if (shortcut.key === 'Escape') return '通用'
  if (shortcut.key === '?') return '帮助'
  return '其他'
}
