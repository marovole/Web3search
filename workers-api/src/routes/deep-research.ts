/**
 * Deep Research API Routes
 * Async research task management with streaming progress
 * Part of Week 2 T11: Deep Research async pipeline
 */

import { Hono } from 'hono'
import type { SupabaseClient } from '@supabase/supabase-js'
import type { Env } from '../types/env'
import type { ChatCompletionMessage, ChatRole } from '../types/chat'
import type {
  DeepResearchRequest,
  DeepResearchTask,
  ResearchStatus,
  ResearchDepth,
  ResearchListParams,
  ResearchListResponse,
} from '../types/deep-research'
import { getSupabaseClient } from '../lib/supabase'
import { createOpenRouterClient } from '../lib/openrouter'
import { ROUTING_STRATEGIES, getModelConfig } from '../lib/model-routing'
import { executeOpenRouterRequest } from '../lib/resilience'
import { parseStreamResponse, createStreamingResponse } from '../lib/streaming'
import { createRateLimitMiddleware } from '../middlewares/rate-limit'
import { ensureConversationExists, persistMessage } from '../lib/conversation'

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
      // Use service role to bypass RLS for creating tasks
      const supabase = getSupabaseClient(c.env, true)

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
 * GET /stream
 * Deep Research with SSE streaming
 * Streams progress updates through research pipeline stages
 *
 * Query Parameters:
 *   - query (required): The research query (max 2000 characters)
 *   - conversation_id (optional): Existing conversation ID to continue
 *   - model (optional): Model ID to use (defaults to primary deep-research model)
 *   - type (optional): Research type - 'general' | 'tokenomics' | 'security' | 'competitive'
 */
deepResearch.get(
  '/stream',
  createRateLimitMiddleware({
    scope: 'deep-research-ip-day',
    limit: 5,
    windowSeconds: 60 * 60 * 24, // 24 hours
    key: (c) => c.req.header('cf-connecting-ip') || 'anonymous',
  }),
  async (c) => {
    // Parse and validate query parameters
    const queryParam = c.req.query('query')
    const conversationParam = c.req.query('conversation_id')
    const modelParam = c.req.query('model')
    const typeParam = c.req.query('type') as 'general' | 'tokenomics' | 'security' | 'competitive' | undefined

    // Validate query parameter
    const query = typeof queryParam === 'string' ? queryParam.trim() : ''
    if (!query) {
      return c.json(
        {
          error: {
            code: 'MISSING_QUERY',
            message: 'Query parameter "query" is required',
            status: 400,
          },
        },
        400
      )
    }

    // Enforce query length limit for GET requests (URL length constraints)
    if (query.length > 2000) {
      return c.json(
        {
          error: {
            code: 'URI_TOO_LONG',
            message: 'Query exceeds maximum length of 2000 characters',
            status: 414,
          },
        },
        414
      )
    }

    try {
      // Use service role to bypass RLS for creating and updating tasks
      const supabase = getSupabaseClient(c.env, true)

      // Determine model configuration
      const useCase = 'deep-research' as const
      const modelId =
        typeof modelParam === 'string' && modelParam.trim()
          ? modelParam.trim()
          : ROUTING_STRATEGIES[useCase].primary[0]
      const modelConfig = getModelConfig(modelId)

      if (!modelConfig) {
        return c.json(
          {
            error: {
              code: 'INVALID_MODEL',
              message: `Model "${modelId}" not found`,
              status: 400,
            },
          },
          400
        )
      }

      // Ensure conversation exists
      const conversationId =
        typeof conversationParam === 'string' && conversationParam.trim()
          ? conversationParam.trim()
          : crypto.randomUUID()

      await ensureConversationExists(supabase, conversationId, {
        title: `Deep Research: ${query.substring(0, 100)}`,
      })

      // Save user message
      await persistMessage(supabase, {
        conversation_id: conversationId,
        role: 'user',
        content: query,
        metadata: null, // Metadata no longer supported via GET query params
      })

      // Create SSE stream
      return streamDeepResearch({
        query,
        conversationId,
        modelConfig,
        supabase,
        env: c.env,
        researchType: typeParam || 'general',
      })
    } catch (error) {
      console.error('Deep Research stream handler failed:', error)
      return c.json(
        {
          error: {
            code: 'DEEP_RESEARCH_ERROR',
            message: 'Failed to start deep research',
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
    // Use service role to read tasks (RLS might block anonymous reads)
    const supabase = getSupabaseClient(c.env, true)

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
    // Use service role to list tasks (RLS might block anonymous reads)
    const supabase = getSupabaseClient(c.env, true)

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

    const sources = await searchSources(plan.search_queries, env)

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
 * Generate research plan with search queries (Optimized for Tongyi DeepResearch)
 * Uses ReAct-style prompting for better research planning
 */
export async function generateResearchPlan(
  query: string,
  modelConfig: any,
  env: Env,
  depth: 'quick' | 'standard' | 'deep' = 'standard'
): Promise<{ search_queries: string[]; plan: string; parsed_plan?: any }> {
  const { 
    DEEPRESEARCH_SYSTEM_PROMPT, 
    getResearchConfig,
    buildResearchPlanPrompt 
  } = await import('../lib/research-prompts')
  
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
  const result = await response.json() as any

  const content = result.choices?.[0]?.message?.content || ''

  // Try to parse JSON response
  let parsedPlan: any = null
  let searchQueries: string[] = []
  
  try {
    // Try to extract JSON from the response
    const jsonMatch = content.match(/\{[\s\S]*\}/)
    if (jsonMatch) {
      parsedPlan = JSON.parse(jsonMatch[0])
      // Extract search queries from parsed plan
      if (parsedPlan.search_queries && Array.isArray(parsedPlan.search_queries)) {
        searchQueries = parsedPlan.search_queries.map((q: any) => 
          typeof q === 'string' ? q : q.query
        ).filter(Boolean)
      }
    }
  } catch (e) {
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

/**
 * Search for sources based on queries
 * Exported for use in streaming endpoints
 * Integrates with real search APIs (Brave, Tavily, Serper)
 */
export async function searchSources(queries: string[], env: Env): Promise<any[]> {
  const { fetchSearchResultsForQueries } = await import('../lib/search-providers')

  if (!queries.length) {
    return []
  }

  return fetchSearchResultsForQueries(queries, env)
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

  const messages: ChatCompletionMessage[] = [
    {
      role: 'system' as ChatRole,
      content:
        'Analyze these sources and extract relevant information with citations.',
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
  const result = await response.json() as any

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
 * Synthesize research findings into final answer (Optimized for Tongyi DeepResearch)
 * Uses comprehensive prompting for structured analysis with citations
 */
export async function synthesizeFindings(
  analysis: any,
  query: string,
  modelConfig: any,
  env: Env,
  options?: {
    sources?: any[]
    plan?: any
    depth?: 'quick' | 'standard' | 'deep'
    researchType?: 'general' | 'tokenomics' | 'security' | 'competitive'
  }
): Promise<{
  result: any
  summary: string
  answer: string
}> {
  const { 
    DEEPRESEARCH_SYSTEM_PROMPT,
    buildSynthesisPrompt,
    formatSourcesForPrompt,
    getResearchConfig,
    getSystemPromptByType,
    buildTokenomicsPrompt,
    TOKENOMICS_AUDITOR_PROMPT,
  } = await import('../lib/research-prompts')
  
  const openrouter = createOpenRouterClient(env)
  const depth = options?.depth || 'standard'
  const researchType = options?.researchType || 'general'
  const config = getResearchConfig(depth)
  const isTokenomics = researchType === 'tokenomics'
  
  // Format sources for the prompt
  const sourcesContext = options?.sources 
    ? formatSourcesForPrompt(options.sources)
    : JSON.stringify(analysis, null, 2)
  
  const planContext = options?.plan 
    ? (typeof options.plan === 'string' ? options.plan : JSON.stringify(options.plan, null, 2))
    : ''

  // Select system prompt based on research type
  const systemPrompt = getSystemPromptByType(researchType)
  
  // Build user prompt based on research type
  const userPrompt = isTokenomics
    ? buildTokenomicsPrompt(query) + `\n\n## 收集到的信息来源\n${sourcesContext}`
    : buildSynthesisPrompt(query, planContext, sourcesContext)

  const messages: ChatCompletionMessage[] = [
    {
      role: 'system' as ChatRole,
      content: systemPrompt,
    },
    {
      role: 'user' as ChatRole,
      content: userPrompt,
    },
  ]

  const payload = {
    model: modelConfig.model,
    messages,
    temperature: config.temperature,
    max_tokens: config.synthesis_max_tokens,
    stream: false,
  }

  const response = await openrouter.request(payload)
  const result = await response.json() as any

  const content = result.choices?.[0]?.message?.content || ''

  // Try to parse structured JSON response
  let parsedResult: any = null
  try {
    const jsonMatch = content.match(/\{[\s\S]*\}/)
    if (jsonMatch) {
      parsedResult = JSON.parse(jsonMatch[0])
    }
  } catch (e) {
    console.warn('Failed to parse synthesis JSON, using raw content')
  }

  // Build structured result based on research type
  const structuredResult = isTokenomics && parsedResult?.scorecard
    ? {
        // Tokenomics audit result
        research_type: 'tokenomics' as const,
        summary: parsedResult.verdict?.summary || `Tokenomics audit for: ${query}`,
        answer: parsedResult ? formatTokenomicsAnswer(parsedResult) : content,
        scorecard: parsedResult.scorecard,
        red_flags: parsedResult.red_flags || [],
        tokenomics_analysis: parsedResult.analysis,
        stress_test: parsedResult.stress_test,
        verdict: parsedResult.verdict,
        data_quality: parsedResult.data_quality,
        sources: options?.sources || [],
        citations: analysis.citations || [],
        research_depth: depth,
        total_sources: options?.sources?.length || 0,
        total_citations: analysis.citations?.length || 0,
        confidence_score: parsedResult.data_quality?.transparency_score 
          ? parsedResult.data_quality.transparency_score / 10 
          : 0.75,
      }
    : {
        // General research result
        research_type: 'general' as const,
        summary: parsedResult?.executive_summary || `Research summary for: ${query}`,
        answer: parsedResult ? formatStructuredAnswer(parsedResult) : content,
        key_findings: parsedResult?.key_findings?.map((f: any) => 
          typeof f === 'string' ? f : f.finding
        ) || ['Key findings extracted from analysis'],
        sources: options?.sources || [],
        citations: analysis.citations || [],
        research_depth: depth,
        total_sources: options?.sources?.length || 0,
        total_citations: analysis.citations?.length || 0,
        confidence_score: parsedResult?.metadata?.overall_confidence || 0.75,
        structured_analysis: parsedResult?.detailed_analysis || null,
        risks_and_uncertainties: parsedResult?.risks_and_uncertainties || null,
        conclusion: parsedResult?.conclusion || null,
      }

  return {
    result: structuredResult,
    summary: structuredResult.summary,
    answer: structuredResult.answer,
  }
}

/**
 * Format structured analysis result into readable answer
 */
function formatStructuredAnswer(parsed: any): string {
  const parts: string[] = []
  
  // Executive Summary
  if (parsed.executive_summary) {
    parts.push(`## 执行摘要\n${parsed.executive_summary}`)
  }
  
  // Detailed Analysis
  if (parsed.detailed_analysis?.sections) {
    parts.push('\n## 详细分析')
    for (const section of parsed.detailed_analysis.sections) {
      parts.push(`\n### ${section.title}\n${section.content}`)
    }
  }
  
  // Key Findings
  if (parsed.key_findings?.length > 0) {
    parts.push('\n## 关键发现')
    for (const finding of parsed.key_findings) {
      const text = typeof finding === 'string' ? finding : finding.finding
      const confidence = typeof finding === 'object' ? ` (置信度: ${(finding.confidence * 100).toFixed(0)}%)` : ''
      parts.push(`- ${text}${confidence}`)
    }
  }
  
  // Risks and Uncertainties
  if (parsed.risks_and_uncertainties) {
    const risks = parsed.risks_and_uncertainties
    if (risks.limitations?.length || risks.uncertainties?.length) {
      parts.push('\n## 风险与不确定性')
      if (risks.limitations?.length) {
        parts.push('**局限性:**')
        risks.limitations.forEach((l: string) => parts.push(`- ${l}`))
      }
      if (risks.uncertainties?.length) {
        parts.push('**不确定因素:**')
        risks.uncertainties.forEach((u: string) => parts.push(`- ${u}`))
      }
    }
  }
  
  // Conclusion
  if (parsed.conclusion) {
    parts.push('\n## 结论')
    if (parsed.conclusion.summary) {
      parts.push(parsed.conclusion.summary)
    }
    if (parsed.conclusion.recommendations?.length) {
      parts.push('\n**建议:**')
      parsed.conclusion.recommendations.forEach((r: string) => parts.push(`- ${r}`))
    }
  }
  
  return parts.join('\n')
}

/**
 * Format tokenomics audit result into readable answer
 */
function formatTokenomicsAnswer(parsed: any): string {
  const parts: string[] = []
  
  // Scorecard Header
  if (parsed.scorecard) {
    const { score, rating, color } = parsed.scorecard
    const emoji = color === 'green' ? '🟢' : color === 'yellow' ? '🟡' : '🔴'
    parts.push(`## ${emoji} Tokenomics Scorecard: ${score}/100 (${rating})`)
  }
  
  // Red Flags
  if (parsed.red_flags?.length > 0) {
    parts.push('\n## 🚨 Red Flags')
    for (const flag of parsed.red_flags) {
      parts.push(`- ${flag}`)
    }
  }
  
  // 5-Dimension Analysis
  if (parsed.analysis) {
    const { supply_dynamics, allocation, vesting, value_accrual, sustainability } = parsed.analysis
    
    parts.push('\n## 📊 5-Dimension Audit')
    
    if (supply_dynamics) {
      parts.push('\n### 1. Supply Dynamics & FDV')
      if (supply_dynamics.circulating_supply) parts.push(`- 流通供应量: ${supply_dynamics.circulating_supply}`)
      if (supply_dynamics.max_supply) parts.push(`- 最大供应量: ${supply_dynamics.max_supply}`)
      if (supply_dynamics.fdv) parts.push(`- FDV: ${supply_dynamics.fdv}`)
      if (supply_dynamics.inflation_rate) parts.push(`- 通胀率: ${supply_dynamics.inflation_rate}`)
      if (supply_dynamics.findings) parts.push(`\n${supply_dynamics.findings}`)
    }
    
    if (allocation) {
      parts.push('\n### 2. Token Allocation & Centralization')
      if (allocation.insider_percentage !== undefined) parts.push(`- 内部人持仓: ${allocation.insider_percentage}%`)
      if (allocation.centralization_risk) parts.push(`- 中心化风险: ${allocation.centralization_risk}`)
      if (allocation.breakdown) {
        parts.push('- 分配明细:')
        for (const [key, value] of Object.entries(allocation.breakdown)) {
          parts.push(`  - ${key}: ${value}%`)
        }
      }
      if (allocation.findings) parts.push(`\n${allocation.findings}`)
    }
    
    if (vesting) {
      parts.push('\n### 3. Vesting & Unlock Schedule')
      if (vesting.tge_date) parts.push(`- TGE日期: ${vesting.tge_date}`)
      if (vesting.next_major_unlock) parts.push(`- 下次重大解锁: ${vesting.next_major_unlock}`)
      if (vesting.monthly_sell_pressure_usd) parts.push(`- 月度抛压: ${vesting.monthly_sell_pressure_usd}`)
      if (vesting.findings) parts.push(`\n${vesting.findings}`)
    }
    
    if (value_accrual) {
      parts.push('\n### 4. Value Accrual')
      if (value_accrual.mechanism) parts.push(`- 价值捕获机制: ${value_accrual.mechanism}`)
      if (value_accrual.yield_type) parts.push(`- 收益类型: ${value_accrual.yield_type}`)
      if (value_accrual.protocol_revenue) parts.push(`- 协议收入: ${value_accrual.protocol_revenue}`)
      if (value_accrual.findings) parts.push(`\n${value_accrual.findings}`)
    }
    
    if (sustainability) {
      parts.push('\n### 5. Sustainability & Ponzi Check')
      if (sustainability.death_spiral_risk) parts.push(`- 死亡螺旋风险: ${sustainability.death_spiral_risk}`)
      if (sustainability.ponzi_score !== undefined) parts.push(`- Ponzi评分: ${sustainability.ponzi_score}/10`)
      if (sustainability.findings) parts.push(`\n${sustainability.findings}`)
    }
  }
  
  // Stress Test
  if (parsed.stress_test) {
    parts.push('\n## 🔥 Stress Test: 50% Market Crash')
    if (parsed.stress_test.treasury_runway) parts.push(`- Treasury Runway: ${parsed.stress_test.treasury_runway}`)
    if (parsed.stress_test.staking_impact) parts.push(`- Staking Impact: ${parsed.stress_test.staking_impact}`)
    if (parsed.stress_test.protocol_survival) parts.push(`- Protocol Survival: ${parsed.stress_test.protocol_survival}`)
    if (parsed.stress_test.findings) parts.push(`\n${parsed.stress_test.findings}`)
  }
  
  // Verdict
  if (parsed.verdict) {
    parts.push('\n## 📋 Investment Verdict')
    if (parsed.verdict.recommendation) parts.push(`**Recommendation:** ${parsed.verdict.recommendation}`)
    if (parsed.verdict.investment_horizon) parts.push(`**Horizon:** ${parsed.verdict.investment_horizon}`)
    if (parsed.verdict.key_catalysts?.length) {
      parts.push('\n**Positive Catalysts:**')
      parsed.verdict.key_catalysts.forEach((c: string) => parts.push(`- ${c}`))
    }
    if (parsed.verdict.key_risks?.length) {
      parts.push('\n**Key Risks:**')
      parsed.verdict.key_risks.forEach((r: string) => parts.push(`- ${r}`))
    }
    if (parsed.verdict.summary) parts.push(`\n${parsed.verdict.summary}`)
  }
  
  // Data Quality
  if (parsed.data_quality) {
    parts.push('\n## 📝 Data Quality Assessment')
    if (parsed.data_quality.transparency_score !== undefined) {
      parts.push(`- Transparency Score: ${parsed.data_quality.transparency_score}/10`)
    }
    if (parsed.data_quality.missing_data?.length) {
      parts.push('- Missing Data:')
      parsed.data_quality.missing_data.forEach((d: string) => parts.push(`  - ${d}`))
    }
    if (parsed.data_quality.conflicting_sources?.length) {
      parts.push('- Conflicting Sources:')
      parsed.data_quality.conflicting_sources.forEach((c: string) => parts.push(`  - ${c}`))
    }
  }
  
  return parts.join('\n')
}

// ============================================
// Deep Research Streaming Functions
// ============================================

interface DeepResearchStreamParams {
  query: string
  conversationId: string
  modelConfig: any
  supabase: SupabaseClient
  env: Env
  researchType?: 'general' | 'tokenomics' | 'security' | 'competitive'
}

/**
 * Stream Deep Research progress using Server-Sent Events (SSE)
 * Emits progress events for each stage: data_collection, analysis, report_generation, complete
 * Persists final assistant response to database
 */
function streamDeepResearch({
  query,
  conversationId,
  modelConfig,
  supabase,
  env,
  researchType = 'general',
}: DeepResearchStreamParams): Response {
  const encoder = new TextEncoder()
  let heartbeat: ReturnType<typeof setInterval> | null = null
  let isCancelled = false
  const isTokenomics = researchType === 'tokenomics'

  const stream = new ReadableStream({
    start(controller) {
      // SSE event emitter helper
      const emit = (event: {
        type: 'progress' | 'content' | 'complete' | 'error'
        stage?: string
        section?: string
        content: string
        session_id?: string
        timestamp?: string
      }) => {
        // Skip if stream was cancelled
        if (isCancelled) return

        try {
          // Ensure timestamp is always present
          const enrichedEvent = {
            ...event,
            timestamp: event.timestamp ?? new Date().toISOString(),
          }
          const data = JSON.stringify(enrichedEvent)
          controller.enqueue(encoder.encode(`data: ${data}\n\n`))
        } catch (error) {
          // Silently ignore errors if controller is closed
          if (!isCancelled) {
            console.warn('Failed to emit SSE event:', error)
          }
        }
      }

      // Keep-alive heartbeat to prevent Cloudflare timeout
      heartbeat = setInterval(() => {
        if (isCancelled) return
        try {
          controller.enqueue(encoder.encode(': keep-alive\n\n'))
        } catch (error) {
          // Silently ignore if controller is closed
        }
      }, 15_000)

      // Execute research pipeline
      ;(async () => {
        try {
          // Stage 1: Data Collection - Generate Research Plan
          const { getSystemPromptByType, getTokenomicsSearchQueries, buildTokenomicsPrompt } = await import('../lib/research-prompts')
          
          emit({
            type: 'progress',
            stage: 'data_collection',
            content: isTokenomics 
              ? '🔍 启动 Tokenomics 深度审计模式...'
              : '正在分析研究需求，制定调研计划...',
          })

          // For tokenomics, use specialized search queries
          let plan: { search_queries: string[]; plan: string; parsed_plan?: any }
          
          if (isTokenomics) {
            // Extract project/token from query for specialized search
            const tokenomicsQueries = getTokenomicsSearchQueries(query, query)
            plan = {
              search_queries: tokenomicsQueries,
              plan: `Tokenomics audit for: ${query}`,
              parsed_plan: { query_understanding: `Tokenomics audit mode: ${query}` }
            }
          } else {
            plan = await generateResearchPlan(query, modelConfig, env, 'standard')
          }

          emit({
            type: 'progress',
            stage: 'data_collection',
            content: isTokenomics
              ? `📊 代币经济学审计：将分析 ${plan.search_queries.length} 个关键维度...`
              : (plan.parsed_plan?.query_understanding 
                ? `已理解研究需求：${plan.parsed_plan.query_understanding.substring(0, 100)}...`
                : `研究计划已生成，将执行 ${plan.search_queries.length} 个搜索策略...`),
          })

          // Stage 2: Source Search
          const sources = await searchSources(plan.search_queries, env)

          emit({
            type: 'content',
            section: 'sources',
            content: JSON.stringify({
              count: sources.length,
              queries: plan.search_queries,
              dimensions: plan.parsed_plan?.research_dimensions?.map((d: any) => d.dimension) || [],
            }),
          })

          // Stage 3: Analysis (simplified - now integrated into synthesis)
          emit({
            type: 'progress',
            stage: 'analysis',
            content: `已收集 ${sources.length} 个信息来源，正在进行深度分析...`,
          })

          // Build citations from sources
          const analysis = {
            citations: sources.slice(0, 10).map((source: any, index: number) => ({
              source_id: index + 1,
              title: source.title,
              url: source.url,
              snippet: source.snippet?.substring(0, 200),
              relevance_score: source.relevance_score || 0.7,
            }))
          }

          emit({
            type: 'progress',
            stage: 'analysis',
            content: isTokenomics
              ? `📈 正在执行 5 维度审计分析...`
              : `正在综合 ${sources.length} 个来源的信息，生成研究报告...`,
          })

          // Stage 4: Report Generation (with enhanced synthesis)
          emit({
            type: 'progress',
            stage: 'report_generation',
            content: isTokenomics
              ? '📝 生成 Tokenomics 审计报告（含压力测试）...'
              : '正在生成结构化研究报告...',
          })

          const synthesis = await synthesizeFindings(
            analysis,
            query,
            modelConfig,
            env,
            {
              sources,
              plan: plan.parsed_plan || plan.plan,
              depth: 'deep',
              researchType: researchType,
            }
          )

          // Emit final answer as content (so UI can display it)
          emit({
            type: 'content',
            section: 'answer',
            content: synthesis.answer,
          })
          
          // Emit structured result if available
          if (synthesis.result.structured_analysis || synthesis.result.key_findings) {
            emit({
              type: 'content',
              section: 'structured_result',
              content: JSON.stringify({
                key_findings: synthesis.result.key_findings,
                confidence_score: synthesis.result.confidence_score,
                risks: synthesis.result.risks_and_uncertainties,
                conclusion: synthesis.result.conclusion,
              }),
            })
          }

          // Persist assistant response
          await persistMessage(supabase, {
            conversation_id: conversationId,
            role: 'assistant',
            content: synthesis.answer,
            metadata: {
              research_result: synthesis.result,
              citations: analysis.citations,
            },
          })

          // Stage 5: Complete
          emit({
            type: 'complete',
            content: synthesis.summary || 'Research completed successfully',
            session_id: conversationId,
          })

          clearInterval(heartbeat)
          controller.enqueue(
            encoder.encode('event: done\ndata: {"status":"completed"}\n\n')
          )
          controller.close()
        } catch (error) {
          if (heartbeat) {
            clearInterval(heartbeat)
          }
          console.error('Deep Research pipeline failed:', error)

          if (isCancelled) return // Don't try to write to closed stream

          try {
            const errorMessage =
              error instanceof Error
                ? error.message
                : 'Deep research pipeline encountered an error'

            emit({
              type: 'error',
              content: errorMessage,
            })

            controller.enqueue(
              encoder.encode(
                `event: error\ndata: ${JSON.stringify({ error: errorMessage })}\n\n`
              )
            )
            controller.close()
          } catch (closeError) {
            // Silently ignore if controller is already closed
            console.warn('Failed to send error event (stream may be closed)')
          }
        }
      })()
    },
    cancel() {
      // Cleanup if client disconnects
      console.log('Deep Research stream cancelled by client')
      isCancelled = true
      if (heartbeat) {
        clearInterval(heartbeat)
      }
    },
  })

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      Connection: 'keep-alive',
    },
  })
}
