import type { Env } from '../types/env'

interface ConvexHttpResult<T> {
  data: T | null
  error: { code: string; message: string } | null
}

function getConvexSiteUrl(env: Env): string | null {
  const convexUrl = env.CONVEX_URL
  if (!convexUrl) return null
  return convexUrl.replace('.convex.cloud', '.convex.site')
}

export async function createDeepResearchTask(
  env: Env,
  taskData: {
    externalId: string
    query: string
    researchDepth: string
    maxSources: number
    focusAreas: string[]
    modelId: string
    modelProvider: string
    clientSessionId?: string | null
    metadata?: Record<string, unknown>
    tags?: string[]
  }
): Promise<ConvexHttpResult<{ task_id: string; internal_id: string }>> {
  const convexUrl = getConvexSiteUrl(env)
  if (!convexUrl) {
    return { data: null, error: { code: 'CONFIG_ERROR', message: 'CONVEX_URL not configured' } }
  }

  try {
    const requestBody: Record<string, unknown> = {
      externalId: taskData.externalId,
      query: taskData.query,
      researchDepth: taskData.researchDepth,
      maxSources: taskData.maxSources,
      focusAreas: taskData.focusAreas,
      modelId: taskData.modelId,
      metadata: taskData.metadata || {},
    }
    
    if (taskData.clientSessionId) {
      requestBody.clientSessionId = taskData.clientSessionId
    }
    
    const response = await fetch(`${convexUrl}/api/v1/deep-research`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestBody),
    })

    if (!response.ok) {
      const errorBody = await response.text()
      console.error('[Convex HTTP] Create task failed:', errorBody)
      return { data: null, error: { code: 'CREATE_FAILED', message: errorBody } }
    }

    const result = await response.json() as { task_id: string; internal_id: string }
    return { data: result, error: null }
  } catch (error) {
    console.error('[Convex HTTP] Create task error:', error)
    return { data: null, error: { code: 'NETWORK_ERROR', message: error instanceof Error ? error.message : 'Unknown error' } }
  }
}

export async function getDeepResearchTask(
  env: Env,
  externalId: string
): Promise<ConvexHttpResult<Record<string, unknown> | null>> {
  const convexUrl = getConvexSiteUrl(env)
  if (!convexUrl) {
    return { data: null, error: { code: 'CONFIG_ERROR', message: 'CONVEX_URL not configured' } }
  }

  try {
    const response = await fetch(`${convexUrl}/api/v1/deep-research/by-external-id?id=${encodeURIComponent(externalId)}`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    })

    if (!response.ok) {
      const errorBody = await response.text()
      console.error('[Convex HTTP] Get task failed:', errorBody)
      return { data: null, error: { code: 'FETCH_FAILED', message: errorBody } }
    }

    const result = await response.json() as { task: Record<string, unknown> | null }
    return { data: result.task, error: null }
  } catch (error) {
    console.error('[Convex HTTP] Get task error:', error)
    return { data: null, error: { code: 'NETWORK_ERROR', message: error instanceof Error ? error.message : 'Unknown error' } }
  }
}

export async function updateDeepResearchTask(
  env: Env,
  externalId: string,
  updates: {
    status?: string
    progressPercent?: number
    currentStep?: string
    stepsCompleted?: number
    result?: Record<string, unknown>
    error?: string
  }
): Promise<ConvexHttpResult<{ success: boolean }>> {
  const convexUrl = getConvexSiteUrl(env)
  if (!convexUrl) {
    return { data: null, error: { code: 'CONFIG_ERROR', message: 'CONVEX_URL not configured' } }
  }

  try {
    const response = await fetch(`${convexUrl}/api/v1/deep-research/update`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ externalId, ...updates }),
    })

    if (!response.ok) {
      const errorBody = await response.text()
      console.error('[Convex HTTP] Update task failed:', errorBody)
      return { data: null, error: { code: 'UPDATE_FAILED', message: errorBody } }
    }

    const result = await response.json() as { success: boolean }
    return { data: result, error: null }
  } catch (error) {
    console.error('[Convex HTTP] Update task error:', error)
    return { data: null, error: { code: 'NETWORK_ERROR', message: error instanceof Error ? error.message : 'Unknown error' } }
  }
}

export async function searchProjects(
  env: Env,
  query: string,
  limit = 10
): Promise<ConvexHttpResult<{ query: string; count: number; results: Array<{ symbol: string; name: string; coingecko_id?: string; description?: string }> }>> {
  const convexUrl = getConvexSiteUrl(env)
  if (!convexUrl) {
    return { data: null, error: { code: 'CONFIG_ERROR', message: 'CONVEX_URL not configured' } }
  }

  try {
    const url = `${convexUrl}/api/v1/projects/search?q=${encodeURIComponent(query)}&limit=${limit}`
    const response = await fetch(url, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    })

    if (!response.ok) {
      const errorBody = await response.text()
      console.error('[Convex HTTP] Search projects failed:', errorBody)
      return { data: null, error: { code: 'SEARCH_FAILED', message: errorBody } }
    }

    const result = await response.json() as { query: string; count: number; results: Array<{ symbol: string; name: string; coingecko_id?: string; description?: string }> }
    return { data: result, error: null }
  } catch (error) {
    console.error('[Convex HTTP] Search projects error:', error)
    return { data: null, error: { code: 'NETWORK_ERROR', message: error instanceof Error ? error.message : 'Unknown error' } }
  }
}
