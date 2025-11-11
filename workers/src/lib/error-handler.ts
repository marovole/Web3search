/**
 * 统一的错误处理系统
 * 提供一致的错误响应格式和日志记录
 */

export enum ErrorCode {
  // 通用错误
  INTERNAL_ERROR = 'INTERNAL_ERROR',
  INVALID_REQUEST = 'INVALID_REQUEST',
  NOT_FOUND = 'NOT_FOUND',
  UNAUTHORIZED = 'UNAUTHORIZED',
  FORBIDDEN = 'FORBIDDEN',
  RATE_LIMITED = 'RATE_LIMITED',
  
  // 验证错误
  VALIDATION_ERROR = 'VALIDATION_ERROR',
  INVALID_INPUT = 'INVALID_INPUT',
  MISSING_REQUIRED_FIELD = 'MISSING_REQUIRED_FIELD',
  
  // 数据库错误
  DATABASE_ERROR = 'DATABASE_ERROR',
  DATABASE_CONNECTION_FAILED = 'DATABASE_CONNECTION_FAILED',
  RECORD_NOT_FOUND = 'RECORD_NOT_FOUND',
  DUPLICATE_RECORD = 'DUPLICATE_RECORD',
  
  // 外部服务错误
  EXTERNAL_API_ERROR = 'EXTERNAL_API_ERROR',
  OPENROUTER_ERROR = 'OPENROUTER_ERROR',
  SUPABASE_ERROR = 'SUPABASE_ERROR',
  
  // 业务逻辑错误
  CONVERSATION_NOT_FOUND = 'CONVERSATION_NOT_FOUND',
  MESSAGE_TOO_LONG = 'MESSAGE_TOO_LONG',
  INVALID_CONVERSATION_ID = 'INVALID_CONVERSATION_ID',
  
  // 安全错误
  SECURITY_VIOLATION = 'SECURITY_VIOLATION',
  SUSPICIOUS_ACTIVITY = 'SUSPICIOUS_ACTIVITY',
  INJECTION_ATTEMPT = 'INJECTION_ATTEMPT'
}

export enum ErrorSeverity {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical'
}

export interface AppError {
  code: ErrorCode
  message: string
  details?: any
  severity: ErrorSeverity
  timestamp: string
  requestId?: string
  userId?: string
  path?: string
  method?: string
}

export interface ErrorResponse {
  error: {
    code: ErrorCode
    message: string
    details?: any
    timestamp: string
    requestId?: string
  }
  status: number
}

/**
 * 应用程序错误类
 */
export class ApplicationError extends Error {
  public readonly code: ErrorCode
  public readonly severity: ErrorSeverity
  public readonly details?: any
  public readonly timestamp: string
  public readonly requestId?: string
  public readonly userId?: string
  public readonly path?: string
  public readonly method?: string

  constructor(options: {
    code: ErrorCode
    message: string
    severity?: ErrorSeverity
    details?: any
    requestId?: string
    userId?: string
    path?: string
    method?: string
  }) {
    super(options.message)
    this.name = 'ApplicationError'
    this.code = options.code
    this.severity = options.severity || ErrorSeverity.MEDIUM
    this.details = options.details
    this.timestamp = new Date().toISOString()
    this.requestId = options.requestId
    this.userId = options.userId
    this.path = options.path
    this.method = options.method
  }

  /**
   * 转换为HTTP响应格式
   */
  toResponse(status: number): ErrorResponse {
    return {
      error: {
        code: this.code,
        message: this.message,
        details: this.details,
        timestamp: this.timestamp,
        requestId: this.requestId
      },
      status
    }
  }

  /**
   * 获取HTTP状态码
   */
  getHttpStatus(): number {
    switch (this.code) {
      case ErrorCode.INVALID_REQUEST:
      case ErrorCode.VALIDATION_ERROR:
      case ErrorCode.INVALID_INPUT:
      case ErrorCode.MISSING_REQUIRED_FIELD:
      case ErrorCode.MESSAGE_TOO_LONG:
      case ErrorCode.INVALID_CONVERSATION_ID:
        return 400

      case ErrorCode.UNAUTHORIZED:
        return 401

      case ErrorCode.FORBIDDEN:
      case ErrorCode.SECURITY_VIOLATION:
      case ErrorCode.INJECTION_ATTEMPT:
        return 403

      case ErrorCode.NOT_FOUND:
      case ErrorCode.RECORD_NOT_FOUND:
      case ErrorCode.CONVERSATION_NOT_FOUND:
        return 404

      case ErrorCode.RATE_LIMITED:
        return 429

      case ErrorCode.DATABASE_ERROR:
      case ErrorCode.DATABASE_CONNECTION_FAILED:
      case ErrorCode.EXTERNAL_API_ERROR:
      case ErrorCode.OPENROUTER_ERROR:
      case ErrorCode.SUPABASE_ERROR:
        return 502

      case ErrorCode.INTERNAL_ERROR:
      default:
        return 500
    }
  }
}

/**
 * 错误处理器工厂
 */
export class ErrorHandler {
  /**
   * 创建验证错误
   */
  static validation(message: string, details?: any): ApplicationError {
    return new ApplicationError({
      code: ErrorCode.VALIDATION_ERROR,
      message,
      details,
      severity: ErrorSeverity.LOW
    })
  }

  /**
   * 创建未授权错误
   */
  static unauthorized(message: string = 'Unauthorized'): ApplicationError {
    return new ApplicationError({
      code: ErrorCode.UNAUTHORIZED,
      message,
      severity: ErrorSeverity.MEDIUM
    })
  }

  /**
   * 创建禁止访问错误
   */
  static forbidden(message: string = 'Forbidden'): ApplicationError {
    return new ApplicationError({
      code: ErrorCode.FORBIDDEN,
      message,
      severity: ErrorSeverity.HIGH
    })
  }

  /**
   * 创建未找到错误
   */
  static notFound(resource: string, id?: string): ApplicationError {
    const message = id ? `${resource} with id ${id} not found` : `${resource} not found`
    return new ApplicationError({
      code: ErrorCode.NOT_FOUND,
      message,
      severity: ErrorSeverity.LOW
    })
  }

  /**
   * 创建数据库错误
   */
  static database(message: string, details?: any): ApplicationError {
    return new ApplicationError({
      code: ErrorCode.DATABASE_ERROR,
      message: 'Database operation failed',
      details: { originalMessage: message, ...details },
      severity: ErrorSeverity.HIGH
    })
  }

  /**
   * 创建外部API错误
   */
  static externalAPI(service: string, message: string, details?: any): ApplicationError {
    return new ApplicationError({
      code: ErrorCode.EXTERNAL_API_ERROR,
      message: `${service} API error: ${message}`,
      details,
      severity: ErrorSeverity.MEDIUM
    })
  }

  /**
   * 创建安全违规错误
   */
  static securityViolation(message: string, details?: any): ApplicationError {
    return new ApplicationError({
      code: ErrorCode.SECURITY_VIOLATION,
      message,
      details,
      severity: ErrorSeverity.CRITICAL
    })
  }

  /**
   * 创建内部错误
   */
  static internal(message: string, details?: any): ApplicationError {
    return new ApplicationError({
      code: ErrorCode.INTERNAL_ERROR,
      message: 'Internal server error',
      details: { originalMessage: message, ...details },
      severity: ErrorSeverity.CRITICAL
    })
  }

  /**
   * 从未知错误创建应用程序错误
   */
  static fromUnknown(error: unknown, context?: {
    requestId?: string
    userId?: string
    path?: string
    method?: string
  }): ApplicationError {
    if (error instanceof ApplicationError) {
      return error
    }

    if (error instanceof Error) {
      // 检查是否是已知的数据库错误
      if (error.message.includes('duplicate key')) {
        return new ApplicationError({
          code: ErrorCode.DUPLICATE_RECORD,
          message: 'Record already exists',
          details: { originalError: error.message },
          severity: ErrorSeverity.MEDIUM,
          ...context
        })
      }

      if (error.message.includes('connection')) {
        return new ApplicationError({
          code: ErrorCode.DATABASE_CONNECTION_FAILED,
          message: 'Database connection failed',
          details: { originalError: error.message },
          severity: ErrorSeverity.HIGH,
          ...context
        })
      }

      // 通用错误
      return new ApplicationError({
        code: ErrorCode.INTERNAL_ERROR,
        message: 'An unexpected error occurred',
        details: { originalError: error.message, stack: error.stack },
        severity: ErrorSeverity.HIGH,
        ...context
      })
    }

    // 未知错误类型
    return new ApplicationError({
      code: ErrorCode.INTERNAL_ERROR,
      message: 'An unexpected error occurred',
      details: { unknownError: String(error) },
      severity: ErrorSeverity.HIGH,
      ...context
    })
  }
}

/**
 * 结构化错误日志记录器
 */
export class ErrorLogger {
  /**
   * 记录错误
   */
  static log(error: ApplicationError, additionalContext?: any): void {
    const logEntry = {
      level: this.getLogLevel(error.severity),
      code: error.code,
      message: error.message,
      severity: error.severity,
      timestamp: error.timestamp,
      requestId: error.requestId,
      userId: error.userId,
      path: error.path,
      method: error.method,
      details: error.details,
      ...additionalContext
    }

    // 根据严重程度选择日志级别
    switch (error.severity) {
      case ErrorSeverity.CRITICAL:
        console.error('[CRITICAL]', JSON.stringify(logEntry, null, 2))
        break
      case ErrorSeverity.HIGH:
        console.error('[ERROR]', JSON.stringify(logEntry, null, 2))
        break
      case ErrorSeverity.MEDIUM:
        console.warn('[WARN]', JSON.stringify(logEntry, null, 2))
        break
      case ErrorSeverity.LOW:
        console.info('[INFO]', JSON.stringify(logEntry, null, 2))
        break
    }
  }

  /**
   * 获取日志级别
   */
  private static getLogLevel(severity: ErrorSeverity): string {
    switch (severity) {
      case ErrorSeverity.CRITICAL:
        return 'CRITICAL'
      case ErrorSeverity.HIGH:
        return 'ERROR'
      case ErrorSeverity.MEDIUM:
        return 'WARN'
      case ErrorSeverity.LOW:
        return 'INFO'
      default:
        return 'ERROR'
    }
  }
}

/**
 * Hono错误处理中间件
 */
export function createErrorHandler() {
  return async (c: any, next: any) => {
    try {
      await next()
    } catch (error) {
      const requestId = c.get('requestId') || crypto.randomUUID()
      const userId = c.get('userId')
      
      const appError = ErrorHandler.fromUnknown(error, {
        requestId,
        userId,
        path: c.req.path,
        method: c.req.method
      })

      // 记录错误
      ErrorLogger.log(appError, {
        userAgent: c.req.header('User-Agent'),
        ip: c.req.header('CF-Connecting-IP') || c.req.header('X-Forwarded-For')
      })

      // 返回错误响应
      const status = appError.getHttpStatus()
      const response = appError.toResponse(status)

      // 设置响应头
      c.header('Content-Type', 'application/json')
      c.header('X-Request-ID', requestId)

      return c.json(response, status)
    }
  }
}

export default ErrorHandler