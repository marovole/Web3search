/**
 * 情绪时间线组件
 * 显示历史情绪变化趋势
 */
import React, { useState } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { formatScore, safeToFixed } from '@/lib/safeFormatters';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Calendar, TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface SentimentTimelineProps {
  symbol: string;
  className?: string;
}

interface TimelineData {
  time: string;
  timestamp: string;
  score: number;
  volume: number;
  classification: string;
  event?: string;
}

export function SentimentTimeline({ symbol, className }: SentimentTimelineProps) {
  const [timeRange, setTimeRange] = useState('24h');
  const [timelineData, setTimelineData] = useState<TimelineData[]>([]);

  // 生成模拟历史数据（实际应该从API获取）
  React.useEffect(() => {
    const generateTimelineData = () => {
      const now = new Date();
      const data: TimelineData[] = [];
      let hours = 24;

      switch (timeRange) {
        case '7d':
          hours = 168; // 7天
          break;
        case '30d':
          hours = 720; // 30天
          break;
        default:
          hours = 24; // 1天
      }

      const interval = hours > 24 ? Math.ceil(hours / 24) : 1;

      for (let i = hours; i >= 0; i -= interval) {
        const timestamp = new Date(now.getTime() - i * 60 * 60 * 1000);
        const baseScore = Math.sin(i * 0.2) * 0.5 + Math.random() * 0.3;
        const volume = Math.floor(Math.random() * 1000) + 500;

        let classification = 'neutral';
        if (baseScore > 0.3) {
          classification = 'positive';
        } else if (baseScore > 0.6) {
          classification = 'strong_positive';
        } else if (baseScore < -0.3) {
          classification = 'negative';
        } else if (baseScore < -0.6) {
          classification = 'strong_negative';
        }

        data.push({
          time: timestamp.toLocaleDateString('zh-CN', {
            month: 'short',
            day: 'numeric',
            hour: interval > 1 ? undefined : '2-digit',
            minute: interval > 1 ? undefined : '2-digit'
          }),
          timestamp: timestamp.toISOString(),
          score: Number.parseFloat(safeToFixed(baseScore, 3, '0.000')),
          volume,
          classification,
          event: Math.random() > 0.8 ? generateRandomEvent() : undefined
        });
      }

      setTimelineData(data);
    };

    generateTimelineData();
  }, [symbol, timeRange]);

  const generateRandomEvent = () => {
    const events = [
      '重大新闻发布',
      '技术更新',
      '市场波动',
      '社区热议',
      'KOL发声',
      '价格异动'
    ];
    return events[Math.floor(Math.random() * events.length)];
  };

  const getTrendIcon = (score: number) => {
    if (score > 0.1) {
      return <TrendingUp className="w-4 h-4 text-green-600" />;
    } else if (score < -0.1) {
      return <TrendingDown className="w-4 h-4 text-red-600" />;
    }
    return <Minus className="w-4 h-4 text-gray-600" />;
  };

  const getEventBadgeColor = (classification: string) => {
    switch (classification) {
      case 'strong_positive':
        return 'bg-green-100 text-green-800';
      case 'positive':
        return 'bg-green-50 text-green-600';
      case 'negative':
        return 'bg-red-50 text-red-600';
      case 'strong_negative':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getLineColor = (classification: string) => {
    switch (classification) {
      case 'strong_positive':
      case 'positive':
        return '#10b981';
      case 'strong_negative':
      case 'negative':
        return '#ef4444';
      default:
        return '#6b7280';
    }
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 border border-gray-200 rounded shadow-lg">
          <p className="font-medium mb-2">{label}</p>
          <div className="space-y-1 text-sm">
            <p>
              情绪分数: <span className="font-bold">{formatScore(data.score, 3, '0.000')}</span>
            </p>
            <p>
              讨论量: <span className="font-bold">{data.volume.toLocaleString()}</span>
            </p>
            <p>
              分类: <span className="font-bold">{data.classification}</span>
            </p>
            {data.event && (
              <p className="text-blue-600">
                事件: <span className="font-bold">{data.event}</span>
              </p>
            )}
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">{symbol} 历史情绪分析</CardTitle>
          <Select value={timeRange} onValueChange={setTimeRange}>
            <SelectTrigger className="w-24">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="24h">24小时</SelectItem>
              <SelectItem value="7d">7天</SelectItem>
              <SelectItem value="30d">30天</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </CardHeader>

      <CardContent>
        <div className="h-64">
          {timelineData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={timelineData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#8884d8" stopOpacity={0.8} />
                    <stop offset="95%" stopColor="#8884d8" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis
                  dataKey="time"
                  stroke="#666"
                  fontSize={10}
                  tick={{ fontSize: 9 }}
                />
                <YAxis
                  domain={[-1, 1]}
                  ticks={[-1, -0.5, 0, 0.5, 1]}
                  stroke="#666"
                  fontSize={10}
                  tick={{ fontSize: 9 }}
                />
                <Tooltip content={<CustomTooltip />} />
                <Area
                  type="monotone"
                  dataKey="score"
                  stroke="#8884d8"
                  strokeWidth={2}
                  fill="url(#colorGradient)"
                />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-full flex items-center justify-center text-muted-foreground">
              加载中...
            </div>
          )}
        </div>

        {/* 重要事件标记 */}
        {timelineData.filter(d => d.event).length > 0 && (
          <div className="mt-4 space-y-2">
            <h4 className="text-sm font-medium">重要事件</h4>
            <div className="space-y-1">
              {timelineData
                .filter(d => d.event)
                .slice(0, 3)
                .map((data, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-2 bg-gray-50 rounded"
                  >
                    <div className="flex items-center space-x-2">
                      {getTrendIcon(data.score)}
                      <span className="text-xs">{data.time}</span>
                      <span className="text-xs">{data.event}</span>
                    </div>
                    <Badge
                      variant="secondary"
                      className={getEventBadgeColor(data.classification)}
                    >
                      {formatScore(data.score, 2, '0.00')}
                    </Badge>
                  </div>
                ))}
            </div>
          </div>
        )}

        {/* 统计摘要 */}
        {timelineData.length > 0 && (
          <div className="mt-4 pt-4 border-t">
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <div className="text-xs text-muted-foreground">平均分数</div>
                <div className="text-sm font-bold">
                  {formatScore(
                    timelineData.reduce((sum, d) => sum + d.score, 0) / timelineData.length,
                    3,
                    '0.000'
                  )}
                </div>
              </div>
              <div>
                <div className="text-xs text-muted-foreground">最高分数</div>
                <div className="text-sm font-bold text-green-600">
                  {formatScore(Math.max(...timelineData.map(d => d.score)), 3, '0.000')}
                </div>
              </div>
              <div>
                <div className="text-xs text-muted-foreground">最低分数</div>
                <div className="text-sm font-bold text-red-600">
                  {formatScore(Math.min(...timelineData.map(d => d.score)), 3, '0.000')}
                </div>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}