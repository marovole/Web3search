/**
 * Deep Research Input Validation
 * Validates and sanitizes research query input
 */

export const MAX_RESEARCH_QUERY_LENGTH = 5000

export interface ValidationResult {
  valid: boolean
  sanitized: string
  error?: string
}

/**
 * Validate and sanitize research query input
 * Prevents injection attacks and ensures safe processing
 */
export function validateResearchQuery(input: string): ValidationResult {
  // Check for empty or invalid input
  if (!input || typeof input !== 'string') {
    return { valid: false, sanitized: '', error: 'Query is required' }
  }

  const trimmed = input.trim()

  // Check minimum length
  if (trimmed.length < 2) {
    return { valid: false, sanitized: '', error: 'Query must be at least 2 characters' }
  }

  // Check maximum length
  if (trimmed.length > MAX_RESEARCH_QUERY_LENGTH) {
    return {
      valid: false,
      sanitized: '',
      error: `Query exceeds maximum length of ${MAX_RESEARCH_QUERY_LENGTH} characters`,
    }
  }

  // Check for potential prompt injection patterns
  const injectionPatterns = [
    /ignore\s+previous\s+instructions/i,
    /system\s*:/i,
    /assistant\s*:/i,
    /\b(jailbreak|jail\s*break)\b/i,
    /\b(dan|do\s*anything\s*now)\b/i,
    /<script\b/i,
    /javascript:/i,
    /on\w+\s*=/i,
  ]

  for (const pattern of injectionPatterns) {
    if (pattern.test(trimmed)) {
      return { valid: false, sanitized: '', error: 'Query contains prohibited content' }
    }
  }

  // Sanitize the input (remove potential XSS vectors)
  const sanitized = trimmed
    .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
    .replace(/javascript:/gi, '')
    .replace(/on\w+\s*=/gi, '')
    .replace(/data:/g, '')

  return { valid: true, sanitized }
}
