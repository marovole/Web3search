type LogLevel = 'debug' | 'info' | 'warn' | 'error' | 'none'

interface LoggerConfig {
  level: LogLevel
  enableInProduction: boolean
  prefix: string
}

const LOG_LEVELS: Record<LogLevel, number> = {
  debug: 0,
  info: 1,
  warn: 2,
  error: 3,
  none: 4,
}

const isDevelopment = import.meta.env.DEV
const isProduction = import.meta.env.PROD

const defaultConfig: LoggerConfig = {
  level: isDevelopment ? 'debug' : 'error',
  enableInProduction: false,
  prefix: '[Web3Search]',
}

class Logger {
  private config: LoggerConfig

  constructor(config: Partial<LoggerConfig> = {}) {
    this.config = { ...defaultConfig, ...config }
  }

  private shouldLog(level: LogLevel): boolean {
    if (isProduction && !this.config.enableInProduction) {
      return level === 'error'
    }
    return LOG_LEVELS[level] >= LOG_LEVELS[this.config.level]
  }

  private formatMessage(level: string, message: string): string {
    return `${this.config.prefix} [${level.toUpperCase()}] ${message}`
  }

  debug(message: string, ...args: unknown[]): void {
    if (this.shouldLog('debug')) {
      console.debug(this.formatMessage('debug', message), ...args)
    }
  }

  info(message: string, ...args: unknown[]): void {
    if (this.shouldLog('info')) {
      console.info(this.formatMessage('info', message), ...args)
    }
  }

  warn(message: string, ...args: unknown[]): void {
    if (this.shouldLog('warn')) {
      console.warn(this.formatMessage('warn', message), ...args)
    }
  }

  error(message: string, ...args: unknown[]): void {
    if (this.shouldLog('error')) {
      console.error(this.formatMessage('error', message), ...args)
    }
  }

  group(label: string): void {
    if (this.shouldLog('debug')) {
      console.group(this.formatMessage('group', label))
    }
  }

  groupEnd(): void {
    if (this.shouldLog('debug')) {
      console.groupEnd()
    }
  }

  setLevel(level: LogLevel): void {
    this.config.level = level
  }

  setEnableInProduction(enable: boolean): void {
    this.config.enableInProduction = enable
  }
}

export const logger = new Logger()
export default logger
