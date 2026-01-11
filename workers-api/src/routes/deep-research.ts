/**
 * Deep Research API Routes
 * Thin route layer that delegates to services
 */

import { Hono } from 'hono'
import type { Env } from '../types/env'
import type {
  DeepResearchRequest,
  ResearchStatus,
  ResearchDepth,
  ResearchType,
} from '../types/deep-research'
import { getSupabaseClient } from '../lib/supabase'
import { ROUTING_STRATEGIES, getModelConfig } from '../lib/model-routing'
import { createRateLimitMiddleware } from '../middlewares/rate-limit'
import { ensureConversationExists, persistMessage } from '../lib/conversation'
import {
  fetchMarketContext,
  extractContractAddress,
  detectChainFromQuery,
  type MarketContext,
} from '../lib/context-builders/market-context'
import { buildContextInjectedPrompt } from '../lib/research-prompts'
import {
  validateResearchQuery,
  MAX_RESEARCH_QUERY_LENGTH,
  processResearchTask,
  generateResearchPlan,
  searchSources,
  synthesizeFindings,
  SSEEmitter,
  createSSEResponse,
  createHeartbeatInterval,
  type ModelConfig,
} from '../services/deep-research'

const DEFAULT_RESEARCH_DEPTH: ResearchDepth = 'standard'

const deepResearch = new Hono<{ Bindings: Env }>()

deepResearch.post(
  '/',
  createRateLimitMiddleware({
    scope: 'deep-research-user-day',
    limit: 5,
    windowSeconds: 60 * 60 * 24,
    key: async (c) => {
      const body = await c.req.json().catch(() => ({}))
      return body.user_id || 'anonymous'
    },
  }),
  async (c) => {
    let body: DeepResearchRequest
    try {
      body = await c.req.json<DeepResearchRequest>()
    } catch {
      return c.json({ error: { code: 'INVALID_JSON', message: 'Body must be valid JSON', status: 400 } }, 400)
    }

    const query = body.query?.trim()
    if (!query) {
      return c.json({ error: { code: 'MISSING_QUERY', message: 'Field "query" is required', status: 400 } }, 400)
    }

    if (query.length > MAX_RESEARCH_QUERY_LENGTH) {
      return c.json({ error: { code: 'QUERY_TOO_LONG', message: `Query exceeds ${MAX_RESEARCH_QUERY_LENGTH} characters`, status: 400 } }, 400)
    }

    try {
      const supabase = getSupabaseClient(c.env, true)
      const useCase = 'deep-research' as const
      const modelId = body.model || ROUTING_STRATEGIES[useCase].primary[0]
      const modelConfig = getModelConfig(modelId)

      if (!modelConfig) {
        return c.json({ error: { code: 'INVALID_MODEL', message: `Model ${modelId} not found`, status: 400 } }, 400)
      }

      let conversationId = body.conversation_id
      if (!conversationId) {
        conversationId = crypto.randomUUID()
        await ensureConversationExists(supabase, conversationId, { title: `Research: ${query.substring(0, 100)}` })
      }

      const taskId = crypto.randomUUID()
      const taskData = {
        id: taskId,
        user_id: null,
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

      const { error } = await supabase.from('deep_research_tasks').insert(taskData).select().single()

      if (error) {
        console.error('Failed to create research task:', error)
        throw error
      }

      c.executionCtx.waitUntil(processResearchTask(taskId, query, modelConfig, supabase, c.env))

      return c.json({
        task_id: taskId,
        status: 'pending',
        message: 'Research task created and processing in background',
        poll_url: `/api/v1/deep-research/${taskId}`,
        stream_url: `/api/v1/deep-research/${taskId}/stream`,
      }, 202)
    } catch (error) {
      console.error('Failed to create deep research task:', error)
      return c.json({ error: { code: 'RESEARCH_TASK_ERROR', message: 'Failed to create research task', status: 500 } }, 500)
    }
  }
)

deepResearch.get(
  '/stream',
  createRateLimitMiddleware({
    scope: 'deep-research-ip-day',
    limit: 5,
    windowSeconds: 60 * 60 * 24,
    key: (c) => c.req.header('cf-connecting-ip') || 'anonymous',
  }),
  async (c) => {
    const queryParam = c.req.query('query')
    const conversationParam = c.req.query('conversation_id')
    const modelParam = c.req.query('model')
    const typeParam = c.req.query('type') as ResearchType | undefined

    const validation = validateResearchQuery(queryParam || '')
    if (!validation.valid) {
      return c.json({ error: { code: 'INVALID_QUERY', message: validation.error || 'Invalid query', status: 400 } }, 400)
    }

    const query = validation.sanitized

    try {
      const supabase = getSupabaseClient(c.env, true)
      const useCase = 'deep-research' as const
      const modelId = typeof modelParam === 'string' && modelParam.trim() ? modelParam.trim() : ROUTING_STRATEGIES[useCase].primary[0]
      const modelConfig = getModelConfig(modelId)

      if (!modelConfig) {
        return c.json({ error: { code: 'INVALID_MODEL', message: `Model "${modelId}" not found`, status: 400 } }, 400)
      }

      const conversationId = typeof conversationParam === 'string' && conversationParam.trim() ? conversationParam.trim() : crypto.randomUUID()
      await ensureConversationExists(supabase, conversationId, { title: `Deep Research: ${query.substring(0, 100)}` })
      await persistMessage(supabase, { conversation_id: conversationId, role: 'user', content: query, metadata: null })

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
      return c.json({ error: { code: 'DEEP_RESEARCH_ERROR', message: 'Failed to start deep research', status: 500 } }, 500)
    }
  }
)

deepResearch.get('/:id', async (c) => {
  const taskId = c.req.param('id')

  if (!taskId) {
    return c.json({ error: { code: 'MISSING_TASK_ID', message: 'Task ID is required', status: 400 } }, 400)
  }

  try {
    const supabase = getSupabaseClient(c.env, true)
    const { data: task, error } = await supabase.from('deep_research_tasks').select('*').eq('id', taskId).single()

    if (error) {
      if (error.code === 'PGRST116') {
        return c.json({ error: { code: 'TASK_NOT_FOUND', message: 'Research task not found', status: 404 } }, 404)
      }
      throw error
    }

    return c.json({ task })
  } catch (error) {
    console.error('Failed to fetch research task:', error)
    return c.json({ error: { code: 'FETCH_TASK_ERROR', message: 'Failed to fetch research task', status: 500 } }, 500)
  }
})

deepResearch.get('/', async (c) => {
  try {
    const supabase = getSupabaseClient(c.env, true)
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

    if (error) throw error

    return c.json({ tasks: tasks || [], total: count || 0, limit, offset })
  } catch (error) {
    console.error('Failed to list research tasks:', error)
    return c.json({ error: { code: 'LIST_TASKS_ERROR', message: 'Failed to list research tasks', status: 500 } }, 500)
  }
})

export default deepResearch

interface StreamDeepResearchParams {
  query: string
  conversationId: string
  modelConfig: ModelConfig
  supabase: ReturnType<typeof getSupabaseClient>
  env: Env
  researchType: ResearchType
}

function streamDeepResearch({ query, conversationId, modelConfig, supabase, env, researchType }: StreamDeepResearchParams): Response {
  const isTokenomics = researchType === 'tokenomics'

  return createSSEResponse(
    async (emitter, controller) => {
      const heartbeat = createHeartbeatInterval(emitter)

      try {
        const contractAddress = extractContractAddress(query)
        const chain = contractAddress ? detectChainFromQuery(query) : null
        const cacheKey = contractAddress && chain && env.CACHE ? `research:report:${chain}:${contractAddress.toLowerCase()}:${researchType}` : null

        if (cacheKey) {
          try {
            const cached = await env.CACHE!.get(cacheKey)
            if (cached) {
              const cachedReport = JSON.parse(cached)
              emitter.emitProgress('cache_hit', `命中缓存，直接返回研究结果（合约: ${contractAddress}）`)
              if (cachedReport.answer) emitter.emitContent('answer', cachedReport.answer)
              if (cachedReport.result?.key_findings || cachedReport.result?.scorecard) {
                emitter.emitContent('structured_result', JSON.stringify({
                  key_findings: cachedReport.result?.key_findings,
                  scorecard: cachedReport.result?.scorecard,
                  risks: cachedReport.result?.risks_and_uncertainties,
                  conclusion: cachedReport.result?.conclusion || cachedReport.result?.verdict,
                }))
              }
              await persistMessage(supabase, {
                conversation_id: conversationId,
                role: 'assistant',
                content: cachedReport.answer || '',
                metadata: { research_result: cachedReport.result, citations: cachedReport.citations || [], cache_hit: true },
              })
              emitter.emitComplete(cachedReport.summary || 'Research completed (from cache)', conversationId)
              clearInterval(heartbeat)
              emitter.sendDone(true)
              emitter.close()
              return
            }
          } catch (cacheError) {
            console.warn('Deep Research cache read failed:', cacheError)
          }
        }

        let marketContext: MarketContext | null = null
        if (contractAddress && chain) {
          const marketStartTime = Date.now()
          emitter.emitToolCall({ tool: 'market_data', provider: 'dexscreener+goplus', status: 'started', latency_ms: 0, result_summary: `Fetching market data for ${contractAddress}...`, query: contractAddress })
          emitter.emitProgress('market_data', `正在获取合约 ${contractAddress} 的市场数据...`)
          try {
            marketContext = await fetchMarketContext(contractAddress, chain, env)
            const marketLatency = Date.now() - marketStartTime
            emitter.emitToolCall({ tool: 'market_data', provider: 'dexscreener+goplus', status: 'completed', latency_ms: marketLatency, result_summary: `Price: $${marketContext.price?.usd?.toFixed(6) || 'N/A'}, Risk: ${marketContext.security?.risk_level || 'unknown'}`, query: contractAddress })
            emitter.emitProgress('market_data_fetched', marketContext.from_cache ? `已获取市场数据（缓存）：$${marketContext.price?.usd?.toFixed(6) || 'N/A'}` : `已获取实时市场数据：$${marketContext.price?.usd?.toFixed(6) || 'N/A'}`)
          } catch (marketError) {
            const marketLatency = Date.now() - marketStartTime
            emitter.emitToolCall({ tool: 'market_data', provider: 'dexscreener+goplus', status: 'failed', latency_ms: marketLatency, result_summary: 'Market data fetch failed, proceeding without context', query: contractAddress })
            console.warn('Market context fetch failed:', marketError)
            emitter.emitProgress('market_data_fetched', '市场数据获取失败，继续执行通用研究流程。')
          }
        } else {
          emitter.emitProgress('market_data_fetched', contractAddress ? '未能识别区块链网络，跳过市场数据注入。' : '未检测到合约地址，跳过市场数据注入。')
        }

        const { getSystemPromptByType, getTokenomicsSearchQueries } = await import('../lib/research-prompts')
        emitter.emitProgress('data_collection', isTokenomics ? '🔍 启动 Tokenomics 深度审计模式...' : '正在分析研究需求，制定调研计划...')

        const planStartTime = Date.now()
        emitter.emitToolCall({ tool: 'plan_generation', status: 'started', latency_ms: 0, result_summary: 'Generating research plan...', query })

        let plan: { search_queries: string[]; plan: string; parsed_plan?: unknown }
        if (isTokenomics) {
          const tokenomicsQueries = getTokenomicsSearchQueries(query, query)
          plan = { search_queries: tokenomicsQueries, plan: `Tokenomics audit for: ${query}`, parsed_plan: { query_understanding: `Tokenomics audit mode: ${query}` } }
        } else {
          plan = await generateResearchPlan(query, modelConfig, env, 'standard')
        }

        const planLatency = Date.now() - planStartTime
        emitter.emitToolCall({ tool: 'plan_generation', status: 'completed', latency_ms: planLatency, result_summary: `Generated ${plan.search_queries.length} search queries`, source_count: plan.search_queries.length })
        emitter.emitThinking({ stage: 'planning', thought: (plan.parsed_plan as { query_understanding?: string })?.query_understanding || `将执行 ${plan.search_queries.length} 个搜索策略来收集信息` })
        emitter.emitProgress('data_collection', isTokenomics ? `📊 代币经济学审计：将分析 ${plan.search_queries.length} 个关键维度...` : `研究计划已生成，将执行 ${plan.search_queries.length} 个搜索策略...`)

        const searchStartTime = Date.now()
        emitter.emitToolCall({ tool: 'search', provider: 'brave|tavily|serper', status: 'started', latency_ms: 0, result_summary: `Searching with ${plan.search_queries.length} queries...`, query: plan.search_queries.slice(0, 3).join(', ') })
        emitter.emitThinking({ stage: 'searching', thought: `正在执行多源搜索：${plan.search_queries.slice(0, 2).join('、')}...` })

        const sources = await searchSources(plan.search_queries, env)
        const searchLatency = Date.now() - searchStartTime

        emitter.emitToolCall({ tool: 'search', provider: 'brave|tavily|serper', status: 'completed', latency_ms: searchLatency, result_summary: `Found ${sources.length} relevant sources`, source_count: sources.length })
        emitter.emitContent('sources', JSON.stringify({ count: sources.length, queries: plan.search_queries, dimensions: (plan.parsed_plan as { research_dimensions?: Array<{ dimension: string }> })?.research_dimensions?.map((d) => d.dimension) || [] }))
        emitter.emitProgress('analysis', `已收集 ${sources.length} 个信息来源，正在进行深度分析...`)

        const analysis = { citations: sources.slice(0, 10).map((source, index) => ({ source_id: index + 1, title: source.title, url: source.url, snippet: source.snippet?.substring(0, 200), relevance_score: source.relevance_score || 0.7 })) }

        emitter.emitProgress('analysis', isTokenomics ? `📈 正在执行 5 维度审计分析...` : `正在综合 ${sources.length} 个来源的信息，生成研究报告...`)
        emitter.emitProgress('report_generation', isTokenomics ? '📝 生成 Tokenomics 审计报告（含压力测试）...' : '正在生成结构化研究报告...')
        emitter.emitThinking({ stage: 'synthesizing', thought: `正在综合 ${sources.length} 个来源的信息，结合市场数据生成深度报告...` })

        const systemPrompt = buildContextInjectedPrompt(getSystemPromptByType(researchType), marketContext)
        const synthesisStartTime = Date.now()
        emitter.emitToolCall({ tool: 'synthesis', provider: modelConfig.provider || 'openrouter', status: 'started', latency_ms: 0, result_summary: 'Invoking LLM for comprehensive report synthesis...' })

        const synthesis = await synthesizeFindings(analysis, query, modelConfig, env, { sources, plan: plan.parsed_plan as { query_understanding: string } || plan.plan, depth: 'deep', researchType, marketContext, systemPrompt })

        const synthesisLatency = Date.now() - synthesisStartTime
        emitter.emitToolCall({ tool: 'synthesis', provider: modelConfig.provider || 'openrouter', status: 'completed', latency_ms: synthesisLatency, result_summary: (synthesis.result as { scorecard?: { score: number; rating: string }; key_findings?: string[] }).scorecard ? `Score: ${(synthesis.result as { scorecard: { score: number; rating: string } }).scorecard.score}/100 (${(synthesis.result as { scorecard: { score: number; rating: string } }).scorecard.rating})` : `Generated ${(synthesis.result as { key_findings?: string[] }).key_findings?.length || 0} key findings` })

        emitter.emitContent('answer', synthesis.answer)
        if ((synthesis.result as { structured_analysis?: unknown; key_findings?: string[] }).structured_analysis || (synthesis.result as { key_findings?: string[] }).key_findings) {
          emitter.emitContent('structured_result', JSON.stringify({ key_findings: (synthesis.result as { key_findings?: string[] }).key_findings, confidence_score: (synthesis.result as { confidence_score?: number }).confidence_score, risks: (synthesis.result as { risks_and_uncertainties?: unknown }).risks_and_uncertainties, conclusion: (synthesis.result as { conclusion?: unknown }).conclusion }))
        }

        await persistMessage(supabase, {
          conversation_id: conversationId,
          role: 'assistant',
          content: synthesis.answer,
          metadata: { research_result: synthesis.result, citations: analysis.citations, market_context: marketContext ? { price: marketContext.price, security: marketContext.security, fetched_at: marketContext.fetched_at } : null },
        })

        if (cacheKey && env.CACHE) {
          const cachePayload = { answer: synthesis.answer, summary: synthesis.summary, result: synthesis.result, citations: analysis.citations, market_context: marketContext, cached_at: new Date().toISOString() }
          env.CACHE.put(cacheKey, JSON.stringify(cachePayload), { expirationTtl: 3600 }).catch((err) => console.warn('Deep Research cache write failed:', err))
        }

        emitter.emitComplete(synthesis.summary || 'Research completed successfully', conversationId)
        clearInterval(heartbeat)
        emitter.sendDone()
        emitter.close()
      } catch (error) {
        clearInterval(heartbeat)
        console.error('Deep Research pipeline failed:', error)
        if (!emitter.isCancelled()) {
          const errorMessage = error instanceof Error ? error.message : 'Deep research pipeline encountered an error'
          emitter.emitError(errorMessage)
          emitter.sendErrorEvent(errorMessage)
          emitter.close()
        }
      }
    },
    () => console.log('Deep Research stream cancelled by client')
  )
}

export { generateResearchPlan, searchSources, synthesizeFindings }
