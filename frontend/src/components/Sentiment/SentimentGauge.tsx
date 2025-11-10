/**
 * 情绪指示器组件
 * 显示单个币种的实时情绪状态
 */
import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { SentimentData } from './WebSocketManager';
import { coerceFiniteNumber, formatPercentage, formatScore, safeToFixed } from '@/lib/safeFormatters';

interface SentimentGaugeProps {
  symbol: string;
  data?: SentimentData;
  isLoading?: boolean;
  className?: string;
}

export function SentimentGauge({
  symbol,
  data,
  isLoading = false,
  className
}: SentimentGaugeProps) {
  const getSentimentColor = (score: number) => {
    if (score >= 0.6) return 'text-green-600';
    if (score >= 0.2) return 'text-blue-600';
    if (score >= -0.2) return 'text-gray-600';
    if (score >= -0.6) return 'text-orange-600';
    return 'text-red-600';
  };

  const getSentimentBgColor = (score: number) => {
    if (score >= 0.6) return 'bg-green-100';
    if (score >= 0.2) return 'bg-blue-100';
    if (score >= -0.2) return 'bg-gray-100';
    if (score >= -0.6) return 'bg-orange-100';
    return 'bg-red-100';
  };

  const getClassificationLabel = (classification: string) => {
    switch (classification) {
      case 'strong_positive':
        return { label: '强烈积极', color: 'bg-green-500' };
      case 'positive':
        return { label: '积极', color: 'bg-green-400' };
      case 'neutral':
        return { label: '中性', color: 'bg-gray-400' };
      case 'negative':
        return { label: '消极', color: 'bg-orange-400' };
      case 'strong_negative':
        return { label: '强烈消极', color: 'bg-red-500' };
      default:
        return { label: '未知', color: 'bg-gray-400' };
    }
  };

  const formatNumber = (value: unknown) => {
    const num = coerceFiniteNumber(value);
    if (num === null) return 'N/A';
    if (num >= 1000000) {
      return `${safeToFixed(num / 1000000, 1, '0')}M`;
    }
    if (num >= 1000) {
      return `${safeToFixed(num / 1000, 1, '0')}K`;
    }
    return safeToFixed(num, 0, '0');
  };

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader className="pb-3">
          <CardTitle className="text-lg">{symbol}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="h-16 bg-gray-100 rounded animate-pulse" />
            <div className="space-y-2">
              <div className="h-4 bg-gray-100 rounded animate-pulse" />
              <div className="h-4 bg-gray-100 rounded animate-pulse w-3/4" />
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!data) {
    return (
      <Card className={className}>
        <CardHeader className="pb-3">
          <CardTitle className="text-lg">{symbol}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center text-muted-foreground py-8">
            暂无数据
          </div>
        </CardContent>
      </Card>
    );
  }

  const { sentiment_score, confidence, classification, volume, engagement, sentiment_distribution } = data.data;
  const sentimentInfo = getClassificationLabel(classification);

  return (
    <Card className={className}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">{symbol}</CardTitle>
          <Badge variant="secondary" className={sentimentInfo.color}>
            {sentimentInfo.label}
          </Badge>
        </div>
      </CardHeader>

      <CardContent>
        <div className="space-y-4">
          {/* 主要情绪分数 */}
          <div className="text-center">
            <div className={`text-3xl font-bold ${getSentimentColor(sentiment_score)}`}>
              {formatScore(sentiment_score, 3, '0.000')}
            </div>
            <div className="text-sm text-muted-foreground">情绪分数</div>
          </div>

          {/* 置信度 */}
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>置信度</span>
              <span>{formatPercentage(confidence * 100, 1, '0.0%')}</span>
            </div>
            <Progress value={confidence * 100} className="h-2" />
          </div>

          {/* 情绪分布 */}
          {sentiment_distribution && (
            <div className="space-y-2">
              <div className="text-sm font-medium">情绪分布</div>
              <div className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span>积极</span>
                  <span>{formatPercentage(sentiment_distribution.positive, 1, '0.0%')}</span>
                </div>
                <Progress
                  value={sentiment_distribution.positive}
                  className="h-1 bg-green-200"
                />
                <div className="flex justify-between text-xs">
                  <span>中性</span>
                  <span>{formatPercentage(sentiment_distribution.neutral, 1, '0.0%')}</span>
                </div>
                <Progress
                  value={sentiment_distribution.neutral}
                  className="h-1 bg-gray-200"
                />
                <div className="flex justify-between text-xs">
                  <span>消极</span>
                  <span>{formatPercentage(sentiment_distribution.negative, 1, '0.0%')}</span>
                </div>
                <Progress
                  value={sentiment_distribution.negative}
                  className="h-1 bg-red-200"
                />
              </div>
            </div>
          )}

          {/* 数据量指标 */}
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <div className="text-muted-foreground">讨论量</div>
              <div className="font-medium">{formatNumber(volume)}</div>
            </div>
            <div>
              <div className="text-muted-foreground">参与度</div>
              <div className="font-medium">{formatNumber(engagement)}</div>
            </div>
          </div>

          {/* 平台分布预览 */}
          {data.data.platform_distribution && (
            <div className="space-y-2">
              <div className="text-sm font-medium">平台分布</div>
              <div className="flex flex-wrap gap-1">
                {Object.entries(data.data.platform_distribution).map(([platform, score]) => (
                  <Badge
                    key={platform}
                    variant="outline"
                    className="text-xs"
                  >
                    {platform}: {formatScore(score, 2, '0.00')}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* 更新时间 */}
          <div className="text-xs text-muted-foreground text-center">
            更新时间: {new Date(data.data.updated_at).toLocaleTimeString()}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}