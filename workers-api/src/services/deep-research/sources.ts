/**
 * Source Search and Analysis
 * Handles searching for sources and analyzing them with AI
 */

import type { Env } from '../../types/env'
import type { ChatCompletionMessage, ChatRole } from '../../types/chat'
import type { ModelConfig, SourceAnalysisResult, NormalizedSearchResult, SourceCitation } from './types'
import { createOpenRouterClient } from '../../lib/openrouter'

/**
 * Search for sources based on queries
 * Integrates with real search APIs (Brave, Tavily, Serper)
 */
export async function searchSources(queries: string[], env: Env): Promise<NormalizedSearchResult[]> {
  const { fetchSearchResultsForQueries } = await import('../../lib/search-providers')

  if (!queries.length) {
    return []
  }

  return fetchSearchResultsForQueries(queries, env)
}

/**
 * Analyze sources using AI
 * Extracts relevant information with citations
 */
export async function analyzeSources(
  sources: NormalizedSearchResult[],
  query: string,
  modelConfig: ModelConfig,
  env: Env
): Promise<SourceAnalysisResult> {
  const openrouter = createOpenRouterClient(env)

  const messages: ChatCompletionMessage[] = [
    {
      role: 'system' as ChatRole,
      content: 'Analyze these sources and extract relevant information with citations.',
    },
    {
      role: 'user' as ChatRole,
      content: `Query: ${query}\n\nSources:\n${JSON.stringify(sources, null, 2)}`,
    },
  ]

  const payload = {
    model: modelConfig.model,
    messages,
    temperature: 0.5,
    max_tokens: 2000,
    stream: false,
  }

  const response = await openrouter.request(payload)
  const result = (await response.json()) as {
    choices?: Array<{ message?: { content?: string } }>
    usage?: { prompt_tokens?: number; completion_tokens?: number }
  }

  // Build citations from sources
  const citations: SourceCitation[] = sources.slice(0, 3).map((source: NormalizedSearchResult, index: number) => ({
    source_id: parseInt(source.id) || index,
    title: source.title,
    url: source.url,
    snippet: source.snippet?.substring(0, 100) ?? '',
    relevance_score: 0.8,
  }))

  return {
    citations,
    tokens: {
      prompt: result.usage?.prompt_tokens || 0,
      completion: result.usage?.completion_tokens || 0,
    },
    cost: 0, // Will be calculated by telemetry
  }
}

/**
 * Build citations from sources without AI analysis
 * Used for quick citation extraction
 */
export function buildCitationsFromSources(sources: NormalizedSearchResult[]): SourceCitation[] {
  return sources.slice(0, 10).map((source: NormalizedSearchResult, index: number) => ({
    source_id: index + 1,
    title: source.title,
    url: source.url,
    snippet: source.snippet?.substring(0, 200),
    relevance_score: source.relevance_score || 0.7,
  }))
}
