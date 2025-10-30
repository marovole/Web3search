// Service Worker for Web3search Frontend
const CACHE_VERSION = '1.0.0'
const CACHE_NAME = `web3search-v${CACHE_VERSION}`
const STATIC_CACHE = `web3search-static-v${CACHE_VERSION}`
const API_CACHE = `web3search-api-v${CACHE_VERSION}`

// 需要缓存的静态资源
const STATIC_ASSETS = [
  '/',
  '/offline.html',
  // CSS文件会自动添加
  // JS文件会自动添加
]

// API缓存策略配置
const API_CACHE_CONFIG = {
  // 需要缓存的API端点
  cacheableEndpoints: [
    '/api/health',
    '/api/config',
  ],
  // 缓存时间（毫秒）
  cacheTime: 5 * 60 * 1000, // 5分钟
}

// 安装Service Worker
self.addEventListener('install', (event) => {
  console.log('Service Worker installing...')
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then((cache) => {
        return cache.addAll(STATIC_ASSETS)
      })
      .then(() => {
        console.log('Service Worker installed')
        return self.skipWaiting()
      })
  )
})

// 激活Service Worker
self.addEventListener('activate', (event) => {
  console.log('Service Worker activating...')
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            // 删除所有旧版本的缓存
            if (!cacheName.startsWith(`web3search-v${CACHE_VERSION.split('.')[0]}`)) {
              console.log('Deleting old cache:', cacheName)
              return caches.delete(cacheName)
            }
            // 如果版本号不匹配，也删除
            if (cacheName !== STATIC_CACHE && cacheName !== API_CACHE && cacheName !== CACHE_NAME) {
              console.log('Deleting mismatched cache:', cacheName)
              return caches.delete(cacheName)
            }
          })
        )
      })
      .then(() => {
        console.log('Service Worker activated with version:', CACHE_VERSION)
        return self.clients.claim()
      })
  )
})

// 拦截网络请求
self.addEventListener('fetch', (event) => {
  const { request } = event
  const url = new URL(request.url)

  // 处理API请求
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(handleApiRequest(request))
    return
  }

  // 处理静态资源请求
  event.respondWith(handleStaticRequest(request))
})

// 处理API请求的缓存策略
async function handleApiRequest(request) {
  const url = new URL(request.url)
  const endpoint = url.pathname

  // 只缓存GET请求
  if (request.method !== 'GET') {
    return fetch(request)
  }

  // 检查是否是需要缓存的端点
  const isCacheable = API_CACHE_CONFIG.cacheableEndpoints.some(cacheEndpoint =>
    endpoint === cacheEndpoint || endpoint.startsWith(cacheEndpoint)
  )

  if (!isCacheable) {
    return fetch(request)
  }

  try {
    // 尝试从缓存获取
    const cachedResponse = await caches.match(request)
    if (cachedResponse) {
      // 检查缓存是否过期
      const cachedTime = cachedResponse.headers.get('sw-cached-time')
      if (cachedTime && (Date.now() - parseInt(cachedTime)) < API_CACHE_CONFIG.cacheTime) {
        // 添加缓存标识头
        const headers = new Headers(cachedResponse.headers)
        headers.set('x-cache', 'HIT')
        headers.set('x-cache-age', String(Math.floor((Date.now() - parseInt(cachedTime)) / 1000)))
        return new Response(cachedResponse.body, {
          status: cachedResponse.status,
          statusText: cachedResponse.statusText,
          headers: headers,
        })
      }
    }

    // 从网络获取
    const networkResponse = await fetch(request)

    if (networkResponse.ok) {
      // 克隆响应以便缓存
      const responseToCache = networkResponse.clone()

      // 添加缓存时间戳
      const headers = new Headers(responseToCache.headers)
      headers.set('sw-cached-time', Date.now().toString())

      const cachedResponse = new Response(responseToCache.body, {
        status: responseToCache.status,
        statusText: responseToCache.statusText,
        headers: headers,
      })

      // 缓存响应
      const cache = await caches.open(API_CACHE)
      cache.put(request, cachedResponse)
    }

    // 为网络响应添加缓存标识
    const responseHeaders = new Headers(networkResponse.headers)
    responseHeaders.set('x-cache', 'MISS')
    return new Response(networkResponse.body, {
      status: networkResponse.status,
      statusText: networkResponse.statusText,
      headers: responseHeaders,
    })
  } catch (error) {
    console.log('API request failed, trying cache:', error)

    // 网络失败时尝试从缓存获取
    const cachedResponse = await caches.match(request)
    if (cachedResponse) {
      return cachedResponse
    }

    // 返回离线响应
    return new Response(
      JSON.stringify({ error: 'Network unavailable', offline: true }),
      {
        status: 503,
        headers: { 'Content-Type': 'application/json' }
      }
    )
  }
}

// 处理静态资源的缓存策略
async function handleStaticRequest(request) {
  const url = new URL(request.url)

  // 非HTTP(s)请求不处理
  if (!url.protocol.startsWith('http')) {
    return fetch(request)
  }

  try {
    // 缓存优先策略
    const cachedResponse = await caches.match(request)
    if (cachedResponse) {
      return cachedResponse
    }

    // 从网络获取
    const networkResponse = await fetch(request)

    // 缓存成功的响应
    if (networkResponse.ok) {
      const cache = await caches.open(STATIC_CACHE)
      cache.put(request, networkResponse.clone())
    }

    return networkResponse
  } catch (error) {
    console.log('Static request failed, trying cache:', error)

    // 尝试从缓存获取
    const cachedResponse = await caches.match(request)
    if (cachedResponse) {
      return cachedResponse
    }

    // 如果是导航请求，返回离线页面
    if (request.mode === 'navigate') {
      return caches.match('/offline.html')
    }

    // 返回错误响应
    return new Response('Offline', {
      status: 503,
      statusText: 'Service Unavailable'
    })
  }
}

// 监听消息事件
self.addEventListener('message', (event) => {
  const { type, payload } = event.data

  switch (type) {
    case 'SKIP_WAITING':
      self.skipWaiting()
      break

    case 'GET_VERSION':
      event.ports[0].postMessage({ version: CACHE_NAME })
      break

    case 'CLEAR_CACHE':
      clearAllCaches().then(() => {
        event.ports[0].postMessage({ success: true })
      }).catch(error => {
        event.ports[0].postMessage({ success: false, error: error.message })
      })
      break

    default:
      console.log('Unknown message type:', type)
  }
})

// 清除所有缓存
async function clearAllCaches() {
  const cacheNames = await caches.keys()
  return Promise.all(
    cacheNames.map(cacheName => caches.delete(cacheName))
  )
}

// 后台同步示例（如果需要）
self.addEventListener('sync', (event) => {
  if (event.tag === 'background-sync') {
    event.waitUntil(doBackgroundSync())
  }
})

async function doBackgroundSync() {
  // 这里可以执行后台同步逻辑
  console.log('Background sync triggered')
}