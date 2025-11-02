import React, { useState, useCallback, useEffect } from 'react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Textarea } from '@/components/ui/textarea'
import { Input } from '@/components/ui/input'
import { 
  MessageCircle, 
  Send, 
  Mail, 
  Phone, 
  Bug, 
  ThumbsUp,
  ThumbsDown,
  Clock,
  CheckCircle,
  AlertTriangle,
  HelpCircle,
  ExternalLink
} from 'lucide-react'

/**
 * 反馈类型
 */
export type FeedbackType = 
  | 'bug'
  | 'feature'
  | 'improvement'
  | 'question'
  | 'complaint'
  | 'compliment'

/**
 * 反馈严重程度
 */
export type FeedbackSeverity = 'low' | 'medium' | 'high' | 'urgent'

/**
 * 反馈状态
 */
export type FeedbackStatus = 'pending' | 'in_progress' | 'resolved' | 'closed'

/**
 * 反馈数据接口
 */
export interface FeedbackData {
  id: string
  type: FeedbackType
  severity: FeedbackSeverity
  title: string
  description: string
  email?: string
  attachments?: File[]
  userAgent: string
  url: string
  timestamp: number
  userId?: string
  metadata?: Record<string, any>
}

/**
 * 支持渠道
 */
export interface SupportChannel {
  id: string
  name: string
  type: 'email' | 'phone' | 'chat' | 'helpdesk' | 'faq'
  contact: string
  available?: string
  icon?: React.ReactNode
  description?: string
}

/**
 * 反馈配置
 */
const FEEDBACK_CONFIGS: Record<FeedbackType, {
  icon: React.ReactNode
  color: string
  bgColor: string
  title: string
  placeholder: string
  questions: string[]
}> = {
  bug: {
    icon: <Bug className="w-5 h-5" />,
    color: 'text-red-600',
    bgColor: 'bg-red-50',
    title: '报告错误',
    placeholder: '请详细描述遇到的问题...',
    questions: [
      '问题发生的时间',
      '操作步骤',
      '预期行为 vs 实际行为',
      '错误信息截图'
    ]
  },
  feature: {
    icon: <ThumbsUp className="w-5 h-5" />,
    color: 'text-green-600',
    bgColor: 'bg-green-50',
    title: '功能建议',
    placeholder: '请描述您希望添加的功能...',
    questions: [
      '功能用途',
      '期望的使用方式',
      '对现有功能的影响'
    ]
  },
  improvement: {
    icon: <AlertTriangle className="w-5 h-5" />,
    color: 'text-blue-600',
    bgColor: 'bg-blue-50',
    title: '改进建议',
    placeholder: '请提出您的改进建议...',
    questions: [
      '当前问题',
      '改进方案',
      '预期效果'
    ]
  },
  question: {
    icon: <HelpCircle className="w-5 h-5" />,
    color: 'text-purple-600',
    bgColor: 'bg-purple-50',
    title: '使用咨询',
    placeholder: '请描述您的问题...',
    questions: [
      '具体问题',
      '相关场景',
      '已尝试的解决方法'
    ]
  },
  complaint: {
    icon: <ThumbsDown className="w-5 h-5" />,
    color: 'text-orange-600',
    bgColor: 'bg-orange-50',
    title: '投诉反馈',
    placeholder: '请详细描述投诉内容...',
    questions: [
      '投诉对象',
      '具体问题',
      '期望解决方案'
    ]
  },
  compliment: {
    icon: <ThumbsUp className="w-5 h-5" />,
    color: 'text-pink-600',
    bgColor: 'bg-pink-50',
    title: '表扬建议',
    placeholder: '请分享您的使用体验...',
    questions: [
      '满意的方面',
      '具体体验',
      '改进建议'
    ]
  }
}

/**
 * 反馈表单组件
 */
export const FeedbackForm: React.FC<{
  type: FeedbackType
  onSubmit: (data: FeedbackData) => Promise<void>
  onCancel?: () => void
  className?: string
  showEmail?: boolean
  allowAttachments?: boolean
}> = ({ 
  type, 
  onSubmit, 
  onCancel, 
  className,
  showEmail = true,
  allowAttachments = true 
}) => {
  const config = FEEDBACK_CONFIGS[type]
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    email: '',
    severity: 'medium' as FeedbackSeverity
  })
  const [attachments, setAttachments] = useState<File[]>([])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!formData.title.trim() || !formData.description.trim()) {
      return
    }

    setIsSubmitting(true)

    try {
      const feedbackData: FeedbackData = {
        id: `feedback-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        type,
        severity: formData.severity,
        title: formData.title,
        description: formData.description,
        email: formData.email || undefined,
        attachments: attachments.length > 0 ? attachments : undefined,
        userAgent: navigator.userAgent,
        url: window.location.href,
        timestamp: Date.now(),
        metadata: {
          viewport: {
            width: window.innerWidth,
            height: window.innerHeight
          },
          timestamp: new Date().toISOString()
        }
      }

      await onSubmit(feedbackData)
      setSubmitted(true)
    } catch (error) {
      console.error('Failed to submit feedback:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setAttachments(Array.from(e.target.files))
    }
  }

  const removeAttachment = (index: number) => {
    setAttachments(prev => prev.filter((_, i) => i !== index))
  }

  if (submitted) {
    return (
      <Card className={cn("p-6 text-center space-y-4", className)}>
        <CheckCircle className="w-12 h-12 text-green-500 mx-auto" />
        <div>
          <h3 className="text-lg font-semibold text-foreground">
            反馈提交成功
          </h3>
          <p className="text-sm text-muted-foreground">
            感谢您的反馈，我们会尽快处理并回复您。
          </p>
        </div>
        <Button onClick={onCancel} variant="outline">
          关闭
        </Button>
      </Card>
    )
  }

  return (
    <Card className={cn("p-6 space-y-4", className)}>
      {/* 表单头部 */}
      <div className={cn("flex items-center gap-3 p-3 rounded-lg", config.bgColor)}>
        <div className={config.color}>
          {config.icon}
        </div>
        <div>
          <h3 className="font-semibold text-foreground">{config.title}</h3>
          <p className="text-sm text-muted-foreground">
            请详细描述您的反馈，帮助我们改进产品
          </p>
        </div>
      </div>

      {/* 表单内容 */}
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* 标题 */}
        <div>
          <label className="block text-sm font-medium mb-2">
            标题 *
          </label>
          <Input
            value={formData.title}
            onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
            placeholder="请简要概括您的反馈"
            required
          />
        </div>

        {/* 描述 */}
        <div>
          <label className="block text-sm font-medium mb-2">
            详细描述 *
          </label>
          <Textarea
            value={formData.description}
            onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
            placeholder={config.placeholder}
            rows={5}
            required
          />
        </div>

        {/* 严重程度 */}
        <div>
          <label className="block text-sm font-medium mb-2">
            严重程度
          </label>
          <div className="flex gap-2">
            {(['low', 'medium', 'high', 'urgent'] as FeedbackSeverity[]).map((severity) => (
              <Button
                key={severity}
                type="button"
                variant={formData.severity === severity ? 'default' : 'outline'}
                size="sm"
                onClick={() => setFormData(prev => ({ ...prev, severity }))}
              >
                {severity === 'low' && '低'}
                {severity === 'medium' && '中'}
                {severity === 'high' && '高'}
                {severity === 'urgent' && '紧急'}
              </Button>
            ))}
          </div>
        </div>

        {/* 邮箱 */}
        {showEmail && (
          <div>
            <label className="block text-sm font-medium mb-2">
              联系邮箱（可选）
            </label>
            <Input
              type="email"
              value={formData.email}
              onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
              placeholder="用于接收处理结果"
            />
          </div>
        )}

        {/* 附件 */}
        {allowAttachments && (
          <div>
            <label className="block text-sm font-medium mb-2">
              附件（可选）
            </label>
            <input
              type="file"
              multiple
              accept="image/*,.pdf,.doc,.docx,.txt"
              onChange={handleFileChange}
              className="block w-full text-sm text-muted-foreground file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-primary file:text-primary-foreground hover:file:bg-primary/80"
            />
            
            {/* 附件列表 */}
            {attachments.length > 0 && (
              <div className="mt-2 space-y-1">
                {attachments.map((file, index) => (
                  <div key={index} className="flex items-center justify-between text-sm bg-muted p-2 rounded">
                    <span>{file.name}</span>
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => removeAttachment(index)}
                    >
                      删除
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* 提示问题 */}
        <div className="text-sm text-muted-foreground">
          <p className="font-medium mb-2">建议包含以下信息：</p>
          <ul className="space-y-1">
            {config.questions.map((question, index) => (
              <li key={index} className="flex items-start gap-2">
                <span className="text-primary">•</span>
                <span>{question}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* 操作按钮 */}
        <div className="flex gap-2">
          <Button
            type="submit"
            disabled={isSubmitting || !formData.title.trim() || !formData.description.trim()}
            className="flex-1"
          >
            {isSubmitting ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                提交中...
              </>
            ) : (
              <>
                <Send className="w-4 h-4 mr-2" />
                提交反馈
              </>
            )}
          </Button>
          
          {onCancel && (
            <Button type="button" variant="outline" onClick={onCancel}>
              取消
            </Button>
          )}
        </div>
      </form>
    </Card>
  )
}

/**
 * 支持渠道组件
 */
export const SupportChannels: React.FC<{
  channels: SupportChannel[]
  className?: string
}> = ({ channels, className }) => {
  return (
    <div className={cn("grid gap-4 md:grid-cols-2 lg:grid-cols-3", className)}>
      {channels.map((channel) => (
        <Card key={channel.id} className="p-4 hover:shadow-md transition-shadow">
          <div className="flex items-start gap-3">
            <div className="flex-shrink-0 text-primary">
              {channel.icon || <MessageCircle className="w-5 h-5" />}
            </div>
            <div className="flex-1 min-w-0">
              <h4 className="font-semibold text-foreground">{channel.name}</h4>
              <p className="text-sm text-muted-foreground mb-2">
                {channel.description}
              </p>
              <div className="space-y-1">
                <p className="text-sm font-medium text-primary">
                  {channel.contact}
                </p>
                {channel.available && (
                  <p className="text-xs text-muted-foreground">
                    服务时间: {channel.available}
                  </p>
                )}
              </div>
            </div>
          </div>
        </Card>
      ))}
    </div>
  )
}

/**
 * 快速反馈按钮组件
 */
export const QuickFeedbackButton: React.FC<{
  onFeedback: (type: FeedbackType) => void
  className?: string
  position?: 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left'
}> = ({ onFeedback, className, position = 'bottom-right' }) => {
  const [isOpen, setIsOpen] = useState(false)

  const positionClasses = {
    'bottom-right': 'bottom-4 right-4',
    'bottom-left': 'bottom-4 left-4',
    'top-right': 'top-4 right-4',
    'top-left': 'top-4 left-4'
  }

  const feedbackTypes: Array<{ type: FeedbackType; label: string; color: string }> = [
    { type: 'bug', label: '错误', color: 'bg-red-500' },
    { type: 'feature', label: '建议', color: 'bg-green-500' },
    { type: 'question', label: '咨询', color: 'bg-blue-500' }
  ]

  return (
    <div className={cn(
      "fixed z-50",
      positionClasses[position],
      className
    )}>
      {/* 反馈选项 */}
      {isOpen && (
        <div className="absolute bottom-12 right-0 space-y-2 animate-fade-in">
          {feedbackTypes.map(({ type, label, color }) => (
            <Button
              key={type}
              size="sm"
              onClick={() => {
                onFeedback(type)
                setIsOpen(false)
              }}
              className={cn("flex items-center gap-2 shadow-lg", color)}
            >
              {FEEDBACK_CONFIGS[type].icon}
              {label}
            </Button>
          ))}
        </div>
      )}

      {/* 主按钮 */}
      <Button
        size="lg"
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          "rounded-full w-12 h-12 shadow-lg",
          isOpen && "rotate-45"
        )}
      >
        <MessageCircle className="w-5 h-5" />
      </Button>
    </div>
  )
}

/**
 * 反馈历史组件
 */
export const FeedbackHistory: React.FC<{
  feedbacks: Array<FeedbackData & { status: FeedbackStatus }>
  className?: string
}> = ({ feedbacks, className }) => {
  const getStatusIcon = (status: FeedbackStatus) => {
    switch (status) {
      case 'pending':
        return <Clock className="w-4 h-4 text-yellow-500" />
      case 'in_progress':
        return <AlertTriangle className="w-4 h-4 text-blue-500" />
      case 'resolved':
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case 'closed':
        return <AlertTriangle className="w-4 h-4 text-gray-500" />
    }
  }

  const getStatusText = (status: FeedbackStatus) => {
    switch (status) {
      case 'pending':
        return '待处理'
      case 'in_progress':
        return '处理中'
      case 'resolved':
        return '已解决'
      case 'closed':
        return '已关闭'
    }
  }

  return (
    <div className={cn("space-y-4", className)}>
      {feedbacks.map((feedback) => (
        <Card key={feedback.id} className="p-4">
          <div className="flex items-start justify-between">
            <div className="flex items-start gap-3 flex-1">
              <div className="flex-shrink-0 mt-1">
                {getStatusIcon(feedback.status)}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <h4 className="font-semibold text-foreground truncate">
                    {feedback.title}
                  </h4>
                  <span className={cn(
                    "text-xs px-2 py-1 rounded",
                    FEEDBACK_CONFIGS[feedback.type].bgColor,
                    FEEDBACK_CONFIGS[feedback.type].color
                  )}>
                    {FEEDBACK_CONFIGS[feedback.type].title}
                  </span>
                </div>
                <p className="text-sm text-muted-foreground mb-2 line-clamp-2">
                  {feedback.description}
                </p>
                <div className="flex items-center gap-4 text-xs text-muted-foreground">
                  <span>{getStatusText(feedback.status)}</span>
                  <span>{new Date(feedback.timestamp).toLocaleDateString()}</span>
                </div>
              </div>
            </div>
          </div>
        </Card>
      ))}
      
      {feedbacks.length === 0 && (
        <div className="text-center py-8 text-muted-foreground">
          <MessageCircle className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>暂无反馈记录</p>
        </div>
      )}
    </div>
  )
}

/**
 * 用户支持中心组件
 */
export const SupportCenter: React.FC<{
  channels: SupportChannel[]
  onSubmitFeedback: (data: FeedbackData) => Promise<void>
  feedbackHistory?: Array<FeedbackData & { status: FeedbackStatus }>
  className?: string
}> = ({ channels, onSubmitFeedback, feedbackHistory = [], className }) => {
  const [activeTab, setActiveTab] = useState<'feedback' | 'channels' | 'history'>('feedback')
  const [selectedFeedbackType, setSelectedFeedbackType] = useState<FeedbackType>('bug')

  return (
    <div className={cn("w-full max-w-4xl mx-auto space-y-6", className)}>
      {/* 标签页 */}
      <div className="flex gap-2 border-b">
        {[
          { id: 'feedback', label: '提交反馈', icon: <MessageCircle className="w-4 h-4" /> },
          { id: 'channels', label: '联系方式', icon: <Phone className="w-4 h-4" /> },
          { id: 'history', label: '反馈历史', icon: <Clock className="w-4 h-4" /> }
        ].map((tab) => (
          <Button
            key={tab.id}
            variant={activeTab === tab.id ? 'default' : 'ghost'}
            onClick={() => setActiveTab(tab.id as any)}
            className="flex items-center gap-2"
          >
            {tab.icon}
            {tab.label}
          </Button>
        ))}
      </div>

      {/* 内容区域 */}
      <div>
        {activeTab === 'feedback' && (
          <div className="space-y-4">
            {/* 反馈类型选择 */}
            <div className="flex gap-2 flex-wrap">
              {Object.entries(FEEDBACK_CONFIGS).map(([type, config]) => (
                <Button
                  key={type}
                  variant={selectedFeedbackType === type ? 'default' : 'outline'}
                  onClick={() => setSelectedFeedbackType(type as FeedbackType)}
                  className="flex items-center gap-2"
                >
                  {config.icon}
                  {config.title}
                </Button>
              ))}
            </div>

            {/* 反馈表单 */}
            <FeedbackForm
              type={selectedFeedbackType}
              onSubmit={onSubmitFeedback}
            />
          </div>
        )}

        {activeTab === 'channels' && (
          <div>
            <h3 className="text-lg font-semibold mb-4">联系我们</h3>
            <SupportChannels channels={channels} />
          </div>
        )}

        {activeTab === 'history' && (
          <div>
            <h3 className="text-lg font-semibold mb-4">反馈历史</h3>
            <FeedbackHistory feedbacks={feedbackHistory} />
          </div>
        )}
      </div>
    </div>
  )
}

/**
 * 错误反馈Hook
 */
export const useErrorFeedback = () => {
  const [feedbackQueue, setFeedbackQueue] = useState<FeedbackData[]>([])

  const submitFeedback = useCallback(async (data: FeedbackData) => {
    try {
      // 这里可以调用API提交反馈
      console.log('Submitting feedback:', data)
      
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      // 添加到队列（实际应用中可能不需要）
      setFeedbackQueue(prev => [...prev, data])
      
      return Promise.resolve()
    } catch (error) {
      console.error('Failed to submit feedback:', error)
      throw error
    }
  }, [])

  const reportError = useCallback((error: Error, context?: string) => {
    const errorData: FeedbackData = {
      id: `error-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      type: 'bug',
      severity: 'high',
      title: `应用程序错误: ${error.name}`,
      description: `${error.message}\n\n上下文: ${context || '无'}\n\n堆栈跟踪:\n${error.stack}`,
      userAgent: navigator.userAgent,
      url: window.location.href,
      timestamp: Date.now(),
      metadata: {
        errorType: error.name,
        context,
        automatic: true
      }
    }

    // 自动提交错误报告
    submitFeedback(errorData).catch(console.error)
  }, [submitFeedback])

  return {
    submitFeedback,
    reportError,
    feedbackQueue
  }
}
