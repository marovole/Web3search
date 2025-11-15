/**
 * Streaming Response Adapter
 * Handles Server-Sent Events (SSE) and OpenRouter streaming format
 *
 * @partof Week 2 T4: Streaming Response Adapter
 */

export interface StreamChunk {
  id: string
  created: number
  model: string
  choices: Array<{
    index: number
    delta: {
      role?: string
      content?: string
    }
    finish_reason: string | null
  }>
  error?: {
    message: string
    type: string
    code?: string
  }
}

export interface AggregatedStream {
  id: string
  model: string
  content: string
  finishReason: string | null
  tokens: {
    prompt: number
    completion: number
    total: number
  }
  error?: {
    message: string
    type: string
    code?: string
  }
}

/**
 * Parse a single SSE line into JSON
 */
function parseSSELine(line: string): StreamChunk | null {
  const linePrefix = 'data: '
  if (!line.startsWith(linePrefix)) {
    return null
  }

  const data = line.substring(linePrefix.length)

  // Ignore [DONE] messages
  if (data === '[DONE]') {
    return null
  }

  try {
    return JSON.parse(data)
  } catch (error) {
    console.error('Failed to parse SSE data:', error)
    return null
  }
}

/**
 * Parse OpenRouter streaming response
 */
export async function* parseStreamResponse(
  body: ReadableStream<Uint8Array>
): AsyncGenerator<StreamChunk, void, unknown> {
  const reader = body.getReader()
  const decoder = new TextDecoder()

  let buffer = ''
  let isCancelled = false

  try {
    while (!isCancelled) {
      const { value, done } = await reader.read()

      if (done) {
        break
      }

      buffer += decoder.decode(value, { stream: true })

      // Split by lines
      const lines = buffer.split('\n')
      // Keep the last line in buffer in case it's incomplete
      buffer = lines.pop() || ''

      for (const line of lines) {
        const chunk = parseSSELine(line)
        if (chunk) {
          yield chunk
        }
      }
    }

    // Process any remaining buffer
    if (buffer.trim()) {
      const lines = buffer.trim().split('\n')
      for (const line of lines) {
        const chunk = parseSSELine(line)
        if (chunk) {
          yield chunk
        }
      }
    }
  } finally {
    reader.releaseLock()
  }
}

/**
 * Aggregate streaming chunks into final response
 */
export async function aggregateStream(
  body: ReadableStream<Uint8Array>,
  onChunk?: (chunk: StreamChunk, aggregated: Partial<AggregatedStream>) => void
): Promise<AggregatedStream> {
  const generator = parseStreamResponse(body)
  let aggregated: Partial<AggregatedStream> = {
    content: '',
    tokens: {
      prompt: 0,
      completion: 0,
      total: 0
    }
  }

  for await (const chunk of generator) {
    // Track error
    if (chunk.error) {
      aggregated.error = chunk.error
      continue
    }

    // Extract metadata from first chunk
    if (!aggregated.id) {
      aggregated.id = chunk.id
      aggregated.model = chunk.model
    }

    // Accumulate content from all choices
    for (const choice of chunk.choices) {
      if (choice.delta.content) {
        aggregated.content = (aggregated.content || '') + choice.delta.content
      }

      if (choice.finish_reason) {
        aggregated.finishReason = choice.finish_reason
      }
    }

    // Call progress callback if provided
    if (onChunk) {
      onChunk(chunk, aggregated)
    }
  }

  // Validate required fields
  if (!aggregated.id || !aggregated.model || !aggregated.tokens) {
    throw new Error('Invalid stream: missing required fields')
  }

  return aggregated as AggregatedStream
}

/**
 * Create a streaming response for client consumption
 */
export function createStreamingResponse(
  body: ReadableStream<Uint8Array>,
  onChunk?: (chunk: StreamChunk) => void
): Response {
  const stream = new ReadableStream({
    async start(controller) {
      const generator = parseStreamResponse(body)

      try {
        for await (const chunk of generator) {
          if (onChunk) {
            onChunk(chunk)
          }

          // Forward the raw chunk to the client
          const data = `data: ${JSON.stringify(chunk)}\n\n`
          controller.enqueue(new TextEncoder().encode(data))
        }

        // Send [DONE] message
        controller.enqueue(new TextEncoder().encode('data: [DONE]\n\n'))
      } catch (error) {
        console.error('Streaming error:', error)

        // Send error to client
        const errorChunk = {
          error: {
            message: error instanceof Error ? error.message : 'Streaming failed',
            type: 'streaming_error'
          }
        }
        controller.enqueue(
          new TextEncoder().encode(`data: ${JSON.stringify(errorChunk)}\n\n`)
        )
      } finally {
        controller.close()
      }
    }
  })

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive'
    }
  })
}

/**
 * Handle streaming errors with proper cleanup
 */
export class StreamError extends Error {
  constructor(
    message: string,
    public originalError?: Error
  ) {
    super(message)
    this.name = 'StreamError'
  }
}

/**
 * Timeout wrapper for streams
 */
export function withTimeout<T>(
  stream: ReadableStream<T>,
  timeoutMs: number
): ReadableStream<T> {
  const abortController = new AbortController()
  const timeoutId = setTimeout(() => abortController.abort(), timeoutMs)

  const reader = stream.getReader()
  let isReleased = false

  const release = () => {
    if (!isReleased) {
      isReleased = true
      clearTimeout(timeoutId)
      reader.releaseLock()
    }
  }

  return new ReadableStream({
    async start(controller) {
      try {
        while (true) {
          const { value, done } = await Promise.race([
            reader.read(),
            new Promise<never>((_, reject) =>
              abortController.signal.addEventListener('abort', () =>
                reject(new Error('Stream timeout'))
              )
            )
          ])

          if (done) {
            controller.close()
            break
          }

          controller.enqueue(value)
        }
      } catch (error) {
        controller.error(error)
      } finally {
        release()
      }
    },
    cancel() {
      release()
    }
  })
}

/**
 * Transform stream for monitoring chunk throughput
 */
export function monitorStream(
  body: ReadableStream<Uint8Array>,
  metrics: {
    chunkCount: number
    firstChunkTime: number | null
    bytesReceived: number
    lastChunkTime: number | null
  }
): ReadableStream<Uint8Array> {
  const reader = body.getReader()
  const startTime = Date.now()

  return new ReadableStream({
    async start(controller) {
      metrics.firstChunkTime = null
      metrics.chunkCount = 0
      metrics.bytesReceived = 0

      try {
        while (true) {
          const { value, done } = await reader.read()

          if (done) {
            controller.close()
            break
          }

          if (!metrics.firstChunkTime) {
            metrics.firstChunkTime = Date.now() - startTime
          }

          metrics.chunkCount++
          metrics.bytesReceived += value.length
          metrics.lastChunkTime = Date.now() - startTime

          controller.enqueue(value)
        }
      } catch (error) {
        controller.error(error)
      } finally {
        reader.releaseLock()
      }
    },
    cancel() {
      reader.releaseLock()
    }
  })
}

// Export for tests
export default {
  parseStreamResponse,
  aggregateStream,
  createStreamingResponse,
  withTimeout,
  monitorStream
}
