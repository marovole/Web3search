import type { DeepResearchSSEEvent, ToolCallEvent, ThinkingEvent, ISSEEmitter } from './types'

export class SSEEmitter implements ISSEEmitter {
  private encoder: TextEncoder
  private controller: ReadableStreamDefaultController<Uint8Array>
  private cancelled = false

  constructor(controller: ReadableStreamDefaultController<Uint8Array>) {
    this.encoder = new TextEncoder()
    this.controller = controller
  }

  emit(event: DeepResearchSSEEvent): void {
    if (this.cancelled) return

    try {
      const enrichedEvent = {
        ...event,
        timestamp: event.timestamp ?? new Date().toISOString(),
      }
      const data = JSON.stringify(enrichedEvent)
      this.controller.enqueue(this.encoder.encode(`data: ${data}\n\n`))
    } catch (error) {
      if (!this.cancelled) {
        console.warn('Failed to emit SSE event:', error)
      }
    }
  }

  emitToolCall(event: Omit<ToolCallEvent, 'type'>): void {
    this.emit({ type: 'tool_call', ...event } as DeepResearchSSEEvent)
  }

  emitThinking(event: Omit<ThinkingEvent, 'type'>): void {
    this.emit({ type: 'thinking', ...event } as DeepResearchSSEEvent)
  }

  emitProgress(stage: string, content: string): void {
    this.emit({ type: 'progress', stage, content })
  }

  emitContent(section: string, content: string): void {
    this.emit({ type: 'content', section, content })
  }

  emitComplete(content: string, sessionId: string): void {
    this.emit({ type: 'complete', content, session_id: sessionId })
  }

  emitError(content: string): void {
    this.emit({ type: 'error', content })
  }

  sendKeepAlive(): void {
    if (this.cancelled) return
    try {
      this.controller.enqueue(this.encoder.encode(': keep-alive\n\n'))
    } catch {
      // Silently ignore if controller is closed
    }
  }

  sendDone(cacheHit = false): void {
    if (this.cancelled) return
    try {
      const data = cacheHit 
        ? '{"status":"completed","cache_hit":true}' 
        : '{"status":"completed"}'
      this.controller.enqueue(this.encoder.encode(`event: done\ndata: ${data}\n\n`))
    } catch {
      // Silently ignore if controller is closed
    }
  }

  sendErrorEvent(errorMessage: string): void {
    if (this.cancelled) return
    try {
      this.controller.enqueue(
        this.encoder.encode(`event: error\ndata: ${JSON.stringify({ error: errorMessage })}\n\n`)
      )
    } catch {
      // Silently ignore if controller is closed
    }
  }

  cancel(): void {
    this.cancelled = true
  }

  isCancelled(): boolean {
    return this.cancelled
  }

  close(): void {
    try {
      this.controller.close()
    } catch {
      // Silently ignore if already closed
    }
  }
}

export function createSSEResponse(
  streamHandler: (emitter: SSEEmitter, controller: ReadableStreamDefaultController<Uint8Array>) => Promise<void>,
  onCancel?: () => void
): Response {
  const stream = new ReadableStream<Uint8Array>({
    start(controller) {
      const emitter = new SSEEmitter(controller)
      
      streamHandler(emitter, controller).catch((error) => {
        console.error('SSE stream handler error:', error)
        if (!emitter.isCancelled()) {
          emitter.emitError(error instanceof Error ? error.message : 'Stream error')
          emitter.close()
        }
      })
    },
    cancel() {
      onCancel?.()
    },
  })

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
    },
  })
}

export function createHeartbeatInterval(emitter: SSEEmitter, intervalMs = 15_000): NodeJS.Timeout {
  return setInterval(() => {
    if (!emitter.isCancelled()) {
      emitter.sendKeepAlive()
    }
  }, intervalMs)
}
