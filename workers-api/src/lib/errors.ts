/**
 * Unified Error Codes for Web3search API
 * 
 * This file defines all error codes used across the API for consistency.
 * Error codes follow HTTP status code patterns and are grouped by category.
 */

// ============================================================================
// Authentication & Authorization Errors (40x)
// ============================================================================
export const AuthErrorCodes = {
  NOT_AUTHENTICATED: 'NOT_AUTHENTICATED',
  AUTH_REQUIRED: 'AUTH_REQUIRED',
  INVALID_AUTH_FORMAT: 'INVALID_AUTH_FORMAT',
  TOKEN_REQUIRED: 'TOKEN_REQUIRED',
  TOKEN_EXPIRED: 'TOKEN_EXPIRED',
  INVALID_TOKEN: 'INVALID_TOKEN',
  AUTH_FAILED: 'AUTH_FAILED',
  PLAN_REQUIRED: 'PLAN_REQUIRED',
} as const;

// ============================================================================
// Client Input Errors (40x)
// ============================================================================
export const InputErrorCodes = {
  INVALID_JSON: 'INVALID_JSON',
  INVALID_INPUT: 'INVALID_INPUT',
  INVALID_QUERY: 'INVALID_QUERY',
  MISSING_QUERY: 'MISSING_QUERY',
  QUERY_TOO_LONG: 'QUERY_TOO_LONG',
  MISSING_TASK_ID: 'MISSING_TASK_ID',
  INVALID_MODEL: 'INVALID_MODEL',
  MODEL_NOT_FOUND: 'MODEL_NOT_FOUND',
  MODEL_CAPABILITY_MISMATCH: 'MODEL_CAPABILITY_MISMATCH',
  INVALID_TYPE: 'INVALID_TYPE',
  INVALID_USERNAME: 'INVALID_USERNAME',
  INVALID_RISK_PREFERENCE: 'INVALID_RISK_PREFERENCE',
  INVALID_THEME: 'INVALID_THEME',
  INVALID_PLAN: 'INVALID_PLAN',
  INVALID_SIGNATURE: 'INVALID_SIGNATURE',
  INVALID_SECTION: 'INVALID_SECTION',
  INVALID_REQUEST: 'INVALID_REQUEST',
  NO_UPDATES: 'NO_UPDATES',
  ENDPOINT_IN_USE: 'ENDPOINT_IN_USE',
  NOT_CONFIGURED: 'NOT_CONFIGURED',
  MISSING_SIGNATURE: 'MISSING_SIGNATURE',
  PRICE_NOT_CONFIGURED: 'PRICE_NOT_CONFIGURED',
} as const;

// ============================================================================
// Resource Not Found Errors (40x)
// ============================================================================
export const NotFoundErrorCodes = {
  NOT_FOUND: 'NOT_FOUND',
  TASK_NOT_FOUND: 'TASK_NOT_FOUND',
  PROFILE_NOT_FOUND: 'PROFILE_NOT_FOUND',
  QUOTA_NOT_FOUND: 'QUOTA_NOT_FOUND',
  RECOMMENDATION_NOT_FOUND: 'RECOMMENDATION_NOT_FOUND',
  NOTIFICATION_NOT_FOUND: 'NOTIFICATION_NOT_FOUND',
  HOLDING_NOT_FOUND: 'HOLDING_NOT_FOUND',
  WATCHLIST_ITEM_NOT_FOUND: 'WATCHLIST_ITEM_NOT_FOUND',
  DIAGNOSIS_NOT_FOUND: 'DIAGNOSIS_NOT_FOUND',
  NO_SUBSCRIPTION: 'NO_SUBSCRIPTION',
} as const;

// ============================================================================
// Conflict Errors (40x)
// ============================================================================
export const ConflictErrorCodes = {
  ALREADY_EXISTS: 'ALREADY_EXISTS',
  USERNAME_TAKEN: 'USERNAME_TAKEN',
} as const;

// ============================================================================
// Rate Limiting & Quota Errors (40x)
// ============================================================================
export const RateLimitErrorCodes = {
  RATE_LIMITED: 'RATE_LIMITED',
  QUOTA_EXCEEDED: 'QUOTA_EXCEEDED',
} as const;

// ============================================================================
// Server Errors (50x)
// ============================================================================
export const ServerErrorCodes = {
  INTERNAL_ERROR: 'INTERNAL_ERROR',
  DATABASE_ERROR: 'DATABASE_ERROR',
  CHAT_ERROR: 'CHAT_ERROR',
  OPENROUTER_ERROR: 'OPENROUTER_ERROR',
  DEEP_RESEARCH_ERROR: 'DEEP_RESEARCH_ERROR',
  RESEARCH_TASK_ERROR: 'RESEARCH_TASK_ERROR',
  FETCH_TASK_ERROR: 'FETCH_TASK_ERROR',
  LIST_TASKS_ERROR: 'LIST_TASKS_ERROR',
  PROCESSING_ERROR: 'PROCESSING_ERROR',
  GITHUB_API_ERROR: 'GITHUB_API_ERROR',
  SEARCH_ERROR: 'SEARCH_ERROR',
  URI_TOO_LONG: 'URI_TOO_LONG',
} as const;

// ============================================================================
// External Service Errors
// ============================================================================
export const ExternalServiceErrorCodes = {
  RATE_LIMIT: 'RATE_LIMIT',
  API_ERROR: 'API_ERROR',
  NO_DATA: 'NO_DATA',
  NO_PRICE: 'NO_PRICE',
  TIMEOUT: 'TIMEOUT',
  UNKNOWN_ERROR: 'UNKNOWN_ERROR',
} as const;

// ============================================================================
// Combined Error Codes Type
// ============================================================================
export type ErrorCode = 
  | typeof AuthErrorCodes[keyof typeof AuthErrorCodes]
  | typeof InputErrorCodes[keyof typeof InputErrorCodes]
  | typeof NotFoundErrorCodes[keyof typeof NotFoundErrorCodes]
  | typeof ConflictErrorCodes[keyof typeof ConflictErrorCodes]
  | typeof RateLimitErrorCodes[keyof typeof RateLimitErrorCodes]
  | typeof ServerErrorCodes[keyof typeof ServerErrorCodes]
  | typeof ExternalServiceErrorCodes[keyof typeof ExternalServiceErrorCodes];

// ============================================================================
// HTTP Status Code Mapping
// ============================================================================
export const ErrorCodeToStatus: Record<ErrorCode, number> = {
  // Authentication (401)
  NOT_AUTHENTICATED: 401,
  AUTH_REQUIRED: 401,
  INVALID_AUTH_FORMAT: 401,
  TOKEN_REQUIRED: 401,
  TOKEN_EXPIRED: 401,
  INVALID_TOKEN: 401,
  AUTH_FAILED: 401,
  PLAN_REQUIRED: 402,
  
  // Input Errors (400)
  INVALID_JSON: 400,
  INVALID_INPUT: 400,
  INVALID_QUERY: 400,
  MISSING_QUERY: 400,
  QUERY_TOO_LONG: 400,
  MISSING_TASK_ID: 400,
  INVALID_MODEL: 400,
  MODEL_NOT_FOUND: 400,
  MODEL_CAPABILITY_MISMATCH: 400,
  INVALID_TYPE: 400,
  INVALID_USERNAME: 400,
  INVALID_RISK_PREFERENCE: 400,
  INVALID_THEME: 400,
  INVALID_PLAN: 400,
  INVALID_SIGNATURE: 400,
  INVALID_SECTION: 400,
  INVALID_REQUEST: 400,
  NO_UPDATES: 400,
  ENDPOINT_IN_USE: 409,
  NOT_CONFIGURED: 500,
  MISSING_SIGNATURE: 400,
  PRICE_NOT_CONFIGURED: 500,
  
  // Not Found (404)
  NOT_FOUND: 404,
  TASK_NOT_FOUND: 404,
  PROFILE_NOT_FOUND: 404,
  QUOTA_NOT_FOUND: 404,
  RECOMMENDATION_NOT_FOUND: 404,
  NOTIFICATION_NOT_FOUND: 404,
  HOLDING_NOT_FOUND: 404,
  WATCHLIST_ITEM_NOT_FOUND: 404,
  DIAGNOSIS_NOT_FOUND: 404,
  NO_SUBSCRIPTION: 404,
  
  // Conflict (409)
  ALREADY_EXISTS: 409,
  USERNAME_TAKEN: 409,
  
  // Rate Limit (429)
  RATE_LIMITED: 429,
  QUOTA_EXCEEDED: 429,
  
  // Server Errors (500)
  INTERNAL_ERROR: 500,
  DATABASE_ERROR: 500,
  CHAT_ERROR: 500,
  OPENROUTER_ERROR: 500,
  DEEP_RESEARCH_ERROR: 500,
  RESEARCH_TASK_ERROR: 500,
  FETCH_TASK_ERROR: 500,
  LIST_TASKS_ERROR: 500,
  PROCESSING_ERROR: 500,
  GITHUB_API_ERROR: 500,
  SEARCH_ERROR: 500,
  URI_TOO_LONG: 414,
  
  // External Services
  RATE_LIMIT: 429,
  API_ERROR: 502,
  NO_DATA: 502,
  NO_PRICE: 502,
  TIMEOUT: 504,
  UNKNOWN_ERROR: 500,
};

// ============================================================================
// Re-exports for convenience
// ============================================================================
export const ErrorCodes = {
  ...AuthErrorCodes,
  ...InputErrorCodes,
  ...NotFoundErrorCodes,
  ...ConflictErrorCodes,
  ...RateLimitErrorCodes,
  ...ServerErrorCodes,
  ...ExternalServiceErrorCodes,
} as const;

// Default error response factory
export function createErrorResponse(
  code: ErrorCode,
  message?: string,
  customStatus?: number
): { error: { code: string; message: string; status: number } } {
  return {
    error: {
      code,
      message: message || getDefaultErrorMessage(code),
      status: customStatus || ErrorCodeToStatus[code],
    },
  };
}

function getDefaultErrorMessage(code: ErrorCode): string {
  const messages: Record<string, string> = {
    NOT_AUTHENTICATED: 'Authentication required',
    AUTH_REQUIRED: 'Authorization header required',
    INVALID_AUTH_FORMAT: 'Invalid authorization format',
    TOKEN_REQUIRED: 'Token is required',
    TOKEN_EXPIRED: 'Token has expired',
    INVALID_TOKEN: 'Invalid token',
    AUTH_FAILED: 'Authentication failed',
    PLAN_REQUIRED: 'Upgrade required',
    INVALID_JSON: 'Invalid JSON in request body',
    INVALID_INPUT: 'Invalid input provided',
    INVALID_QUERY: 'Invalid query parameter',
    MISSING_QUERY: 'Query parameter is required',
    QUERY_TOO_LONG: 'Query exceeds maximum length',
    MISSING_TASK_ID: 'Task ID is required',
    INVALID_MODEL: 'Invalid model configuration',
    MODEL_NOT_FOUND: 'Model not found',
    MODEL_CAPABILITY_MISMATCH: 'Model missing required capabilities',
    INVALID_TYPE: 'Invalid type specified',
    INVALID_USERNAME: 'Invalid username format',
    INVALID_RISK_PREFERENCE: 'Invalid risk preference',
    INVALID_THEME: 'Invalid theme specified',
    INVALID_PLAN: 'Invalid plan specified',
    INVALID_SIGNATURE: 'Invalid signature',
    INVALID_SECTION: 'Invalid report section',
    INVALID_REQUEST: 'Invalid request',
    NO_UPDATES: 'No valid fields to update',
    ENDPOINT_IN_USE: 'Endpoint already registered',
    NOT_CONFIGURED: 'Service not configured',
    MISSING_SIGNATURE: 'Webhook signature required',
    PRICE_NOT_CONFIGURED: 'Price not configured',
    NOT_FOUND: 'Resource not found',
    TASK_NOT_FOUND: 'Task not found',
    PROFILE_NOT_FOUND: 'Profile not found',
    QUOTA_NOT_FOUND: 'Quota not found',
    RECOMMENDATION_NOT_FOUND: 'Recommendation not found',
    NOTIFICATION_NOT_FOUND: 'Notification not found',
    HOLDING_NOT_FOUND: 'Holding not found',
    WATCHLIST_ITEM_NOT_FOUND: 'Watchlist item not found',
    DIAGNOSIS_NOT_FOUND: 'Diagnosis not found',
    NO_SUBSCRIPTION: 'No active subscription',
    ALREADY_EXISTS: 'Resource already exists',
    USERNAME_TAKEN: 'Username is already taken',
    RATE_LIMITED: 'Rate limit exceeded',
    QUOTA_EXCEEDED: 'Quota exceeded',
    INTERNAL_ERROR: 'Internal server error',
    DATABASE_ERROR: 'Database operation failed',
    CHAT_ERROR: 'Chat processing failed',
    OPENROUTER_ERROR: 'AI service error',
    DEEP_RESEARCH_ERROR: 'Deep research failed',
    RESEARCH_TASK_ERROR: 'Research task failed',
    FETCH_TASK_ERROR: 'Failed to fetch task',
    LIST_TASKS_ERROR: 'Failed to list tasks',
    PROCESSING_ERROR: 'Processing failed',
    GITHUB_API_ERROR: 'GitHub API error',
    SEARCH_ERROR: 'Search operation failed',
    URI_TOO_LONG: 'Request URI too long',
    RATE_LIMIT: 'External API rate limit',
    API_ERROR: 'External API error',
    NO_DATA: 'No data from external API',
    NO_PRICE: 'Price data unavailable',
    TIMEOUT: 'Request timeout',
    UNKNOWN_ERROR: 'An unknown error occurred',
  };
  return messages[code] || 'An error occurred';
}
