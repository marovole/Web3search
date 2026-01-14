/**
 * Context Manager
 * Manages shared context across agents
 */

import type { SharedContext, AgentResult } from '../types'

export class ContextManager {
  private contexts: Map<string, SharedContext> = new Map()
  private readonly maxContexts = 100 // Limit concurrent contexts
  private readonly contextTimeout = 30 * 60 * 1000 // 30 minutes

  /**
   * Create or get context for a task
   */
  getOrCreate(taskId: string, factory: () => SharedContext): SharedContext {
    let context = this.contexts.get(taskId)

    if (!context) {
      if (this.contexts.size >= this.maxContexts) {
        this.cleanupStaleContexts()
      }
      context = factory()
      this.contexts.set(taskId, context)
    }

    return context
  }

  /**
   * Get existing context
   */
  get(taskId: string): SharedContext | undefined {
    return this.contexts.get(taskId)
  }

  /**
   * Delete context when task is complete
   */
  delete(taskId: string): void {
    const context = this.contexts.get(taskId)
    if (context) {
      // Clean up any references
      context.agentResults.clear()
      this.contexts.delete(taskId)
    }
  }

  /**
   * Store agent result in context
   */
  storeResult(taskId: string, result: AgentResult): void {
    const context = this.contexts.get(taskId)
    if (context) {
      context.agentResults.set(result.agentId, result)
    }
  }

  /**
   * Get all results from context
   */
  getResults(taskId: string): AgentResult[] {
    const context = this.contexts.get(taskId)
    if (!context) {
      return []
    }
    return Array.from(context.agentResults.values())
  }

  /**
   * Update collected data
   */
  updateCollectedData(
    taskId: string,
    updates: Partial<SharedContext['collectedData']>
  ): void {
    const context = this.contexts.get(taskId)
    if (context) {
      context.collectedData = {
        ...context.collectedData,
        ...updates,
      }
    }
  }

  /**
   * Get data from context
   */
  getCollectedData(taskId: string): SharedContext['collectedData'] | undefined {
    return this.contexts.get(taskId)?.collectedData
  }

  /**
   * Check if context exists
   */
  has(taskId: string): boolean {
    return this.contexts.has(taskId)
  }

  /**
   * Get context count
   */
  size(): number {
    return this.contexts.size
  }

  /**
   * Clean up stale contexts
   */
  private cleanupStaleContexts(): void {
    const now = Date.now()
    const staleThreshold = now - this.contextTimeout

    for (const [taskId, context] of this.contexts.entries()) {
      if (context.startTime < staleThreshold) {
        this.contexts.delete(taskId)
      }
    }

    // If still too many, delete oldest half
    if (this.contexts.size >= this.maxContexts) {
      const entries = Array.from(this.contexts.entries())
        .sort((a, b) => a[1].startTime - b[1].startTime)
        .slice(0, Math.floor(this.maxContexts / 2))

      entries.forEach(([taskId]) => {
        this.contexts.delete(taskId)
      })
    }
  }

  /**
   * Clear all contexts (for testing or reset)
   */
  clear(): void {
    this.contexts.clear()
  }

  /**
   * Export context for debugging
   */
  export(taskId: string): Record<string, unknown> | undefined {
    const context = this.contexts.get(taskId)
    if (!context) return undefined

    return {
      taskId: context.taskId,
      originalQuery: context.originalQuery,
      userId: context.userId,
      agentCount: context.agentResults.size,
      searchResultsCount: context.collectedData.searchResults.length,
      priceDataCount: Object.keys(context.collectedData.priceData).length,
      riskMetricsCount: Object.keys(context.collectedData.riskMetrics).length,
      newsArticlesCount: context.collectedData.newsArticles.length,
      duration: Date.now() - context.startTime,
    }
  }
}

// Singleton instance
let manager: ContextManager | null = null

export function getContextManager(): ContextManager {
  if (!manager) {
    manager = new ContextManager()
  }
  return manager
}
