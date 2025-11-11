/**
 * Deep Research API Routes
 * Async research task management with streaming progress
 * Part of Week 2 T11: Deep Research async pipeline
 */

import { Hono } from 'hono'
import type { SupabaseClient } from '@supabase/supabase-js'
import type { Env } from '../types/env'
import type {
  DeepResearchRequest,
  DeepResearchTask,
  ResearchStatus,
  ResearchDepth,
  ResearchListParams,
  ResearchListResponse,
} from '../types/deep-research'
import { createSupabaseClient } from '../lib/supabase'
import { createOpenRouterClient } from '../lib/openrouter'
import { ROUTING_STRATEGIES, getModelConfig } from '../lib/model-routing'
import { executeOpenRouterRequest } from '../lib/resilience'
import { parseStreamResponse, createStreamingResponse } from '../lib/streaming'
import { createRateLimitMiddleware } from '../middlewares/rate-limit'

const DEFAULT_RESEARCH_DEPTH: ResearchDepth = 'standard'
const MAX_RESEARCH_QUERY_LENGTH = 5000

const deepResearch = new Hono<{ Bindings: Env }>()

/**
 * POST /deep-research
 * Create a new deep research task
 */
deepResearch.post(
  '/',
  createRateLimitMiddleware({
    scope: 'deep-research-user-day',
    limit: 5,
    windowSeconds: 60 * 60 * 24, // 24 hours
    key: async (c) => {
      const body = await c.req.json().catch(() => ({}))
      return body.user_id || 'anonymous'
    },
  }),
  async (c) => {
    // Parse and validate request body
    let body: DeepResearchRequest
    try {
      body = await c.req.json<DeepResearchRequest>()
    } catch {
      return c.json(
        {
          error: {
            code: 'INVALID_JSON',
            message: 'Body must be valid JSON',
            status: 400,
          },
        },
        400
      )
    }

    // Validate required fields
    const query = body.query?.trim()
    if (!query) {
      return c.json(
        {
          error: {
            code: 'MISSING_QUERY',
            message: 'Field "query" is required',
            status: 400,
          },
        },
        400
      )
    }

    if (query.length > MAX_RESEARCH_QUERY_LENGTH) {
      return c.json(
        {
          error: {
            code: 'QUERY_TOO_LONG',
            message: `Query exceeds ${MAX_RESEARCH_QUERY_LENGTH} characters`,
            status: 400,
          },
        },
        400
      )
    }

    try {
      const supabase = createSupabaseClient(c.env)

      // Determine model and provider
      const useCase = 'deep-research' as const
      const modelId = body.model || ROUTING_STRATEGIES[useCase].primary[0]
      const modelConfig = getModelConfig(modelId)

      if (!modelConfig) {
        return c.json(
          {
            error: {
              code: 'INVALID_MODEL',
              message: `Model ${modelId} not found`,
              status: 400,
            },
          },
          400
        )
      }

      // Create conversation if needed
      let conversationId = body.conversation_id
      if (!conversationId) {
        conversationId = crypto.randomUUID()
        await ensureConversationExists(supabase, conversationId, {
          title: `Research: ${query.substring(0, 100)}`,
        })
      }

      // Create deep research task
      const taskId = crypto.randomUUID()
      const taskData = {
        id: taskId,
        user_id: null, // Will be set by RLS or service role
        client_session_id: c.env.CLIENT_SESSION_ID || null,
        conversation_id: conversationId,
        query,
        status: 'pending' as ResearchStatus,
        research_depth: (body.research_depth || DEFAULT_RESEARCH_DEPTH) as ResearchDepth,
        max_sources: body.max_sources || 10,
        focus_areas: body.focus_areas || [],
        model_id: modelConfig.model,
        model_provider: modelConfig.provider,
        temperature: body.temperature || 0.7,
        metadata: body.metadata || {},
        tags: ['deep-research', modelConfig.provider],
      }

      // Insert into database
      const { data: task, error } = await supabase
        .from('deep_research_tasks')
        .insert(taskData)
        .select()
        .single()

      if (error) {
        console.error('Failed to create research task:', error)
        throw error
      }

      // Start async processing in the background
      // Don't await this - let it run in the background
      c.executionCtx.waitUntil(
        processResearchTask(taskId, query, modelConfig, supabase, c.env)
      )

      // Return task ID immediately (async pattern)
      return c.json(
        {
          task_id: taskId,
          status: 'pending',
          message: 'Research task created and processing in background',
          poll_url: `/api/v1/deep-research/${taskId}`,
          stream_url: `/api/v1/deep-research/${taskId}/stream`,
        },
        202
      )
    } catch (error) {
      console.error('Failed to create deep research task:', error)
      return c.json(
        {
          error: {
            code: 'RESEARCH_TASK_ERROR',
            message: 'Failed to create research task',
            status: 500,
          },
        },
        500
      )
    }
  }
)

/**
 * GET /deep-research/:id
 * Get the status and results of a research task
 */
deepResearch.get('/:id', async (c) => {
  const taskId = c.req.param('id')

  if (!taskId) {
    return c.json(
      {
        error: {
          code: 'MISSING_TASK_ID',
          message: 'Task ID is required',
          status: 400,
        },
      },
      400
    )
  }

  try {
    const supabase = createSupabaseClient(c.env)

    const { data: task, error } = await supabase
      .from('deep_research_tasks')
      .select('*')
      .eq('id', taskId)
      .single()

    if (error) {
      if (error.code === 'PGRST116') {
        return c.json(
          {
            error: {
              code: 'TASK_NOT_FOUND',
              message: 'Research task not found',
              status: 404,
            },
          },
          404
        )
      }
      throw error
    }

    return c.json({ task })
  } catch (error) {
    console.error('Failed to fetch research task:', error)
    return c.json(
      {
        error: {
          code: 'FETCH_TASK_ERROR',
          message: 'Failed to fetch research task',
          status: 500,
        },
      },
      500
    )
  }
})

/**
 * GET /deep-research
 * List research tasks for the current user
 */
deepResearch.get('/', async (c) => {
  try {
    const supabase = createSupabaseClient(c.env)

    // Parse query parameters
    const limit = Math.min(parseInt(c.req.query('limit') || '20'), 100)
    const offset = parseInt(c.req.query('offset') || '0')
    const status = c.req.query('status') as ResearchStatus | undefined

    let query = supabase
      .from('deep_research_tasks')
      .select('*', { count: 'exact' })
      .order('created_at', { ascending: false })
      .limit(limit)
      .range(offset, offset + limit - 1)

    if (status) {
      query = query.eq('status', status)
    }

    const { data: tasks, error, count } = await query

    if (error) {
      throw error
    }

    return c.json({
      tasks: tasks || [],
      total: count || 0,
      limit,
      offset,
    })
  } catch (error) {
    console.error('Failed to list research tasks:', error)
    return c.json(
      {
        error: {
          code: 'LIST_TASKS_ERROR',
          message: 'Failed to list research tasks',
          status: 500,
        },
      },
      500
    )
  }
})

export default deepResearch

// ============================================
// Background Task Processing
// ============================================

/**
 * Process a research task in the background
 * This function runs asynchronously after task creation
 */
async function processResearchTask(
  taskId: string,
  query: string,
  modelConfig: any,
  supabase: SupabaseClient,
  env: Env
): Promise<void> {
  const startTime = Date.now()

  try {
    // Mark task as running
    await supabase
      .from('deep_research_tasks')
      .update({
        status: 'running',
        started_at: new Date().toISOString(),
        current_step: 'Initializing research',
        steps_completed: 1,
        total_steps: 5,
        progress_percent: 10,
      })
      .eq('id', taskId)

    // Step 1: Generate research plan
    await updateProgress(supabase, taskId, {
      current_step: 'Generating research plan',
      steps_completed: 2,
      progress_percent: 20,
    })

    const plan = await generateResearchPlan(query, modelConfig, env)

    // Step 2: Search for sources
    await updateProgress(supabase, taskId, {
      current_step: 'Searching for sources',
      steps_completed: 3,
      progress_percent: 40,
    })

    const sources = await searchSources(plan.search_queries)

    // Step 3: Analyze sources
    await updateProgress(supabase, taskId, {
      current_step: 'Analyzing sources',
      steps_completed: 4,
      progress_percent: 60,
    })

    const analysis = await analyzeSources(sources, query, modelConfig, env)

    // Step 4: Synthesize findings
    await updateProgress(supabase, taskId, {
      current_step: 'Synthesizing findings',
      steps_completed: 5,
      progress_percent: 80,
    })

    const synthesis = await synthesizeFindings(analysis, query, modelConfig, env)

    // Step 5: Compile final result
    await updateProgress(supabase, taskId, {
      current_step: 'Compiling final result',
      steps_completed: 5,
      progress_percent: 90,
    })

    const durationMs = Date.now() - startTime

    // Save final result
    const { error } = await supabase
      .from('deep_research_tasks')
      .update({
        status: 'completed',
        completed_at: new Date().toISOString(),
        duration_ms: durationMs,
        progress_percent: 100,
        result: synthesis.result,
        summary: synthesis.summary,
        answer: synthesis.answer,
        sources: sources,
        citations: analysis.citations,
        tokens_prompt: analysis.tokens.prompt,
        tokens_completion: analysis.tokens.completion,
        cost_usd: analysis.cost,
      })
      .eq('id', taskId)

    if (error) {
      throw error
    }

    console.log(`Research task ${taskId} completed successfully`)
  } catch (error) {
    console.error(`Research task ${taskId} failed:`, error)

    // Mark task as failed
    await supabase
      .from('deep_research_tasks')
      .update({
        status: 'failed',
        completed_at: new Date().toISOString(),
        duration_ms: Date.now() - startTime,
        error_code: 'PROCESSING_ERROR',
        error_message: error instanceof Error ? error.message : 'Unknown error',
      })
      .eq('id', taskId)
  }
}

// ============================================
// Helper Functions
// ============================================

async function ensureConversationExists(
  supabase: SupabaseClient,
  conversationId: string,
  options: { title?: string } = {}
) {
  const { error } = await supabase.from('conversations').upsert(
    {
      id: conversationId,
      title: options.title || 'Deep Research',
      metadata: {},
      client_session_id: crypto.randomUUID(),
      model_preset: 'deep-research',
    },
    { onConflict: 'id' }
  )

  if (error) console.warn('Failed to upsert conversation:', error.message)
}

async function updateProgress(
  supabase: SupabaseClient,
  taskId: string,
  progress: {
    current_step?: string
    steps_completed?: number
    progress_percent?: number
  }
) {
  const { error } = await supabase
    .from('deep_research_tasks')
    .update({
      ...progress,
      updated_at: new Date().toISOString(),
    })
    .eq('id', taskId)

  if (error) {
    console.error('Failed to update progress:', error)
  }
}

/**
 * Generate research plan with search queries
 * Exported for use in streaming endpoints
 */
export async function generateResearchPlan(
  query: string,
  modelConfig: any,
  env: Env
): Promise<{ search_queries: string[]; plan: string }> {
  const openrouter = createOpenRouterClient(env)

  const messages = [
    {
      role: 'system',
      content:
        'You are a research assistant. Given a query, generate a research plan with specific search queries.',
    },
    {
      role: 'user',
      content: `Generate a research plan for: "${query}"`,
    },
  ]

  const payload = {
    model: modelConfig.model,
    messages,
    temperature: 0.3,
    max_tokens: 500,
  }

  const response = await openrouter.request(payload)
  const result = await response.json()

  const content = result.choices?.[0]?.message?.content || ''

  // Parse the response to extract search queries
  // This is a simplified version - in production, you'd use structured output
  const searchQueries = extractSearchQueriesFromContent(content, query)

  return {
    search_queries: searchQueries,
    plan: content,
  }
}

function extractSearchQueriesFromContent(content: string, originalQuery: string): string[] {
  // Simplified extraction - in production, use structured output or a more sophisticated method
  const queries: string[] = []

  // Always include the original query
  queries.push(originalQuery)

  // Try to extract numbered lists or bullet points
  const lines = content.split('\n')
  for (const line of lines) {
    // Look for lines that start with numbers or bullets and contain question-like phrases
    if (/^\d+\.|^[-*]/.test(line)) {
      const cleaned = line.replace(/^\d+\.\s*|^[-*]\s*/, '').trim()
      if (cleaned.length > 10 && cleaned.length < 200) {
        queries.push(cleaned)
      }
    }
  }

  // If no queries extracted, create variations of the original query
  if (queries.length <= 1) {
    queries.push(`${originalQuery} latest news`)
    queries.push(`${originalQuery} analysis`)
    queries.push(`${originalQuery} overview`)
  }

  return queries.slice(0, 5) // Limit to 5 queries
}

/**
 * Search for sources based on queries
 * Exported for use in streaming endpoints
 * TODO: Integrate with real search API
 */
export async function searchSources(queries: string[]): Promise<any[]> {
  // Mock source search - in production, integrate with search API
  // For now, return mock sources

  return queries.map((query, index) => ({
    id: `source-${index}`,
    url: `https://example.com/source/${index}`,
    title: `Source about ${query}`,
    snippet: `This is a snippet about ${query}. It contains relevant information for the research.`,
    relevance_score: Math.random() * 0.5 + 0.5, // 0.5 - 1.0
    accessed_at: new Date().toISOString(),
  }))
}

/**
 * Analyze sources using AI
 * Exported for use in streaming endpoints
 */
export async function analyzeSources(
  sources: any[],
  query: string,
  modelConfig: any,
  env: Env
): Promise<{
  citations: any[]
  tokens: { prompt: number; completion: number }
  cost: number
}> {
  const openrouter = createOpenRouterClient(env)

  const messages = [
    {
      role: 'system',
      content:
        'Analyze these sources and extract relevant information with citations.',
    },
    {
      role: 'user',
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
  const result = await response.json()

  const content = result.choices?.[0]?.message?.content || ''

  // Mock citations - in production, parse from response
  const citations = sources.slice(0, 3).map((source: any, index: number) => ({
    source_id: source.id,
    quote: source.snippet.substring(0, 100),
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
 * Synthesize research findings into final answer
 * Exported for use in streaming endpoints
 */
export async function synthesizeFindings(
  analysis: any,
  query: string,
  modelConfig: any,
  env: Env
): Promise<{
  result: any
  summary: string
  answer: string
}> {
  const openrouter = createOpenRouterClient(env)

  const messages = [
    {
      role: 'system',
      content:
        'Synthesize the research findings into a comprehensive answer with summary.',
    },
    {
      role: 'user',
      content: `Query: ${query}\n\nAnalysis: ${JSON.stringify(analysis, null, 2)}`,
    },
  ]

  const payload = {
    model: modelConfig.model,
    messages,
    temperature: 0.7,
    max_tokens: 3000,
    stream: false,
  }

  const response = await openrouter.request(payload)
  const result = await response.json()

  const content = result.choices?.[0]?.message?.content || ''

  return {
    result: {
      summary: `Research summary for: ${query}`,
      answer: content,
      key_findings: ['Finding 1', 'Finding 2', 'Finding 3'],
      sources: [],
      citations: analysis.citations,
      research_depth: 'comprehensive',
      total_sources: 5,
      total_citations: analysis.citations.length,
      confidence_score: 0.85,
    },
    summary: `Research summary for: ${query}`,
    answer: content,
  }
}
