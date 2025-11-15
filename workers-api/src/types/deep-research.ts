/**
 * Deep Research Types
 * Async research task management
 * Part of Week 2 T11: Deep Research async pipeline
 */

export type ResearchStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
export type ResearchDepth = 'quick' | 'standard' | 'comprehensive'

export interface ResearchSource {
  url: string
  title: string
  snippet: string
  relevance_score: number
  accessed_at: string
}

export interface ResearchCitation {
  source_id: string
  quote: string
  page_number?: number
  relevance_score: number
}

export interface DeepResearchRequest {
  query: string
  research_depth?: ResearchDepth
  max_sources?: number
  focus_areas?: string[]
  model?: string
  model_provider?: string
  temperature?: number
  conversation_id?: string
  metadata?: Record<string, unknown>
}

export interface DeepResearchTask {
  id: string
  user_id?: string
  client_session_id?: string
  conversation_id?: string
  query: string
  status: ResearchStatus
  research_depth: ResearchDepth
  max_sources: number
  focus_areas: string[]
  model_id?: string
  model_provider?: string
  temperature: number
  result?: ResearchResult
  summary?: string
  answer?: string
  sources: ResearchSource[]
  citations: ResearchCitation[]
  progress_percent: number
  current_step?: string
  steps_completed: number
  total_steps: number
  tokens_prompt: number
  tokens_completion: number
  cost_usd: number
  started_at?: string
  completed_at?: string
  duration_ms?: number
  error_code?: string
  error_message?: string
  retry_count: number
  created_at: string
  updated_at: string
  expires_at: string
  metadata: Record<string, unknown>
  tags: string[]
}

export interface ResearchResult {
  summary: string
  answer: string
  key_findings: string[]
  sources: ResearchSource[]
  citations: ResearchCitation[]
  research_depth: ResearchDepth
  total_sources: number
  total_citations: number
  confidence_score: number
}

export interface ResearchProgress {
  task_id: string
  status: ResearchStatus
  progress_percent: number
  current_step?: string
  steps_completed: number
  total_steps: number
  estimated_time_remaining?: number
  timestamp: string
  [key: string]: unknown
}

export interface ResearchListParams {
  user_id?: string
  status?: ResearchStatus
  research_depth?: ResearchDepth
  limit?: number
  offset?: number
  from_date?: string
  to_date?: string
}

export interface ResearchListResponse {
  tasks: DeepResearchTask[]
  total: number
  limit: number
  offset: number
}

export interface ResearchStepUpdate {
  step_name: string
  step_number: number
  total_steps: number
  progress_percent: number
  message?: string
  timestamp: string
  [key: string]: unknown
}

// WebSocket/SSE events for real-time updates
export interface ResearchSSEvent {
  event: 'research.started' | 'research.progress' | 'research.step' | 'research.completed' | 'research.failed'
  data: {
    task_id: string
    timestamp: string
    [key: string]: unknown
  }
}

export interface ResearchStartedEvent extends ResearchSSEvent {
  event: 'research.started'
  data: {
    task_id: string
    timestamp: string
    query: string
    estimated_duration: number
  }
}

export interface ResearchProgressEvent extends ResearchSSEvent {
  event: 'research.progress'
  data: ResearchProgress
}

export interface ResearchStepEvent extends ResearchSSEvent {
  event: 'research.step'
  data: ResearchStepUpdate & { task_id: string }
}

export interface ResearchCompletedEvent extends ResearchSSEvent {
  event: 'research.completed'
  data: {
    task_id: string
    timestamp: string
    result: ResearchResult
    duration_ms: number
    cost_usd: number
  }
}

export interface ResearchFailedEvent extends ResearchSSEvent {
  event: 'research.failed'
  data: {
    task_id: string
    timestamp: string
    error_code: string
    error_message: string
    retry_count: number
  }
}

// Database row type (for internal use)
export interface DeepResearchTaskRow {
  id: string
  user_id: string | null
  client_session_id: string | null
  conversation_id: string | null
  query: string
  status: ResearchStatus
  research_depth: ResearchDepth
  max_sources: number
  focus_areas: string[] | null
  model_id: string | null
  model_provider: string | null
  temperature: number
  result: unknown | null
  summary: string | null
  answer: string | null
  sources: unknown | null
  citations: unknown | null
  progress_percent: number
  current_step: string | null
  steps_completed: number
  total_steps: number
  tokens_prompt: number
  tokens_completion: number
  cost_usd: number
  started_at: string | null
  completed_at: string | null
  duration_ms: number | null
  error_code: string | null
  error_message: string | null
  retry_count: number
  created_at: string
  updated_at: string
  expires_at: string
  metadata: unknown | null
  tags: string[] | null
}
