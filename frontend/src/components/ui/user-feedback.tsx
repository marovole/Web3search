import React, { useState, useEffect, useCallback, useRef } from 'react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import { Input } from '@/components/ui/input'
import { 
  MessageSquare, 
  Send, 
  ThumbsUp, 
  ThumbsDown, 
  Star, 
  Flag,
  Lightbulb,
  Bug,
  Heart,
  Award,
  TrendingUp,
  Calendar,
  Filter,
  Search,
  Download,
  ExternalLink,
  Eye,
  MessageCircle,
  CheckCircle,
  Clock,
  AlertTriangle
} from 'lucide-react'

/**
 * 反馈类型
 */
export type FeedbackType = 
  | 'bug_report'
  | 'feature_request'
  | 'improvement'
  | 'compliment'
  | 'complaint'
  | 'question'
  | 'usability'

/**
 * 反馈状态
 */
export type FeedbackStatus = 'pending' | 'in_review' | 'in_progress' | 'resolved' | 'closed'

/**
 * 反馈优先级
 */
export type FeedbackPriority = 'low' | 'medium' | 'high' | 'urgent'

/**
 * 反馈数据接口
 */
export interface UserFeedback {
  id: string
  type: FeedbackType
  title: string
  description: string
  category?: string
  priority: FeedbackPriority
  status: FeedbackStatus
  rating?: number // 1-5 星评分
  tags: string[]
  attachments?: Array<{
    name: string
    url: string
    type: string
    size: number
  }>
  userAgent: string
  url: string
  userId?: string
  timestamp: number
  metadata?: {
    browser?: string
    os?: string
    screen?: string
    sessionId?: string
    referrer?: string
  }
  response?: {
    message: string
    respondedBy?: string
    respondedAt?: number
    resolvedAt?: number
  }
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
  allowRating: boolean
}> = {
  bug_report: {
    icon: <Bug className="w-5 h-5" />,
    color: 'text-red-600',
    bgColor: 'bg-red-50',
    title: '错误报告',
    placeholder: '请详细描述遇到的问题...',
    questions: [
      '问题发生的具体步骤',
      '期望的行为 vs 实际行为',
      '错误信息或截图',
      '复现频率'
    ],
    allowRating: false
  },
  feature_request: {
    icon: <Lightbulb className="w-5 h-5" />,
    color: 'text-green-600',
    bgColor: 'bg-green-50',
    title: '功能建议',
    placeholder: '请描述您希望添加的功能...',
    questions: [
      '功能用途和价值',
      '期望的使用方式',
      '对现有功能的影响'
    ],
    allowRating: true
  },
  improvement: {
    icon: <TrendingUp className="w-5 h-5" />,
    color: 'text-blue-600',
    bgColor: 'bg-blue-50',
    title: '改进建议',
    placeholder: '请提出您的改进建议...',
    questions: [
      '当前存在的问题',
      '具体的改进方案',
      '预期的效果'
    ],
    allowRating: true
  },
  compliment: {
    icon: <Heart className="w-5 h-5" />,
    color: 'text-pink-600',
    bgColor: 'bg-pink-50',
    title: '表扬反馈',
    placeholder: '请分享您的使用体验...',
    questions: [
      '满意的方面',
      '具体的使用场景',
      '推荐给他人的理由'
    ],
    allowRating: true
  },
  complaint: {
    icon: <AlertTriangle className="w-5 h-5" />,
    color: 'text-orange-600',
    bgColor: 'bg-orange-50',
    title: '投诉反馈',
    placeholder: '请详细描述投诉内容...',
    questions: [
      '投诉的具体问题',
      '影响程度',
      '期望的解决方案'
    ],
    allowRating: false
  },
  question: {
    icon: <MessageCircle className="w-5 h-5" />,
    color: 'text-purple-600',
    bgColor: 'bg-purple-50',
    title: '使用咨询',
    placeholder: '请描述您的问题...',
    questions: [
      '具体的问题描述',
      '相关的使用场景',
      '已尝试的解决方法'
    ],
    allowRating: true
  },
  usability: {
    icon: <Eye className="w-5 h-5" />,
    color: 'text-indigo-600',
    bgColor: 'bg-indigo-50',
    title: '可用性反馈',
    placeholder: '请分享您的使用体验...',
    questions: [
      '界面操作的便利性',
      '功能的易用性',
      '学习成本和难度'
    ],
    allowRating: true
  }
}

/**
 * 用户反馈系统Hook
 */
export const useFeedbackSystem = () => {
  const [feedbacks, setFeedbacks] = useState<UserFeedback[]>([])
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [lastSubmitted, setLastSubmitted] = useState<UserFeedback | null>(null)

  // 从存储中加载反馈历史
  useEffect(() => {
    try {
      const saved = localStorage.getItem('user_feedback_history')
      if (saved) {
        const data = JSON.parse(saved)
        setFeedbacks(data.map((item: any) => ({
          ...item,
          timestamp: new Date(item.timestamp).getTime()
        })))
      }
    } catch (error) {
      console.warn('Failed to load feedback history:', error)
    }
  }, [])

  const saveFeedbackHistory = useCallback((newFeedbacks: UserFeedback[]) => {
    try {
      localStorage.setItem('user_feedback_history', JSON.stringify(newFeedbacks))
    } catch (error) {
      console.warn('Failed to save feedback history:', error)
    }
  }, [])

  const submitFeedback = useCallback(async (feedback: Omit<UserFeedback, 'id' | 'timestamp'>) => {
    setIsSubmitting(true)

    try {
      const newFeedback: UserFeedback = {
        ...feedback,
        id: `feedback-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        timestamp: Date.now(),
        metadata: {
          browser: navigator.userAgent,
          os: navigator.platform,
          screen: `${window.screen.width}x${window.screen.height}`,
          sessionId: sessionStorage.getItem('session_id') || 'unknown',
          referrer: document.referrer
        }
      }

      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 1000))

      // 更新本地状态
      const updatedFeedbacks = [newFeedback, ...feedbacks]
      setFeedbacks(updatedFeedbacks)
      saveFeedbackHistory(updatedFeedbacks)
      setLastSubmitted(newFeedback)

      return newFeedback
    } catch (error) {
      console.error('Failed to submit feedback:', error)
      throw error
    } finally {
      setIsSubmitting(false)
    }
  }, [feedbacks, saveFeedbackHistory])

  const getFeedbackStats = useCallback(() => {
    const total = feedbacks.length
    const byType = feedbacks.reduce((acc, feedback) => {
      acc[feedback.type] = (acc[feedback.type] || 0) + 1
      return acc
    }, {} as Record<string, number>)
    
    const byStatus = feedbacks.reduce((acc, feedback) => {
      acc[feedback.status] = (acc[feedback.status] || 0) + 1
      return acc
    }, {} as Record<string, number>)

    const avgRating = feedbacks
      .filter(f => f.rating)
      .reduce((sum, f) => sum + (f.rating || 0), 0) / 
      feedbacks.filter(f => f.rating).length || 0

    return { total, byType, byStatus, avgRating }
  }, [feedbacks])

  const getRecentFeedbacks = useCallback((limit: number = 5) => {
    return feedbacks
      .sort((a, b) => b.timestamp - a.timestamp)
      .slice(0, limit)
  }, [feedbacks])

  return {
    feedbacks,
    isSubmitting,
    lastSubmitted,
    submitFeedback,
    getFeedbackStats,
    getRecentFeedbacks
  }
}

/**
 * 反馈表单组件
 */
export const FeedbackForm: React.FC<{
  type: FeedbackType
  onSubmit: (feedback: UserFeedback) => Promise<void>
  onCancel?: () => void
  className?: string
  allowAnonymous?: boolean
  showRating?: boolean
}> = ({ 
  type, 
  onSubmit, 
  onCancel, 
  className,
  allowAnonymous = true,
  showRating = true 
}) => {
  const config = FEEDBACK_CONFIGS[type]
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    category: '',
    priority: 'medium' as FeedbackPriority,
    rating: 0,
    tags: [] as string[],
    email: ''
  })
  const [attachments, setAttachments] = useState<File[]>([])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!formData.title.trim() || !formData.description.trim()) {
      return
    }

    setIsSubmitting(true)

    try {
      const feedback: UserFeedback = {
        id: '', // 将在submitFeedback中生成
        type,
        title: formData.title,
        description: formData.description,
        category: formData.category || undefined,
        priority: formData.priority,
        status: 'pending',
        rating: showRating && config.allowRating ? formData.rating : undefined,
        tags: formData.tags,
        attachments: attachments.map(file => ({
          name: file.name,
          url: URL.createObjectURL(file), // 实际应用中应该上传到服务器
          type: file.type,
          size: file.size
        })),
        userAgent: navigator.userAgent,
        url: window.location.href,
        timestamp: Date.now(),
        metadata: {
          browser: navigator.userAgent,
          os: navigator.platform,
          screen: `${window.screen.width}x${window.screen.height}`
        }
      }

      await onSubmit(feedback)
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

  const handleRating = (rating: number) => {
    setFormData(prev => ({ ...prev, rating }))
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
            感谢您的反馈，我们会认真处理并尽快回复您。
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

        {/* 评分 */}
        {showRating && config.allowRating && (
          <div>
            <label className="block text-sm font-medium mb-2">
              满意度评分
            </label>
            <div className="flex gap-2">
              {[1, 2, 3, 4, 5].map((star) => (
                <Button
                  key={star}
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => handleRating(star)}
                  className="p-1"
                >
                  <Star className={cn(
                    "w-5 h-5",
                    star <= formData.rating ? "fill-yellow-400 text-yellow-400" : "text-gray-300"
                  )} />
                </Button>
              ))}
            </div>
          </div>
        )}

        {/* 优先级 */}
        <div>
          <label className="block text-sm font-medium mb-2">
            优先级
          </label>
          <div className="flex gap-2">
            {(['low', 'medium', 'high', 'urgent'] as FeedbackPriority[]).map((priority) => (
              <Button
                key={priority}
                type="button"
                variant={formData.priority === priority ? 'default' : 'outline'}
                size="sm"
                onClick={() => setFormData(prev => ({ ...prev, priority }))}
              >
                {priority === 'low' && '低'}
                {priority === 'medium' && '中'}
                {priority === 'high' && '高'}
                {priority === 'urgent' && '紧急'}
              </Button>
            ))}
          </div>
        </div>

        {/* 邮箱 */}
        {allowAnonymous && (
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
        <div>
          <label className="block text-sm font-medium mb-2">
            附件（可选）
          </label>
          <input
            type="file"
            multiple
            accept="image/*,.pdf,.doc,.docx,.txt,.log"
            onChange={handleFileChange}
            className="block w-full text-sm text-muted-foreground file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-primary file:text-primary-foreground hover:file:bg-primary/80"
          />
          
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
 * 快速反馈按钮组件
 */
export const QuickFeedbackButton: React.FC<{
  onFeedback: (type: FeedbackType) => void
  className?: string
  position?: 'bottom-right' | 'bottom-left'
}> = ({ onFeedback, className, position = 'bottom-right' }) => {
  const [isOpen, setIsOpen] = useState(false)

  const positionClasses = {
    'bottom-right': 'bottom-4 right-4',
    'bottom-left': 'bottom-4 left-4'
  }

  const feedbackTypes: Array<{ type: FeedbackType; label: string; color: string }> = [
    { type: 'bug_report', label: '错误', color: 'bg-red-500' },
    { type: 'feature_request', label: '建议', color: 'bg-green-500' },
    { type: 'question', label: '咨询', color: 'bg-blue-500' },
    { type: 'compliment', label: '表扬', color: 'bg-pink-500' }
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
        <MessageSquare className="w-5 h-5" />
      </Button>
    </div>
  )
}

/**
 * 反馈历史组件
 */
export const FeedbackHistory: React.FC<{
  feedbacks: UserFeedback[]
  className?: string
}> = ({ feedbacks, className }) => {
  const [filter, setFilter] = useState<{
    type?: FeedbackType
    status?: FeedbackStatus
    search: string
  }>({
    search: ''
  })

  const filteredFeedbacks = feedbacks.filter(feedback => {
    if (filter.type && feedback.type !== filter.type) return false
    if (filter.status && feedback.status !== filter.status) return false
    if (filter.search) {
      const searchLower = filter.search.toLowerCase()
      return feedback.title.toLowerCase().includes(searchLower) ||
             feedback.description.toLowerCase().includes(searchLower)
    }
    return true
  })

  const getStatusIcon = (status: FeedbackStatus) => {
    switch (status) {
      case 'pending':
        return <Clock className="w-4 h-4 text-yellow-500" />
      case 'in_review':
        return <Eye className="w-4 h-4 text-blue-500" />
      case 'in_progress':
        return <AlertTriangle className="w-4 h-4 text-orange-500" />
      case 'resolved':
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case 'closed':
        return <MessageCircle className="w-4 h-4 text-gray-500" />
    }
  }

  const getStatusText = (status: FeedbackStatus) => {
    switch (status) {
      case 'pending': return '待处理'
      case 'in_review': return '审核中'
      case 'in_progress': return '处理中'
      case 'resolved': return '已解决'
      case 'closed': return '已关闭'
    }
  }

  return (
    <div className={cn("space-y-4", className)}>
      {/* 筛选器 */}
      <Card className="p-4">
        <div className="flex gap-4 items-center">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="搜索反馈..."
              value={filter.search}
              onChange={(e) => setFilter(prev => ({ ...prev, search: e.target.value }))}
              className="pl-10"
            />
          </div>
          
          <select
            value={filter.type || ''}
            onChange={(e) => setFilter(prev => ({ 
              ...prev, 
              type: e.target.value as FeedbackType | undefined 
            }))}
            className="border rounded px-3 py-2 text-sm"
          >
            <option value="">全部类型</option>
            {Object.entries(FEEDBACK_CONFIGS).map(([type, config]) => (
              <option key={type} value={type}>{config.title}</option>
            ))}
          </select>
          
          <select
            value={filter.status || ''}
            onChange={(e) => setFilter(prev => ({ 
              ...prev, 
              status: e.target.value as FeedbackStatus | undefined 
            }))}
            className="border rounded px-3 py-2 text-sm"
          >
            <option value="">全部状态</option>
            <option value="pending">待处理</option>
            <option value="in_review">审核中</option>
            <option value="in_progress">处理中</option>
            <option value="resolved">已解决</option>
            <option value="closed">已关闭</option>
          </select>
        </div>
      </Card>

      {/* 反馈列表 */}
      <div className="space-y-3">
        {filteredFeedbacks.map(feedback => (
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
                    
                    {feedback.rating && (
                      <div className="flex items-center gap-1">
                        {Array.from({ length: 5 }).map((_, i) => (
                          <Star
                            key={i}
                            className={cn(
                              "w-3 h-3",
                              i < feedback.rating ? "fill-yellow-400 text-yellow-400" : "text-gray-300"
                            )}
                          />
                        ))}
                      </div>
                    )}
                  </div>
                  
                  <p className="text-sm text-muted-foreground mb-2 line-clamp-2">
                    {feedback.description}
                  </p>
                  
                  <div className="flex items-center gap-4 text-xs text-muted-foreground">
                    <span>{getStatusText(feedback.status)}</span>
                    <span>{new Date(feedback.timestamp).toLocaleDateString()}</span>
                    {feedback.priority !== 'medium' && (
                      <span className={cn(
                        "px-2 py-1 rounded",
                        feedback.priority === 'urgent' ? "bg-red-100 text-red-700" :
                        feedback.priority === 'high' ? "bg-orange-100 text-orange-700" :
                        "bg-blue-100 text-blue-700"
                      )}>
                        {feedback.priority === 'urgent' && '紧急'}
                        {feedback.priority === 'high' && '高'}
                        {feedback.priority === 'low' && '低'}
                      </span>
                    )}
                  </div>
                  
                  {feedback.response && (
                    <div className="mt-3 p-3 bg-muted rounded text-sm">
                      <div className="font-medium text-foreground mb-1">官方回复</div>
                      <div className="text-muted-foreground">{feedback.response.message}</div>
                      {feedback.response.respondedAt && (
                        <div className="text-xs text-muted-foreground mt-1">
                          {new Date(feedback.response.respondedAt).toLocaleDateString()}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </Card>
        ))}
      </div>

      {filteredFeedbacks.length === 0 && (
        <div className="text-center py-8 text-muted-foreground">
          <MessageSquare className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>暂无反馈记录</p>
        </div>
      )}
    </div>
  )
}

/**
 * 反馈统计组件
 */
export const FeedbackStats: React.FC<{
  feedbacks: UserFeedback[]
  className?: string
}> = ({ feedbacks, className }) => {
  const stats = {
    total: feedbacks.length,
    byType: feedbacks.reduce((acc, feedback) => {
      acc[feedback.type] = (acc[feedback.type] || 0) + 1
      return acc
    }, {} as Record<string, number>),
    byStatus: feedbacks.reduce((acc, feedback) => {
      acc[feedback.status] = (acc[feedback.status] || 0) + 1
      return acc
    }, {} as Record<string, number>),
    avgRating: feedbacks
      .filter(f => f.rating)
      .reduce((sum, f) => sum + (f.rating || 0), 0) / 
      feedbacks.filter(f => f.rating).length || 0,
    resolved: feedbacks.filter(f => f.status === 'resolved').length,
    pending: feedbacks.filter(f => f.status === 'pending').length
  }

  return (
    <div className={cn("grid gap-4 md:grid-cols-2 lg:grid-cols-4", className)}>
      <Card className="p-4 text-center">
        <div className="text-2xl font-bold text-primary">{stats.total}</div>
        <div className="text-sm text-muted-foreground">总反馈数</div>
      </Card>
      
      <Card className="p-4 text-center">
        <div className="text-2xl font-bold text-green-600">{stats.resolved}</div>
        <div className="text-sm text-muted-foreground">已解决</div>
      </Card>
      
      <Card className="p-4 text-center">
        <div className="text-2xl font-bold text-yellow-600">{stats.pending}</div>
        <div className="text-sm text-muted-foreground">待处理</div>
      </Card>
      
      <Card className="p-4 text-center">
        <div className="text-2xl font-bold text-blue-600">
          {stats.avgRating.toFixed(1)}
        </div>
        <div className="text-sm text-muted-foreground">平均评分</div>
      </Card>
    </div>
  )
}
