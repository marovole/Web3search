/**
 * 平台对比组件
 * 显示不同社交媒体平台的情绪数据对比
 */
import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { coerceFiniteNumber, formatPercentage, formatScore, safeToFixed } from '@/lib/safeFormatters';

interface PlatformStats {
  [platform: string]: {
    score: number;
    volume: number;
    percentage: number;
  };
}

interface PlatformComparisonProps {
  stats: PlatformStats;
  className?: string;
}

interface BarDataItem {
  platform: string;
  score: number;
  volume: number;
  fullPlatform: string;
}

interface PieDataItem {
  name: string;
  value: number;
  fullPlatform: string;
}

const PLATFORM_COLORS = {
  twitter: '#1DA1F2',
  reddit: '#FF4500',
  telegram: '#0088cc',
  discord: '#5865F2'
};

const PLATFORM_LABELS = {
  twitter: 'Twitter',
  reddit: 'Reddit',
  telegram: 'Telegram',
  discord: 'Discord'
};

export function PlatformComparison({ stats, className }: PlatformComparisonProps) {
  if (!stats || Object.keys(stats).length === 0) {
    return (
      <Card className={className}>
        <CardContent className="pt-6">
          <div className="h-32 flex items-center justify-center text-muted-foreground">
            暂无平台数据
          </div>
        </CardContent>
      </Card>
    );
  }

  // 准备柱状图数据
  const barData: BarDataItem[] = Object.entries(stats).map(([platform, data]) => {
    const normalizedScore = coerceFiniteNumber(data.score)

    return {
      platform: PLATFORM_LABELS[platform as keyof typeof PLATFORM_LABELS] || platform,
      score: normalizedScore !== null
        ? Number.parseFloat(safeToFixed(normalizedScore, 3, '0.000'))
        : 0,
      volume: data.volume,
      fullPlatform: platform
    }
  })

  // 准备饼图数据
  const totalVolume = Object.values(stats).reduce((sum, data) => sum + data.volume, 0)
  const pieData: PieDataItem[] = Object.entries(stats).map(([platform, data]) => {
    return {
      name: PLATFORM_LABELS[platform as keyof typeof PLATFORM_LABELS] || platform,
      value: totalVolume > 0 ? (data.volume / totalVolume) * 100 : 0,
      fullPlatform: platform
    }
  })

  // 准备饼图数据
  const pieData = Object.entries(stats).map(([platform, data]) => {
    const normalizedPercentage = coerceFiniteNumber(data.percentage);

    return {
      name: PLATFORM_LABELS[platform as keyof typeof PLATFORM_LABELS] || platform,
      value: normalizedPercentage ?? 0,
      fullPlatform: platform
    };
  });

  // 自定义Tooltip
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 border border-gray-200 rounded shadow-lg">
          <p className="font-medium mb-1">{data.platform}</p>
          <p style={{ color: '#666' }}>
            情绪分数: <span style={{ color: '#333', fontWeight: 'bold' }}>
              {formatScore(data.score, 3, '0.000')}
            </span>
          </p>
          <p style={{ color: '#666' }}>
            讨论量: <span style={{ color: '#333', fontWeight: 'bold' }}>
              {data.volume.toLocaleString()}
            </span>
          </p>
        </div>
      );
    }
    return null;
  };

  // 饼图Tooltip
  const PieTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0];
      return (
        <div className="bg-white p-3 border border-gray-200 rounded shadow-lg">
          <p className="font-medium">{data.name}</p>
          <p className="text-sm" style={{ color: '#666' }}>
            占比: <span style={{ color: '#333', fontWeight: 'bold' }}>
              {`${safeToFixed(data.value, 1, '0.0')}%`}
            </span>
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className={`space-y-4 ${className}`}>
      {/* 平台情绪分数对比 */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">平台情绪分数对比</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={barData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis
                dataKey="platform"
                tick={{ fontSize: 12 }}
                axisLine={{ stroke: '#666' }}
              />
              <YAxis
                domain={[-1, 1]}
                ticks={[-1, -0.5, 0, 0.5, 1]}
                tick={{ fontSize: 10 }}
                axisLine={{ stroke: '#666' }}
                label={{
                  value: '情绪分数',
                  angle: -90,
                  position: 'insideLeft',
                  style: { fontSize: 10 }
                }}
              />
              <Tooltip content={<CustomTooltip />} />
              <Bar
                dataKey="score"
                fill={(entry: any) => PLATFORM_COLORS[entry.fullPlatform] || '#8884d8'}
                radius={[4, 4, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* 平台讨论量分布 */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">平台讨论量分布</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            {/* 饼图 */}
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={(entry) => `${safeToFixed(entry.value, 1, '0.0')}%`}
                    outerRadius={60}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {pieData.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={PLATFORM_COLORS[entry.fullPlatform] || '#8884d8'}
                      />
                    ))}
                  </Pie>
                  <Tooltip content={<PieTooltip />} />
                </PieChart>
              </ResponsiveContainer>
            </div>

            {/* 详细数据 */}
            <div className="space-y-2">
              {Object.entries(stats).map(([platform, data]) => (
                <div key={platform} className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{
                        backgroundColor: PLATFORM_COLORS[platform as keyof typeof PLATFORM_COLORS]
                      }}
                    />
                    <span className="text-sm font-medium">
                      {PLATFORM_LABELS[platform as keyof typeof PLATFORM_LABELS] || platform}
                    </span>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-bold">
                      {formatPercentage(data.percentage, 1, 'N/A')}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {data.volume.toLocaleString()}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 平台情绪状态汇总 */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">平台情绪状态</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-3">
            {Object.entries(stats).map(([platform, data]) => {
              let status: { label: string; color: string };
              if (data.score >= 0.3) {
                status = { label: '积极', color: 'bg-green-100 text-green-800' };
              } else if (data.score >= -0.3) {
                status = { label: '中性', color: 'bg-gray-100 text-gray-800' };
              } else {
                status = { label: '消极', color: 'bg-red-100 text-red-800' };
              }

              return (
                <div
                  key={platform}
                  className="flex items-center justify-between p-2 border rounded"
                >
                  <div className="flex items-center space-x-2">
                    <div
                      className="w-2 h-2 rounded-full"
                      style={{
                        backgroundColor: PLATFORM_COLORS[platform as keyof typeof PLATFORM_COLORS]
                      }}
                    />
                    <span className="text-xs">
                      {PLATFORM_LABELS[platform as keyof typeof PLATFORM_LABELS] || platform}
                    </span>
                  </div>
                  <Badge variant="secondary" className={status.color}>
                    {status.label}
                  </Badge>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}