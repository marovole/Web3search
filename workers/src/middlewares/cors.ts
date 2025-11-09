import type { MiddlewareHandler } from 'hono'
import type { Env } from '../types/env'

const DEFAULT_HEADERS = 'Content-Type, Authorization'
const ALLOW_METHODS = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
const MAX_AGE = '86400' // 24 hours

/**
 * 解析 CORS 允许的来源列表
 */
const parseOrigins = (value?: string): string[] =>
  value
    ?.split(',')
    .map(origin => origin.trim())
    .filter(Boolean) ?? []

/**
 * 检查来源是否匹配通配符模式
 * 支持 *.example.com 格式
 */
const isWildcardMatch = (origin: string, pattern: string): boolean => {
  if (!pattern.startsWith('*.')) {
    return false
  }

  const domain = pattern.slice(2) // 移除 "*."
  try {
    const { hostname } = new URL(origin)
    return hostname === domain || hostname.endsWith(`.${domain}`)
  } catch {
    return false
  }
}

/**
 * 解析允许的来源
 * 优先级：精确匹配 > 通配符匹配 > 开发环境默认
 */
const resolveAllowedOrigin = (
  origin: string | undefined,
  allowedOrigins: string[]
): string | undefined => {
  if (!origin) {
    return undefined
  }

  // 精确匹配
  if (allowedOrigins.includes(origin)) {
    return origin
  }

  // 通配符匹配
  const wildcardMatch = allowedOrigins.find(pattern =>
    isWildcardMatch(origin, pattern)
  )
  if (wildcardMatch) {
    return origin
  }

  // 开发环境：允许 localhost 和 127.0.0.1
  if (
    !allowedOrigins.length &&
    (origin.includes('localhost') || origin.includes('127.0.0.1'))
  ) {
    return origin
  }

  return undefined
}

/**
 * CORS 中间件
 * 处理跨域请求头和 OPTIONS 预检请求
 */
export const cors = (): MiddlewareHandler<{ Bindings: Env }> => async (c, next) => {
  const allowedOrigins = parseOrigins(c.env.CORS_ORIGINS)
  const requestOrigin = c.req.header('Origin')
  const allowOrigin = resolveAllowedOrigin(requestOrigin, allowedOrigins)

  // Echo Access-Control-Request-Headers 而不是使用静态列表，以支持更多客户端请求头
  const requestHeaders = c.req.header('Access-Control-Request-Headers')
  const allowHeaders = requestHeaders ?? DEFAULT_HEADERS

  const corsHeaders = {
    'Access-Control-Allow-Origin': allowOrigin ?? (allowedOrigins[0] ?? ''),
    'Access-Control-Allow-Methods': ALLOW_METHODS,
    'Access-Control-Allow-Headers': allowHeaders,
    'Access-Control-Allow-Credentials': allowOrigin ? 'true' : 'false',
    'Access-Control-Max-Age': MAX_AGE,
  }

  // 处理 OPTIONS 预检请求
  if (c.req.method === 'OPTIONS') {
    return c.body(null, 204, corsHeaders)
  }

  await next()

  // 添加 CORS 头部到响应
  for (const [key, value] of Object.entries(corsHeaders)) {
    if (value) {
      c.header(key, value, { append: false })
    }
  }
}
