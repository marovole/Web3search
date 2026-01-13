declare global {
  interface Window {
    Sentry?: {
      init: (config: any) => void
      captureException: (error: any, context?: any) => void
      addBreadcrumb: (crumb: any) => void
      setContext: (key: string, value: any) => void
      startTransaction: (config: any) => any
    }
  }
}

let isInitialized = false
const traceIdMap = new Map<string, string>()

export function initSentry() {
  if (isInitialized) return
  
  if (import.meta.env.PROD && typeof window !== 'undefined' && window.Sentry) {
    try {
      window.Sentry.init({
        dsn: import.meta.env.VITE_SENTRY_DSN,
        environment: import.meta.env.MODE,
        tracesSampleRate: 0.1,
      })
      isInitialized = true
    } catch (error) {
      console.warn('Sentry initialization failed:', error)
    }
  }
}

export function captureException(error: any, context?: Record<string, any>) {
  const errorId = generateTraceId()
  
  if (context?.traceId) {
    traceIdMap.set(context.traceId, new Date().toISOString())
  }
  
  if (!import.meta.env.PROD) {
    console.error('Error captured:', errorId, error, context)
    return errorId
  }
  
  if (isInitialized && window.Sentry) {
    try {
      window.Sentry.captureException(error, {
        tags: { errorId },
        extra: context,
      })
    } catch (e) {
      console.error('Failed to send to Sentry:', e)
    }
  }
  
  return errorId
}

export function addBreadcrumb(crumb: any) {
  if (!import.meta.env.PROD) {
    console.log('Breadcrumb:', crumb)
    return
  }
  
  if (isInitialized && window.Sentry) {
    try {
      window.Sentry.addBreadcrumb(crumb)
    } catch (e) {
      console.error('Failed to add breadcrumb:', e)
    }
  }
}

export function setContext(key: string, value: any) {
  if (!import.meta.env.PROD) {
    console.log('Context set:', key, value)
    return
  }
  
  if (isInitialized && window.Sentry) {
    try {
      window.Sentry.setContext(key, value)
    } catch (e) {
      console.error('Failed to set context:', e)
    }
  }
}

export function startTransaction(name: string, op?: string) {
  if (!import.meta.env.PROD) {
    console.log('Transaction started:', name, op)
    return null
  }
  
  if (isInitialized && window.Sentry) {
    try {
      return window.Sentry.startTransaction({ name, op })
    } catch (e) {
      console.error('Failed to start transaction:', e)
      return null
    }
  }
  
  return null
}

export function trackCoreWebVitals() {
  if (!import.meta.env.PROD) {
    console.log('Core Web Vitals tracking')
  }
}

export function trackPageLoad() {
  if (!import.meta.env.PROD) {
    console.log('Page load tracking')
  }
}

export function trackResourceLoading() {
  if (!import.meta.env.PROD) {
    console.log('Resource loading tracking')
  }
}

function generateTraceId(): string {
  return `ERR-${Date.now().toString(36).toUpperCase()}-${Math.random().toString(36).substr(2, 5).toUpperCase()}`
}

export function getTraceId(errorId: string): string | undefined {
  return traceIdMap.get(errorId)
}
