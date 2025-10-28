/**
 * 环境变量管理工具
 * 提供类型安全的环境变量访问和验证
 */

// 环境变量接口定义
interface EnvConfig {
  // 应用环境
  ENVIRONMENT: 'development' | 'staging' | 'production'

  // API配置
  USE_MOCK_API: boolean
  API_BASE_URL: string

  // 功能开关
  ENABLE_SENTRY: boolean
  ENABLE_ANALYTICS: boolean
  ENABLE_EXPERIMENTAL_FEATURES: boolean

  // 调试模式
  DEBUG_MODE: boolean

  // 默认设置
  DEFAULT_CHAT_MODE: 'quick' | 'deep'
}

// 默认配置
const DEFAULT_CONFIG: Partial<EnvConfig> = {
  ENVIRONMENT: 'development',
  USE_MOCK_API: false,
  API_BASE_URL: 'http://localhost:8000',
  ENABLE_SENTRY: false,
  ENABLE_ANALYTICS: false,
  ENABLE_EXPERIMENTAL_FEATURES: false,
  DEBUG_MODE: false,
  DEFAULT_CHAT_MODE: 'quick',
}

/**
 * 获取环境变量值，提供类型安全
 */
function getEnvVar(key: string, defaultValue?: string): string {
  const value = import.meta.env[key]
  if (value === undefined) {
    if (defaultValue !== undefined) {
      console.warn(`⚠️ Environment variable ${key} not found, using default: ${defaultValue}`)
      return defaultValue
    }
    throw new Error(`❌ Required environment variable ${key} is not defined`)
  }
  return value
}

/**
 * 解析布尔值环境变量
 */
function parseBool(value: string, defaultValue: boolean = false): boolean {
  if (value === 'true' || value === '1') return true
  if (value === 'false' || value === '0') return false
  console.warn(`⚠️ Invalid boolean value for environment variable: ${value}, using default: ${defaultValue}`)
  return defaultValue
}

/**
 * 验证环境变量
 */
function validateConfig(config: EnvConfig): void {
  // 验证API Base URL格式
  try {
    new URL(config.API_BASE_URL)
  } catch {
    throw new Error(`❌ Invalid API_BASE_URL: ${config.API_BASE_URL}`)
  }

  // 验证环境类型
  const validEnvironments = ['development', 'staging', 'production']
  if (!validEnvironments.includes(config.ENVIRONMENT)) {
    throw new Error(`❌ Invalid ENVIRONMENT: ${config.ENVIRONMENT}`)
  }

  // 生产环境特定验证
  if (config.ENVIRONMENT === 'production') {
    if (config.USE_MOCK_API) {
      console.warn('⚠️ Using mock API in production environment')
    }
    if (config.DEBUG_MODE) {
      console.warn('⚠️ Debug mode enabled in production environment')
    }
  }
}

/**
 * 加载和验证环境配置
 */
export function loadEnvConfig(): EnvConfig {
  try {
    const config: EnvConfig = {
      ENVIRONMENT: getEnvVar('VITE_ENVIRONMENT', DEFAULT_CONFIG.ENVIRONMENT) as EnvConfig['ENVIRONMENT'],
      USE_MOCK_API: parseBool(getEnvVar('VITE_USE_MOCK_API', String(DEFAULT_CONFIG.USE_MOCK_API))),
      API_BASE_URL: getEnvVar('VITE_API_BASE_URL', DEFAULT_CONFIG.API_BASE_URL),
      ENABLE_SENTRY: parseBool(getEnvVar('VITE_ENABLE_SENTRY', String(DEFAULT_CONFIG.ENABLE_SENTRY))),
      ENABLE_ANALYTICS: parseBool(getEnvVar('VITE_ENABLE_ANALYTICS', String(DEFAULT_CONFIG.ENABLE_ANALYTICS))),
      ENABLE_EXPERIMENTAL_FEATURES: parseBool(getEnvVar('VITE_ENABLE_EXPERIMENTAL_FEATURES', String(DEFAULT_CONFIG.ENABLE_EXPERIMENTAL_FEATURES))),
      DEBUG_MODE: parseBool(getEnvVar('VITE_DEBUG_MODE', String(DEFAULT_CONFIG.DEBUG_MODE))),
      DEFAULT_CHAT_MODE: getEnvVar('VITE_DEFAULT_CHAT_MODE', DEFAULT_CONFIG.DEFAULT_CHAT_MODE) as EnvConfig['DEFAULT_CHAT_MODE'],
    }

    validateConfig(config)

    // 在开发环境显示配置信息
    if (config.DEBUG_MODE) {
      console.log('🔧 Environment Configuration:', {
        environment: config.ENVIRONMENT,
        useMockApi: config.USE_MOCK_API,
        apiBaseUrl: config.API_BASE_URL,
        enableSentry: config.ENABLE_SENTRY,
        enableAnalytics: config.ENABLE_ANALYTICS,
        enableExperimentalFeatures: config.ENABLE_EXPERIMENTAL_FEATURES,
        debugMode: config.DEBUG_MODE,
        defaultChatMode: config.DEFAULT_CHAT_MODE,
      })
    }

    return config
  } catch (error) {
    console.error('❌ Failed to load environment configuration:', error)
    throw error
  }
}

/**
 * 获取当前环境配置（单例模式）
 */
let envConfig: EnvConfig | null = null

export function getEnvConfig(): EnvConfig {
  if (!envConfig) {
    envConfig = loadEnvConfig()
  }
  return envConfig
}

/**
 * 检查特定功能是否启用
 */
export function isFeatureEnabled(feature: keyof Pick<EnvConfig, 'ENABLE_SENTRY' | 'ENABLE_ANALYTICS' | 'ENABLE_EXPERIMENTAL_FEATURES'>): boolean {
  return getEnvConfig()[feature]
}

/**
 * 获取API配置
 */
export function getApiConfig() {
  const config = getEnvConfig()
  return {
    baseUrl: config.API_BASE_URL,
    useMock: config.USE_MOCK_API,
  }
}

/**
 * 检查是否为开发环境
 */
export function isDevelopment(): boolean {
  return getEnvConfig().ENVIRONMENT === 'development'
}

/**
 * 检查是否为生产环境
 */
export function isProduction(): boolean {
  return getEnvConfig().ENVIRONMENT === 'production'
}