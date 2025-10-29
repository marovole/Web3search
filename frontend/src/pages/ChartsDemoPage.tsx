import React from 'react'
import { ResponsiveChart, ChartLegend, SimpleBarChart, SimpleLineChart } from '@/components/Charts/ResponsiveChart'
import { BarChart3, TrendingUp } from 'lucide-react'

/**
 * 图表组件演示页面
 * 展示响应式图表在不同设备上的表现
 */
export default function ChartsDemoPage() {
  // 示例数据
  const barData = [
    { label: 'Bitcoin', value: 45000, color: '#F7931A' },
    { label: 'Ethereum', value: 3200, color: '#627EEA' },
    { label: 'Solana', value: 95, color: '#9945FF' },
    { label: 'Cardano', value: 0.45, color: '#0033AD' }
  ]

  const lineData = [
    { label: '1月', value: 100 },
    { label: '2月', value: 120 },
    { label: '3月', value: 95 },
    { label: '4月', value: 145 },
    { label: '5月', value: 130 },
    { label: '6月', value: 160 }
  ]

  const legendItems = [
    { label: 'Bitcoin', color: '#F7931A', value: '$45,000' },
    { label: 'Ethereum', color: '#627EEA', value: '$3,200' },
    { label: 'Solana', color: '#9945FF', value: '$95' },
    { label: 'Cardano', color: '#0033AD', value: '$0.45' }
  ]

  return (
    <div className="container mx-auto max-w-6xl p-6 space-y-6">
      {/* 页面标题 */}
      <div className="flex items-center gap-3 mb-8">
        <div className="p-3 bg-primary/10 rounded-lg">
          <BarChart3 className="w-6 h-6 text-primary" />
        </div>
        <div>
          <h1 className="text-2xl font-bold">图表展示</h1>
          <p className="text-sm text-muted-foreground">响应式图表组件演示</p>
        </div>
      </div>

      {/* 柱状图示例 */}
      <ResponsiveChart
        title="加密货币价格对比"
        description="主流加密货币当前价格（USD）"
        height={350}
      >
        <div className="space-y-4">
          <SimpleBarChart data={barData} />
          <ChartLegend items={legendItems} />
        </div>
      </ResponsiveChart>

      {/* 折线图示例 */}
      <ResponsiveChart
        title="价格趋势分析"
        description="过去6个月的价格变化"
        height={300}
      >
        <SimpleLineChart data={lineData} />
      </ResponsiveChart>

      {/* 小型图表网格 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <ResponsiveChart
          title="市值占比"
          description="加密货币市值分布"
          height={250}
        >
          <div className="space-y-3">
            {barData.map((item, index) => (
              <div key={index} className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: item.color }}
                  />
                  <span className="text-sm font-medium">{item.label}</span>
                </div>
                <span className="text-sm text-muted-foreground">{item.value}</span>
              </div>
            ))}
          </div>
        </ResponsiveChart>

        <ResponsiveChart
          title="市场表现"
          description="关键指标监控"
          height={250}
        >
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
              <div className="flex items-center gap-2">
                <TrendingUp size={20} className="text-green-500" />
                <span className="font-medium">总市值</span>
              </div>
              <span className="font-bold">$1.2T</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
              <div className="flex items-center gap-2">
                <TrendingUp size={20} className="text-green-500" />
                <span className="font-medium">24h 变化</span>
              </div>
              <span className="font-bold text-green-500">+5.2%</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
              <div className="flex items-center gap-2">
                <TrendingUp size={20} className="text-red-500" />
                <span className="font-medium">24h 交易量</span>
              </div>
              <span className="font-bold">$85B</span>
            </div>
          </div>
        </ResponsiveChart>
      </div>

      {/* 移动端优化说明 */}
      <div className="bg-muted/50 rounded-lg p-6 border border-border">
        <h3 className="font-semibold mb-3">响应式特性</h3>
        <ul className="space-y-2 text-sm text-muted-foreground">
          <li className="flex items-start gap-2">
            <span className="text-primary">•</span>
            <span>自动适应容器宽度，在移动端优化显示</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-primary">•</span>
            <span>触摸友好的交互，支持手势操作</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-primary">•</span>
            <span>在窄屏幕上自动调整布局和字体大小</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-primary">•</span>
            <span>优化加载性能，支持懒加载和动画</span>
          </li>
        </ul>
      </div>
    </div>
  )
}
