import React from 'react'
import { motion, AnimatePresence } from 'framer-motion'

interface ShortcutKey {
  key: string
  ctrlKey?: boolean
  shiftKey?: boolean
  altKey?: boolean
  metaKey?: boolean
}

interface ShortcutIndicatorProps {
  keys: ShortcutKey[]
  visible: boolean
  message?: string
  duration?: number
}

/**
 * 快捷键提示指示器
 * 当用户按下快捷键组合时显示提示
 */
export function ShortcutIndicator({
  keys,
  visible,
  message = '快捷键已触发',
  duration = 1500
}: ShortcutIndicatorProps) {
  const [showMessage, setShowMessage] = React.useState(false)

  React.useEffect(() => {
    if (visible) {
      setShowMessage(true)
      const timer = setTimeout(() => {
        setShowMessage(false)
      }, duration)
      return () => clearTimeout(timer)
    }
  }, [visible, duration])

  return (
    <AnimatePresence>
      {visible && (
        <div className="fixed bottom-8 left-1/2 transform -translate-x-1/2 z-50">
          {/* 快捷键组合显示 */}
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.9 }}
            transition={{ duration: 0.2 }}
            className="flex items-center gap-2 px-4 py-3 bg-background border border-border rounded-lg shadow-lg"
          >
            {keys.map((key, index) => (
              <React.Fragment key={index}>
                {index > 0 && (
                  <span className="text-muted-foreground text-sm">+</span>
                )}
                <div className="flex items-center gap-1">
                  {/* 修饰键 */}
                  {key.ctrlKey && (
                    <kbd className="px-2 py-1 bg-muted rounded text-xs font-mono">
                      Ctrl
                    </kbd>
                  )}
                  {key.metaKey && (
                    <kbd className="px-2 py-1 bg-muted rounded text-xs font-mono">
                      ⌘
                    </kbd>
                  )}
                  {key.altKey && (
                    <kbd className="px-2 py-1 bg-muted rounded text-xs font-mono">
                      ⌥
                    </kbd>
                  )}
                  {key.shiftKey && (
                    <kbd className="px-2 py-1 bg-muted rounded text-xs font-mono">
                      ⇧
                    </kbd>
                  )}
                  {/* 主键 */}
                  <kbd className="px-2 py-1 bg-primary text-primary-foreground rounded text-xs font-mono">
                    {formatKey(key.key)}
                  </kbd>
                </div>
              </React.Fragment>
            ))}
          </motion.div>

          {/* 消息提示 */}
          <AnimatePresence>
            {showMessage && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.2, delay: 0.1 }}
                className="mt-2 text-center text-sm text-muted-foreground"
              >
                {message}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}
    </AnimatePresence>
  )
}

/**
 * 格式化按键显示
 */
function formatKey(key: string): string {
  const keyMap: Record<string, string> = {
    ' ': 'Space',
    'ArrowUp': '↑',
    'ArrowDown': '↓',
    'ArrowLeft': '←',
    'ArrowRight': '→',
    'Escape': 'Esc',
    'Enter': 'Enter',
    'Tab': 'Tab',
    '/': '/',
    '?': '?',
    'g': 'G',
    'n': 'N'
  }

  return keyMap[key] || key.toUpperCase()
}
