/**
 * 情绪分析组件入口
 * 导出所有情绪相关的组件和Hook
 */

// 主要组件
export { SentimentDashboard } from './SentimentDashboard';
export { SentimentMobileDashboard } from './SentimentMobileDashboard';
export { SentimentGauge } from './SentimentGauge';
export { SentimentChart, SentimentAreaChart } from './SentimentChart';
export { PlatformComparison } from './PlatformComparison';
export { SentimentTimeline } from './SentimentTimeline';

// WebSocket管理器
export { webSocketManager } from './WebSocketManager';
export type { SentimentData, WebSocketMessage } from './WebSocketManager';

// React Hooks
export { useWebSocket } from './hooks/useWebSocket';
export { useSentimentData } from './hooks/useSentimentData';
export type { UseWebSocketOptions, UseWebSocketReturn } from './hooks/useWebSocket';
export type { UseSentimentDataOptions, UseSentimentDataReturn } from './hooks/useSentimentData';

// 性能监控
export { PerformanceMonitor } from './PerformanceMonitor';