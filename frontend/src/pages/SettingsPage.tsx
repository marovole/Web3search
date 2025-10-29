import React, { useState } from 'react'
import { motion } from 'framer-motion'
import {
  Settings,
  Palette,
  MessageSquare,
  Keyboard,
  Bell,
  Shield,
  Download,
  Upload,
  RotateCcw,
  Moon,
  Sun,
  Monitor,
  Volume2,
  VolumeX,
  Save
} from 'lucide-react'
import { useUserPreferences } from '@/contexts/UserPreferencesContext'
import { cn } from '@/lib/utils'

interface SettingsSectionProps {
  icon: React.ReactNode
  title: string
  description: string
  children: React.ReactNode
}

function SettingsSection({ icon, title, description, children }: SettingsSectionProps) {
  return (
    <div className="bg-card rounded-lg border border-border p-6">
      <div className="flex items-start gap-4 mb-6">
        <div className="p-2 bg-primary/10 rounded-lg text-primary">
          {icon}
        </div>
        <div className="flex-1">
          <h3 className="text-lg font-semibold">{title}</h3>
          <p className="text-sm text-muted-foreground mt-1">{description}</p>
        </div>
      </div>
      <div className="space-y-4">
        {children}
      </div>
    </div>
  )
}

interface ToggleSettingProps {
  label: string
  description?: string
  checked: boolean
  onChange: (checked: boolean) => void
  disabled?: boolean
}

function ToggleSetting({ label, description, checked, onChange, disabled }: ToggleSettingProps) {
  return (
    <div className={cn("flex items-start justify-between", disabled && "opacity-50")}>
      <div className="flex-1">
        <label className="text-sm font-medium">{label}</label>
        {description && (
          <p className="text-xs text-muted-foreground mt-1">{description}</p>
        )}
      </div>
      <button
        onClick={() => onChange(!checked)}
        disabled={disabled}
        className={cn(
          "relative inline-flex h-6 w-11 items-center rounded-full transition-colors",
          checked ? "bg-primary" : "bg-muted",
          !disabled && "hover:opacity-80",
          disabled && "cursor-not-allowed"
        )}
        role="switch"
        aria-checked={checked}
      >
        <span
          className={cn(
            "inline-block h-4 w-4 transform rounded-full bg-white transition-transform",
            checked ? "translate-x-6" : "translate-x-1"
          )}
        />
      </button>
    </div>
  )
}

interface SelectSettingProps<T extends string = string> {
  label: string
  description?: string
  value: T
  onChange: (value: T) => void
  options: { label: string; value: T }[]
  disabled?: boolean
}

function SelectSetting<T extends string>({ label, description, value, onChange, options, disabled }: SelectSettingProps<T>) {
  return (
    <div className={cn("flex items-start justify-between", disabled && "opacity-50")}>
      <div className="flex-1 pr-4">
        <label className="text-sm font-medium">{label}</label>
        {description && (
          <p className="text-xs text-muted-foreground mt-1">{description}</p>
        )}
      </div>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value as T)}
        disabled={disabled}
        className={cn(
          "px-3 py-1.5 bg-background border border-border rounded-md text-sm",
          "focus:outline-none focus:ring-2 focus:ring-primary",
          disabled && "cursor-not-allowed opacity-50"
        )}
      >
        {options.map(option => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  )
}

interface RangeSettingProps {
  label: string
  description?: string
  value: number
  onChange: (value: number) => void
  min?: number
  max?: number
  step?: number
  disabled?: boolean
}

function RangeSetting({ label, description, value, onChange, min = 0, max = 100, step = 1, disabled }: RangeSettingProps) {
  return (
    <div className={cn("space-y-2", disabled && "opacity-50")}>
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium">{label}</label>
        <span className="text-sm text-muted-foreground">{value}{step >= 1 ? '' : 's'}</span>
      </div>
      {description && (
        <p className="text-xs text-muted-foreground">{description}</p>
      )}
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        disabled={disabled}
        className={cn(
          "w-full h-2 bg-muted rounded-lg appearance-none cursor-pointer",
          "focus:outline-none focus:ring-2 focus:ring-primary",
          disabled && "cursor-not-allowed"
        )}
      />
    </div>
  )
}

/**
 * 用户设置页面
 */
export default function SettingsPage() {
  const { preferences, updatePreference, updatePreferences, resetPreferences, exportPreferences, importPreferences } = useUserPreferences()
  const [importData, setImportData] = useState('')
  const [showImportDialog, setShowImportDialog] = useState(false)
  const [showResetConfirm, setShowResetConfirm] = useState(false)

  // 导入设置
  const handleImport = () => {
    if (importPreferences(importData)) {
      setShowImportDialog(false)
      setImportData('')
      alert('设置导入成功！')
    } else {
      alert('设置导入失败，请检查格式是否正确')
    }
  }

  // 导出设置
  const handleExport = () => {
    const data = exportPreferences()
    const blob = new Blob([data], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `web3search-settings-${new Date().toISOString().split('T')[0]}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  // 重置设置
  const handleReset = () => {
    resetPreferences()
    setShowResetConfirm(false)
    alert('设置已重置为默认值！')
  }

  return (
    <div className="container mx-auto max-w-4xl p-6 space-y-6">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-primary/10 rounded-lg">
            <Settings className="w-6 h-6 text-primary" />
          </div>
          <div>
            <h1 className="text-2xl font-bold">设置</h1>
            <p className="text-sm text-muted-foreground">自定义您的体验</p>
          </div>
        </div>

        {/* 操作按钮 */}
        <div className="flex gap-2">
          <button
            onClick={handleExport}
            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity"
          >
            <Download size={16} />
            导出设置
          </button>
          <button
            onClick={() => setShowImportDialog(true)}
            className="flex items-center gap-2 px-4 py-2 bg-muted hover:bg-muted/80 rounded-lg transition-colors"
          >
            <Upload size={16} />
            导入设置
          </button>
        </div>
      </div>

      {/* 设置分组 */}
      <div className="space-y-6">
        {/* 界面设置 */}
        <SettingsSection
          icon={<Palette size={20} />}
          title="外观"
          description="自定义应用的外观和主题"
        >
          <SelectSetting
            label="主题"
            description="选择浅色、深色或跟随系统"
            value={preferences.theme}
            onChange={(value) => updatePreference('theme', value)}
            options={[
              { label: '浅色', value: 'light' },
              { label: '深色', value: 'dark' },
              { label: '跟随系统', value: 'system' }
            ]}
          />

          <SelectSetting
            label="语言"
            description="选择界面语言"
            value={preferences.language}
            onChange={(value) => updatePreference('language', value)}
            options={[
              { label: '简体中文', value: 'zh-CN' },
              { label: 'English', value: 'en-US' }
            ]}
          />

          <SelectSetting
            label="字体大小"
            description="调整界面字体大小"
            value={preferences.fontSize}
            onChange={(value) => updatePreference('fontSize', value)}
            options={[
              { label: '小', value: 'small' },
              { label: '中', value: 'medium' },
              { label: '大', value: 'large' }
            ]}
          />

          <ToggleSetting
            label="紧凑模式"
            description="减少间距，显示更多内容"
            checked={preferences.compactMode}
            onChange={(checked) => updatePreference('compactMode', checked)}
          />

          <ToggleSetting
            label="动画效果"
            description="启用界面动画和过渡效果"
            checked={preferences.enableAnimations}
            onChange={(checked) => updatePreference('enableAnimations', checked)}
          />
        </SettingsSection>

        {/* 聊天设置 */}
        <SettingsSection
          icon={<MessageSquare size={20} />}
          title="聊天"
          description="配置聊天功能的默认行为"
        >
          <SelectSetting
            label="默认聊天模式"
            description="选择快速聊天或深度研究"
            value={preferences.defaultChatMode}
            onChange={(value) => updatePreference('defaultChatMode', value)}
            options={[
              { label: '快速聊天', value: 'quick' },
              { label: '深度研究', value: 'deep' }
            ]}
          />

          <ToggleSetting
            label="自动保存聊天"
            description="自动保存聊天记录到本地"
            checked={preferences.autoSaveChat}
            onChange={(checked) => updatePreference('autoSaveChat', checked)}
          />

          <ToggleSetting
            label="Markdown预览"
            description="在聊天中显示Markdown格式"
            checked={preferences.showMarkdownPreview}
            onChange={(checked) => updatePreference('showMarkdownPreview', checked)}
          />

          <SelectSetting
            label="最大聊天历史"
            description="本地存储的聊天记录数量"
            value={preferences.maxChatHistory.toString()}
            onChange={(value) => updatePreference('maxChatHistory', parseInt(value))}
            options={[
              { label: '50条', value: '50' },
              { label: '100条', value: '100' },
              { label: '200条', value: '200' },
              { label: '500条', value: '500' },
              { label: '无限制', value: '-1' }
            ]}
          />
        </SettingsSection>

        {/* 快捷键设置 */}
        <SettingsSection
          icon={<Keyboard size={20} />}
          title="键盘快捷键"
          description="管理键盘快捷键功能"
        >
          <ToggleSetting
            label="启用快捷键"
            description="使用键盘快捷键快速操作"
            checked={preferences.enableKeyboardShortcuts}
            onChange={(checked) => updatePreference('enableKeyboardShortcuts', checked)}
          />

          <ToggleSetting
            label="显示快捷键提示"
            description="按键时显示快捷键提示"
            checked={preferences.enableShortcutHints}
            onChange={(checked) => updatePreference('enableShortcutHints', checked)}
          />
        </SettingsSection>

        {/* 通知设置 */}
        <SettingsSection
          icon={<Bell size={20} />}
          title="通知"
          description="配置通知和提醒设置"
        >
          <ToggleSetting
            label="启用通知"
            description="允许显示通知"
            checked={preferences.enableNotifications}
            onChange={(checked) => updatePreference('enableNotifications', checked)}
          />

          <ToggleSetting
            label="声音提醒"
            description="操作时播放提示音"
            checked={preferences.enableSound}
            onChange={(checked) => updatePreference('enableSound', checked)}
          />

          <ToggleSetting
            label="桌面通知"
            description="在系统通知中心显示"
            checked={preferences.enableDesktopNotifications}
            onChange={(checked) => updatePreference('enableDesktopNotifications', checked)}
          />
        </SettingsSection>

        {/* 隐私设置 */}
        <SettingsSection
          icon={<Shield size={20} />}
          title="隐私和安全"
          description="控制数据收集和错误报告"
        >
          <ToggleSetting
            label="分析数据"
            description="帮助我们改进产品体验"
            checked={preferences.enableAnalytics}
            onChange={(checked) => updatePreference('enableAnalytics', checked)}
          />

          <ToggleSetting
            label="错误报告"
            description="自动发送错误信息以帮助修复问题"
            checked={preferences.enableErrorReporting}
            onChange={(checked) => updatePreference('enableErrorReporting', checked)}
          />

          <ToggleSetting
            label="性能追踪"
            description="收集性能数据以优化应用"
            checked={preferences.enablePerformanceTracking}
            onChange={(checked) => updatePreference('enablePerformanceTracking', checked)}
          />
        </SettingsSection>

        {/* 高级设置 */}
        <SettingsSection
          icon={<Monitor size={20} />}
          title="高级"
          description="其他高级配置选项"
        >
          <ToggleSetting
            label="自动刷新数据"
            description="定期自动获取最新数据"
            checked={preferences.autoRefreshData}
            onChange={(checked) => updatePreference('autoRefreshData', checked)}
          />

          <RangeSetting
            label="刷新间隔"
            description="自动刷新的时间间隔"
            value={preferences.refreshInterval}
            onChange={(value) => updatePreference('refreshInterval', value)}
            min={10}
            max={300}
            step={10}
          />

          <ToggleSetting
            label="离线模式"
            description="优先使用本地缓存的数据"
            checked={preferences.enableOfflineMode}
            onChange={(checked) => updatePreference('enableOfflineMode', checked)}
          />
        </SettingsSection>
      </div>

      {/* 危险操作区域 */}
      <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-destructive mb-4">危险操作</h3>
        <button
          onClick={() => setShowResetConfirm(true)}
          className="flex items-center gap-2 px-4 py-2 bg-destructive text-destructive-foreground rounded-lg hover:opacity-90 transition-opacity"
        >
          <RotateCcw size={16} />
          重置所有设置
        </button>
      </div>

      {/* 导入对话框 */}
      {showImportDialog && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-background rounded-lg border border-border p-6 max-w-md w-full">
            <h3 className="text-lg font-semibold mb-4">导入设置</h3>
            <textarea
              value={importData}
              onChange={(e) => setImportData(e.target.value)}
              placeholder="粘贴导出的设置JSON数据..."
              className="w-full h-32 px-3 py-2 bg-muted rounded-md text-sm"
            />
            <div className="flex gap-2 mt-4">
              <button
                onClick={handleImport}
                className="flex-1 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity"
              >
                导入
              </button>
              <button
                onClick={() => {
                  setShowImportDialog(false)
                  setImportData('')
                }}
                className="flex-1 px-4 py-2 bg-muted hover:bg-muted/80 rounded-lg transition-colors"
              >
                取消
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 重置确认对话框 */}
      {showResetConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-background rounded-lg border border-border p-6 max-w-md w-full">
            <h3 className="text-lg font-semibold mb-4 text-destructive">确认重置</h3>
            <p className="text-sm text-muted-foreground mb-6">
              此操作将把所有设置重置为默认值，此操作不可撤销。
            </p>
            <div className="flex gap-2">
              <button
                onClick={handleReset}
                className="flex-1 px-4 py-2 bg-destructive text-destructive-foreground rounded-lg hover:opacity-90 transition-opacity"
              >
                确认重置
              </button>
              <button
                onClick={() => setShowResetConfirm(false)}
                className="flex-1 px-4 py-2 bg-muted hover:bg-muted/80 rounded-lg transition-colors"
              >
                取消
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
