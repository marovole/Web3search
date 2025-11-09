/**
 * Report Generation Types
 * Type definitions for report generation API
 */

export interface ReportRequestBody {
  topic: string
  sections: ReportSection[]
  format?: 'markdown' | 'json'
  save_to_database?: boolean
}

export interface ReportSection {
  id: string
  title: string
  description?: string
  focus_points?: string[]
}

export interface ReportStreamChunk {
  section_id: string
  section_title: string
  delta: string
  is_complete: boolean
}

export interface SavedReport {
  id: string
  topic: string
  sections: ReportSection[]
  content: Record<string, string> // section_id -> content
  metadata: {
    model: string
    tokens_used: number
    generation_time_ms: number
    created_at: string
  }
}

export interface ReportGenerationState {
  topic: string
  sections: ReportSection[]
  current_section: number
  completed_sections: string[]
  content: Record<string, string>
  start_time: number
}

export const DEFAULT_REPORT_SECTIONS: ReportSection[] = [
  {
    id: 'overview',
    title: 'Overview',
    description: 'General introduction and key concepts',
    focus_points: ['definition', 'importance', 'key metrics']
  },
  {
    id: 'technical_analysis',
    title: 'Technical Analysis',
    description: 'Technical architecture and implementation details',
    focus_points: ['architecture', 'mechanisms', 'protocols']
  },
  {
    id: 'market_analysis',
    title: 'Market Analysis',
    description: 'Market data, trends, and statistics',
    focus_points: ['market cap', 'trading volume', 'price trends']
  },
  {
    id: 'use_cases',
    title: 'Use Cases & Applications',
    description: 'Real-world applications and use cases',
    focus_points: ['adoption', 'industry use', 'case studies']
  },
  {
    id: 'risks_challenges',
    title: 'Risks & Challenges',
    description: 'Potential risks, limitations, and challenges',
    focus_points: ['technical risks', 'regulatory risks', 'adoption barriers']
  }
]