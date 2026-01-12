/**
 * Central Coordinator
 * Orchestrates the execution of multiple sub-agents
 */

import type { Env } from '../../../types/env'
import type { ModelConfig } from '../../model-routing'
import type {
  MultiAgentTask,
  SharedContext,
  SubAgent,
  AgentInput,
  AgentResult,
  CoordinatorResult,
  AggregatedResult,
} from '../types'
import type { ISSEEmitter } from '../../../services/deep-research/types'
import { getSubAgentRegistry } from '../agents/registry'
import { createSSEResponse, createHeartbeatInterval } from '../../../services/deep-research/streaming.service'
import { KvTaskStorage, createTaskStorage } from '../task-storage'

export class CentralCoordinator {
  private registry = getSubAgentRegistry()
  private taskStorage: KvTaskStorage

  constructor(
    private readonly env: Env,
    private readonly modelConfig: ModelConfig
  ) {
    this.taskStorage = createTaskStorage(env)
  }

  /**
   * Execute a multi-agent task
   */
  async executeTask(task: MultiAgentTask, emitter: ISSEEmitter): Promise<CoordinatorResult> {
    const startTime = Date.now()
    const taskId = task.id

    try {
      // Emit task start
      emitter.emitProgress('coordinator', `Starting task: ${task.query.slice(0, 50)}...`)

      // Step 1: Create shared context
      const context = this.createContext(task)

      // Step 2: Select and initialize agents
      const agents = this.registry.getAgentsForIntent(
        task.intent,
        this.env,
        this.modelConfig
      )

      emitter.emitProgress('coordinator', `Initialized ${agents.length} agents`)

      // Step 3: Execute parallel sub-tasks (Researcher, Analyzer, Risk, News run in parallel)
      const parallelAgentIds = ['researcher', 'analyzer', 'risk', 'news']
      const parallelAgents = agents.filter((a) => parallelAgentIds.includes(a.id))

      if (parallelAgents.length > 0) {
        emitter.emitProgress('coordinator', 'Executing parallel research tasks...')

        const parallelResults = await this.executeParallelAgents(
          parallelAgents,
          context,
          { taskId, query: task.query },
          emitter
        )

        // Store results in context
        parallelResults.forEach((result) => {
          context.agentResults.set(result.agentId, result)
        })
      }

      // Step 4: Execute Reporter (sequential - depends on all previous results)
      const reporterAgent = agents.find((a) => a.id === 'reporter')
      if (reporterAgent) {
        emitter.emitProgress('coordinator', 'Generating final report...')

        const reporterInput: AgentInput = {
          taskId,
          query: task.query,
          dependentResults: parallelAgentIds,
        }

        const reporterResult = await reporterAgent.execute(context, reporterInput, emitter)
        context.agentResults.set(reporterResult.agentId, reporterResult)
      }

      // Step 5: Extract final result from Reporter
      const reporterResult = context.agentResults.get('reporter')

      if (!reporterResult || reporterResult.status !== 'completed') {
        throw new Error('Report generation failed')
      }

      const aggregatedResult = reporterResult.output as AggregatedResult

      // Emit completion
      emitter.emitComplete(JSON.stringify(aggregatedResult), taskId)

      const duration = Date.now() - startTime

      return {
        taskId,
        success: true,
        output: aggregatedResult,
        tokensUsed: this.calculateTotalTokens(context),
        duration,
      }
    } catch (error) {
      const duration = Date.now() - startTime

      emitter.emitError(error instanceof Error ? error.message : 'Unknown error')

      return {
        taskId,
        success: false,
        output: null,
        tokensUsed: 0,
        duration,
        error: error instanceof Error ? error.message : 'Unknown error',
      }
    }
  }

  /**
   * Get task storage for external use
   */
  getTaskStorage(): KvTaskStorage {
    return this.taskStorage
  }

  /**
   * Create shared context for the task
   */
  private createContext(task: MultiAgentTask): SharedContext {
    return {
      taskId: task.id,
      originalQuery: task.query,
      userId: task.userId,
      env: this.env,
      modelConfig: this.modelConfig,
      collectedData: {
        searchResults: [],
        priceData: {},
        riskMetrics: {},
        newsArticles: [],
      },
      agentResults: new Map(),
      startTime: Date.now(),
    }
  }

  /**
   * Execute multiple agents in parallel
   */
  private async executeParallelAgents(
    agents: SubAgent[],
    context: SharedContext,
    input: AgentInput,
    emitter: ISSEEmitter
  ): Promise<AgentResult[]> {
    const results: AgentResult[] = []
    const startPromises = agents.map(async (agent) => {
      try {
        emitter.emitProgress(agent.id, `${agent.name}: Starting analysis...`)

        const result = await agent.execute(context, input, emitter)

        emitter.emitProgress(
          agent.id,
          `${agent.name}: ${result.status === 'completed' ? 'Completed' : 'Failed'}`
        )

        results.push(result)
        return result
      } catch (error) {
        const failedResult: AgentResult = {
          agentId: agent.id,
          agentName: agent.name,
          status: 'failed',
          output: null,
          metrics: {
            tokensUsed: 0,
            duration: 0,
            sourcesProcessed: 0,
          },
          error: error instanceof Error ? error.message : 'Unknown error',
        }
        results.push(failedResult)
        return failedResult
      }
    })

    await Promise.all(startPromises)
    return results
  }

  /**
   * Calculate total tokens used
   */
  private calculateTotalTokens(context: SharedContext): number {
    let total = 0
    context.agentResults.forEach((result) => {
      total += result.metrics.tokensUsed
    })
    return total
  }

  /**
   * Create SSE response for task execution
   */
  static createResponse(
    env: Env,
    modelConfig: ModelConfig,
    executeHandler: (coordinator: CentralCoordinator, emitter: ISSEEmitter) => Promise<void>
  ): Response {
    return createSSEResponse(async (emitter, controller) => {
      const heartbeat = createHeartbeatInterval(emitter)

      try {
        const coordinator = new CentralCoordinator(env, modelConfig)
        await executeHandler(coordinator, emitter)
      } finally {
        clearInterval(heartbeat)
        emitter.close()
      }
    })
  }
}
