/**
 * Multi-Agent Framework Type Definitions
 * Based on DeepResearch CentralCoordinator + SubAgent pattern
 */

import type { Env } from '../../types/env'
import type { ModelConfig } from '../model-routing'
import type { ISSEEmitter } from '../../services/deep-research/types'

// ============================================================================
// Task Types
// ============================================================================

export type TaskIntent =
  | 'comprehensive_research'
  | 'market_analysis'
  | 'token_deep_dive'
  | 'news_synthesis'
  | 'portfolio_review'

export type TaskStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'

export interface TaskConfig {
  depth: 'quick' | 'standard' | 'deep'
  outputFormat: 'summary' | 'detailed' | 'report'
  focusAreas?: string[]
  maxAgents?: number
  timeout?: number
}

export interface MultiAgentTask {
  id: string
  userId: string
  query: string
  intent: TaskIntent
  config: TaskConfig
  createdAt: string
  deadline?: string
}

// ============================================================================
// Context Types
// ============================================================================

export interface SharedContext {
  taskId: string
  originalQuery: string
  userId: string
  env: Env
  modelConfig: ModelConfig
  collectedData: CollectedData
  agentResults: Map<string, AgentResult>
  startTime: number
}

export interface CollectedData {
  searchResults: NormalizedSearchResult[]
  priceData: PriceDataMap
  riskMetrics: RiskMetricMap
  newsArticles: NewsArticle[]
  portfolioData?: PortfolioData
  socialMetrics?: SocialMetricMap
}

export interface NormalizedSearchResult {
  id: string
  title: string
  url: string
  snippet: string
  relevanceScore: number
  provider: string
  publishedAt?: string
}

export interface PriceDataMap {
  [tokenAddress: string]: TokenPriceData
}

export interface TokenPriceData {
  symbol: string
  name: string
  currentPrice: number
  priceChange24h: number
  marketCap: number
  volume24h: number
  liquidity: number
}

export interface RiskMetricMap {
  [tokenAddress: string]: RiskAssessment
}

export interface RiskAssessment {
  overallScore: number // 0-100, higher is riskier
  scamProbability: number
  liquidityRisk: number
  concentrationRisk: number
  contractRisk: number
  redFlags: string[]
  auditStatus: 'verified' | 'pending' | 'failed' | 'unknown'
  holderDistribution?: HolderStats
}

export interface HolderStats {
  top10HolderPercent: number
  totalHolders: number
  deployerBalancePercent: number
}

export interface NewsArticle {
  id: string
  title: string
  url: string
  source: string
  publishedAt: string
  sentiment: 'positive' | 'negative' | 'neutral'
  engagement: number
  snippet: string
}

export interface SocialMetricMap {
  [tokenAddress: string]: SocialMetrics
}

export interface SocialMetrics {
  twitterFollowers?: number
  discordMembers?: number
  telegramMembers?: number
  holderCount: number
  sentimentScore: number // -1 to 1
  recentMentions: number
}

export interface PortfolioData {
  totalValue: number
  pnl24h: number
  pnl7d: number
  holdings: Holding[]
}

export interface Holding {
  tokenAddress: string
  symbol: string
  balance: number
  value: number
  percentOfPortfolio: number
}

// ============================================================================
// Agent Types
// ============================================================================

export type AgentStatus = 'pending' | 'running' | 'completed' | 'failed'

export interface AgentInput {
  taskId: string
  query: string
  focusArea?: string
  dependentResults?: string[]
}

export interface AgentResult {
  agentId: string
  agentName: string
  status: AgentStatus
  output: unknown
  metrics: {
    tokensUsed: number
    duration: number
    sourcesProcessed: number
  }
  error?: string
}

export interface SubAgent {
  readonly id: string
  readonly name: string
  readonly description: string
  readonly capabilities: string[]
  readonly inputRequirements: string[]

  execute(
    context: SharedContext,
    input: AgentInput,
    emitter?: ISSEEmitter
  ): Promise<AgentResult>

  validateInput(input: AgentInput): { valid: boolean; missing: string[] }
}

export interface SubAgentClass {
  new (env: Env, modelConfig: ModelConfig): SubAgent
}

// ============================================================================
// Coordinator Types
// ============================================================================

export interface CoordinatorResult {
  taskId: string
  success: boolean
  output: AggregatedResult | null
  tokensUsed: number
  duration: number
  error?: string
}

export interface AggregatedResult {
  summary: string
  sections: ResultSection[]
  keyFindings: string[]
  recommendations: string[]
  citations: SourceCitation[]
  confidenceScore: number
}

export interface ResultSection {
  title: string
  content: string
  agentSource?: string
  importance: 'high' | 'medium' | 'low'
}

export interface SourceCitation {
  sourceId: string
  title: string
  url: string
  snippet: string
  relevanceScore: number
}

// ============================================================================
// Model Response Types
// ============================================================================

export interface ModelResponse {
  id: string
  object: string
  created: number
  model: string
  choices: Array<{
    index: number
    message: {
      role: string
      content: string
    }
    finish_reason: string
  }>
  usage: {
    prompt_tokens: number
    completion_tokens: number
    total_tokens: number
  }
}

// ============================================================================
// Event Types
// ============================================================================

export interface MultiAgentSSEEvent {
  type: 'progress' | 'agent_start' | 'agent_complete' | 'agent_error' | 'content' | 'complete' | 'error'
  timestamp: string
  taskId: string
  data?: Record<string, unknown>
}

export interface AgentProgressEvent {
  agentId: string
  agentName: string
  stage: string
  message: string
  progressPercent?: number
}
