/**
 * Multi-Agent Framework Error Types
 */

export class AgentError extends Error {
  constructor(
    message: string,
    public code: string,
    public agentId?: string,
    public recoverable: boolean = false
  ) {
    super(message)
    this.name = 'AgentError'
  }
}

export class CoordinatorError extends Error {
  constructor(
    message: string,
    public code: string,
    public taskId?: string,
    public recoverable: boolean = false
  ) {
    super(message)
    this.name = 'CoordinatorError'
  }
}

export class ContextError extends Error {
  constructor(
    message: string,
    public code: string,
    public operation: 'read' | 'write' | 'delete'
  ) {
    super(message)
    this.name = 'ContextError'
  }
}

export class TimeoutError extends Error {
  constructor(
    message: string,
    public agentId?: string,
    public timeout: number = 0
  ) {
    super(message)
    this.name = 'TimeoutError'
  }
}

export class ValidationError extends Error {
  constructor(
    message: string,
    public field?: string,
    public value?: unknown
  ) {
    super(message)
    this.name = 'ValidationError'
  }
}

export function isRecoverableError(error: Error): boolean {
  if (error instanceof AgentError) return error.recoverable
  if (error instanceof CoordinatorError) return error.recoverable
  return false
}

export function getErrorCode(error: Error): string {
  if ('code' in error && typeof (error as { code?: string }).code === 'string') {
    return (error as { code: string }).code
  }
  return 'UNKNOWN_ERROR'
}
