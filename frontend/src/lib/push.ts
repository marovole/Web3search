const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

function urlBase64ToUint8Array(base64String: string): Uint8Array {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4)
  const base64 = (base64String + padding)
    .replace(/-/g, '+')
    .replace(/_/g, '/')
  
  const rawData = window.atob(base64)
  const outputArray = new Uint8Array(rawData.length)
  
  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i)
  }
  return outputArray
}

function arrayBufferToBase64(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer)
  let binary = ''
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i])
  }
  return window.btoa(binary)
}

export function isPushSupported(): boolean {
  return 'serviceWorker' in navigator && 
         'PushManager' in window && 
         'Notification' in window
}

export function getNotificationPermission(): NotificationPermission {
  if (!('Notification' in window)) {
    return 'denied'
  }
  return Notification.permission
}

export async function requestNotificationPermission(): Promise<NotificationPermission> {
  if (!('Notification' in window)) {
    throw new Error('Notifications not supported')
  }
  
  const permission = await Notification.requestPermission()
  return permission
}

export async function registerServiceWorker(): Promise<ServiceWorkerRegistration | null> {
  if (!('serviceWorker' in navigator)) {
    console.warn('[Push] Service Worker not supported')
    return null
  }

  try {
    const registration = await navigator.serviceWorker.register('/sw.js', {
      scope: '/'
    })
    
    console.log('[Push] Service Worker registered:', registration.scope)
    return registration
  } catch (error) {
    console.error('[Push] Service Worker registration failed:', error)
    return null
  }
}

export async function getVapidPublicKey(): Promise<string | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/push/vapid-public-key`)
    if (!response.ok) {
      console.error('[Push] Failed to get VAPID public key')
      return null
    }
    const data = await response.json()
    return data.publicKey
  } catch (error) {
    console.error('[Push] Error fetching VAPID key:', error)
    return null
  }
}

export async function subscribeToPush(
  accessToken: string
): Promise<{ success: boolean; error?: string }> {
  if (!isPushSupported()) {
    return { success: false, error: 'Push notifications not supported' }
  }

  const permission = await requestNotificationPermission()
  if (permission !== 'granted') {
    return { success: false, error: 'Notification permission denied' }
  }

  const registration = await registerServiceWorker()
  if (!registration) {
    return { success: false, error: 'Service Worker registration failed' }
  }

  const vapidPublicKey = await getVapidPublicKey()
  if (!vapidPublicKey) {
    return { success: false, error: 'VAPID public key not available' }
  }

  try {
    let subscription = await registration.pushManager.getSubscription()
    
    if (!subscription) {
      subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(vapidPublicKey)
      })
    }

    const p256dh = subscription.getKey('p256dh')
    const auth = subscription.getKey('auth')

    if (!p256dh || !auth) {
      return { success: false, error: 'Failed to get subscription keys' }
    }

    const response = await fetch(`${API_BASE_URL}/api/v1/push/subscribe`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`
      },
      body: JSON.stringify({
        endpoint: subscription.endpoint,
        keys: {
          p256dh: arrayBufferToBase64(p256dh),
          auth: arrayBufferToBase64(auth)
        },
        userAgent: navigator.userAgent
      })
    })

    if (!response.ok) {
      const errorData = await response.json()
      return { success: false, error: errorData.error?.message || 'Subscription failed' }
    }

    console.log('[Push] Successfully subscribed to push notifications')
    return { success: true }
  } catch (error) {
    console.error('[Push] Subscription error:', error)
    return { success: false, error: error instanceof Error ? error.message : 'Unknown error' }
  }
}

export async function unsubscribeFromPush(
  accessToken: string
): Promise<{ success: boolean; error?: string }> {
  if (!('serviceWorker' in navigator)) {
    return { success: false, error: 'Service Worker not supported' }
  }

  try {
    const registration = await navigator.serviceWorker.ready
    const subscription = await registration.pushManager.getSubscription()

    if (!subscription) {
      return { success: true }
    }

    await subscription.unsubscribe()

    const response = await fetch(`${API_BASE_URL}/api/v1/push/unsubscribe`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`
      },
      body: JSON.stringify({
        endpoint: subscription.endpoint
      })
    })

    if (!response.ok) {
      console.warn('[Push] Server unsubscribe failed, but local unsubscribe succeeded')
    }

    console.log('[Push] Successfully unsubscribed from push notifications')
    return { success: true }
  } catch (error) {
    console.error('[Push] Unsubscribe error:', error)
    return { success: false, error: error instanceof Error ? error.message : 'Unknown error' }
  }
}

export async function getPushSubscriptionStatus(): Promise<{
  supported: boolean
  permission: NotificationPermission
  subscribed: boolean
}> {
  if (!isPushSupported()) {
    return { supported: false, permission: 'denied', subscribed: false }
  }

  const permission = getNotificationPermission()
  
  try {
    const registration = await navigator.serviceWorker.ready
    const subscription = await registration.pushManager.getSubscription()
    
    return {
      supported: true,
      permission,
      subscribed: !!subscription
    }
  } catch {
    return {
      supported: true,
      permission,
      subscribed: false
    }
  }
}

export async function testPushNotification(
  accessToken: string
): Promise<{ success: boolean; message?: string; error?: string }> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/push/test`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`
      }
    })

    const data = await response.json()
    
    if (!response.ok) {
      return { success: false, error: data.error?.message || 'Test failed' }
    }

    return { success: data.success, message: data.message }
  } catch (error) {
    return { success: false, error: error instanceof Error ? error.message : 'Unknown error' }
  }
}
