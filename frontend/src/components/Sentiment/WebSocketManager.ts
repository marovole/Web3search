/**
 * WebSocket管理器
 * 负责管理WebSocket连接、订阅和消息处理
 */
export interface SentimentData {
  symbol: string;
  timestamp: string;
  data: {
    sentiment_score: number;
    confidence: number;
    classification: 'strong_negative' | 'negative' | 'neutral' | 'positive' | 'strong_positive';
    volume: number;
    engagement: number;
    sentiment_distribution: {
      positive: number;
      negative: number;
      neutral: number;
    };
    platform_distribution: {
      twitter: number;
      reddit: number;
      telegram: number;
      discord: number;
    };
    insights?: {
      trending_topics?: string[];
      kol_analysis?: any;
    };
    updated_at: string;
  };
}

export interface WebSocketMessage {
  type: string;
  timestamp: string;
  [key: string]: any;
}

export interface SubscriptionOptions {
  autoReconnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  heartbeatInterval?: number;
}

class WebSocketManager {
  private ws: WebSocket | null = null;
  private clientId: string | null = null;
  private subscriptions: Set<string> = new Set();
  private listeners: Map<string, ((data: any) => void)[]> = new Map();
  private reconnectAttempts = 0;
  private heartbeatTimer: NodeJS.Timeout | null = null;
  private options: Required<SubscriptionOptions>;

  constructor() {
    this.options = {
      autoReconnect: true,
      reconnectInterval: 5000,
      maxReconnectAttempts: 10,
      heartbeatInterval: 30000,
    };
  }

  /**
   * 连接WebSocket
   */
  async connect(clientId?: string): Promise<void> {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      return;
    }

    this.clientId = clientId || this.generateClientId();

    try {
      const wsUrl = `${this.getWebSocketUrl()}/api/v1/ws/sentiment/${this.clientId}`;
      this.ws = new WebSocket(wsUrl);

      await new Promise<void>((resolve, reject) => {
        const timeout = setTimeout(() => {
          reject(new Error('WebSocket连接超时'));
        }, 10000);

        this.ws!.onopen = () => {
          clearTimeout(timeout);
          this.reconnectAttempts = 0;
          this.startHeartbeat();
          console.log(`WebSocket已连接: ${this.clientId}`);
          resolve();
        };

        this.ws!.onmessage = (event) => {
          this.handleMessage(event.data);
        };

        this.ws!.onclose = (event) => {
          clearTimeout(timeout);
          console.log(`WebSocket连接已关闭: ${event.code} ${event.reason}`);
          this.stopHeartbeat();
          this.handleDisconnect();
        };

        this.ws!.onerror = (error) => {
          clearTimeout(timeout);
          console.error('WebSocket错误:', error);
          reject(error);
        };
      });
    } catch (error) {
      console.error('WebSocket连接失败:', error);
      throw error;
    }
  }

  /**
   * 断开连接
   */
  disconnect(): void {
    this.stopHeartbeat();

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    this.subscriptions.clear();
    this.reconnectAttempts = 0;
    console.log('WebSocket已断开连接');
  }

  /**
   * 订阅币种情绪数据
   */
  subscribe(symbol: string): Promise<boolean> {
    return new Promise((resolve) => {
      if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
        resolve(false);
        return;
      }

      const message = {
        type: 'subscribe',
        symbol: symbol.toUpperCase(),
      };

      this.ws.send(JSON.stringify(message));
      this.subscriptions.add(symbol.toUpperCase());

      // 监听订阅确认
      const handleSubscribe = (data: any) => {
        if (data.type === 'subscribe_response' && data.symbol === symbol.toUpperCase()) {
          this.off('subscribe_response', handleSubscribe);
          resolve(data.success);
        }
      };

      this.on('subscribe_response', handleSubscribe);

      // 5秒超时
      setTimeout(() => {
        this.off('subscribe_response', handleSubscribe);
        resolve(false);
      }, 5000);
    });
  }

  /**
   * 取消订阅币种情绪数据
   */
  unsubscribe(symbol: string): Promise<boolean> {
    return new Promise((resolve) => {
      if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
        resolve(false);
        return;
      }

      const message = {
        type: 'unsubscribe',
        symbol: symbol.toUpperCase(),
      };

      this.ws.send(JSON.stringify(message));
      this.subscriptions.delete(symbol.toUpperCase());

      // 监听取消订阅确认
      const handleUnsubscribe = (data: any) => {
        if (data.type === 'unsubscribe_response' && data.symbol === symbol.toUpperCase()) {
          this.off('unsubscribe_response', handleUnsubscribe);
          resolve(data.success);
        }
      };

      this.on('unsubscribe_response', handleUnsubscribe);

      // 5秒超时
      setTimeout(() => {
        this.off('unsubscribe_response', handleUnsubscribe);
        resolve(false);
      }, 5000);
    });
  }

  /**
   * 强制更新币种数据
   */
  forceUpdate(symbol: string): Promise<boolean> {
    return new Promise((resolve) => {
      if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
        resolve(false);
        return;
      }

      const message = {
        type: 'force_update',
        symbol: symbol.toUpperCase(),
      };

      this.ws.send(JSON.stringify(message));

      // 监听强制更新确认
      const handleForceUpdate = (data: any) => {
        if (data.type === 'force_update_response' && data.symbol === symbol.toUpperCase()) {
          this.off('force_update_response', handleForceUpdate);
          resolve(data.success);
        }
      };

      this.on('force_update_response', handleForceUpdate);

      // 5秒超时
      setTimeout(() => {
        this.off('force_update_response', handleForceUpdate);
        resolve(false);
      }, 5000);
    });
  }

  /**
   * 获取连接状态
   */
  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }

  /**
   * 获取客户端ID
   */
  getClientId(): string | null {
    return this.clientId;
  }

  /**
   * 获取订阅列表
   */
  getSubscriptions(): string[] {
    return Array.from(this.subscriptions);
  }

  /**
   * 添加事件监听器
   */
  on(event: string, callback: (data: any) => void): void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event)!.push(callback);
  }

  /**
   * 移除事件监听器
   */
  off(event: string, callback?: (data: any) => void): void {
    if (!this.listeners.has(event)) {
      return;
    }

    if (callback) {
      const callbacks = this.listeners.get(event)!;
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    } else {
      this.listeners.delete(event);
    }
  }

  /**
   * 触发事件
   */
  private emit(event: string, data: any): void {
    const callbacks = this.listeners.get(event);
    if (callbacks) {
      callbacks.forEach(callback => callback(data));
    }
  }

  /**
   * 处理接收到的消息
   */
  private handleMessage(data: string): void {
    try {
      const message: WebSocketMessage = JSON.parse(data);

      // 触发通用消息事件
      this.emit('message', message);

      // 触发特定类型事件
      this.emit(message.type, message);

      // 特殊处理情绪数据更新
      if (message.type === 'sentiment_update') {
        this.emit('sentiment_update', message as any);
      }

      // 处理错误消息
      if (message.type === 'error') {
        console.error('WebSocket错误:', message.message);
        this.emit('error', message);
      }

      // 处理ping/pong
      if (message.type === 'pong') {
        this.emit('pong', message);
      }
    } catch (error) {
      console.error('解析WebSocket消息失败:', error);
    }
  }

  /**
   * 处理连接断开
   */
  private handleDisconnect(): void {
    this.emit('disconnect', { clientId: this.clientId });

    // 自动重连
    if (this.options.autoReconnect && this.reconnectAttempts < this.options.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`尝试重连 (${this.reconnectAttempts}/${this.options.maxReconnectAttempts})...`);

      setTimeout(() => {
        this.connect(this.clientId || undefined).catch(error => {
          console.error('重连失败:', error);
        });
      }, this.options.reconnectInterval);
    }
  }

  /**
   * 开始心跳
   */
  private startHeartbeat(): void {
    this.heartbeatTimer = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'ping' }));
      }
    }, this.options.heartbeatInterval);
  }

  /**
   * 停止心跳
   */
  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  /**
   * 生成客户端ID
   */
  private generateClientId(): string {
    return `client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * 获取WebSocket URL
   */
  private getWebSocketUrl(): string {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    return `${protocol}//${host}`;
  }
}

// 创建全局WebSocket管理器实例
export const webSocketManager = new WebSocketManager();