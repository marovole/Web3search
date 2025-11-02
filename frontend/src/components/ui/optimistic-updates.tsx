import React, { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { EnhancedProgress, useOptimisticUpdate, useTaskProgress } from '@/components/ui/progress'
import { Loading, useSimpleLoading } from '@/components/ui/loading'
import { cn } from '@/lib/utils'
import { Send, RefreshCw, Check, AlertCircle } from 'lucide-react'

/**
 * 乐观更新消息组件
 */
interface OptimisticMessage {
  id: string
  content: string
  timestamp: Date
  isOptimistic?: boolean
  status?: 'sending' | 'sent' | 'error'
}

interface OptimisticChatProps {
  className?: string
  onSendMessage: (message: string) => Promise<void>
}

export const OptimisticChat: React.FC<OptimisticChatProps> = ({
  className,
  onSendMessage
}) => {
  const [messages, setMessages] = useState<OptimisticMessage[]>([])
  const [inputValue, setInputValue] = useState('')
  
  const { 
    start: startSending, 
    stop: stopSending, 
    isLoading: isSending, 
    update: updateSending 
  } = useSimpleLoading('chat-sending')

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isSending) return

    const tempId = `temp-${Date.now()}`
    const optimisticMessage: OptimisticMessage = {
      id: tempId,
      content: inputValue,
      timestamp: new Date(),
      isOptimistic: true,
      status: 'sending'
    }

    // 乐观更新：立即显示消息
    setMessages(prev => [...prev, optimisticMessage])
    setInputValue('')
    startSending()

    try {
      // 模拟发送延迟
      await new Promise(resolve => setTimeout(resolve, 1500))
      await onSendMessage(inputValue)

      // 更新消息状态为已发送
      setMessages(prev => prev.map(msg => 
        msg.id === tempId 
          ? { ...msg, isOptimistic: false, status: 'sent' }
          : msg
      ))

      stopSending()
    } catch (error) {
      // 标记消息发送失败
      setMessages(prev => prev.map(msg => 
        msg.id === tempId 
          ? { ...msg, status: 'error' }
          : msg
      ))
      stopSending()
    }
  }

  const handleRetryMessage = async (messageId: string) => {
    const message = messages.find(msg => msg.id === messageId)
    if (!message) return

    setMessages(prev => prev.map(msg => 
      msg.id === messageId 
        ? { ...msg, status: 'sending' }
        : msg
    ))

    try {
      await onSendMessage(message.content)
      setMessages(prev => prev.map(msg => 
        msg.id === messageId 
          ? { ...msg, isOptimistic: false, status: 'sent' }
          : msg
      ))
    } catch (error) {
      setMessages(prev => prev.map(msg => 
        msg.id === messageId 
          ? { ...msg, status: 'error' }
          : msg
      ))
    }
  }

  const getMessageIcon = (status?: string) => {
    switch (status) {
      case 'sending':
        return <RefreshCw className="w-3 h-3 animate-spin" />
      case 'sent':
        return <Check className="w-3 h-3 text-green-500" />
      case 'error':
        return <AlertCircle className="w-3 h-3 text-red-500" />
      default:
        return null
    }
  }

  return (
    <div className={cn("flex flex-col h-full", className)}>
      {/* 消息列表 */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={cn(
              "flex gap-3 max-w-[80%] animate-fade-in",
              "ml-auto" // 用户消息右对齐
            )}
          >
            <div className="flex-1 space-y-2">
              <div className={cn(
                "rounded-lg p-3 relative",
                message.isOptimistic && "opacity-70",
                message.status === 'error' && "bg-red-50 border border-red-200",
                "bg-primary text-primary-foreground"
              )}>
                <p className="text-sm">{message.content}</p>
                {getMessageIcon(message.status)}
              </div>
              
              {message.status === 'error' && (
                <div className="flex items-center gap-2">
                  <span className="text-xs text-red-500">发送失败</span>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => handleRetryMessage(message.id)}
                    className="h-6 px-2 text-xs"
                  >
                    重试
                  </Button>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* 输入区域 */}
      <div className="border-t p-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
            placeholder="输入消息..."
            className="flex-1 px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
            disabled={isSending}
          />
          <Button
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || isSending}
            size="sm"
          >
            {isSending ? (
              <Loading size="sm" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </Button>
        </div>
      </div>
    </div>
  )
}

/**
 * 任务进度演示组件
 */
export const TaskProgressDemo: React.FC = () => {
  const taskProgress = useTaskProgress('demo-task')

  const runDemoTask = async () => {
    taskProgress.startTask('正在处理数据...')
    
    // 模拟任务步骤
    const steps = [
      { progress: 25, message: '正在分析数据...' },
      { progress: 50, message: '正在生成报告...' },
      { progress: 75, message: '正在优化结果...' },
      { progress: 100, message: '任务完成！' }
    ]

    for (const step of steps) {
      await new Promise(resolve => setTimeout(resolve, 1000))
      taskProgress.updateProgress(step.progress, step.message)
    }

    taskProgress.completeTask('所有任务已完成')
  }

  return (
    <Card className="p-6 space-y-4">
      <h3 className="text-lg font-semibold">任务进度演示</h3>
      
      <EnhancedProgress
        value={taskProgress.progress}
        showLabel
        variant={taskProgress.status === 'error' ? 'error' : 
                taskProgress.status === 'completed' ? 'success' : 'default'}
      />

      <div className="flex items-center justify-between">
        <span className="text-sm text-muted-foreground">
          {taskProgress.message}
        </span>
        <span className="text-sm font-medium">
          {taskProgress.status === 'running' && '进行中'}
          {taskProgress.status === 'completed' && '已完成'}
          {taskProgress.status === 'error' && '出错'}
          {taskProgress.status === 'idle' && '待开始'}
        </span>
      </div>

      <div className="flex gap-2">
        <Button
          onClick={runDemoTask}
          disabled={taskProgress.status === 'running'}
          size="sm"
        >
          {taskProgress.status === 'running' ? (
            <>
              <Loading size="sm" />
              运行中...
            </>
          ) : (
            '开始任务'
          )}
        </Button>
        
        {taskProgress.status !== 'idle' && (
          <Button
            onClick={taskProgress.reset}
            variant="outline"
            size="sm"
          >
            重置
          </Button>
        )}
      </div>

      {taskProgress.error && (
        <div className="text-sm text-red-500 bg-red-50 p-3 rounded">
          错误: {taskProgress.error}
        </div>
      )}
    </Card>
  )
}

/**
 * 乐观更新表单演示
 */
export const OptimisticFormDemo: React.FC = () => {
  const [formData, setFormData] = useState({ name: '', email: '' })
  
  const {
    value: optimisticData,
    actualValue,
    update,
    reset,
    isUpdating,
    error
  } = useOptimisticUpdate(formData, async (newData) => {
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    // 模拟随机失败
    if (Math.random() < 0.3) {
      throw new Error('保存失败，请重试')
    }
    
    return newData
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    try {
      await update(formData)
      console.log('保存成功')
    } catch (error) {
      console.error('保存失败:', error)
    }
  }

  const handleInputChange = (field: 'name' | 'email', value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  return (
    <Card className="p-6 space-y-4">
      <h3 className="text-lg font-semibold">乐观更新表单</h3>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1">姓名</label>
          <input
            type="text"
            value={formData.name}
            onChange={(e) => handleInputChange('name', e.target.value)}
            className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
            disabled={isUpdating}
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">邮箱</label>
          <input
            type="email"
            value={formData.email}
            onChange={(e) => handleInputChange('email', e.target.value)}
            className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
            disabled={isUpdating}
          />
        </div>

        <div className="flex gap-2">
          <Button
            type="submit"
            disabled={isUpdating || !formData.name || !formData.email}
          >
            {isUpdating ? (
              <>
                <Loading size="sm" />
                保存中...
              </>
            ) : (
              '保存'
            )}
          </Button>
          
          {optimisticData !== actualValue && (
            <Button
              type="button"
              onClick={reset}
              variant="outline"
            >
              撤销
            </Button>
          )}
        </div>
      </form>

      {/* 状态显示 */}
      <div className="text-xs space-y-1 bg-muted p-3 rounded">
        <div>实际数据: {JSON.stringify(actualValue)}</div>
        <div>乐观数据: {JSON.stringify(optimisticData)}</div>
        <div>更新状态: {isUpdating ? '更新中' : '空闲'}</div>
      </div>

      {error && (
        <div className="text-sm text-red-500 bg-red-50 p-3 rounded">
          错误: {error.message}
        </div>
      )}
    </Card>
  )
}
