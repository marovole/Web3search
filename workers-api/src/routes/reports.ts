/**
 * Report Generation Routes
 * Handles research report generation using OpenRouter API
 * Implements streaming response for real-time report generation
 */

import { Hono } from 'hono'
import type { Env } from '../types/env'
import type {
  ReportRequestBody,
  ReportStreamChunk,
  ReportSection,
  ReportGenerationState
} from '../types/reports'
import { createOpenRouterClient } from '../lib/openrouter'
import { getSupabaseClient } from '../lib/supabase'
import { createRateLimitMiddleware } from '../middlewares/rate-limit'

const reports = new Hono<{ Bindings: Env }>()

const DEFAULT_MODEL = 'mistralai/devstral-2512:free'
const MAX_TOKENS_PER_SECTION = 2000

/**
 * Token usage data from OpenRouter API response
 */
interface SectionGenerationUsage {
  prompt_tokens: number
  completion_tokens: number
  total_tokens: number
}

/**
 * Result from generating a single section
 */
interface SectionGenerationResult {
  content: string
  usage: SectionGenerationUsage
}

/**
 * Extract and normalize token usage from OpenRouter API response
 * Handles missing total_tokens by calculating from prompt + completion
 */
function normalizeOpenRouterUsage(data: Record<string, unknown>): SectionGenerationUsage {
  const usagePayload = (data.usage ?? {}) as Record<string, unknown>
  const prompt_tokens = typeof usagePayload.prompt_tokens === 'number'
    ? usagePayload.prompt_tokens
    : 0
  const completion_tokens = typeof usagePayload.completion_tokens === 'number'
    ? usagePayload.completion_tokens
    : 0
  const total_tokens = typeof usagePayload.total_tokens === 'number'
    ? usagePayload.total_tokens
    : prompt_tokens + completion_tokens

  return { prompt_tokens, completion_tokens, total_tokens }
}

/**
 * POST /generate
 * Generate a comprehensive research report with streaming response
 */
reports.post(
  '/generate',
  createRateLimitMiddleware({
    scope: 'reports-ip-hour',
    limit: 5, // 5 reports per hour
    windowSeconds: 60 * 60,
    key: (c) => c.req.header('cf-connecting-ip') || 'anonymous',
  }),
  async (c) => {
    // Parse and validate request body
    let body: ReportRequestBody
    try {
      body = await c.req.json<ReportRequestBody>()
    } catch {
      return c.json(
        {
          error: {
            code: 'INVALID_JSON',
            message: 'Request body must be valid JSON',
            status: 400,
          },
        },
        400
      )
    }

    // Validate required fields
    const { topic, sections, format: _format = 'markdown', save_to_database = false } = body
    if (!topic || !sections || sections.length === 0) {
      return c.json(
        {
          error: {
            code: 'INVALID_REQUEST',
            message: 'Missing required fields: topic, sections',
            status: 400,
          },
        },
        400
      )
    }

    // Validate sections format
    for (const section of sections) {
      if (!section.id || !section.title) {
        return c.json(
          {
            error: {
              code: 'INVALID_SECTION',
              message: 'Each section must have id and title',
              status: 400,
            },
          },
          400
        )
      }
    }

    // Initialize OpenRouter client
    const openrouter = createOpenRouterClient(c.env)
    const supabase = getSupabaseClient(c.env)

    // Initialize generation state
    const state: ReportGenerationState = {
      topic,
      sections,
      current_section: 0,
      completed_sections: [],
      content: {},
      start_time: Date.now(),
    }

    // Set up streaming response
    const { readable, writable } = new TransformStream()
    const writer = writable.getWriter()
    const encoder = new TextEncoder()

    // Start generation process in background
    const generateReport = async () => {
      try {
        // Send initial report header
        const header = {
          type: 'report_start',
          topic,
          sections: sections.map(s => ({ id: s.id, title: s.title })),
          total_sections: sections.length,
        }
        await writer.write(encoder.encode(`data: ${JSON.stringify(header)}\n\n`))

        // Initialize token usage accumulator
        let tokensUsed = 0

        // Generate each section
        for (let i = 0; i < sections.length; i++) {
          const section = sections[i]
          state.current_section = i

          const sectionPrompt = buildSectionPrompt(state, section)

          try {
            // Generate content and extract token usage
            const { content, usage } = await generateSectionContent(openrouter, sectionPrompt)

            // Send section content as stream
            const chunk: ReportStreamChunk = {
              section_id: section.id,
              section_title: section.title,
              delta: content,
              is_complete: true,
            }

            await writer.write(encoder.encode(`data: ${JSON.stringify(chunk)}\n\n`))

            // Update state and accumulate tokens
            state.content[section.id] = content
            state.completed_sections.push(section.id)
            tokensUsed += usage.total_tokens

            // Send progress update
            const progress = {
              type: 'progress_update',
              current_section: i + 1,
              total_sections: sections.length,
              completed_sections: state.completed_sections,
              progress_percent: Math.round(((i + 1) / sections.length) * 100),
            }
            await writer.write(encoder.encode(`data: ${JSON.stringify(progress)}\n\n`))

          } catch (error) {
            // Send error for this section
            const errorChunk = {
              type: 'section_error',
              section_id: section.id,
              error: error instanceof Error ? error.message : 'Unknown error',
            }
            await writer.write(encoder.encode(`data: ${JSON.stringify(errorChunk)}\n\n`))
          }
        }

        // Save to database if requested
        let report_id: string | null = null
        if (save_to_database && supabase) {
          try {
            report_id = await saveReportToDatabase(supabase, state, tokensUsed)
          } catch (error) {
            console.error('Failed to save report to database:', error)
          }
        }

        // Send completion message
        const completion = {
          type: 'report_complete',
          report_id,
          topic,
          total_sections: sections.length,
          completed_sections: state.completed_sections,
          content: state.content,
          generation_time_ms: Date.now() - state.start_time,
          tokens_used: tokensUsed,
        }
        await writer.write(encoder.encode(`data: ${JSON.stringify(completion)}\n\n`))

      } catch (error) {
        // Send global error
        const errorResponse = {
          type: 'generation_error',
          error: error instanceof Error ? error.message : 'Unknown error',
        }
        await writer.write(encoder.encode(`data: ${JSON.stringify(errorResponse)}\n\n`))
      } finally {
        // Close the stream
        await writer.write(encoder.encode('event: done\ndata: {"status":"completed"}\n\n'))
        await writer.close()
      }
    }

    // Start generation without blocking the response
    c.executionCtx.waitUntil(generateReport())

    // Return streaming response
    return new Response(readable, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    })
  }
)

/**
 * Build a detailed prompt for generating a specific report section
 */
function buildSectionPrompt(state: ReportGenerationState, section: ReportSection): string {
  const { topic, sections, content } = state

  // Build context from previous sections
  const previousContext = Object.entries(content)
    .map(([sectionId, sectionContent]) => {
      const prevSection = sections.find(s => s.id === sectionId)
      return `## ${prevSection?.title || sectionId}\n${sectionContent.slice(0, 500)}...`
    })
    .join('\n\n')

  const focusPoints = section.focus_points?.length
    ? `\nFocus on these specific aspects: ${section.focus_points.join(', ')}`
    : ''

  return `You are generating a comprehensive research report on "${topic}".

CURRENT SECTION: ${section.title}
${section.description ? `Description: ${section.description}` : ''}

${previousContext ? `PREVIOUS SECTIONS (for context):\n${previousContext}\n\n` : ''}

Please write a detailed, informative section about "${section.title}" for a report on ${topic}.${focusPoints}

Requirements:
- Write in clear, professional language
- Include specific data, metrics, and examples where possible
- Maintain consistency with previous sections
- Aim for 800-1200 words
- Use markdown formatting with headers and bullet points
- Focus on factual, well-researched information
- Acknowledge uncertainty or speculation appropriately

Content:`
}

/**
 * Generate content for a single section using OpenRouter
 * Returns both the generated content and token usage statistics
 */
async function generateSectionContent(
  openrouter: { request: (payload: Record<string, unknown>) => Promise<Response> },
  prompt: string
): Promise<SectionGenerationResult> {
  const payload = {
    model: DEFAULT_MODEL,
    messages: [
      {
        role: 'system',
        content: 'You are an expert researcher specializing in cryptocurrency and blockchain technology. Provide detailed, accurate, and well-structured information.'
      },
      {
        role: 'user',
        content: prompt
      }
    ],
    max_tokens: MAX_TOKENS_PER_SECTION,
    temperature: 0.7,
    stream: false
  }

  const response = await openrouter.request(payload)

  if (!response.ok) {
    throw new Error(`OpenRouter API request failed: ${response.status}`)
  }

  const data = await response.json()

  if (!data || !data.choices || data.choices.length === 0) {
    throw new Error('OpenRouter API returned invalid response')
  }

  return {
    content: data.choices[0]?.message?.content || '',
    usage: normalizeOpenRouterUsage(data as Record<string, unknown>)
  }
}

/**
 * Save completed report to Supabase database
 */
async function saveReportToDatabase(
  supabase: ReturnType<typeof getSupabaseClient>,
  state: ReportGenerationState,
  tokensUsed: number
): Promise<string> {
  const { topic, sections, content } = state

  const { data, error } = await supabase
    .from('reports')
    .insert({
      topic,
      sections: sections,
      content: content,
      metadata: {
        model: DEFAULT_MODEL,
        tokens_used: tokensUsed,
        generation_time_ms: Date.now() - state.start_time,
      }
    })
    .select('id')
    .single()

  if (error) {
    throw error
  }

  return data.id
}

export default reports
