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
  ENABLE_PERFORMANCE_MONITORING: boolean

  // 调试模式
  DEBUG_MODE: boolean

  // Sentry配置
  SENTRY_DSN: string
  SENTRY_ENVIRONMENT: string

  // Google Analytics配置
  GA_MEASUREMENT_ID: string

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
  ENABLE_PERFORMANCE_MONITORING: true,
  DEBUG_MODE: false,
  SENTRY_DSN: '',
  SENTRY_ENVIRONMENT: 'development',
  GA_MEASUREMENT_ID: '',
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
 * 获取API Base URL
 * 支持环境变量配置和运行时检测
 */
function getApiBaseUrl(): string {
  const envUrl = import.meta.env.VITE_API_BASE_URL
  const defaultUrl = 'https://api.lulaai.xyz'

  // 如果没有配置环境变量，使用默认值
  if (!envUrl) {
    console.warn('⚠️ VITE_API_BASE_URL not configured, using default:', defaultUrl)
    return defaultUrl
  }

  // 验证URL格式
  try {
    new URL(envUrl)
    return envUrl
  } catch {
    console.error('❌ Invalid VITE_API_BASE_URL:', envUrl)
    console.log('✅ Fallback to default:', defaultUrl)
    return defaultUrl
  }
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
      API_BASE_URL: getApiBaseUrl(),
      ENABLE_SENTRY: parseBool(getEnvVar('VITE_ENABLE_SENTRY', String(DEFAULT_CONFIG.ENABLE_SENTRY))),
      ENABLE_ANALYTICS: parseBool(getEnvVar('VITE_ENABLE_ANALYTICS', String(DEFAULT_CONFIG.ENABLE_ANALYTICS))),
      ENABLE_EXPERIMENTAL_FEATURES: parseBool(getEnvVar('VITE_ENABLE_EXPERIMENTAL_FEATURES', String(DEFAULT_CONFIG.ENABLE_EXPERIMENTAL_FEATURES))),
      ENABLE_PERFORMANCE_MONITORING: parseBool(getEnvVar('VITE_ENABLE_PERFORMANCE_MONITORING', String(DEFAULT_CONFIG.ENABLE_PERFORMANCE_MONITORING))),
      DEBUG_MODE: parseBool(getEnvVar('VITE_DEBUG_MODE', String(DEFAULT_CONFIG.DEBUG_MODE))),
      SENTRY_DSN: getEnvVar('VITE_SENTRY_DSN', DEFAULT_CONFIG.SENTRY_DSN),
      SENTRY_ENVIRONMENT: getEnvVar('VITE_SENTRY_ENVIRONMENT', DEFAULT_CONFIG.SENTRY_ENVIRONMENT),
      GA_MEASUREMENT_ID: getEnvVar('VITE_GA_MEASUREMENT_ID', DEFAULT_CONFIG.GA_MEASUREMENT_ID),
      DEFAULT_CHAT_MODE: getEnvVar('VITE_DEFAULT_CHAT_MODE', DEFAULT_CONFIG.DEFAULT_CHAT_MODE) as EnvConfig['DEFAULT_CHAT_MODE'],
    }

    validateConfig(config)

    // 生产环境配置：自动检测并使用完整后端URL
    // 注意：不使用相对路径，避免与API路径前缀重复（/api + /api/v1 = /api/api/v1）
    const isProduction = config.ENVIRONMENT === 'production' ||
      (typeof window !== 'undefined' && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1')

    if (isProduction && !config.API_BASE_URL.startsWith('http')) {
      console.warn('⚠️ Production environment detected but API_BASE_URL is not a complete URL. Using default backend URL.')
      config.API_BASE_URL = 'https://api.lulaai.xyz'
    }

    // 验证URL格式：确保没有路径重复
    if (config.API_BASE_URL.includes('/api/v1') || config.API_BASE_URL.includes('/api/api')) {
      console.error('❌ API_BASE_URL contains API path! This will cause path duplication.')
      console.error(`   Current: ${config.API_BASE_URL}`)
      console.error(`   Expected: https://api.lulaai.xyz`)
      throw new Error('Invalid API_BASE_URL configuration: contains API path')
    }

    console.log(`✅ API Configuration: ${config.API_BASE_URL} (Environment: ${config.ENVIRONMENT}, isProduction: ${isProduction})`)

    // 在开发环境显示配置信息
    if (config.DEBUG_MODE) {
      console.log('🔧 Environment Configuration:', {
        environment: config.ENVIRONMENT,
        useMockApi: config.USE_MOCK_API,
        apiBaseUrl: config.API_BASE_URL,
        enableSentry: config.ENABLE_SENTRY,
        enableAnalytics: config.ENABLE_ANALYTICS,
        enableExperimentalFeatures: config.ENABLE_EXPERIMENTAL_FEATURES,
        enablePerformanceMonitoring: config.ENABLE_PERFORMANCE_MONITORING,
        debugMode: config.DEBUG_MODE,
        sentryDsn: config.SENTRY_DSN ? '***configured***' : 'not set',
        sentryEnvironment: config.SENTRY_ENVIRONMENT,
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
 * 获取当前环境配置（单例模式，运行时检测生产环境）
 */
let envConfig: EnvConfig | null = null

export function getEnvConfig(): EnvConfig {
  if (!envConfig) {
    envConfig = loadEnvConfig()

    // 运行时验证：确保API URL格式正确
    if (typeof window !== 'undefined') {
      const hostname = window.location.hostname
      const isProductionDomain = hostname !== 'localhost' && hostname !== '127.0.0.1'

      // 验证URL不包含重复的API路径
      if (envConfig.API_BASE_URL.includes('/api/v1') || envConfig.API_BASE_URL.includes('/api/api')) {
        console.error('❌ API_BASE_URL contains duplicate API path!')
        console.error(`   Invalid: ${envConfig.API_BASE_URL}`)
        envConfig.API_BASE_URL = 'https://api.lulaai.xyz'
        console.log(`✅ Corrected to: ${envConfig.API_BASE_URL}`)
      }

      // 验证生产环境使用HTTPS
      if (isProductionDomain && !envConfig.API_BASE_URL.startsWith('https://')) {
        console.warn('⚠️  Production detected but API URL is not HTTPS')
        console.warn(`   Current: ${envConfig.API_BASE_URL}`)
        envConfig.API_BASE_URL = 'https://api.lulaai.xyz'
        console.log(`✅ Switched to: ${envConfig.API_BASE_URL}`)
      }

      // 输出最终配置（仅在非生产环境或DEBUG模式）
      if (envConfig.DEBUG_MODE || !isProductionDomain) {
        console.log(`🌐 API Configuration:`, {
          hostname,
          environment: envConfig.ENVIRONMENT,
          apiBaseUrl: envConfig.API_BASE_URL,
        })
      }
    }
  }
  return envConfig
}

/**
 * 检查特定功能是否启用
 */
export function isFeatureEnabled(feature: keyof Pick<EnvConfig, 'ENABLE_SENTRY' | 'ENABLE_ANALYTICS' | 'ENABLE_EXPERIMENTAL_FEATURES' | 'ENABLE_PERFORMANCE_MONITORING'>): boolean {
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