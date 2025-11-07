/**
 * Web3 Search Cloudflare Worker
 * 功能：API代理、边缘缓存、速率限制、安全增强
 */

interface Env {
  BACKEND_API_URL: string
  CACHE_TTL: string
  ENABLE_CACHE: string
  ENABLE_RATE_LIMIT: string
  CORS_ORIGINS?: string // 允许的CORS来源，逗号分隔，例如: "https://web3search.vercel.app,https://www.web3search.vercel.app"
  CACHE?: KVNamespace // KV存储（可选）
}

/**
 * 根据环境变量和请求来源生成CORS头部
 */
function getCorsHeaders(request: Request, env: Env): Record<string, string> {
  const origin = request.headers.get('Origin')
  const allowedOrigins = env.CORS_ORIGINS 
    ? env.CORS_ORIGINS.split(',').map(o => o.trim())
    : []
  
  // 如果没有配置允许的来源，默认拒绝（生产环境必须配置）
  let allowOrigin = ''
  
  if (origin && allowedOrigins.length > 0) {
    // 检查请求来源是否在允许列表中
    if (allowedOrigins.includes(origin)) {
      allowOrigin = origin
    } else {
      // 如果不在列表中，检查是否有匹配的域名模式（支持子域名）
      for (const allowed of allowedOrigins) {
        // 简单的子域名匹配：如果允许 "*.example.com"，则匹配 "app.example.com"
        if (allowed.startsWith('*.')) {
          const domain = allowed.slice(2)
          if (origin.endsWith('.' + domain) || origin === 'https://' + domain) {
            allowOrigin = origin
            break
          }
        }
      }
    }
  }
  
  // 开发环境：如果没有配置，允许本地开发
  if (!allowOrigin && (!env.CORS_ORIGINS || env.CORS_ORIGINS === '')) {
    if (origin && (origin.includes('localhost') || origin.includes('127.0.0.1'))) {
      allowOrigin = origin
    }
  }
  
  return {
    'Access-Control-Allow-Origin': allowOrigin || (allowedOrigins.length > 0 ? allowedOrigins[0] : ''),
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    'Access-Control-Allow-Credentials': allowOrigin ? 'true' : 'false',
    'Access-Control-Max-Age': '86400',
  }
}

// 安全头部
const SECURITY_HEADERS = {
  'X-Content-Type-Options': 'nosniff',
  'X-Frame-Options': 'DENY',
  'X-XSS-Protection': '1; mode=block',
  'Referrer-Policy': 'strict-origin-when-cross-origin',
}

/**
 * 处理OPTIONS预检请求
 */
function handleOptions(request: Request, env: Env): Response {
  const corsHeaders = getCorsHeaders(request, env)
  return new Response(null, {
    status: 204,
    headers: corsHeaders,
  })
}

/**
 * 生成缓存键
 */
function getCacheKey(request: Request): string {
  const url = new URL(request.url)
  const method = request.method
  // 包含方法和完整URL作为缓存键
  return `${method}:${url.pathname}${url.search}`
}

/**
 * 从缓存获取响应（Cloudflare Cache API）
 */
async function getFromCache(request: Request, env: Env): Promise<Response | null> {
  if (env.ENABLE_CACHE !== 'true') return null
  
  try {
    const cache = caches.default
    const cachedResponse = await cache.match(request)
    
    if (cachedResponse) {
      console.log('Cache HIT:', request.url)
      return new Response(cachedResponse.body, {
        status: cachedResponse.status,
        headers: {
          ...Object.fromEntries(cachedResponse.headers.entries()),
          'X-Cache': 'HIT',
        },
      })
    }
  } catch (error) {
    console.error('Cache read error:', error)
  }
  
  return null
}

/**
 * 存储响应到缓存
 */
async function saveToCache(request: Request, response: Response, env: Env): Promise<void> {
  if (env.ENABLE_CACHE !== 'true') return
  if (request.method !== 'GET') return // 只缓存GET请求
  
  try {
    const cache = caches.default
    const cacheTTL = parseInt(env.CACHE_TTL || '3600', 10)
    
    // 克隆响应并添加缓存头
    const responseToCache = new Response(response.body, {
      status: response.status,
      headers: {
        ...Object.fromEntries(response.headers.entries()),
        'Cache-Control': `public, max-age=${cacheTTL}`,
        'X-Cache': 'MISS',
      },
    })
    
    await cache.put(request, responseToCache)
    console.log('Cached response for:', request.url)
  } catch (error) {
    console.error('Cache write error:', error)
  }
}

/**
 * 速率限制检查（简单实现，基于IP）
 */
async function checkRateLimit(request: Request, env: Env): Promise<boolean> {
  if (env.ENABLE_RATE_LIMIT !== 'true') return true
  
  // TODO: 实现基于KV的速率限制
  // 当前版本：简单通过，后续可扩展
  return true
}

/**
 * 代理请求到后端API
 */
async function proxyRequest(request: Request, env: Env): Promise<Response> {
  const url = new URL(request.url)
  
  // 构建后端URL
  const backendUrl = new URL(url.pathname + url.search, env.BACKEND_API_URL)
  
  // 准备请求头
  const headers = new Headers(request.headers)
  headers.set('X-Forwarded-For', request.headers.get('CF-Connecting-IP') || '')
  headers.set('X-Forwarded-Host', url.hostname)
  
  // 发送请求到后端
  try {
    const backendRequest = new Request(backendUrl.toString(), {
      method: request.method,
      headers,
      body: request.method !== 'GET' && request.method !== 'HEAD' ? request.body : null,
    })
    
    const response = await fetch(backendRequest)
    
    // 构建响应
    const responseHeaders = new Headers(response.headers)
    
    // 添加CORS和安全头部
    const corsHeaders = getCorsHeaders(request, env)
    Object.entries(corsHeaders).forEach(([key, value]) => {
      if (value) {
        responseHeaders.set(key, value)
      }
    })
    Object.entries(SECURITY_HEADERS).forEach(([key, value]) => {
      responseHeaders.set(key, value)
    })
    
    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: responseHeaders,
    })
  } catch (error) {
    console.error('Backend request error:', error)
    return new Response(
      JSON.stringify({
        error: 'Backend service unavailable',
        message: 'Unable to reach backend API',
      }),
      {
        status: 503,
        headers: {
          'Content-Type': 'application/json',
          ...getCorsHeaders(request, env),
        },
      }
    )
  }
}

/**
 * 主处理函数
 */
export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    // 处理OPTIONS预检请求
    if (request.method === 'OPTIONS') {
      return handleOptions(request, env)
    }
    
    // 速率限制检查
    const rateLimitOk = await checkRateLimit(request, env)
    if (!rateLimitOk) {
      return new Response(
        JSON.stringify({ error: 'Too many requests' }),
        {
          status: 429,
          headers: {
            'Content-Type': 'application/json',
            'Retry-After': '60',
            ...getCorsHeaders(request, env),
          },
        }
      )
    }
    
    // 尝试从缓存获取
    const cachedResponse = await getFromCache(request, env)
    if (cachedResponse) {
      return cachedResponse
    }
    
    // 代理请求到后端
    const response = await proxyRequest(request, env)
    
    // 保存到缓存（异步，不阻塞响应）
    if (response.ok && request.method === 'GET') {
      ctx.waitUntil(saveToCache(request, response.clone(), env))
    }
    
    return response
  },
}
