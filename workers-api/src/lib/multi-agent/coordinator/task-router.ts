/**
 * Task Router
 * Routes tasks to appropriate agent combinations based on intent
 */

import type { TaskIntent, TaskConfig, SubAgent } from '../types'
import { getSubAgentRegistry } from '../agents/registry'

export interface TaskRoute {
  intent: TaskIntent
  agents: string[]
  priority: number
  description: string
}

export class TaskRouter {
  private routes: Map<TaskIntent, TaskRoute> = new Map()

  constructor() {
    // Define routes for each intent
    this.routes.set('comprehensive_research', {
      intent: 'comprehensive_research',
      agents: ['researcher', 'analyzer', 'risk', 'news', 'reporter'],
      priority: 1,
      description: 'Full research pipeline - all agents active',
    })

    this.routes.set('market_analysis', {
      intent: 'market_analysis',
      agents: ['researcher', 'analyzer', 'news', 'reporter'],
      priority: 2,
      description: 'Market-focused analysis - price and sentiment',
    })

    this.routes.set('token_deep_dive', {
      intent: 'token_deep_dive',
      agents: ['researcher', 'analyzer', 'risk', 'news', 'reporter'],
      priority: 1,
      description: 'Deep token analysis - all agents with focus on risk',
    })

    this.routes.set('news_synthesis', {
      intent: 'news_synthesis',
      agents: ['news', 'analyzer', 'reporter'],
      priority: 3,
      description: 'News-focused - aggregation and sentiment analysis',
    })

    this.routes.set('portfolio_review', {
      intent: 'portfolio_review',
      agents: ['researcher', 'analyzer', 'risk', 'reporter'],
      priority: 2,
      description: 'Portfolio analysis - holdings and risk assessment',
    })
  }

  /**
   * Detect intent from user query
   */
  detectIntent(query: string): TaskIntent {
    const queryLower = query.toLowerCase()

    // Pattern-based intent detection
    const patterns = {
      token_deep_dive: [
        /token\s+(address|contract)?\s*0x[a-f0-9]{40}/i,
        /\$?[A-Z]{2,8}\s+(token|coin)?\s*(analysis|review|audit)/i,
        /(audit|due\s*diligence)\s+(of|for)\s+\$?[A-Z]{2,8}/i,
      ],
      portfolio_review: [
        /(portfolio|holdings|positions)\s*(analysis|review|check)/i,
        /(my|your)\s+(portfolio|holdings)/i,
        /(assess|evaluate)\s+(my|your)\s+(investments|positions)/i,
      ],
      news_synthesis: [
        /(latest|recent)\s+(news|updates|developments)/i,
        /(summarize|summary)\s+(of\s+)?(the\s+)?(latest\s+)?(crypto|blockchain)?\s*news/i,
        /(what.?s\s+happening|whats\s+new)\s+(in\s+)?(crypto|web3)/i,
      ],
      market_analysis: [
        /(market\s+)?analysis/i,
        /(price\s+)?trend/i,
        /(should\s+i|buy|sell|invest)/i,
        /( bullish|bearish|market\s+(sentiment|outlook))/i,
      ],
    }

    // Check patterns in order of specificity
    for (const [intent, intentPatterns] of Object.entries(patterns)) {
      for (const pattern of intentPatterns) {
        if (pattern.test(queryLower)) {
          return intent as TaskIntent
        }
      }
    }

    // Default to comprehensive research for general queries
    return 'comprehensive_research'
  }

  /**
   * Get route for specific intent
   */
  getRoute(intent: TaskIntent): TaskRoute | undefined {
    return this.routes.get(intent)
  }

  /**
   * Get all routes
   */
  getAllRoutes(): TaskRoute[] {
    return Array.from(this.routes.values()).sort((a, b) => a.priority - b.priority)
  }

  /**
   * Check if intent is valid
   */
  isValidIntent(intent: string): intent is TaskIntent {
    return this.routes.has(intent as TaskIntent)
  }

  /**
   * Adjust config based on intent
   */
  adjustConfig(intent: TaskIntent, config: TaskConfig): TaskConfig {
    const adjusted = { ...config }

    // Adjust depth based on intent
    switch (intent) {
      case 'news_synthesis':
        adjusted.depth = 'quick'
        break
      case 'token_deep_dive':
        adjusted.depth = 'deep'
        break
      case 'portfolio_review':
        if (!adjusted.focusAreas) adjusted.focusAreas = ['risk', 'performance']
        break
    }

    return adjusted
  }

  /**
   * Get agent IDs for a route
   */
  getAgentIds(intent: TaskIntent): string[] {
    const route = this.routes.get(intent)
    return route?.agents || this.routes.get('comprehensive_research')!.agents
  }

  /**
   * Create a routing summary for debugging/logging
   */
  createRoutingSummary(query: string, intent: TaskIntent): string {
    const route = this.routes.get(intent)
    return `[Router] Query: "${query.slice(0, 50)}..." -> Intent: ${intent} -> Agents: ${route?.agents.join(', ')}`
  }
}

// Singleton instance
let router: TaskRouter | null = null

export function getTaskRouter(): TaskRouter {
  if (!router) {
    router = new TaskRouter()
  }
  return router
}
