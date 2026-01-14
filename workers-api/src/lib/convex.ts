import type { Env } from '../types/env'

export class ConvexHttpClient {
  private baseUrl: string
  private deployKey?: string

  constructor(url: string, deployKey?: string) {
    this.baseUrl = url.replace(/\/$/, '')
    this.deployKey = deployKey
  }

  async query<T>(functionPath: string, args?: Record<string, unknown>): Promise<T> {
    const response = await fetch(`${this.baseUrl}/api/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(this.deployKey && { 'Authorization': `Bearer ${this.deployKey}` })
      },
      body: JSON.stringify({
        path: functionPath,
        args: args || {}
      })
    })

    if (!response.ok) {
      const error = await response.text()
      throw new Error(`Convex query failed: ${error}`)
    }

    const result = await response.json() as { value: T }
    return result.value
  }

  async mutation<T>(functionPath: string, args?: Record<string, unknown>): Promise<T> {
    const response = await fetch(`${this.baseUrl}/api/mutation`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(this.deployKey && { 'Authorization': `Bearer ${this.deployKey}` })
      },
      body: JSON.stringify({
        path: functionPath,
        args: args || {}
      })
    })

    if (!response.ok) {
      const error = await response.text()
      throw new Error(`Convex mutation failed: ${error}`)
    }

    const result = await response.json() as { value: T }
    return result.value
  }
}

let cachedClient: ConvexHttpClient | null = null
let cachedUrl: string | null = null

export function getConvexClient(env: Env): ConvexHttpClient {
  const convexUrl = env.CONVEX_URL

  if (!convexUrl) {
    throw new Error('CONVEX_URL environment variable is not set')
  }

  if (cachedClient && cachedUrl === convexUrl) {
    return cachedClient
  }

  cachedClient = new ConvexHttpClient(convexUrl, env.CONVEX_DEPLOY_KEY)
  cachedUrl = convexUrl
  return cachedClient
}

export async function testDatabaseConnection(env: Env): Promise<boolean> {
  try {
    getConvexClient(env)
    return true
  } catch {
    return false
  }
}
