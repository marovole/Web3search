/**
 * 情绪图表组件
 * 使用Recharts显示实时情绪趋势
 */
import React, { useMemo } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  AreaChart
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { SentimentData } from './WebSocketManager';

interface SentimentChartProps {
  symbols: string[];
  data: Record<string, SentimentData>;
  isLoading?: boolean;
  className?: string;
}

interface ChartData {
  time: string;
  [symbol: string]: number | string;
}

export function SentimentChart({
  symbols,
  data,
  isLoading = false,
  className
}: SentimentChartProps) {
  // 获取币种颜色
  const getSymbolColor = (symbol: string) => {
    const colors: Record<string, string> = {
      BTC: '#f7931a',
      ETH: '#627eea',
      SOL: '#14f195',
      BNB: '#f3ba2f',
      ADA: '#0033ad',
      DOT: '#e6007a',
      AVAX: '#e84142',
      MATIC: '#8247e5',
      LINK: '#2a5ada',
      UNI: '#ff007a'
    };
    return colors[symbol] || '#8884d8';
  };

  // 生成图表数据
  const chartData = useMemo(() => {
    if (Object.keys(data).length === 0) {
      return [];
    }

    const timeLabels = [];
    const now = new Date();

    // 生成过去24小时的时间点（每2小时一个点）
    for (let i = 23; i >= 0; i -= 2) {
      const time = new Date(now.getTime() - i * 60 * 60 * 1000);
      timeLabels.push(time.toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit'
      }));
    }

    // 为每个时间点生成数据
    return timeLabels.map((time, index) => {
      const dataPoint: ChartData = { time };

      symbols.forEach(symbol => {
        const sentimentData = data[symbol];
        if (sentimentData) {
          // 模拟历史数据变化（实际应该从API获取历史数据）
          const baseScore = sentimentData.data.sentiment_score;
          const variation = Math.sin(index * 0.5) * 0.1;
          dataPoint[symbol] = parseFloat((baseScore + variation).toFixed(3));
        } else {
          dataPoint[symbol] = 0;
        }
      });

      return dataPoint;
    });
  }, [symbols, data]);

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>实时情绪趋势</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64 bg-gray-100 rounded animate-pulse" />
        </CardContent>
      </Card>
    );
  }

  if (chartData.length === 0) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>实时情绪趋势</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center text-muted-foreground">
            暂无数据
          </div>
        </CardContent>
      </Card>
    );
  }

  // 自定义Tooltip
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border border-gray-200 rounded shadow-lg">
          <p className="font-medium mb-2">{`时间: ${label}`}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} style={{ color: entry.color }}>
              {`${entry.name}: ${entry.value?.toFixed(3) || '0.000'}`}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className={className}>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis
            dataKey="time"
            stroke="#666"
            fontSize={12}
            tick={{ fontSize: 10 }}
          />
          <YAxis
            domain={[-1, 1]}
            ticks={[-1, -0.5, 0, 0.5, 1]}
            stroke="#666"
            fontSize={12}
            tick={{ fontSize: 10 }}
            label={{
              value: '情绪分数',
              angle: -90,
              position: 'insideLeft',
              style: { fontSize: 12 }
            }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            wrapperStyle={{
              paddingTop: '10px',
              fontSize: '12px'
            }}
          />
          {symbols.map(symbol => (
            <Line
              key={symbol}
              type="monotone"
              dataKey={symbol}
              stroke={getSymbolColor(symbol)}
              strokeWidth={2}
              dot={false}
              connectNulls={false}
              name={symbol}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

/**
 * 面积图版本的情绪趋势图
 */
export function SentimentAreaChart({
  symbols,
  data,
  isLoading = false,
  className
}: SentimentChartProps) {
  const getSymbolColor = (symbol: string) => {
    const colors: Record<string, string> = {
      BTC: '#f7931a',
      ETH: '#627eea',
      SOL: '#14f195',
      BNB: '#f3ba2f'
    };
    return colors[symbol] || '#8884d8';
  };

  const chartData = useMemo(() => {
    if (Object.keys(data).length === 0) {
      return [];
    }

    const timeLabels = [];
    const now = new Date();

    for (let i = 23; i >= 0; i -= 2) {
      const time = new Date(now.getTime() - i * 60 * 60 * 1000);
      timeLabels.push(time.toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit'
      }));
    }

    return timeLabels.map((time, index) => {
      const dataPoint: ChartData = { time };

      symbols.forEach(symbol => {
        const sentimentData = data[symbol];
        if (sentimentData) {
          const baseScore = sentimentData.data.sentiment_score;
          const variation = Math.sin(index * 0.5) * 0.1;
          dataPoint[symbol] = parseFloat((baseScore + variation).toFixed(3));
        } else {
          dataPoint[symbol] = 0;
        }
      });

      return dataPoint;
    });
  }, [symbols, data]);

  if (isLoading) {
    return (
      <Card className={className}>
        <CardContent>
          <div className="h-64 bg-gray-100 rounded animate-pulse" />
        </CardContent>
      </Card>
    );
  }

  return (
    <div className={className}>
      <ResponsiveContainer width="100%" height={250}>
        <AreaChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis
            dataKey="time"
            stroke="#666"
            fontSize={10}
            tick={{ fontSize: 9 }}
          />
          <YAxis
            domain={[-1, 1]}
            stroke="#666"
            fontSize={10}
            tick={{ fontSize: 9 }}
          />
          <Tooltip />
          {symbols.slice(0, 3).map(symbol => (
            <Area
              key={symbol}
              type="monotone"
              dataKey={symbol}
              stroke={getSymbolColor(symbol)}
              fill={getSymbolColor(symbol)}
              fillOpacity={0.3}
              strokeWidth={1}
              name={symbol}
            />
          ))}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}