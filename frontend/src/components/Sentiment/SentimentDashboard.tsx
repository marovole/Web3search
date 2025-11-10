/**
 * 情绪仪表板组件
 * 显示实时情绪数据的主要仪表板
 */
import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Separator } from '@/components/ui/separator';
import { useSentimentData } from './hooks/useSentimentData';
import { SentimentGauge } from './SentimentGauge';
import { SentimentChart } from './SentimentChart';
import { PlatformComparison } from './PlatformComparison';
import { SentimentTimeline } from './SentimentTimeline';
import { SentimentMobileDashboard } from './SentimentMobileDashboard';
import { RefreshCw, Wifi, WifiOff, AlertCircle, Plus, X, Smartphone, Monitor } from 'lucide-react';
import { formatPercentage, formatScore } from '@/lib/safeFormatters';

interface SentimentDashboardProps {
  defaultSymbols?: string[];
  className?: string;
}

export function SentimentDashboard({
  defaultSymbols = ['BTC', 'ETH', 'SOL'],
  className
}: SentimentDashboardProps) {
  const [symbols, setSymbols] = useState<string[]>(defaultSymbols);
  const [newSymbol, setNewSymbol] = useState('');
  const [showAddSymbol, setShowAddSymbol] = useState(false);
  const [isMobile, setIsMobile] = useState(false);

  // 检测移动设备
  React.useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // 如果是移动设备，使用移动端组件
  if (isMobile) {
    return <SentimentMobileDashboard defaultSymbols={defaultSymbols} className={className} />;
  }

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

  return (
    <div className={`space-y-6 ${className}`}>
      {/* 头部状态栏 */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <CardTitle className="text-xl">情绪分析仪表板</CardTitle>
              <Badge variant={isConnected ? "default" : "destructive"}>
                {isConnected ? (
                  <><Wifi className="w-3 h-3 mr-1" />已连接</>
                ) : (
                  <><WifiOff className="w-3 h-3 mr-1" />未连接</>
                )}
              </Badge>
              {isLoading && (
                <RefreshCw className="w-4 h-4 animate-spin" />
              )}
            </div>

            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleRefresh}
                disabled={!isConnected || isLoading}
              >
                <RefreshCw className={`w-4 h-4 mr-1 ${isLoading ? 'animate-spin' : ''}`} />
                刷新
              </Button>
            </div>
          </div>
        </CardHeader>

        {/* 币种管理 */}
        <CardContent className="pt-0">
          <div className="flex flex-wrap gap-2">
            {symbols.map(symbol => (
              <Badge
                key={symbol}
                variant="secondary"
                className="px-3 py-1 cursor-pointer hover:bg-red-100"
                onClick={() => handleRemoveSymbol(symbol)}
              >
                {symbol}
                <X className="w-3 h-3 ml-1" />
              </Badge>
            ))}

            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowAddSymbol(true)}
              className="h-6"
            >
              <Plus className="w-3 h-3 mr-1" />
              添加币种
            </Button>
          </div>

          {showAddSymbol && (
            <div className="mt-3 flex items-center space-x-2">
              <Input
                placeholder="输入币种符号 (如 DOGE)"
                value={newSymbol}
                onChange={(e) => setNewSymbol(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleAddSymbol()}
                className="flex-1"
              />
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
          )}
        </CardContent>
      </Card>

      {/* 错误提示 */}
      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2 text-red-600">
              <AlertCircle className="w-4 h-4" />
              <span className="text-sm">{error}</span>
              <Button
                variant="ghost"
                size="sm"
                onClick={clearError}
                className="ml-auto text-red-600 hover:text-red-800"
              >
                <X className="w-4 h-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* 总体统计 */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="text-center">
                <div className="text-2xl font-bold">
                  {formatScore(stats?.averageScore, 3, '0.000')}
                </div>
                <div className="text-sm text-muted-foreground">平均情绪分数</div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="text-center">
                <div className="text-2xl font-bold">
                  {stats.totalVolume.toLocaleString()}
                </div>
                <div className="text-sm text-muted-foreground">总讨论量</div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {formatPercentage(stats?.positivePercentage, 1, 'N/A')}
                </div>
                <div className="text-sm text-muted-foreground">积极情绪</div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="text-center">
                <div className="text-2xl font-bold text-red-600">
                  {formatPercentage(stats?.negativePercentage, 1, 'N/A')}
                </div>
                <div className="text-sm text-muted-foreground">消极情绪</div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* 情绪仪表盘网格 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        {/* 情绪指示器 */}
        {symbols.map(symbol => (
          <SentimentGauge
            key={symbol}
            symbol={symbol}
            data={sentimentData[symbol]}
            isLoading={isLoading}
          />
        ))}
      </div>

      <Separator />

      {/* 图表区域 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 实时趋势图 */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>实时情绪趋势</CardTitle>
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
              <CardTitle>平台数据分布</CardTitle>
            </CardHeader>
            <CardContent>
              <PlatformComparison stats={platformStats} />
            </CardContent>
          </Card>
        )}

        {/* 时间线分析 */}
        {symbols.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>历史时间线</CardTitle>
            </CardHeader>
            <CardContent>
              <SentimentTimeline symbol={symbols[0]} />
            </CardContent>
          </Card>
        )}
      </div>

      {/* 连接状态提示 */}
      {!isConnected && (
        <Card className="border-yellow-200 bg-yellow-50">
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2 text-yellow-600">
              <AlertCircle className="w-4 h-4" />
              <span className="text-sm">
                WebSocket连接已断开，尝试重新连接中...
              </span>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}