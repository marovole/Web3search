import { z } from 'zod'

export const DeepResearchRequestSchema = z.object({
  query: z
    .string()
    .min(2, 'Query must be at least 2 characters')
    .max(5000, 'Query exceeds maximum length of 5000 characters'),
  research_type: z.enum(['general', 'tokenomics', 'security', 'competitive']).optional(),
  research_depth: z.enum(['quick', 'standard', 'deep']).optional(),
  max_sources: z.number().int().min(1).max(50).optional(),
  focus_areas: z.array(z.string()).optional(),
  model: z.string().optional(),
  model_provider: z.string().optional(),
  temperature: z.number().min(0).max(2).optional(),
  conversation_id: z.string().uuid().optional(),
  metadata: z.record(z.unknown()).optional(),
})

export type ValidatedDeepResearchRequest = z.infer<typeof DeepResearchRequestSchema>

export const ResearchPlanResponseSchema = z.object({
  query_understanding: z.string(),
  research_dimensions: z
    .array(
      z.object({
        dimension: z.string(),
        importance: z.enum(['high', 'medium', 'low']),
        description: z.string(),
      })
    )
    .optional(),
  search_queries: z.array(
    z.union([z.string(), z.object({ query: z.string(), purpose: z.string().optional() })])
  ),
  expected_challenges: z.array(z.string()).optional(),
})

export type ValidatedResearchPlanResponse = z.infer<typeof ResearchPlanResponseSchema>

export const SearchResultSchema = z.object({
  id: z.string().optional(),
  title: z.string(),
  url: z.string().url(),
  snippet: z.string(),
  relevance_score: z.number().min(0).max(1).optional(),
  provider: z.string().optional(),
})

export const SearchResultsSchema = z.array(SearchResultSchema)

export type ValidatedSearchResult = z.infer<typeof SearchResultSchema>

export const TokenomicsScorecardSchema = z.object({
  score: z.number().min(0).max(100),
  rating: z.enum(['Ponzi Risk', 'Speculative', 'Sustainable']),
  color: z.enum(['red', 'yellow', 'green']),
})

export const AIResponseSchema = z.object({
  choices: z
    .array(
      z.object({
        message: z.object({
          content: z.string(),
          role: z.string().optional(),
        }),
        finish_reason: z.string().optional(),
      })
    )
    .min(1),
  usage: z
    .object({
      prompt_tokens: z.number().optional(),
      completion_tokens: z.number().optional(),
      total_tokens: z.number().optional(),
    })
    .optional(),
})

export type ValidatedAIResponse = z.infer<typeof AIResponseSchema>

export function validateDeepResearchRequest(
  data: unknown
): { success: true; data: ValidatedDeepResearchRequest } | { success: false; error: string } {
  const result = DeepResearchRequestSchema.safeParse(data)
  if (result.success) {
    return { success: true, data: result.data }
  }
  const errorMessage = result.error.errors.map((e) => `${e.path.join('.')}: ${e.message}`).join(', ')
  return { success: false, error: errorMessage }
}

export function validateAIResponse(
  data: unknown
): { success: true; data: ValidatedAIResponse } | { success: false; error: string } {
  const result = AIResponseSchema.safeParse(data)
  if (result.success) {
    return { success: true, data: result.data }
  }
  return { success: false, error: 'Invalid AI response format' }
}

export function safeParseSearchResults(data: unknown): ValidatedSearchResult[] {
  const result = SearchResultsSchema.safeParse(data)
  if (result.success) {
    return result.data
  }
  console.warn('Search results validation failed, returning empty array')
  return []
}
