import React, { useState, useEffect } from 'react'
import { useAgentTasks, AgentTask } from '../../hooks/useAgentTasks'

interface CreateTaskModalProps {
  isOpen: boolean
  onClose: () => void
  onCreated?: (task: AgentTask) => void
}

type TaskType = 'price_alert' | 'risk_monitor' | 'news_brief'

interface TaskTypeOption {
  id: TaskType
  label: string
  description: string
  icon: React.ReactNode
  color: string
}

const TASK_TYPES: TaskTypeOption[] = [
  {
    id: 'price_alert',
    label: '价格预警',
    description: '监控代币价格并在达到目标时通知',
    color: 'text-yellow-600 bg-yellow-50 border-yellow-200',
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
      </svg>
    )
  },
  {
    id: 'risk_monitor',
    label: '风险监控',
    description: '持续扫描代币合约风险和异常交易',
    color: 'text-red-600 bg-red-50 border-red-200',
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
      </svg>
    )
  },
  {
    id: 'news_brief',
    label: '新闻速报',
    description: '聚合特定赛道或项目的最新关键新闻',
    color: 'text-blue-600 bg-blue-50 border-blue-200',
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" />
      </svg>
    )
  }
]

const CreateTaskModal: React.FC<CreateTaskModalProps> = ({ isOpen, onClose, onCreated }) => {
  const { createTask } = useAgentTasks()
  
  // Base State
  const [selectedType, setSelectedType] = useState<TaskType>('price_alert')
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Type Specific State
  // Price Alert
  const [paToken, setPaToken] = useState('')
  const [paCondition, setPaCondition] = useState<'above' | 'below'>('above')
  const [paPrice, setPaPrice] = useState('')

  // Risk Monitor
  const [rmToken, setRmToken] = useState('')
  const [rmThreshold, setRmThreshold] = useState(50)
  const [rmMonitorRedFlags, setRmMonitorRedFlags] = useState(true)

  // News Brief
  const [nbIncludeWatchlist, setNbIncludeWatchlist] = useState(false)
  const [nbFrequency, setNbFrequency] = useState<'hourly' | 'daily'>('daily')
  const [nbLanguage, setNbLanguage] = useState<'zh' | 'en'>('zh')
  const [nbMaxArticles, setNbMaxArticles] = useState(5)

  // Reset form when modal opens/closes
  useEffect(() => {
    if (isOpen) {
      setError(null)
      setName('')
      setDescription('')
      // Reset other fields if needed, or keep last state
    }
  }, [isOpen])

  if (!isOpen) return null

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    
    if (!name.trim()) {
      setError('请输入任务名称')
      return
    }

    setIsSubmitting(true)

    try {
      let config: Record<string, unknown> = {}
      let schedule = undefined

      switch (selectedType) {
        case 'price_alert':
          if (!paToken || !paPrice) {
            throw new Error('请完善价格预警配置')
          }
          config = {
            token: paToken,
            condition: paCondition,
            target_price: parseFloat(paPrice)
          }
          break
        case 'risk_monitor':
          if (!rmToken) {
            throw new Error('请输入要监控的代币')
          }
          config = {
            token: rmToken,
            alert_threshold: rmThreshold,
            monitor_red_flags: rmMonitorRedFlags
          }
          schedule = '0 * * * *' // Hourly default for risk monitor
          break
        case 'news_brief':
          config = {
            include_watchlist: nbIncludeWatchlist,
            language: nbLanguage,
            max_articles: nbMaxArticles
          }
          schedule = nbFrequency === 'hourly' ? '0 * * * *' : '0 8 * * *' // Hourly or Daily at 8am
          break
      }

      const newTask = await createTask({
        name,
        description,
        type: selectedType,
        config,
        schedule
      })

      if (newTask) {
        onCreated?.(newTask)
        onClose()
      } else {
        // Error is usually handled by hook but we can fallback
        setError('创建任务失败，请重试')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '发生未知错误')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto" aria-labelledby="modal-title" role="dialog" aria-modal="true">
      {/* Backdrop */}
      <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div 
          className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity backdrop-blur-sm" 
          aria-hidden="true"
          onClick={onClose}
        ></div>

        {/* Center Trick */}
        <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>

        {/* Modal Panel */}
        <div className="relative inline-block align-bottom bg-white rounded-xl text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-2xl w-full">
          <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
            <div className="flex justify-between items-center mb-5">
              <h3 className="text-xl font-bold text-gray-900" id="modal-title">
                新建智能体任务
              </h3>
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-gray-500 transition-colors"
              >
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Task Type Selector */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">任务类型</label>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  {TASK_TYPES.map((type) => (
                    <button
                      key={type.id}
                      type="button"
                      onClick={() => setSelectedType(type.id)}
                      className={`relative flex flex-col items-center p-4 border rounded-xl transition-all ${
                        selectedType === type.id
                          ? `ring-2 ring-offset-2 ring-blue-500 ${type.color}`
                          : 'border-gray-200 hover:bg-gray-50 text-gray-600'
                      }`}
                    >
                      <div className={`mb-2 ${selectedType !== type.id ? 'text-gray-400' : ''}`}>
                        {type.icon}
                      </div>
                      <span className="text-sm font-bold">{type.label}</span>
                    </button>
                  ))}
                </div>
                {/* Type Description */}
                <p className="mt-2 text-sm text-gray-500 text-center">
                  {TASK_TYPES.find(t => t.id === selectedType)?.description}
                </p>
              </div>

              {/* Basic Info */}
              <div className="space-y-4">
                <div>
                  <label htmlFor="task-name" className="block text-sm font-medium text-gray-700 mb-1">
                    任务名称 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    id="task-name"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm py-2 px-3 border"
                    placeholder="例如：BTC 价格监控"
                    required
                  />
                </div>
                <div>
                  <label htmlFor="task-desc" className="block text-sm font-medium text-gray-700 mb-1">
                    描述 (可选)
                  </label>
                  <textarea
                    id="task-desc"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    rows={2}
                    className="w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm py-2 px-3 border"
                    placeholder="简要描述这个任务的目标..."
                  />
                </div>
              </div>

              {/* Dynamic Config Area */}
              <div className="border-t border-gray-100 pt-5">
                <h4 className="text-sm font-medium text-gray-900 mb-4 flex items-center gap-2">
                  <span className="w-1 h-4 bg-blue-600 rounded-full"></span>
                  详细配置
                </h4>
                
                {/* Price Alert Config */}
                {selectedType === 'price_alert' && (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="sm:col-span-2">
                      <label className="block text-sm font-medium text-gray-700 mb-1">监控代币</label>
                      <input
                        type="text"
                        value={paToken}
                        onChange={(e) => setPaToken(e.target.value.toUpperCase())}
                        className="w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm py-2 px-3 border"
                        placeholder="例如: BTC, ETH"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">触发条件</label>
                      <select
                        value={paCondition}
                        onChange={(e) => setPaCondition(e.target.value as 'above' | 'below')}
                        className="w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm py-2 px-3 border"
                      >
                        <option value="above">价格高于 (&gt;)</option>
                        <option value="below">价格低于 (&lt;)</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">目标价格 (USD)</label>
                      <input
                        type="number"
                        step="0.000001"
                        value={paPrice}
                        onChange={(e) => setPaPrice(e.target.value)}
                        className="w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm py-2 px-3 border"
                        placeholder="0.00"
                      />
                    </div>
                  </div>
                )}

                {/* Risk Monitor Config */}
                {selectedType === 'risk_monitor' && (
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">监控代币</label>
                      <input
                        type="text"
                        value={rmToken}
                        onChange={(e) => setRmToken(e.target.value.toUpperCase())}
                        className="w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm py-2 px-3 border"
                        placeholder="例如: PEPE"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        风险评分阈值 ({rmThreshold})
                      </label>
                      <input
                        type="range"
                        min="0"
                        max="100"
                        value={rmThreshold}
                        onChange={(e) => setRmThreshold(parseInt(e.target.value))}
                        className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                      />
                      <p className="text-xs text-gray-500 mt-1">当风险评分超过此值时报警</p>
                    </div>
                    <div className="flex items-center">
                      <input
                        id="monitor-red-flags"
                        type="checkbox"
                        checked={rmMonitorRedFlags}
                        onChange={(e) => setRmMonitorRedFlags(e.target.checked)}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                      <label htmlFor="monitor-red-flags" className="ml-2 block text-sm text-gray-900">
                        包含红旗指标 (Red Flags) 监控
                      </label>
                    </div>
                  </div>
                )}

                {/* News Brief Config */}
                {selectedType === 'news_brief' && (
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">推送频率</label>
                        <select
                          value={nbFrequency}
                          onChange={(e) => setNbFrequency(e.target.value as 'hourly' | 'daily')}
                          className="w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm py-2 px-3 border"
                        >
                          <option value="daily">每天早报 (08:00)</option>
                          <option value="hourly">每小时更新</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">语言</label>
                        <select
                          value={nbLanguage}
                          onChange={(e) => setNbLanguage(e.target.value as 'zh' | 'en')}
                          className="w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm py-2 px-3 border"
                        >
                          <option value="zh">中文</option>
                          <option value="en">English</option>
                        </select>
                      </div>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">最大新闻条数 ({nbMaxArticles})</label>
                      <input
                        type="number"
                        min="3"
                        max="10"
                        value={nbMaxArticles}
                        onChange={(e) => setNbMaxArticles(parseInt(e.target.value))}
                        className="w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm py-2 px-3 border"
                      />
                    </div>
                    <div className="flex items-center">
                      <input
                        id="include-watchlist"
                        type="checkbox"
                        checked={nbIncludeWatchlist}
                        onChange={(e) => setNbIncludeWatchlist(e.target.checked)}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                      <label htmlFor="include-watchlist" className="ml-2 block text-sm text-gray-900">
                        仅包含我的关注列表 (Watchlist) 中的代币
                      </label>
                    </div>
                  </div>
                )}
              </div>

              {/* Error Message */}
              {error && (
                <div className="rounded-md bg-red-50 p-4">
                  <div className="flex">
                    <div className="flex-shrink-0">
                      <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <div className="ml-3">
                      <h3 className="text-sm font-medium text-red-800">创建失败</h3>
                      <div className="mt-2 text-sm text-red-700">
                        <p>{error}</p>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Footer Buttons */}
              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-lg text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  取消
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="inline-flex justify-center items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-lg text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isSubmitting ? (
                    <>
                      <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      创建中...
                    </>
                  ) : (
                    '立即创建'
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  )
}

export default CreateTaskModal