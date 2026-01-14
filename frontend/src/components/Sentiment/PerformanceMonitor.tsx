/**
 * 性能监控组件
 * 监控WebSocket连接性能和前端渲染性能
 */
import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useWebSocket } from './hooks/useWebSocket';
import { Activity, Zap, AlertTriangle, CheckCircle, Timer, Wifi, WifiOff } from 'lucide-react';
import { safeToFixed } from '@/lib/safeFormatters';

interface PerformanceMetrics {
  connectionLatency: number;
  messageFrequency: number;
  renderTime: number;
  memoryUsage: number;
  connectionQuality: 'excellent' | 'good' | 'poor' | 'disconnected';
  uptime: number;
  messagesReceived: number;
  errorsCount: number;
}

interface PerformanceMonitorProps {
  className?: string;
  symbols?: string[];
}

export function PerformanceMonitor({
  className,
  symbols = ['BTC', 'ETH']
}: PerformanceMonitorProps) {
  const [metrics, setMetrics] = useState<PerformanceMetrics>({
    connectionLatency: 0,
    messageFrequency: 0,
    renderTime: 0,
    memoryUsage: 0,
    connectionQuality: 'disconnected',
    uptime: 0,
    messagesReceived: 0,
    errorsCount: 0
  });

  const [isMonitoring, setIsMonitoring] = useState(false);
  const [latencyHistory, setLatencyHistory] = useState<number[]>([]);
  const [messageTimestamps, setMessageTimestamps] = useState<number[]>([]);

  const startTimeRef = useRef<number>(Date.now());
  const frameCountRef = useRef<number>(0);
  const lastFrameTimeRef = useRef<number>(Date.now());

  const {
    isConnected,
    lastMessage,
    error,
    connect,
    disconnect
  } = useWebSocket({
    symbols,
    autoConnect: false
  });

  // 计算连接质量
  const calculateConnectionQuality = (latency: number): 'excellent' | 'good' | 'poor' | 'disconnected' => {
    if (!isConnected) return 'disconnected';
    if (latency < 50) return 'excellent';
    if (latency < 150) return 'good';
    return 'poor';
  };

  // 测量连接延迟
  const measureLatency = async () => {
    if (!isConnected) return 0;

    const startTime = performance.now();
    try {
      // 发送ping消息并等待响应
      const response = await fetch('/health', {
        method: 'GET',
        cache: 'no-cache'
      });
      const endTime = performance.now();
      return endTime - startTime;
    } catch {
      return 0;
    }
  };

  // 监控渲染性能
  const measureRenderPerformance = () => {
    frameCountRef.current++;
    const currentTime = Date.now();

    if (currentTime - lastFrameTimeRef.current >= 1000) {
      const fps = frameCountRef.current;
      const frameTime = 1000 / fps;

      setMetrics(prev => ({
        ...prev,
        renderTime: frameTime
      }));

      frameCountRef.current = 0;
      lastFrameTimeRef.current = currentTime;
    }

    requestAnimationFrame(measureRenderPerformance);
  };

  // 获取内存使用情况
  const getMemoryUsage = () => {
    if ('memory' in performance) {
      const memory = (performance as any).memory;
      return memory.usedJSHeapSize / 1024 / 1024; // MB
    }
    return 0;
  };

  // 更新消息频率
  const updateMessageFrequency = () => {
    const now = Date.now();
    const recentMessages = messageTimestamps.filter(
      timestamp => now - timestamp < 5000 // 5秒内的消息
    );

    const frequency = recentMessages.length / 5; // 每秒消息数
    setMessageTimestamps(recentMessages);

    setMetrics(prev => ({
      ...prev,
      messageFrequency: frequency
    }));
  };

  // 性能监控循环
  useEffect(() => {
    if (!isMonitoring) return;

    const monitoringInterval = setInterval(async () => {
      const latency = await measureLatency();
      const memoryUsage = getMemoryUsage();
      const uptime = (Date.now() - startTimeRef.current) / 1000;

      setLatencyHistory(prev => {
        const newHistory = [...prev, latency];
        return newHistory.slice(-20); // 保留最近20个数据点
      });

      setMetrics(prev => ({
        ...prev,
        connectionLatency: latency,
        memoryUsage,
        connectionQuality: calculateConnectionQuality(latency),
        uptime,
        messagesReceived: prev.messagesReceived + (lastMessage ? 1 : 0),
        errorsCount: prev.errorsCount + (error ? 1 : 0)
      }));

      updateMessageFrequency();
    }, 2000); // 每2秒更新一次

    return () => clearInterval(monitoringInterval);
  }, [isMonitoring, isConnected, lastMessage, error]);

  // 监听消息
  useEffect(() => {
    if (lastMessage) {
      setMessageTimestamps(prev => [...prev, Date.now()]);
    }
  }, [lastMessage]);

  // 启动渲染性能监控
  useEffect(() => {
    const animationId = requestAnimationFrame(measureRenderPerformance);
    return () => cancelAnimationFrame(animationId);
  }, []);

  // 开始/停止监控
  const toggleMonitoring = () => {
    if (isMonitoring) {
      setIsMonitoring(false);
    } else {
      setIsMonitoring(true);
      startTimeRef.current = Date.now();
      if (!isConnected) {
        reconnect();
      }
    }
  };

  // 获取连接质量颜色
  const getQualityColor = (quality: string) => {
    switch (quality) {
      case 'excellent': return 'text-green-600 bg-green-50';
      case 'good': return 'text-blue-600 bg-blue-50';
      case 'poor': return 'text-yellow-600 bg-yellow-50';
      case 'disconnected': return 'text-red-600 bg-red-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  // 获取连接质量图标
  const getQualityIcon = (quality: string) => {
    switch (quality) {
      case 'excellent': return <CheckCircle className="w-4 h-4" />;
      case 'good': return <Wifi className="w-4 h-4" />;
      case 'poor': return <AlertTriangle className="w-4 h-4" />;
      case 'disconnected': return <WifiOff className="w-4 h-4" />;
      default: return <Activity className="w-4 h-4" />;
    }
  };

  return (
    <div className={`space-y-4 ${className}`}>
      {/* 控制面板 */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base">性能监控</CardTitle>
            <Button
              variant={isMonitoring ? "destructive" : "default"}
              size="sm"
              onClick={toggleMonitoring}
            >
              {isMonitoring ? '停止监控' : '开始监控'}
            </Button>
          </div>
        </CardHeader>
      </Card>

      {isMonitoring && (
        <>
          {/* 连接状态 */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm">连接状态</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <div className="flex items-center space-x-2">
                  {getQualityIcon(metrics.connectionQuality)}
                  <div>
                    <div className="text-xs text-muted-foreground">连接质量</div>
                    <Badge className={getQualityColor(metrics.connectionQuality)}>
                      {metrics.connectionQuality}
                    </Badge>
                  </div>
                </div>
                <div>
                  <div className="text-xs text-muted-foreground">延迟</div>
                  <div className="text-sm font-bold">
                    {safeToFixed(metrics.connectionLatency, 0, '0')}ms
                  </div>
                </div>
                <div>
                  <div className="text-xs text-muted-foreground">运行时间</div>
                  <div className="text-sm font-bold">
                    {Math.floor(metrics.uptime / 60)}m {Math.floor(metrics.uptime % 60)}s
                  </div>
                </div>
                <div>
                  <div className="text-xs text-muted-foreground">消息频率</div>
                  <div className="text-sm font-bold">
                    {safeToFixed(metrics.messageFrequency, 1, '0.0')}/s
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 性能指标 */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm">性能指标</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-xs text-muted-foreground">渲染时间</div>
                  <div className="text-sm font-bold">
                    {safeToFixed(metrics.renderTime, 1, '0.0')}ms
                  </div>
                </div>
                <div>
                  <div className="text-xs text-muted-foreground">内存使用</div>
                  <div className="text-sm font-bold">
                    {safeToFixed(metrics.memoryUsage, 1, '0.0')}MB
                  </div>
                </div>
                <div>
                  <div className="text-xs text-muted-foreground">接收消息</div>
                  <div className="text-sm font-bold text-green-600">
                    {metrics.messagesReceived}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-muted-foreground">错误次数</div>
                  <div className="text-sm font-bold text-red-600">
                    {metrics.errorsCount}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 延迟历史图表 */}
          {latencyHistory.length > 0 && (
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm">延迟历史</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-end space-x-1 h-16">
                  {latencyHistory.map((latency, index) => {
                    const height = Math.min((latency / 500) * 100, 100);
                    const color = latency < 50 ? 'bg-green-500' :
                                 latency < 150 ? 'bg-blue-500' :
                                 latency < 300 ? 'bg-yellow-500' : 'bg-red-500';

                    return (
                      <div
                        key={index}
                        className={`flex-1 ${color} rounded-t`}
                        style={{ height: `${height}%` }}
                        title={`${safeToFixed(latency, 0, '0')}ms`}
                      />
                    );
                  })}
                </div>
                <div className="flex justify-between text-xs text-muted-foreground mt-1">
                  <span>0ms</span>
                  <span>历史记录 ({latencyHistory.length})</span>
                  <span>500ms+</span>
                </div>
              </CardContent>
            </Card>
          )}

          {/* 优化建议 */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm">优化建议</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {metrics.connectionLatency > 200 && (
                  <div className="flex items-center space-x-2 text-yellow-600">
                    <Zap className="w-4 h-4" />
                    <span className="text-sm">
                      连接延迟较高，建议检查网络连接
                    </span>
                  </div>
                )}
                {metrics.renderTime > 16.67 && (
                  <div className="flex items-center space-x-2 text-yellow-600">
                    <Timer className="w-4 h-4" />
                    <span className="text-sm">
                      渲染时间较长，考虑优化组件或减少数据更新频率
                    </span>
                  </div>
                )}
                {metrics.memoryUsage > 100 && (
                  <div className="flex items-center space-x-2 text-yellow-600">
                    <AlertTriangle className="w-4 h-4" />
                    <span className="text-sm">
                      内存使用较高，建议清理不必要的数据缓存
                    </span>
                  </div>
                )}
                {metrics.connectionQuality === 'excellent' &&
                 metrics.renderTime < 16.67 &&
                 metrics.memoryUsage < 50 && (
                  <div className="flex items-center space-x-2 text-green-600">
                    <CheckCircle className="w-4 h-4" />
                    <span className="text-sm">
                      性能表现优秀！
                    </span>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}