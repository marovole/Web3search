/**
 * Analytics Event Type Definitions
 * Provides type-safe event tracking for Google Analytics and Sentry
 *
 * @module types/analytics-events
 */

/**
 * Search type options
 */
export type SearchType = 'quick' | 'deep'

/**
 * Chat channel types
 */
export type ChatChannel = 'chat' | 'support' | 'deep_research' | 'system'

/**
 * Deep research workflow stages
 */
export type DeepResearchStage = 'query' | 'analysis' | 'summarization' | 'presentation'

/**
 * Page view event payload
 */
export interface PageViewPayload {
  /** Page path (e.g., '/search', '/chat') */
  page_path: string
  /** Page title */
  page_title?: string
  /** Referrer URL */
  referrer?: string
}

/**
 * Search event payload
 */
export interface SearchEventPayload {
  /** Search query string */
  query: string
  /** Search type (quick or deep) */
  type: SearchType
  /** Number of results returned */
  resultCount?: number
  /** Response time in milliseconds */
  responseTimeMs?: number
}

/**
 * Chat interaction event payload
 */
export interface ChatEventPayload {
  /** Chat channel identifier */
  channel: ChatChannel
  /** Message ID for tracking */
  messageId?: string
  /** Interaction duration in milliseconds */
  durationMs?: number
  /** Number of response tokens */
  responseTokens?: number
}

/**
 * Deep research event payload
 */
export interface DeepResearchEventPayload {
  /** Research query */
  query: string
  /** Current workflow stage */
  stage: DeepResearchStage
  /** Whether the stage completed successfully */
  success: boolean
  /** Stage duration in milliseconds */
  durationMs?: number
  /** Research variant/mode */
  variant?: string
}

/**
 * Error event payload
 */
export interface ErrorEventPayload {
  /** Error message */
  message: string
  /** Error stack trace */
  stack?: string
  /** Error severity level */
  severity?: 'low' | 'medium' | 'high' | 'critical'
}

/**
 * Custom event payload (extensible)
 */
export interface CustomEventPayload {
  /** Mark event as important (triggers Sentry logging) */
  important?: boolean
  /** Additional custom properties */
  [key: string]: any
}

/**
 * Map of event names to their payload types
 * Enables type-safe event tracking
 */
export interface AnalyticsEventPayloadMap {
  page_view: PageViewPayload
  search: SearchEventPayload
  chat: ChatEventPayload
  deep_research: DeepResearchEventPayload
  error: ErrorEventPayload
  custom: CustomEventPayload
}

/**
 * Valid analytics event names
 */
export type AnalyticsEventName = keyof AnalyticsEventPayloadMap
