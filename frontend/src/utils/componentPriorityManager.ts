/**
 * 组件加载优先级管理器
 * 根据用户行为和使用频率优化组件加载优先级
 */

interface ComponentPriority {
  name: string
  priority: number // 1-10, 10最高
  loadTime: number
  lastUsed: number
  useCount: number
}

class ComponentPriorityManager {
  private priorities: Map<string, ComponentPriority> = new Map()

  /**
   * 设置组件优先级
   */
  setPriority(componentName: string, priority: number) {
    const existing = this.priorities.get(componentName) || {
      name: componentName,
      priority: 5,
      loadTime: 0,
      lastUsed: 0,
      useCount: 0,
    }

    this.priorities.set(componentName, {
      ...existing,
      priority: Math.max(1, Math.min(10, priority)),
    })
  }

  /**
   * 记录组件使用
   */
  recordUsage(componentName: string, loadTime: number = 0) {
    const existing = this.priorities.get(componentName) || {
      name: componentName,
      priority: 5,
      loadTime: 0,
      lastUsed: 0,
      useCount: 0,
    }

    this.priorities.set(componentName, {
      ...existing,
      loadTime: existing.loadTime > 0 
        ? (existing.loadTime + loadTime) / 2 
        : loadTime,
      lastUsed: Date.now(),
      useCount: existing.useCount + 1,
    })

    // 动态调整优先级：使用频率越高，优先级越高
    const newPriority = Math.min(10, 5 + Math.floor(existing.useCount / 10))
    if (newPriority > existing.priority) {
      this.setPriority(componentName, newPriority)
    }
  }

  /**
   * 获取组件优先级
   */
  getPriority(componentName: string): number {
    return this.priorities.get(componentName)?.priority || 5
  }

  /**
   * 获取预加载列表（按优先级排序）
   */
  getPreloadList(): string[] {
    return Array.from(this.priorities.values())
      .sort((a, b) => b.priority - a.priority)
      .map(c => c.name)
  }

  /**
   * 生成加载策略建议
   */
  generateStrategy(): {
    immediate: string[]
    lazy: string[]
    prefetch: string[]
  } {
    const components = Array.from(this.priorities.values())
      .sort((a, b) => b.priority - a.priority)

    return {
      immediate: components
        .filter(c => c.priority >= 8)
        .map(c => c.name),
      lazy: components
        .filter(c => c.priority >= 5 && c.priority < 8)
        .map(c => c.name),
      prefetch: components
        .filter(c => c.priority < 5)
        .map(c => c.name),
    }
  }
}

// 创建全局实例
const componentPriorityManager = new ComponentPriorityManager()

// 设置默认优先级
componentPriorityManager.setPriority('ChatPage', 10)
componentPriorityManager.setPriority('ChatInterface', 10)
componentPriorityManager.setPriority('MessageBubble', 9)
componentPriorityManager.setPriority('InputBox', 9)
componentPriorityManager.setPriority('ModeSwitch', 8)
componentPriorityManager.setPriority('HistoryPage', 7)
componentPriorityManager.setPriority('WatchlistPage', 7)
componentPriorityManager.setPriority('SettingsPage', 6)
componentPriorityManager.setPriority('ResponsiveChart', 5)
componentPriorityManager.setPriority('MonitoringDashboard', 4)

export default componentPriorityManager
export { ComponentPriorityManager }
export type { ComponentPriority }

