const OPENROUTER_URL = 'https://openrouter.ai/api/v1/chat/completions'
const DEFAULT_MODEL = 'meta-llama/llama-3.2-3b-instruct:free'
const DEFAULT_TIMEOUT_MS = 30_000
const MAX_RETRIES = 2

export interface OpenRouterMessage {
  role: 'system' | 'user' | 'assistant'
  content: string
}

export interface CallOpenRouterOptions {
  messages: OpenRouterMessage[]
  stream?: boolean
  temperature?: number
  max_tokens?: number
  model?: string
}

export interface CallOpenRouterResult {
  payload?: unknown
  stream?: ReadableStream<Uint8Array>
}

export interface WorkerEnv {
  OPENROUTER_API_KEY: string
}

class OpenRouterError extends Error {
  constructor(public status: number, public payload: unknown) {
    super(`OpenRouter request failed (${status})`)
    this.name = 'OpenRouterError'
  }
}

const buildHeaders = (apiKey: string) => ({
  Authorization: `Bearer ${apiKey}`,
  'HTTP-Referer': 'https://web3search.pages.dev',
  'X-Title': 'Web3search',
  'Content-Type': 'application/json',
})

const safeParseBody = async (response: Response) => {
  try {
    return await response.clone().json()
  } catch {
    try {
      return await response.text()
    } catch {
      return null
    }
  }
}

const delay = (ms: number) =>
  new Promise<void>((resolve) => {
    setTimeout(resolve, ms)
  })

export const callOpenRouter = async (
  env: WorkerEnv,
  opts: CallOpenRouterOptions
): Promise<CallOpenRouterResult> => {
  const apiKey = env.OPENROUTER_API_KEY
  if (!apiKey) {
    throw new Error('OPENROUTER_API_KEY is not configured')
  }

  const headers = buildHeaders(apiKey)
  const body = {
    model: opts.model || DEFAULT_MODEL,
    messages: opts.messages,
    temperature: opts.temperature ?? 0.7,
    max_tokens: opts.max_tokens ?? 600,
    stream: Boolean(opts.stream),
  }

  const execute = async () => {
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), DEFAULT_TIMEOUT_MS)

    try {
      const response = await fetch(OPENROUTER_URL, {
        method: 'POST',
        headers,
        body: JSON.stringify(body),
        signal: controller.signal,
      })

      if (!response.ok) {
        throw new OpenRouterError(response.status, await safeParseBody(response))
      }

      return response
    } finally {
      clearTimeout(timeout)
    }
  }

  let attempt = 0
  while (attempt <= MAX_RETRIES) {
    try {
      const response = await execute()

      if (body.stream) {
        if (!response.body) {
          throw new Error('OpenRouter stream response missing body')
        }
        return { stream: response.body }
      }

      return { payload: await response.json() }
    } catch (error) {
      attempt += 1
      if (attempt > MAX_RETRIES) {
        if (error instanceof OpenRouterError) {
          throw error
        }
        throw error instanceof Error
          ? new Error(`OpenRouter request failed: ${error.message}`)
          : new Error('Unknown OpenRouter error')
      }

      await delay(250 * attempt)
    }
  }

  throw new Error('OpenRouter retry limit reached')
}
