import React from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Command } from 'lucide-react'
import { ShortcutHelpItem } from '@/hooks/useKeyboardShortcuts'
import { cn } from '@/lib/utils'

interface ShortcutHelpProps {
  isOpen: boolean
  onClose: () => void
  shortcuts: ShortcutHelpItem[]
  className?: string
}

/**
 * 快捷键帮助面板组件
 * 显示所有可用的键盘快捷键
 */
export function ShortcutHelp({
  isOpen,
  onClose,
  shortcuts,
  className
}: ShortcutHelpProps) {
  // 按分类组织快捷键
  const groupedShortcuts = shortcuts.reduce((acc, shortcut) => {
    if (!acc[shortcut.category]) {
      acc[shortcut.category] = []
    }
    acc[shortcut.category].push(shortcut)
    return acc
  }, {} as Record<string, ShortcutHelpItem[]>)

  // 分类标题
  const categoryTitles: Record<string, string> = {
    '导航': 'Navigation',
    '操作': 'Actions',
    '通用': 'General',
    '帮助': 'Help',
    '其他': 'Other'
  }

  React.useEffect(() => {
    if (isOpen) {
      // 阻止背景滚动
      document.body.style.overflow = 'hidden'
    } else {
      // 恢复滚动
      document.body.style.overflow = ''
    }

    // ESC键关闭
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose()
      }
    }

    if (isOpen) {
      document.addEventListener('keydown', handleEsc)
    }

    return () => {
      document.body.style.overflow = ''
      document.removeEventListener('keydown', handleEsc)
    }
  }, [isOpen, onClose])

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* 背景遮罩 */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50"
            onClick={onClose}
          />

          {/* 帮助面板 */}
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              transition={{ duration: 0.2 }}
              className={cn(
                "w-full max-w-2xl bg-background rounded-lg shadow-xl",
                "border border-border",
                className
              )}
              onClick={(e) => e.stopPropagation()}
            >
              {/* 头部 */}
              <div className="flex items-center justify-between p-6 border-b border-border">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-primary/10 rounded-lg">
                    <Command className="w-5 h-5 text-primary" />
                  </div>
                  <div>
                    <h2 className="text-xl font-semibold">键盘快捷键</h2>
                    <p className="text-sm text-muted-foreground">
                      使用快捷键提高工作效率
                    </p>
                  </div>
                </div>
                <button
                  onClick={onClose}
                  className="p-2 hover:bg-muted rounded-lg transition-colors"
                  aria-label="关闭帮助"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* 内容 */}
              <div className="p-6 max-h-[60vh] overflow-y-auto">
                {Object.entries(groupedShortcuts).length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    <Command className="w-12 h-12 mx-auto mb-4 opacity-50" />
                    <p>暂无快捷键配置</p>
                  </div>
                ) : (
                  <div className="space-y-6">
                    {Object.entries(groupedShortcuts).map(([category, items]) => (
                      <div key={category}>
                        <h3 className="text-sm font-medium text-muted-foreground mb-3 uppercase tracking-wider">
                          {categoryTitles[category] || category}
                        </h3>
                        <div className="space-y-2">
                          {items.map((shortcut, index) => (
                            <motion.div
                              key={`${shortcut.category}-${index}`}
                              initial={{ opacity: 0, x: -10 }}
                              animate={{ opacity: 1, x: 0 }}
                              transition={{ duration: 0.2, delay: index * 0.02 }}
                              className="flex items-center justify-between p-3 rounded-lg hover:bg-muted/50 transition-colors"
                            >
                              <span className="text-sm">{shortcut.description}</span>
                              <kbd className="px-3 py-1.5 bg-muted rounded-md text-xs font-mono border border-border shadow-sm">
                                {shortcut.key}
                              </kbd>
                            </motion.div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* 底部提示 */}
              <div className="p-4 bg-muted/50 rounded-b-lg border-t border-border">
                <p className="text-xs text-center text-muted-foreground">
                  按 <kbd className="px-1.5 py-0.5 bg-background rounded border">ESC</kbd> 键关闭此面板
                </p>
              </div>
            </motion.div>
          </div>
        </>
      )}
    </AnimatePresence>
  )
}
