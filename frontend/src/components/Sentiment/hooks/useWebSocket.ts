/**
 * WebSocket React Hook
 * 提供WebSocket连接和数据的React集成
 */
import { useState, useEffect, useCallback, useRef } from 'react';
import { webSocketManager, SentimentData, WebSocketMessage } from '../WebSocketManager';

export interface UseWebSocketOptions {
  clientId?: string;
  autoConnect?: boolean;
  autoReconnect?: boolean;
}

export interface UseWebSocketReturn {
  isConnected: boolean;
  clientId: string | null;
  subscriptions: string[];
  error: string | null;
  lastMessage: WebSocketMessage | null;
  sentimentData: Record<string, SentimentData>;
  connect: () => Promise<void>;
  disconnect: () => void;
  subscribe: (symbol: string) => Promise<boolean>;
  unsubscribe: (symbol: string) => Promise<boolean>;
  forceUpdate: (symbol: string) => Promise<boolean>;
  clearError: () => void;
}

export function useWebSocket(options: UseWebSocketOptions = {}): UseWebSocketReturn {
  const {
    clientId: initialClientId,
    autoConnect = true,
    autoReconnect = true
  } = options;

  // 状态管理
  const [isConnected, setIsConnected] = useState(false);
  const [clientId, setClientId] = useState<string | null>(initialClientId || null);
  const [subscriptions, setSubscriptions] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [sentimentData, setSentimentData] = useState<Record<string, SentimentData>>({});

  // 使用ref来避免重复的事件监听器
  const managerRef = useRef(webSocketManager);

  // 清除错误
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // 连接WebSocket
  const connect = useCallback(async () => {
    try {
      setError(null);
      await managerRef.current.connect(initialClientId);
      setClientId(managerRef.current.getClientId());
    } catch (err) {
      setError(err instanceof Error ? err.message : '连接失败');
    }
  }, [initialClientId]);

  // 断开连接
  const disconnect = useCallback(() => {
    managerRef.current.disconnect();
    setClientId(null);
    setSubscriptions([]);
    clearError();
  }, [clearError]);

  // 订阅币种
  const subscribe = useCallback(async (symbol: string): Promise<boolean> => {
    try {
      clearError();
      const success = await managerRef.current.subscribe(symbol);
      if (success) {
        setSubscriptions(managerRef.current.getSubscriptions());
      }
      return success;
    } catch (err) {
      setError(err instanceof Error ? err.message : '订阅失败');
      return false;
    }
  }, [clearError]);

  // 取消订阅
  const unsubscribe = useCallback(async (symbol: string): Promise<boolean> => {
    try {
      clearError();
      const success = await managerRef.current.unsubscribe(symbol);
      if (success) {
        setSubscriptions(managerRef.current.getSubscriptions());
      }
      return success;
    } catch (err) {
      setError(err instanceof Error ? err.message : '取消订阅失败');
      return false;
    }
  }, [clearError]);

  // 强制更新
  const forceUpdate = useCallback(async (symbol: string): Promise<boolean> => {
    try {
      clearError();
      return await managerRef.current.forceUpdate(symbol);
    } catch (err) {
      setError(err instanceof Error ? err.message : '强制更新失败');
      return false;
    }
  }, [clearError]);

  // 设置事件监听器
  useEffect(() => {
    const manager = managerRef.current;

    // 连接状态变化
    const handleConnect = () => {
      setIsConnected(true);
      setClientId(manager.getClientId());
      clearError();
    };

    const handleDisconnect = () => {
      setIsConnected(false);
      setSubscriptions([]);
    };

    // 消息处理
    const handleMessage = (message: WebSocketMessage) => {
      setLastMessage(message);
    };

    // 情绪数据更新
    const handleSentimentUpdate = (message: any) => {
      if (message.symbol && message.data) {
        setSentimentData(prev => ({
          ...prev,
          [message.symbol]: message.data
        }));
      }
    };

    // 错误处理
    const handleError = (message: any) => {
      setError(message.message);
    };

    // 注册监听器
    manager.on('connection_established', handleConnect);
    manager.on('disconnect', handleDisconnect);
    manager.on('message', handleMessage);
    manager.on('sentiment_update', handleSentimentUpdate);
    manager.on('error', handleError);

    // 清理函数
    return () => {
      manager.off('connection_established', handleConnect);
      manager.off('disconnect', handleDisconnect);
      manager.off('message', handleMessage);
      manager.off('sentiment_update', handleSentimentUpdate);
      manager.off('error', handleError);
    };
  }, [clearError]);

  // 自动连接
  useEffect(() => {
    if (autoConnect && !isConnected) {
      connect();
    }
  }, [autoConnect, isConnected, connect]);

  // 组件卸载时断开连接
  useEffect(() => {
    return () => {
      if (autoReconnect) {
        disconnect();
      }
    };
  }, [autoReconnect, disconnect]);

  return {
    isConnected,
    clientId,
    subscriptions,
    error,
    lastMessage,
    sentimentData,
    connect,
    disconnect,
    subscribe,
    unsubscribe,
    forceUpdate,
    clearError,
  };
}