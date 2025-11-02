export type SeverityLevel = 'fatal' | 'error' | 'warning' | 'log' | 'info' | 'debug'

export function initSentry() {}
export function captureException(_error: Error, _context?: Record<string, any>) {}
export function captureMessage(_message: string, _level: SeverityLevel = 'info', _context?: Record<string, any>) {}
export function setUser(_user: { id: string; email?: string; username?: string }) {}
export function clearUser() {}
export function addBreadcrumb(_breadcrumb: any) {}
export function setContext(_key: string, _context: Record<string, any>) {}
export function startSpan(_name: string, _operation: string = 'navigation', _callback?: any) { return null }
export function startTransaction(_name: string, _operation: string = 'navigation') { return null }
export function trackCoreWebVitals() {}
export function trackUserInteraction(_action: string, _element?: string, _properties?: Record<string, any>) {}
export function trackAPIRequest(_url: string, _method: string, _status: number, _duration: number, _responseSize?: number) {}
export function trackPageLoad() {}
export function trackResourceLoading() {}
export function trackError(_error: Error, _context?: Record<string, any>) {}

export default {
  initSentry,
  captureException,
  captureMessage,
  setUser,
  clearUser,
  addBreadcrumb,
  setContext,
  startSpan,
  startTransaction,
  trackCoreWebVitals,
  trackUserInteraction,
  trackAPIRequest,
  trackPageLoad,
  trackResourceLoading,
  trackError,
}