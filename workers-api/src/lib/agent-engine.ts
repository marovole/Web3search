import type { Env } from '../types/env'
import { createOpenRouterClient } from './openrouter'
import { getSupabaseClient } from './supabase'
import { registerAllAgentTools } from './agent-tools'

interface AgentRun {
  id: string
  task_id: string
  user_id: string
  status: string
  started_at: string
  completed_at?: string
  duration_ms?: number
  input?: unknown
  output?: unknown
  triggered_by?: string
  error_message?: string
  steps?: unknown
  tokens_used?: number
}

interface AgentTask {
  id: string
  run_count: number
  success_count: number
  failure_count: number
}

export interface AgentTool {
  name: string
  description: string
  parameters: Record<string, { type: string; description: string; required?: boolean }>
  execute: (params: Record<string, unknown>, context: AgentContext) => Promise<ToolResult>
}

export interface ToolResult {
  success: boolean
  data?: unknown
  error?: string
}

export interface AgentContext {
  env: Env
  userId: string
  taskId: string
  runId: string
}

export interface AgentStep {
  type: 'thought' | 'action' | 'observation' | 'answer'
  content: string
  tool?: string
  params?: Record<string, unknown>
  result?: ToolResult
  timestamp: string
}

export interface AgentRunResult {
  success: boolean
  output: unknown
  steps: AgentStep[]
  tokensUsed: number
  error?: string
}

const toolRegistry: Map<string, AgentTool> = new Map()

export function registerTool(tool: AgentTool): void {
  toolRegistry.set(tool.name, tool)
}

export function getTool(name: string): AgentTool | undefined {
  return toolRegistry.get(name)
}

export function getAvailableTools(): AgentTool[] {
  return Array.from(toolRegistry.values())
}

// Auto-register all tools on module load
registerAllAgentTools(registerTool)

export async function executeAgentTask(
  env: Env,
  taskId: string,
  userId: string,
  taskType: string,
  config: Record<string, unknown>
): Promise<AgentRunResult> {
  const supabase = getSupabaseClient(env, true)

  const { data: run, error: runError } = await supabase
    .from<AgentRun>('agent_runs')
    .insert({
      task_id: taskId,
      user_id: userId,
      status: 'running',
      input: config,
      triggered_by: 'schedule',
    })
    .select()
    .single()

  if (runError || !run) {
    console.error('[AgentEngine] Failed to create run:', runError)
    return { success: false, output: null, steps: [], tokensUsed: 0, error: 'Failed to create run' }
  }

  const runData = run as AgentRun
  const context: AgentContext = { env, userId, taskId, runId: runData.id }
  const steps: AgentStep[] = []
  let tokensUsed = 0

  try {
    const result = await runAgentLoop(context, taskType, config, steps)
    tokensUsed = result.tokensUsed

    await supabase
      .from<AgentRun>('agent_runs')
      .update({
        status: 'completed',
        completed_at: new Date().toISOString(),
        duration_ms: Date.now() - new Date(runData.started_at).getTime(),
        output: result.output,
        steps,
        tokens_used: tokensUsed,
      })
      .eq('id', runData.id)

    await supabase
      .from('agent_tasks')
      .update({
        last_run_at: new Date().toISOString(),
        run_count: (await getRunCount(supabase, taskId)) + 1,
        success_count: (await getSuccessCount(supabase, taskId)) + 1,
      })
      .eq('id', taskId)

    return { success: true, output: result.output, steps, tokensUsed }
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error'

    await supabase
      .from<AgentRun>('agent_runs')
      .update({
        status: 'failed',
        completed_at: new Date().toISOString(),
        duration_ms: Date.now() - new Date(runData.started_at).getTime(),
        error_message: errorMessage,
        steps,
        tokens_used: tokensUsed,
      })
      .eq('id', runData.id)

    await supabase
      .from('agent_tasks')
      .update({
        last_run_at: new Date().toISOString(),
        run_count: (await getRunCount(supabase, taskId)) + 1,
        failure_count: (await getFailureCount(supabase, taskId)) + 1,
      })
      .eq('id', taskId)

    return { success: false, output: null, steps, tokensUsed, error: errorMessage }
  }
}

async function runAgentLoop(
  context: AgentContext,
  taskType: string,
  config: Record<string, unknown>,
  steps: AgentStep[]
): Promise<{ output: unknown; tokensUsed: number }> {
  const openrouter = createOpenRouterClient(context.env)

  const systemPrompt = buildSystemPrompt(taskType, config)

  const messages: Array<{ role: 'system' | 'user' | 'assistant'; content: string }> = [
    { role: 'system', content: systemPrompt },
    { role: 'user', content: buildTaskPrompt(taskType, config) },
  ]

  let totalTokens = 0
  const maxIterations = 5
  let iteration = 0

  while (iteration < maxIterations) {
    iteration++

    const response = await openrouter.request({
      model: 'deepseek/deepseek-v3.2-speciale',
      messages,
      temperature: 0.3,
      max_tokens: 2000,
    })

    const data = await response.json() as {
      choices?: Array<{ message?: { content?: string } }>
      usage?: { total_tokens?: number }
    }

    totalTokens += data.usage?.total_tokens || 0

    const content = data.choices?.[0]?.message?.content || ''

    if (content.includes('[ANSWER]')) {
      const answer = content.split('[ANSWER]')[1]?.trim() || content
      steps.push({ type: 'answer', content: answer, timestamp: new Date().toISOString() })
      return { output: { answer, raw: content }, tokensUsed: totalTokens }
    }

    if (content.includes('[ACTION]')) {
      const thoughtMatch = content.match(/\[THOUGHT\]([\s\S]*?)\[ACTION\]/)
      if (thoughtMatch) {
        steps.push({ type: 'thought', content: thoughtMatch[1].trim(), timestamp: new Date().toISOString() })
      }

      const actionMatch = content.match(/\[ACTION\]\s*(\w+)\(([\s\S]*?)\)/)
      if (actionMatch) {
        const toolName = actionMatch[1]
        let params: Record<string, unknown> = {}
        try {
          params = JSON.parse(actionMatch[2] || '{}')
        } catch {
          params = { raw: actionMatch[2] }
        }

        const tool = getTool(toolName)
        if (tool) {
          steps.push({
            type: 'action',
            content: `Calling ${toolName}`,
            tool: toolName,
            params,
            timestamp: new Date().toISOString(),
          })

          const result = await tool.execute(params, context)

          steps.push({
            type: 'observation',
            content: JSON.stringify(result.data || result.error),
            result,
            timestamp: new Date().toISOString(),
          })

          messages.push({ role: 'assistant', content })
          messages.push({
            role: 'user',
            content: `[OBSERVATION] ${JSON.stringify(result.data || result.error)}`,
          })
        } else {
          steps.push({ type: 'observation', content: `Tool ${toolName} not found`, timestamp: new Date().toISOString() })
          break
        }
      } else {
        break
      }
    } else {
      steps.push({ type: 'answer', content, timestamp: new Date().toISOString() })
      return { output: { answer: content }, tokensUsed: totalTokens }
    }
  }

  return { output: { answer: 'Max iterations reached', steps }, tokensUsed: totalTokens }
}

function buildSystemPrompt(taskType: string, _config: Record<string, unknown>): string {
  const base = `You are an AI agent specialized in cryptocurrency analysis.
You can use tools to gather information and then provide answers.

Format your responses as:
[THOUGHT] Your reasoning about what to do next
[ACTION] toolName({"param": "value"})

Or when you have the final answer:
[ANSWER] Your final response

Available task types: price_alert, risk_monitor, news_brief, portfolio_health, opportunity_finder`

  const typeSpecific: Record<string, string> = {
    price_alert: '\n\nYou are monitoring price movements and triggering alerts when conditions are met.',
    risk_monitor: '\n\nYou are monitoring risk indicators and warning about potential issues.',
    news_brief: '\n\nYou are summarizing relevant cryptocurrency news.',
    portfolio_health: '\n\nYou are analyzing portfolio composition and health.',
    opportunity_finder: '\n\nYou are finding investment opportunities based on user preferences.',
  }

  return base + (typeSpecific[taskType] || '')
}

function buildTaskPrompt(taskType: string, config: Record<string, unknown>): string {
  return `Execute task type: ${taskType}\nConfiguration: ${JSON.stringify(config, null, 2)}`
}

export function getToolsForTaskType(_taskType: string): AgentTool[] {
  return getAvailableTools()
}

async function getRunCount(supabase: ReturnType<typeof getSupabaseClient>, taskId: string): Promise<number> {
  const { data } = await supabase.from<AgentTask>('agent_tasks').select('run_count').eq('id', taskId).single()
  const task = data as AgentTask | null
  return task?.run_count || 0
}

async function getSuccessCount(supabase: ReturnType<typeof getSupabaseClient>, taskId: string): Promise<number> {
  const { data } = await supabase.from<AgentTask>('agent_tasks').select('success_count').eq('id', taskId).single()
  const task = data as AgentTask | null
  return task?.success_count || 0
}

async function getFailureCount(supabase: ReturnType<typeof getSupabaseClient>, taskId: string): Promise<number> {
  const { data } = await supabase.from<AgentTask>('agent_tasks').select('failure_count').eq('id', taskId).single()
  const task = data as AgentTask | null
  return task?.failure_count || 0
}
