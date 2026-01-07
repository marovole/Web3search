import type { SupabaseClient } from '@supabase/supabase-js'
import type { Env } from '../../types/env'
import type { ChatCompletionMessage, ChatRole } from '../../types/chat'
import type { MarketContext } from '../../lib/context-builders/market-context'
import type { ModelConfig } from '../../lib/model-routing'
import type { ResearchDepth, ResearchType } from '../../types/deep-research'
import type {
  GeneratedResearchPlan,
  ParsedResearchPlan,
  NormalizedSearchResult,
  SourceAnalysisResult,
  SourceCitation,
  SynthesisOptions,
  SynthesisResult,
  ProgressUpdate,
  GeneralResearchResult,
  TokenomicsResearchResult,
  ResearchConfig,
} from './types'
import { createOpenRouterClient } from '../../lib/openrouter'
import { formatStructuredAnswer, formatTokenomicsAnswer } from './formatter.service'

const RESEARCH_CONFIGS: Record<ResearchDepth, ResearchConfig> = {
  quick: {
    temperature: 0.5,
    plan_max_tokens: 1000,
    synthesis_max_tokens: 2000,
    max_queries: 3,
    max_sources: 5,
  },
  standard: {
    temperature: 0.7,
    plan_max_tokens: 2000,
    synthesis_max_tokens: 4000,
    max_queries: 5,
    max_sources: 10,
  },
  deep: {
    temperature: 0.7,
    plan_max_tokens: 3000,
    synthesis_max_tokens: 8000,
    max_queries: 8,
    max_sources: 20,
  },
}

export function getResearchConfig(depth: ResearchDepth): ResearchConfig {
  return RESEARCH_CONFIGS[depth]
}

export async function updateTaskProgress(
  supabase: SupabaseClient,
  taskId: string,
  progress: ProgressUpdate
): Promise<void> {
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

export async function generateResearchPlan(
  query: string,
  modelConfig: ModelConfig,
  env: Env,
  depth: ResearchDepth = 'standard'
): Promise<GeneratedResearchPlan> {
  const { DEEPRESEARCH_SYSTEM_PROMPT, buildResearchPlanPrompt } = await import(
    '../../lib/research-prompts'
  )

  const openrouter = createOpenRouterClient(env)
  const config = getResearchConfig(depth)

  const messages: ChatCompletionMessage[] = [
    { role: 'system' as ChatRole, content: DEEPRESEARCH_SYSTEM_PROMPT },
    { role: 'user' as ChatRole, content: buildResearchPlanPrompt(query) },
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

  let parsedPlan: ParsedResearchPlan | null = null
  let searchQueries: string[] = []

  try {
    const jsonMatch = content.match(/\{[\s\S]*\}/)
    if (jsonMatch) {
      parsedPlan = JSON.parse(jsonMatch[0])
      if (parsedPlan?.search_queries && Array.isArray(parsedPlan.search_queries)) {
        searchQueries = parsedPlan.search_queries
          .map((q) => (typeof q === 'string' ? q : q.query))
          .filter(Boolean)
      }
    }
  } catch (e) {
    console.warn('Failed to parse research plan JSON, falling back to extraction')
  }

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
  maxQueries = 5
): string[] {
  const queries: string[] = [originalQuery]

  const lines = content.split('\n')
  for (const line of lines) {
    if (/^\d+\.|^[-*]/.test(line)) {
      const cleaned = line.replace(/^\d+\.\s*|^[-*]\s*/, '').trim()
      const quotedMatch = cleaned.match(/"([^"]+)"/)
      const queryText = quotedMatch ? quotedMatch[1] : cleaned
      if (queryText.length > 5 && queryText.length < 200) {
        queries.push(queryText)
      }
    }
  }

  if (queries.length <= 1) {
    queries.push(`${originalQuery} 最新动态`)
    queries.push(`${originalQuery} 深度分析`)
    queries.push(`${originalQuery} 市场趋势`)
  }

  return queries.slice(0, maxQueries)
}

export async function searchSources(
  queries: string[],
  env: Env
): Promise<NormalizedSearchResult[]> {
  const { fetchSearchResultsForQueries } = await import('../../lib/search-providers')

  if (!queries.length) {
    return []
  }

  return fetchSearchResultsForQueries(queries, env)
}

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
    usage?: { prompt_tokens?: number; completion_tokens?: number }
  }

  const citations: SourceCitation[] = sources.slice(0, 3).map((source, index) => ({
    source_id: index + 1,
    title: source.title,
    url: source.url,
    snippet: source.snippet.substring(0, 200),
    relevance_score: source.relevance_score || 0.8,
  }))

  return {
    citations,
    tokens: {
      prompt: result.usage?.prompt_tokens || 0,
      completion: result.usage?.completion_tokens || 0,
    },
    cost: 0,
  }
}

export async function synthesizeFindings(
  analysis: SourceAnalysisResult,
  query: string,
  modelConfig: ModelConfig,
  env: Env,
  options?: SynthesisOptions
): Promise<SynthesisResult> {
  const {
    getSystemPromptByType,
    buildSynthesisPrompt,
    formatSourcesForPrompt,
    buildTokenomicsPrompt,
  } = await import('../../lib/research-prompts')

  const openrouter = createOpenRouterClient(env)
  const depth = options?.depth || 'standard'
  const researchType = options?.researchType || 'general'
  const config = getResearchConfig(depth)
  const isTokenomics = researchType === 'tokenomics'

  const sourcesContext = options?.sources
    ? formatSourcesForPrompt(options.sources)
    : JSON.stringify(analysis, null, 2)

  const planContext = options?.plan
    ? typeof options.plan === 'string'
      ? options.plan
      : JSON.stringify(options.plan, null, 2)
    : ''

  const systemPrompt = options?.systemPrompt || getSystemPromptByType(researchType)

  const userPrompt = isTokenomics
    ? buildTokenomicsPrompt(query) + `\n\n## 收集到的信息来源\n${sourcesContext}`
    : buildSynthesisPrompt(query, planContext, sourcesContext, options?.marketContext)

  const messages: ChatCompletionMessage[] = [
    { role: 'system' as ChatRole, content: systemPrompt },
    { role: 'user' as ChatRole, content: userPrompt },
  ]

  const payload = {
    model: modelConfig.model,
    messages,
    temperature: config.temperature,
    max_tokens: config.synthesis_max_tokens,
    stream: false,
  }

  const response = await openrouter.request(payload)
  const result = (await response.json()) as {
    choices?: Array<{ message?: { content?: string } }>
  }

  const content = result.choices?.[0]?.message?.content || ''

  let parsedResult: Record<string, unknown> | null = null
  try {
    const jsonMatch = content.match(/\{[\s\S]*\}/)
    if (jsonMatch) {
      parsedResult = JSON.parse(jsonMatch[0])
    }
  } catch (e) {
    console.warn('Failed to parse synthesis JSON, using raw content')
  }

  const structuredResult = buildStructuredResult(
    parsedResult,
    content,
    query,
    analysis,
    options,
    isTokenomics,
    depth
  )

  return {
    result: structuredResult,
    summary: structuredResult.summary,
    answer: structuredResult.answer,
  }
}

function buildStructuredResult(
  parsedResult: Record<string, unknown> | null,
  content: string,
  query: string,
  analysis: SourceAnalysisResult,
  options: SynthesisOptions | undefined,
  isTokenomics: boolean,
  depth: ResearchDepth
): GeneralResearchResult | TokenomicsResearchResult {
  if (isTokenomics && parsedResult?.scorecard) {
    return {
      research_type: 'tokenomics' as const,
      summary: (parsedResult.verdict as { summary?: string })?.summary || `Tokenomics audit for: ${query}`,
      answer: formatTokenomicsAnswer(parsedResult as Parameters<typeof formatTokenomicsAnswer>[0]),
      scorecard: parsedResult.scorecard as TokenomicsResearchResult['scorecard'],
      red_flags: (parsedResult.red_flags as string[]) || [],
      tokenomics_analysis: parsedResult.analysis,
      stress_test: parsedResult.stress_test,
      verdict: parsedResult.verdict as TokenomicsResearchResult['verdict'],
      data_quality: parsedResult.data_quality as TokenomicsResearchResult['data_quality'],
      sources: (options?.sources || []) as NormalizedSearchResult[],
      citations: analysis.citations || [],
      research_depth: depth,
      total_sources: options?.sources?.length || 0,
      total_citations: analysis.citations?.length || 0,
      confidence_score: (parsedResult.data_quality as { transparency_score?: number })?.transparency_score
        ? ((parsedResult.data_quality as { transparency_score: number }).transparency_score / 10)
        : 0.75,
    }
  }

  return {
    research_type: 'general' as const,
    summary: (parsedResult?.executive_summary as string) || `Research summary for: ${query}`,
    answer: parsedResult
      ? formatStructuredAnswer(parsedResult as Parameters<typeof formatStructuredAnswer>[0])
      : content,
    key_findings:
      (parsedResult?.key_findings as Array<string | { finding: string }>)?.map((f) =>
        typeof f === 'string' ? f : f.finding
      ) || ['Key findings extracted from analysis'],
    sources: (options?.sources || []) as NormalizedSearchResult[],
    citations: analysis.citations || [],
    research_depth: depth,
    total_sources: options?.sources?.length || 0,
    total_citations: analysis.citations?.length || 0,
    confidence_score: (parsedResult?.metadata as { overall_confidence?: number })?.overall_confidence || 0.75,
    structured_analysis: parsedResult?.detailed_analysis || null,
    risks_and_uncertainties: parsedResult?.risks_and_uncertainties as GeneralResearchResult['risks_and_uncertainties'],
    conclusion: parsedResult?.conclusion as GeneralResearchResult['conclusion'],
  }
}

export async function processResearchTask(
  taskId: string,
  query: string,
  modelConfig: ModelConfig,
  supabase: SupabaseClient,
  env: Env
): Promise<void> {
  const startTime = Date.now()

  try {
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

    await updateTaskProgress(supabase, taskId, {
      current_step: 'Generating research plan',
      steps_completed: 2,
      progress_percent: 20,
    })

    const plan = await generateResearchPlan(query, modelConfig, env)

    await updateTaskProgress(supabase, taskId, {
      current_step: 'Searching for sources',
      steps_completed: 3,
      progress_percent: 40,
    })

    const sources = await searchSources(plan.search_queries, env)

    await updateTaskProgress(supabase, taskId, {
      current_step: 'Analyzing sources',
      steps_completed: 4,
      progress_percent: 60,
    })

    const analysisResult = await analyzeSources(sources, query, modelConfig, env)

    await updateTaskProgress(supabase, taskId, {
      current_step: 'Synthesizing findings',
      steps_completed: 5,
      progress_percent: 80,
    })

    const synthesis = await synthesizeFindings(analysisResult, query, modelConfig, env)

    await updateTaskProgress(supabase, taskId, {
      current_step: 'Compiling final result',
      steps_completed: 5,
      progress_percent: 90,
    })

    const durationMs = Date.now() - startTime

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
        citations: analysisResult.citations,
        tokens_prompt: analysisResult.tokens?.prompt || 0,
        tokens_completion: analysisResult.tokens?.completion || 0,
        cost_usd: analysisResult.cost || 0,
      })
      .eq('id', taskId)

    if (error) {
      throw error
    }

    console.log(`Research task ${taskId} completed successfully`)
  } catch (error) {
    console.error(`Research task ${taskId} failed:`, error)

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
