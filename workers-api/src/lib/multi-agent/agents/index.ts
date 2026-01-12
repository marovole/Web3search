/**
 * SubAgent Interface and Base Class
 */

import type { Env } from '../../../types/env'
import type { ModelConfig } from '../../model-routing'
import type { SubAgent as SubAgentInterface, AgentInput, AgentResult, SharedContext } from '../types'
import type { ISSEEmitter } from '../../../services/deep-research/types'

/**
 * SubAgent Interface
 * All specialized agents must implement this interface
 */
export type SubAgent = SubAgentInterface

/**
 * Abstract base class for all sub-agents
 * Provides common functionality and enforces interface implementation
 */
export abstract class BaseSubAgent implements SubAgentInterface {
  abstract readonly id: string
  abstract readonly name: string
  abstract readonly description: string
  abstract readonly capabilities: string[]
  abstract readonly inputRequirements: string[]

  constructor(
    protected readonly env: Env,
    protected readonly modelConfig: ModelConfig
  ) {}

  /**
   * Execute the agent's specialized task - must be implemented by subclasses
   */
  abstract execute(
    context: SharedContext,
    input: AgentInput,
    emitter?: ISSEEmitter
  ): Promise<AgentResult>

  /**
   * Default input validation
   */
  validateInput(input: AgentInput): { valid: boolean; missing: string[] } {
    const missing = this.inputRequirements.filter(
      (req) => !(req in input) || input[req as keyof AgentInput] === undefined
    )
    return {
      valid: missing.length === 0,
      missing,
    }
  }

  /**
   * Get current timestamp in ISO format
   */
  protected getTimestamp(): string {
    return new Date().toISOString()
  }

  /**
   * Calculate duration from start time
   */
  protected getDuration(startTime: number): number {
    return Date.now() - startTime
  }

  /**
   * Emit progress to SSE emitter if available
   */
  protected emitProgress(
    emitter: ISSEEmitter | undefined,
    stage: string,
    message: string
  ): void {
    if (emitter) {
      emitter.emitProgress(stage, message)
    }
  }
}
