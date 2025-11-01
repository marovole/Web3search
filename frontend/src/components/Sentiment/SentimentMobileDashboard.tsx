/**
 * 移动端情绪仪表板组件
 * 专为移动设备优化的情绪数据展示
 */
import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useSentimentData } from './hooks/useSentimentData';
import { SentimentGauge } from './SentimentGauge';
import { SentimentChart } from './SentimentChart';
import { PlatformComparison } from './PlatformComparison';
import { RefreshCw, Wifi, WifiOff, AlertCircle, Plus, Menu, BarChart3, TrendingUp, X } from 'lucide-react';

interface SentimentMobileDashboardProps {
  defaultSymbols?: string[];
  className?: string;
}

export function SentimentMobileDashboard({
  defaultSymbols = ['BTC', 'ETH'],
  className
}: SentimentMobileDashboardProps) {
  const [symbols, setSymbols] = useState<string[]>(defaultSymbols);
  const [newSymbol, setNewSymbol] = useState('');
  const [showAddSymbol, setShowAddSymbol] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'details' | 'charts'>('overview');
  const [showSettings, setShowSettings] = useState(false);

  const {
    sentimentData,
    isLoading,
    error,
    isConnected,
    stats,
    platformStats,
    subscribe,
    unsubscribe,
    refreshData,
    clearError
  } = useSentimentData({ symbols });

  // 添加新币种
  const handleAddSymbol = async () => {
    if (!newSymbol.trim()) return;

    const symbol = newSymbol.trim().toUpperCase();
    if (symbols.includes(symbol)) {
      setNewSymbol('');
      return;
    }

    const success = await subscribe(symbol);
    if (success) {
      setSymbols(prev => [...prev, symbol]);
      setNewSymbol('');
      setShowAddSymbol(false);
    }
  };

  // 移除币种
  const handleRemoveSymbol = async (symbol: string) => {
    const success = await unsubscribe(symbol);
    if (success) {
      setSymbols(prev => prev.filter(s => s !== symbol));
    }
  };

  // 刷新数据
  const handleRefresh = () => {
    refreshData();
  };

  // 主要指标卡片
  const MetricCard = ({ title, value, subtitle, color = 'default' }: {
    title: string;
    value: string | number;
    subtitle?: string;
    color?: 'green' | 'red' | 'blue' | 'default';
  }) => {
    const colorClasses = {
      green: 'text-green-600 bg-green-50',
      red: 'text-red-600 bg-red-50',
      blue: 'text-blue-600 bg-blue-50',
      default: 'text-gray-600 bg-gray-50'
    };

    return (
      <Card className={`${colorClasses[color]}`}>
        <CardContent className="pt-4">
          <div className="text-xs text-muted-foreground">{title}</div>
          <div className="text-lg font-bold">{value}</div>
          {subtitle && (
            <div className="text-xs text-muted-foreground">{subtitle}</div>
          )}
        </CardContent>
      </Card>
    );
  };

  return (
    <div className={`space-y-4 ${className}`}>
      {/* 头部状态栏 */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <CardTitle className="text-lg">情绪分析</CardTitle>
              <Badge variant={isConnected ? "default" : "destructive"} className="text-xs">
                {isConnected ? '已连接' : '未连接'}
              </Badge>
            </div>

            <div className="flex items-center space-x-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={handleRefresh}
                disabled={!isConnected || isLoading}
              >
                <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
              </Button>

              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowSettings(true)}
              >
                <Menu className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* 错误提示 */}
      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-4">
            <div className="flex items-center space-x-2 text-red-600">
              <AlertCircle className="w-4 h-4" />
              <span className="text-sm">{error}</span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* 标签页切换 */}
      <div className="flex space-x-2 p-1 bg-gray-100 rounded-lg">
        <Button
          variant={activeTab === 'overview' ? 'default' : 'ghost'}
          size="sm"
          onClick={() => setActiveTab('overview')}
          className="flex-1"
        >
          <BarChart3 className="w-4 h-4 mr-1" />
          概览
        </Button>
        <Button
          variant={activeTab === 'details' ? 'default' : 'ghost'}
          size="sm"
          onClick={() => setActiveTab('details')}
          className="flex-1"
        >
          <TrendingUp className="w-4 h-4 mr-1" />
          详情
        </Button>
        <Button
          variant={activeTab === 'charts' ? 'default' : 'ghost'}
          size="sm"
          onClick={() => setActiveTab('charts')}
          className="flex-1"
        >
          图表
        </Button>
      </div>

      {/* 概览标签页 */}
      {activeTab === 'overview' && (
        <div className="space-y-4">
          {/* 总体统计 */}
          {stats && (
            <div className="grid grid-cols-2 gap-3">
              <MetricCard
                title="平均情绪"
                value={stats.averageScore.toFixed(3)}
                subtitle={`${stats.positivePercentage.toFixed(1)}% 积极`}
                color={stats.averageScore > 0.1 ? 'green' : stats.averageScore < -0.1 ? 'red' : 'blue'}
              />
              <MetricCard
                title="总讨论量"
                value={stats.totalVolume.toLocaleString()}
                subtitle="24小时内"
                color="blue"
              />
              <MetricCard
                title="积极情绪"
                value={`${stats.positivePercentage.toFixed(1)}%`}
                subtitle={`${Object.keys(stats).length} 个币种`}
                color="green"
              />
              <MetricCard
                title="消极情绪"
                value={`${stats.negativePercentage.toFixed(1)}%`}
                subtitle={`平均${stats.averageScore.toFixed(3)}`}
                color="red"
              />
            </div>
          )}

          {/* 情绪指示器网格 */}
          <div className="grid grid-cols-1 gap-4">
            {symbols.map(symbol => (
              <SentimentGauge
                key={symbol}
                symbol={symbol}
                data={sentimentData[symbol]}
                isLoading={isLoading}
              />
            ))}
          </div>
        </div>
      )}

      {/* 详情标签页 */}
      {activeTab === 'details' && (
        <div className="space-y-4">
          {symbols.map(symbol => (
            <Card key={symbol}>
              <CardHeader className="pb-3">
                <CardTitle className="text-base">{symbol}</CardTitle>
              </CardHeader>
              <CardContent>
                {sentimentData[symbol] ? (
                  <div className="space-y-3">
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <div className="text-muted-foreground">情绪分数</div>
                        <div className="font-bold">
                          {sentimentData[symbol].data.sentiment_score.toFixed(3)}
                        </div>
                      </div>
                      <div>
                        <div className="text-muted-foreground">置信度</div>
                        <div className="font-bold">
                          {(sentimentData[symbol].data.confidence * 100).toFixed(1)}%
                        </div>
                      </div>
                      <div>
                        <div className="text-muted-foreground">讨论量</div>
                        <div className="font-bold">
                          {sentimentData[symbol].data.volume.toLocaleString()}
                        </div>
                      </div>
                      <div>
                        <div className="text-muted-foreground">参与度</div>
                        <div className="font-bold">
                          {sentimentData[symbol].data.engagement.toLocaleString()}
                        </div>
                      </div>
                    </div>

                    {/* 情绪分布 */}
                    {sentimentData[symbol].data.sentiment_distribution && (
                      <div className="space-y-2">
                        <div className="text-sm font-medium">情绪分布</div>
                        <div className="space-y-1">
                          <div className="flex justify-between text-xs">
                            <span>积极</span>
                            <span>
                              {sentimentData[symbol].data.sentiment_distribution.positive.toFixed(1)}%
                            </span>
                          </div>
                          <div className="flex justify-between text-xs">
                            <span>中性</span>
                            <span>
                              {sentimentData[symbol].data.sentiment_distribution.neutral.toFixed(1)}%
                            </span>
                          </div>
                          <div className="flex justify-between text-xs">
                            <span>消极</span>
                            <span>
                              {sentimentData[symbol].data.sentiment_distribution.negative.toFixed(1)}%
                            </span>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* 平台分布 */}
                    {sentimentData[symbol].data.platform_distribution && (
                      <div className="space-y-2">
                        <div className="text-sm font-medium">平台分布</div>
                        <div className="flex flex-wrap gap-1">
                          {Object.entries(sentimentData[symbol].data.platform_distribution).map(([platform, score]) => (
                            <Badge
                              key={platform}
                              variant="outline"
                              className="text-xs"
                            >
                              {platform}: {score.toFixed(2)}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}

                    <div className="text-xs text-muted-foreground text-center">
                      更新时间: {new Date(sentimentData[symbol].data.updated_at).toLocaleTimeString()}
                    </div>
                  </div>
                ) : (
                  <div className="text-center text-muted-foreground py-8">
                    暂无数据
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* 图表标签页 */}
      {activeTab === 'charts' && (
        <div className="space-y-4">
          {/* 实时趋势图 */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">实时情绪趋势</CardTitle>
            </CardHeader>
            <CardContent>
              <SentimentChart
                symbols={symbols}
                data={sentimentData}
                isLoading={isLoading}
              />
            </CardContent>
          </Card>

          {/* 平台对比 */}
          {platformStats && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">平台数据分布</CardTitle>
              </CardHeader>
              <CardContent>
                <PlatformComparison stats={platformStats} />
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* 连接状态提示 */}
      {!isConnected && (
        <Card className="border-yellow-200 bg-yellow-50">
          <CardContent className="pt-4">
            <div className="flex items-center space-x-2 text-yellow-600">
              <AlertCircle className="w-4 h-4" />
              <span className="text-sm">
                WebSocket连接已断开，尝试重新连接中...
              </span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* 设置模态框 */}
      {showSettings && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-sm">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">设置</CardTitle>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowSettings(false)}
                >
                  <X className="w-4 h-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* 币种管理 */}
              <div className="space-y-2">
                <h4 className="text-sm font-medium">监控币种</h4>
                <div className="flex flex-wrap gap-1">
                  {symbols.map(symbol => (
                    <Badge
                      key={symbol}
                      variant="secondary"
                      className="cursor-pointer hover:bg-red-100"
                      onClick={() => handleRemoveSymbol(symbol)}
                    >
                      {symbol} ×
                    </Badge>
                  ))}
                </div>
                {showAddSymbol ? (
                  <div className="space-y-2">
                    <Input
                      placeholder="币种符号"
                      value={newSymbol}
                      onChange={(e) => setNewSymbol(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && handleAddSymbol()}
                    />
                    <div className="flex space-x-2">
                      <Button size="sm" onClick={handleAddSymbol}>
                        添加
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          setShowAddSymbol(false);
                          setNewSymbol('');
                        }}
                      >
                        取消
                      </Button>
                    </div>
                  </div>
                ) : (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowAddSymbol(true)}
                    className="w-full"
                  >
                    <Plus className="w-3 h-3 mr-1" />
                    添加币种
                  </Button>
                )}
              </div>

              {/* 连接状态 */}
              <div className="space-y-2">
                <h4 className="text-sm font-medium">连接状态</h4>
                <div className="flex items-center space-x-2">
                  {isConnected ? (
                    <>
                      <Wifi className="w-4 h-4 text-green-600" />
                      <span className="text-sm text-green-600">WebSocket已连接</span>
                    </>
                  ) : (
                    <>
                      <WifiOff className="w-4 h-4 text-red-600" />
                      <span className="text-sm text-red-600">WebSocket未连接</span>
                    </>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}