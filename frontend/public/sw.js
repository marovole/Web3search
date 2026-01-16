// Service Worker for Web3search Frontend
const CACHE_VERSION = 'v1.0.1'
const CACHE_NAME = `web3search-${CACHE_VERSION}`
const STATIC_CACHE = `web3search-static-${CACHE_VERSION}`
const API_CACHE = `web3search-api-${CACHE_VERSION}`

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
            if (cacheName !== STATIC_CACHE && cacheName !== API_CACHE) {
              console.log('Deleting old cache:', cacheName)
              return caches.delete(cacheName)
            }
          })
        )
      })
      .then(() => {
        console.log('Service Worker activated')
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
        return cachedResponse
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

    return networkResponse
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

  const isNavigation = request.mode === 'navigate'
  const isAsset = ['script', 'style', 'worker'].includes(request.destination)
  const useNetworkFirst = isNavigation || isAsset

  try {
    if (useNetworkFirst) {
      const networkResponse = await fetch(request)

      if (networkResponse.ok) {
        const cache = await caches.open(STATIC_CACHE)
        cache.put(request, networkResponse.clone())
      }

      return networkResponse
    }

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
    if (isNavigation) {
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
  console.log('Background sync triggered')
}

self.addEventListener('push', (event) => {
  console.log('[SW] Push notification received')
  
  let data = {
    title: 'Web3search',
    body: '您有新的通知',
    icon: '/icons/icon-192x192.png',
    badge: '/icons/badge-72x72.png',
    tag: 'default',
    data: {}
  }

  if (event.data) {
    try {
      const payload = event.data.json()
      data = { ...data, ...payload }
    } catch (e) {
      console.error('[SW] Failed to parse push data:', e)
    }
  }

  const options = {
    body: data.body,
    icon: data.icon,
    badge: data.badge,
    tag: data.tag,
    data: data.data,
    vibrate: [200, 100, 200],
    requireInteraction: data.data?.type === 'price_alert' || data.data?.type === 'risk_alert',
    actions: data.actions || []
  }

  event.waitUntil(
    self.registration.showNotification(data.title, options)
  )
})

self.addEventListener('notificationclick', (event) => {
  console.log('[SW] Notification clicked:', event.action)
  
  event.notification.close()

  const data = event.notification.data || {}
  let targetUrl = '/'

  if (event.action === 'view' || !event.action) {
    if (data.link) {
      targetUrl = data.link
    } else if (data.type === 'price_alert') {
      targetUrl = '/notifications?type=price_alert'
    } else if (data.type === 'risk_alert') {
      targetUrl = '/notifications?type=risk_alert'
    } else if (data.type === 'news_brief') {
      targetUrl = '/notifications?type=news_brief'
    } else {
      targetUrl = '/notifications'
    }
  } else if (event.action === 'dismiss') {
    return
  }

  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then((clientList) => {
        for (const client of clientList) {
          if (client.url.includes(self.location.origin) && 'focus' in client) {
            client.navigate(targetUrl)
            return client.focus()
          }
        }
        if (self.clients.openWindow) {
          return self.clients.openWindow(targetUrl)
        }
      })
  )
})

self.addEventListener('notificationclose', (event) => {
  console.log('[SW] Notification closed')
})

self.addEventListener('pushsubscriptionchange', (event) => {
  console.log('[SW] Push subscription changed')
  
  event.waitUntil(
    self.registration.pushManager.subscribe(event.oldSubscription.options)
      .then((subscription) => {
        return fetch('/api/v1/push/subscribe', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            endpoint: subscription.endpoint,
            keys: {
              p256dh: btoa(String.fromCharCode.apply(null, new Uint8Array(subscription.getKey('p256dh')))),
              auth: btoa(String.fromCharCode.apply(null, new Uint8Array(subscription.getKey('auth'))))
            }
          })
        })
      })
  )
})