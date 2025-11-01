/**
 * 情绪数据React Hook
 * 提供情绪数据的状态管理和处理逻辑
 */
import { useState, useEffect, useCallback } from 'react';
import { SentimentData } from '../WebSocketManager';
import { useWebSocket } from './useWebSocket';

export interface UseSentimentDataOptions {
  symbols: string[];
  autoSubscribe?: boolean;
  updateInterval?: number;
}

export interface SentimentStats {
  averageScore: number;
  totalVolume: number;
  totalEngagement: number;
  positivePercentage: number;
  negativePercentage: number;
  neutralPercentage: number;
}

export interface PlatformStats {
  [platform: string]: {
    score: number;
    volume: number;
    percentage: number;
  };
}

export interface UseSentimentDataReturn {
  sentimentData: Record<string, SentimentData>;
  isLoading: boolean;
  error: string | null;
  isConnected: boolean;
  stats: SentimentStats | null;
  platformStats: PlatformStats | null;
  subscribe: (symbol: string) => Promise<boolean>;
  unsubscribe: (symbol: string) => Promise<boolean>;
  refreshData: (symbol?: string) => Promise<void>;
  clearError: () => void;
}

export function useSentimentData(options: UseSentimentDataOptions): UseSentimentDataReturn {
  const { symbols, autoSubscribe = true } = options;

  // WebSocket连接
  const {
    sentimentData,
    isConnected,
    error,
    subscribe: wsSubscribe,
    unsubscribe: wsUnsubscribe,
    forceUpdate,
    clearError
  } = useWebSocket();

  // 本地状态
  const [isLoading, setIsLoading] = useState(false);
  const [subscriptionStatus, setSubscriptionStatus] = useState<Record<string, boolean>>({});

  // 计算统计数据
  const stats = calculateStats(sentimentData);
  const platformStats = calculatePlatformStats(sentimentData);

  // 订阅币种
  const subscribe = useCallback(async (symbol: string): Promise<boolean> => {
    setIsLoading(true);
    try {
      const success = await wsSubscribe(symbol.toUpperCase());
      setSubscriptionStatus(prev => ({
        ...prev,
        [symbol.toUpperCase()]: success
      }));
      return success;
    } finally {
      setIsLoading(false);
    }
  }, [wsSubscribe]);

  // 取消订阅
  const unsubscribe = useCallback(async (symbol: string): Promise<boolean> => {
    setIsLoading(true);
    try {
      const success = await wsUnsubscribe(symbol.toUpperCase());
      setSubscriptionStatus(prev => {
        const newStatus = { ...prev };
        delete newStatus[symbol.toUpperCase()];
        return newStatus;
      });
      return success;
    } finally {
      setIsLoading(false);
    }
  }, [wsUnsubscribe]);

  // 刷新数据
  const refreshData = useCallback(async (symbol?: string): Promise<void> => {
    if (symbol) {
      setIsLoading(true);
      try {
        await forceUpdate(symbol.toUpperCase());
      } finally {
        setIsLoading(false);
      }
    } else {
      // 批量刷新所有订阅的币种
      const subscriptions = Object.keys(subscriptionStatus);
      setIsLoading(true);
      try {
        await Promise.all(
          subscriptions.map(s => forceUpdate(s))
        );
      } finally {
        setIsLoading(false);
      }
    }
  }, [forceUpdate, subscriptionStatus]);

  // 自动订阅指定的币种
  useEffect(() => {
    if (isConnected && autoSubscribe && symbols.length > 0) {
      symbols.forEach(symbol => {
        if (!subscriptionStatus[symbol.toUpperCase()]) {
          subscribe(symbol);
        }
      });
    }
  }, [isConnected, autoSubscribe, symbols, subscriptionStatus, subscribe]);

  // 清理不再需要的订阅
  useEffect(() => {
    const currentSubscriptions = Object.keys(subscriptionStatus);
    const wantedSubscriptions = symbols.map(s => s.toUpperCase());

    currentSubscriptions.forEach(symbol => {
      if (!wantedSubscriptions.includes(symbol)) {
        unsubscribe(symbol);
      }
    });
  }, [symbols, subscriptionStatus, unsubscribe]);

  return {
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
  };
}

/**
 * 计算总体统计数据
 */
function calculateStats(sentimentData: Record<string, SentimentData>): SentimentStats | null {
  const symbols = Object.keys(sentimentData);
  if (symbols.length === 0) {
    return null;
  }

  let totalScore = 0;
  let totalVolume = 0;
  let totalEngagement = 0;
  let positiveCount = 0;
  let negativeCount = 0;
  let neutralCount = 0;

  symbols.forEach(symbol => {
    const data = sentimentData[symbol];
    totalScore += data.data.sentiment_score;
    totalVolume += data.data.volume;
    totalEngagement += data.data.engagement;

    const classification = data.data.classification;
    if (classification === 'positive' || classification === 'strong_positive') {
      positiveCount++;
    } else if (classification === 'negative' || classification === 'strong_negative') {
      negativeCount++;
    } else {
      neutralCount++;
    }
  });

  const total = symbols.length;

  return {
    averageScore: totalScore / total,
    totalVolume,
    totalEngagement,
    positivePercentage: (positiveCount / total) * 100,
    negativePercentage: (negativeCount / total) * 100,
    neutralPercentage: (neutralCount / total) * 100
  };
}

/**
 * 计算平台统计数据
 */
function calculatePlatformStats(sentimentData: Record<string, SentimentData>): PlatformStats | null {
  const symbols = Object.keys(sentimentData);
  if (symbols.length === 0) {
    return null;
  }

  const platformTotals: Record<string, { score: number; volume: number; count: number }> = {};

  symbols.forEach(symbol => {
    const data = sentimentData[symbol];
    const platformDistribution = data.data.platform_distribution;

    Object.entries(platformDistribution).forEach(([platform, score]) => {
      if (!platformTotals[platform]) {
        platformTotals[platform] = { score: 0, volume: 0, count: 0 };
      }
      platformTotals[platform].score += score;
      platformTotals[platform].volume += data.data.volume;
      platformTotals[platform].count++;
    });
  });

  const platformStats: PlatformStats = {};
  let totalVolume = 0;

  // 计算平均分数和百分比
  Object.entries(platformTotals).forEach(([platform, totals]) => {
    const avgScore = totals.score / totals.count;
    platformStats[platform] = {
      score: avgScore,
      volume: totals.volume,
      percentage: 0 // 稍后计算
    };
    totalVolume += totals.volume;
  });

  // 计算百分比
  Object.entries(platformStats).forEach(([platform, stats]) => {
    stats.percentage = totalVolume > 0 ? (stats.volume / totalVolume) * 100 : 0;
  });

  return platformStats;
}