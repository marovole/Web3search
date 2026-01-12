/**
 * SubAgent Registry
 * Factory and registry for all available sub-agents
 */

import type { Env } from '../../../types/env'
import type { ModelConfig } from '../../model-routing'
import type { SubAgent, SubAgentClass } from '../types'
import { ResearcherAgent } from './researcher'
import { AnalyzerAgent } from './analyzer'
import { RiskAgent } from './risk-agent'
import { NewsAgent } from './news-agent'
import { ReporterAgent } from './reporter'

export class SubAgentRegistry {
  private agents: Map<string, SubAgentClass> = new Map()
  private instances: Map<string, SubAgent> = new Map()

  constructor() {
    // Register all available agents
    this.register('researcher', ResearcherAgent)
    this.register('analyzer', AnalyzerAgent)
    this.register('risk', RiskAgent)
    this.register('news', NewsAgent)
    this.register('reporter', ReporterAgent)
  }

  /**
   * Register a new agent class
   */
  register(id: string, agentClass: SubAgentClass): void {
    this.agents.set(id, agentClass)
  }

  /**
   * Get an agent instance (creates if not exists)
   */
  getAgent(
    id: string,
    env: Env,
    modelConfig: ModelConfig
  ): SubAgent | undefined {
    const key = `${id}-${modelConfig.model}`

    if (!this.instances.has(key)) {
      const agentClass = this.agents.get(id)
      if (!agentClass) {
        return undefined
      }
      this.instances.set(key, new agentClass(env, modelConfig))
    }

    return this.instances.get(key)
  }

  /**
   * Get all registered agent IDs
   */
  getAgentIds(): string[] {
    return Array.from(this.agents.keys())
  }

  /**
   * Get agent info
   */
  getAgentInfo(id: string): { id: string; name: string; description: string; capabilities: string[] } | undefined {
    // We return static info without instantiation
    const infoMap: Record<string, { id: string; name: string; description: string; capabilities: string[] }> = {
      researcher: {
        id: 'researcher',
        name: 'Researcher',
        description: 'Information gathering agent - collects data from search, price, and news sources',
        capabilities: ['web_search', 'price_data_collection', 'news_gathering', 'social_sentiment_analysis'],
      },
      analyzer: {
        id: 'analyzer',
        name: 'Analyzer',
        description: 'Data analysis agent - identifies trends, patterns, and insights',
        capabilities: ['trend_analysis', 'pattern_recognition', 'metric_calculation', 'correlation_analysis'],
      },
      risk: {
        id: 'risk',
        name: 'RiskAgent',
        description: 'Risk assessment agent - evaluates security, scam probability, and liquidity risks',
        capabilities: ['scam_detection', 'liquidity_analysis', 'holder_distribution_analysis', 'audit_status_check'],
      },
      news: {
        id: 'news',
        name: 'NewsAgent',
        description: 'News aggregation agent - collects and analyzes news and social media',
        capabilities: ['news_collection', 'social_sentiment_analysis', 'trend_detection', 'influencer_tracking'],
      },
      reporter: {
        id: 'reporter',
        name: 'Reporter',
        description: 'Report generation agent - synthesizes all agent results into a comprehensive report',
        capabilities: ['result_synthesis', 'summary_generation', 'recommendation_creation', 'citation_management'],
      },
    }

    return infoMap[id]
  }

  /**
   * Get agents for a specific intent
   */
  getAgentsForIntent(
    intent: string,
    env: Env,
    modelConfig: ModelConfig
  ): SubAgent[] {
    const agentMap: Record<string, string[]> = {
      comprehensive_research: ['researcher', 'analyzer', 'risk', 'news', 'reporter'],
      market_analysis: ['researcher', 'analyzer', 'news', 'reporter'],
      token_deep_dive: ['researcher', 'analyzer', 'risk', 'news', 'reporter'],
      news_synthesis: ['news', 'analyzer', 'reporter'],
      portfolio_review: ['researcher', 'analyzer', 'risk', 'reporter'],
    }

    const agentIds = agentMap[intent] || agentMap.comprehensive_research

    return agentIds
      .map((id) => this.getAgent(id, env, modelConfig))
      .filter((a): a is SubAgent => a !== undefined)
  }

  /**
   * Clear all cached instances
   */
  clearCache(): void {
    this.instances.clear()
  }
}

// Singleton instance
let registry: SubAgentRegistry | null = null

export function getSubAgentRegistry(): SubAgentRegistry {
  if (!registry) {
    registry = new SubAgentRegistry()
  }
  return registry
}
