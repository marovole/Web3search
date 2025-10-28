// Message types
export interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
  isStreaming?: boolean
}

// Chat modes
export type ChatMode = 'quick' | 'deep'

// API Request types
export interface QuickChatRequest {
  query: string
  conversation_id?: string
}

export interface DeepResearchRequest {
  query: string
  conversation_id?: string
}

// API Response types
export interface QuickChatResponse {
  content: string
  symbol?: string
  query_type: string
  response_time: number
  model: string
  session_id: string
}

export interface DeepResearchResponse {
  report_id: number
  markdown_content: string
  tldr: string
  quality_score?: number
  generation_time?: number
  data_sources?: string[]
}

// Share types
export interface ShareReportRequest {
  expires_in_days?: number
}

export interface ShareReportResponse {
  share_token: string
  share_url: string
  expires_at?: string
}

export interface SharedReportResponse {
  title: string
  symbol: string
  markdown_content: string
  tldr: string
  report_type: string
  quality_score?: number
  data_sources?: string[]
  created_at: string
}

// Report types
export interface Report {
  id: number
  symbol: string
  query: string
  title: string
  markdown_content: string
  tldr: string
  report_type: string
  status: string
  quality_score?: number
  generation_time?: number
  data_sources?: string[]
  created_at: string
  completed_at?: string
}

// Error types
export interface APIError {
  detail: string
}
