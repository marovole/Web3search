/**
 * Research Plan Generation
 * Generates research plans with search queries using AI
 */

import type { Env } from '../../types/env'
import type { ChatCompletionMessage, ChatRole } from '../../types/chat'
import type { ModelConfig, GeneratedResearchPlan, ResearchDepth } from './types'
import { createOpenRouterClient } from '../../lib/openrouter'

/**
 * Generate research plan with search queries (Optimized for Tongyi DeepResearch)
 * Uses ReAct-style prompting for better research planning
 */
export async function generateResearchPlan(
  query: string,
  modelConfig: ModelConfig,
  env: Env,
  depth: ResearchDepth = 'standard'
): Promise<GeneratedResearchPlan> {
  const {
    DEEPRESEARCH_SYSTEM_PROMPT,
    getResearchConfig,
    buildResearchPlanPrompt,
  } = await import('../../lib/research-prompts')

  const openrouter = createOpenRouterClient(env)
  const config = getResearchConfig(depth)

  const messages: ChatCompletionMessage[] = [
    {
      role: 'system' as ChatRole,
      content: DEEPRESEARCH_SYSTEM_PROMPT,
    },
    {
      role: 'user' as ChatRole,
      content: buildResearchPlanPrompt(query),
    },
  ]

  const payload = {
    model: modelConfig.model,
    messages,
    temperature: config.temperature,
    max_tokens: config.plan_max_tokens,
  }

  const response = await openrouter.request(payload)
  const result = (await response.json()) as {
    choices?: Array<{ message?: { content?: string } }>
  }

  const content = result.choices?.[0]?.message?.content || ''

  // Try to parse JSON response
  let parsedPlan: GeneratedResearchPlan['parsed_plan'] = null
  let searchQueries: string[] = []

  try {
    // Try to extract JSON from the response
    const jsonMatch = content.match(/\{[\s\S]*\}/)
    if (jsonMatch) {
      parsedPlan = JSON.parse(jsonMatch[0])
      // Extract search queries from parsed plan
      if (parsedPlan?.search_queries && Array.isArray(parsedPlan.search_queries)) {
        searchQueries = parsedPlan.search_queries
          .map((q: string | { query: string }) => (typeof q === 'string' ? q : q.query))
          .filter(Boolean) as string[]
      }
    }
  } catch {
    console.warn('Failed to parse research plan JSON, falling back to extraction')
  }

  // Fallback: extract queries from text if JSON parsing failed
  if (searchQueries.length === 0) {
    searchQueries = extractSearchQueriesFromContent(content, query, config.max_queries)
  }

  return {
    search_queries: searchQueries.slice(0, config.max_queries),
    plan: content,
    parsed_plan: parsedPlan,
  }
}

/**
 * Extract search queries from unstructured content
 */
function extractSearchQueriesFromContent(
  content: string,
  originalQuery: string,
  maxQueries: number = 5
): string[] {
  const queries: string[] = []

  // Always include the original query
  queries.push(originalQuery)

  // Try to extract numbered lists or bullet points
  const lines = content.split('\n')
  for (const line of lines) {
    if (/^\d+\.|^[-*]/.test(line)) {
      const cleaned = line.replace(/^\d+\.\s*|^[-*]\s*/, '').trim()
      // Extract quoted strings or the whole line
      const quotedMatch = cleaned.match(/"([^"]+)"/)
      const queryText = quotedMatch ? quotedMatch[1] : cleaned
      if (queryText.length > 5 && queryText.length < 200) {
        queries.push(queryText)
      }
    }
  }

  // Fallback queries if extraction failed
  if (queries.length <= 1) {
    queries.push(`${originalQuery} 最新动态`)
    queries.push(`${originalQuery} 深度分析`)
    queries.push(`${originalQuery} 市场趋势`)
  }

  return queries.slice(0, maxQueries)
}
