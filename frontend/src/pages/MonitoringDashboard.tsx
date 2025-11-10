import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  Activity,
  TrendingUp,
  AlertTriangle,
  Users,
  Clock,
  Zap,
  BarChart3,
  RefreshCw,
  Download,
  Settings
} from 'lucide-react'
import { ResponsiveChart, SimpleLineChart, SimpleBarChart, ChartLegend } from '@/components/Charts/ResponsiveChart'
import { useUserPreferences } from '@/contexts/UserPreferencesContext'
import { analytics } from '@/services/analytics'
import performanceMonitor from '@/services/performance'
import { cn } from '@/lib/utils'

// 监控数据类型
interface MonitoringMetrics {
  pageViews: number
  uniqueUsers: number
  averageSessionDuration: number
  bounceRate: number
  errorRate: number
  performanceScore: number
}

// 实时数据接口
interface RealtimeData {
  activeUsers: number
  pageViewsLastHour: number
  topPages: Array<{ path: string; views: number }>
  topReferrers: Array<{ source: string; visits: number }>
  deviceBreakdown: Array<{ device: string; percentage: number }>
}

// 错误统计
interface ErrorStats {
  total: number
  critical: number
  warnings: number
  resolved: number
  recent: Array<{
    message: string
    timestamp: number
    severity: 'low' | 'medium' | 'high' | 'critical'
  }>
}

/**
 * 监控仪表板页面
 */
export default function MonitoringDashboard() {
  const { preferences } = useUserPreferences()
  const [metrics, setMetrics] = useState<MonitoringMetrics>({
    pageViews: 0,
    uniqueUsers: 0,
    averageSessionDuration: 0,
    bounceRate: 0,
    errorRate: 0,
    performanceScore: 0
  })
  const [realtimeData, setRealtimeData] = useState<RealtimeData>({
    activeUsers: 0,
    pageViewsLastHour: 0,
    topPages: [],
    topReferrers: [],
    deviceBreakdown: []
  })
  const [errorStats, setErrorStats] = useState<ErrorStats>({
    total: 0,
    critical: 0,
    warnings: 0,
    resolved: 0,
    recent: []
  })
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date())

  // 模拟数据加载
  const loadMetrics = async () => {
    // 获取性能监控数据
    const monitor = performanceMonitor()
    const performanceMetrics = monitor.getWebVitals()

    setMetrics(prev => ({
      ...prev,
      pageViews: Math.floor(Math.random() * 10000) + 50000,
      uniqueUsers: Math.floor(Math.random() * 1000) + 5000,
      averageSessionDuration: Math.floor(Math.random() * 300) + 120,
      bounceRate: Math.random() * 20 + 30,
      errorRate: Math.random() * 2 + 1,
      performanceScore: monitor.getPerformanceScore()
    }))

    setRealtimeData({
      activeUsers: Math.floor(Math.random() * 50) + 10,
      pageViewsLastHour: Math.floor(Math.random() * 500) + 100,
      topPages: [
        { path: '/', views: 1250 },
        { path: '/chat', views: 980 },
        { path: '/search', views: 750 },
        { path: '/history', views: 520 },
        { path: '/settings', views: 340 }
      ],
      topReferrers: [
        { source: 'Direct', visits: 1450 },
        { source: 'Google', visits: 890 },
        { source: 'Twitter', visits: 340 },
        { source: 'GitHub', visits: 180 }
      ],
      deviceBreakdown: [
        { device: 'Desktop', percentage: 65 },
        { device: 'Mobile', percentage: 30 },
        { device: 'Tablet', percentage: 5 }
      ]
    })

    setErrorStats({
      total: Math.floor(Math.random() * 20) + 5,
      critical: Math.floor(Math.random() * 3),
      warnings: Math.floor(Math.random() * 8) + 2,
      resolved: Math.floor(Math.random() * 15) + 10,
      recent: [
        {
          message: 'Failed to load chat history',
          timestamp: Date.now() - 3600000,
          severity: 'medium'
        },
        {
          message: 'API timeout on search request',
          timestamp: Date.now() - 7200000,
          severity: 'high'
        }
      ]
    })

    setLastUpdate(new Date())
  }

  // 初始化加载
  useEffect(() => {
    loadMetrics()

    // 自动刷新
    let interval: NodeJS.Timeout
    if (autoRefresh) {
      interval = setInterval(loadMetrics, 30000) // 每30秒刷新
    }

    return () => {
      if (interval) clearInterval(interval)
    }
  }, [autoRefresh])

  // 性能数据图表
  const performanceData = [
    { label: 'FCP', value: 1.2 },
    { label: 'LCP', value: 2.1 },
    { label: 'FID', value: 45 },
    { label: 'CLS', value: 0.05 }
  ]

  // 页面浏览量趋势
  const pageViewsData = [
    { label: '00:00', value: 120 },
    { label: '04:00', value: 80 },
    { label: '08:00', value: 200 },
    { label: '12:00', value: 350 },
    { label: '16:00', value: 420 },
    { label: '20:00', value: 380 }
  ]

  // 图例配置
  const deviceLegend = [
    { label: 'Desktop', color: '#3b82f6', value: '65%', device: 'Desktop' },
    { label: 'Mobile', color: '#10b981', value: '30%', device: 'Mobile' },
    { label: 'Tablet', color: '#f59e0b', value: '5%', device: 'Tablet' }
  ]

  return (
    <div className="container mx-auto max-w-7xl p-6 space-y-6">
      {/* 页面标题和控制 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-primary/10 rounded-lg">
            <Activity className="w-6 h-6 text-primary" />
          </div>
          <div>
            <h1 className="text-2xl font-bold">监控仪表板</h1>
            <p className="text-sm text-muted-foreground">
              实时监控应用性能和用户行为
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={loadMetrics}
            className={cn(
              "flex items-center gap-2 px-4 py-2 rounded-lg transition-colors",
              "bg-primary text-primary-foreground hover:opacity-90"
            )}
          >
            <RefreshCw size={16} />
            刷新
          </button>
          <button className="flex items-center gap-2 px-4 py-2 bg-muted hover:bg-muted/80 rounded-lg transition-colors">
            <Download size={16} />
            导出
          </button>
        </div>
      </div>

      {/* 实时统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-card rounded-lg border border-border p-6"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">活跃用户</p>
              <p className="text-2xl font-bold mt-1">{realtimeData.activeUsers}</p>
            </div>
            <div className="p-3 bg-blue-500/10 rounded-lg">
              <Users className="w-6 h-6 text-blue-500" />
            </div>
          </div>
          <div className="mt-4 flex items-center text-xs text-muted-foreground">
            <TrendingUp size={12} className="mr-1 text-green-500" />
            +12% 较上小时
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-card rounded-lg border border-border p-6"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">页面浏览量</p>
              <p className="text-2xl font-bold mt-1">{metrics.pageViews.toLocaleString()}</p>
            </div>
            <div className="p-3 bg-green-500/10 rounded-lg">
              <BarChart3 className="w-6 h-6 text-green-500" />
            </div>
          </div>
          <div className="mt-4 flex items-center text-xs text-muted-foreground">
            <Clock size={12} className="mr-1" />
            过去24小时
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-card rounded-lg border border-border p-6"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">性能评分</p>
              <p className="text-2xl font-bold mt-1">{metrics.performanceScore}</p>
            </div>
            <div className="p-3 bg-purple-500/10 rounded-lg">
              <Zap className="w-6 h-6 text-purple-500" />
            </div>
          </div>
          <div className="mt-4 flex items-center text-xs text-muted-foreground">
            <Activity size={12} className="mr-1" />
            基于Web Vitals
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-card rounded-lg border border-border p-6"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">错误率</p>
              <p className="text-2xl font-bold mt-1">{safeToFixed(metrics.errorRate, 2)}%</p>
            </div>
            <div className="p-3 bg-orange-500/10 rounded-lg">
              <AlertTriangle className="w-6 h-6 text-orange-500" />
            </div>
          </div>
          <div className="mt-4 flex items-center text-xs text-muted-foreground">
            <AlertTriangle size={12} className="mr-1 text-orange-500" />
            {errorStats.total} 个错误
          </div>
        </motion.div>
      </div>

      {/* 图表区域 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ResponsiveChart
          title="页面浏览量趋势"
          description="过去24小时每小时浏览量"
          height={300}
        >
          <SimpleLineChart data={pageViewsData} />
        </ResponsiveChart>

        <ResponsiveChart
          title="设备分布"
          description="用户设备类型统计"
          height={300}
        >
          <div className="space-y-4">
            {deviceLegend.map((item, index) => (
              <div key={index} className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: item.color }}
                    />
                    <span className="font-medium">{item.device}</span>
                  </div>
                  <span className="text-muted-foreground">{item.value}</span>
                </div>
                <div className="h-2 bg-muted rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{
                      backgroundColor: item.color,
                      width: item.value
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </ResponsiveChart>
      </div>

      {/* 详细数据表格 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 热门页面 */}
        <div className="bg-card rounded-lg border border-border p-6">
          <h3 className="font-semibold mb-4">热门页面</h3>
          <div className="space-y-3">
            {realtimeData.topPages.map((page, index) => (
              <div key={index} className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="text-sm text-muted-foreground">#{index + 1}</span>
                  <span className="font-mono text-sm">{page.path}</span>
                </div>
                <span className="text-sm text-muted-foreground">{page.views.toLocaleString()}</span>
              </div>
            ))}
          </div>
        </div>

        {/* 来源分析 */}
        <div className="bg-card rounded-lg border border-border p-6">
          <h3 className="font-semibold mb-4">流量来源</h3>
          <div className="space-y-3">
            {realtimeData.topReferrers.map((referrer, index) => (
              <div key={index} className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="text-sm text-muted-foreground">#{index + 1}</span>
                  <span className="text-sm">{referrer.source}</span>
                </div>
                <span className="text-sm text-muted-foreground">{referrer.visits.toLocaleString()}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 最近错误 */}
      <div className="bg-card rounded-lg border border-border p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold">最近错误</h3>
          <span className="text-sm text-muted-foreground">
            最后更新: {lastUpdate.toLocaleTimeString()}
          </span>
        </div>
        <div className="space-y-2">
          {errorStats.recent.length === 0 ? (
            <p className="text-center text-muted-foreground py-8">
              暂无错误报告
            </p>
          ) : (
            errorStats.recent.map((error, index) => (
              <div key={index} className="flex items-start gap-3 p-3 bg-muted/50 rounded-lg">
                <AlertTriangle
                  size={16}
                  className={cn(
                    "mt-0.5",
                    error.severity === 'critical' && "text-red-500",
                    error.severity === 'high' && "text-orange-500",
                    error.severity === 'medium' && "text-yellow-500",
                    error.severity === 'low' && "text-blue-500"
                  )}
                />
                <div className="flex-1">
                  <p className="text-sm font-medium">{error.message}</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {new Date(error.timestamp).toLocaleString()}
                  </p>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* 状态指示器 */}
      <div className="flex items-center justify-between p-4 bg-muted/50 rounded-lg border border-border">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
          <span className="text-sm font-medium">系统运行正常</span>
        </div>
        <div className="flex items-center gap-4 text-xs text-muted-foreground">
          <span>自动刷新: {autoRefresh ? '开启' : '关闭'}</span>
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className="text-primary hover:underline"
          >
            切换
          </button>
        </div>
      </div>
    </div>
  )
}
