import type { Env } from '../types/env'

export interface QueryResult<T> {
  data: T | null
  error: { message: string; code?: string } | null
  count?: number
}

export interface QueryBuilder<T = Record<string, unknown>> {
  select: (columns?: string, options?: { count?: 'exact' | 'estimated' | 'planned'; head?: boolean }) => QueryBuilder<T>
  insert: (data: Partial<T> | Partial<T>[]) => QueryBuilder<T>
  update: (data: Partial<T>) => QueryBuilder<T>
  upsert: (data: Partial<T> | Partial<T>[], options?: { onConflict?: string }) => QueryBuilder<T>
  delete: () => QueryBuilder<T>
  eq: (column: string, value: unknown) => QueryBuilder<T>
  neq: (column: string, value: unknown) => QueryBuilder<T>
  gt: (column: string, value: unknown) => QueryBuilder<T>
  gte: (column: string, value: unknown) => QueryBuilder<T>
  lt: (column: string, value: unknown) => QueryBuilder<T>
  lte: (column: string, value: unknown) => QueryBuilder<T>
  in: (column: string, values: unknown[]) => QueryBuilder<T>
  is: (column: string, value: null | boolean) => QueryBuilder<T>
  not: (column: string, operator: string, value: unknown) => QueryBuilder<T>
  or: (filters: string) => QueryBuilder<T>
  order: (column: string, options?: { ascending?: boolean }) => QueryBuilder<T>
  limit: (count: number) => QueryBuilder<T>
  range: (from: number, to: number) => QueryBuilder<T>
  single: () => Promise<QueryResult<T>>
  maybeSingle: () => Promise<QueryResult<T | null>>
  then: <TResult>(onfulfilled?: (value: QueryResult<T[]>) => TResult) => Promise<TResult>
}

interface Filter {
  column: string
  op: string
  value: unknown
}

interface QueryState {
  table: string
  operation: 'select' | 'insert' | 'update' | 'upsert' | 'delete'
  data: unknown
  filters: Filter[]
  orFilters: Filter[]
  orderBy: { column: string; ascending: boolean } | null
  limitCount: number | null
  selectColumns: string
  countOption: 'exact' | 'estimated' | 'planned' | null
}

const TABLE_TO_CONVEX: Record<string, string> = {
  users: 'users',
  user_profiles: 'userProfiles',
  user_quotas: 'userQuotas',
  user_preferences: 'userPreferences',
  conversations: 'conversations',
  messages: 'messages',
  watchlist: 'watchlist',
  holdings: 'holdings',
  notifications: 'notifications',
  push_subscriptions: 'pushSubscriptions',
  agent_tasks: 'agentTasks',
  agent_runs: 'agentRuns',
  deep_research_tasks: 'deepResearchTasks',
  reports: 'reports',
  recommendations: 'recommendations',
  recommendation_history: 'recommendationHistory',
  api_call_logs: 'apiCallLogs',
  projects: 'projects',
}

class ConvexQueryBuilder<T = Record<string, unknown>> implements QueryBuilder<T> {
  private _env: Env
  private _state: QueryState

  constructor(env: Env, table: string) {
    this._env = env
    this._state = {
      table,
      operation: 'select',
      data: null,
      filters: [],
      orFilters: [],
      orderBy: null,
      limitCount: null,
      selectColumns: '*',
      countOption: null,
    }
  }

  private async executeConvexQuery<R>(functionPath: string, args: Record<string, unknown>): Promise<R | null> {
    const convexUrl = this._env.CONVEX_URL
    if (!convexUrl) {
      console.warn('[Convex] CONVEX_URL not configured, returning null')
      return null
    }

    try {
      const response = await fetch(`${convexUrl}/api/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(this._env.CONVEX_DEPLOY_KEY && { 'Authorization': `Convex ${this._env.CONVEX_DEPLOY_KEY}` })
        },
        body: JSON.stringify({
          path: functionPath,
          args,
          format: 'json',
        })
      })

      if (!response.ok) {
        const errorText = await response.text()
        console.error(`[Convex] Query failed: ${errorText}`)
        return null
      }

      const result = await response.json() as { value: R }
      return result.value
    } catch (error) {
      console.error('[Convex] Query error:', error)
      return null
    }
  }

  private async executeConvexMutation<R>(functionPath: string, args: Record<string, unknown>): Promise<R | null> {
    const convexUrl = this._env.CONVEX_URL
    if (!convexUrl) {
      console.warn('[Convex] CONVEX_URL not configured, returning null')
      return null
    }

    try {
      const response = await fetch(`${convexUrl}/api/mutation`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(this._env.CONVEX_DEPLOY_KEY && { 'Authorization': `Convex ${this._env.CONVEX_DEPLOY_KEY}` })
        },
        body: JSON.stringify({
          path: functionPath,
          args,
          format: 'json',
        })
      })

      if (!response.ok) {
        const errorText = await response.text()
        console.error(`[Convex] Mutation failed: ${errorText}`)
        return null
      }

      const result = await response.json() as { value: R }
      return result.value
    } catch (error) {
      console.error('[Convex] Mutation error:', error)
      return null
    }
  }

  private getConvexTable(): string {
    return TABLE_TO_CONVEX[this._state.table] || this._state.table
  }

  private buildQueryArgs(): Record<string, unknown> {
    const args: Record<string, unknown> = {
      table: this.getConvexTable(),
    }

    if (this._state.filters.length > 0) {
      args.filters = this._state.filters.map(f => ({
        field: f.column,
        op: f.op,
        value: f.value,
      }))
    }

    if (this._state.orFilters.length > 0) {
      args.orFilters = this._state.orFilters.map(f => ({
        field: f.column,
        op: f.op,
        value: f.value,
      }))
    }

    if (this._state.orderBy) {
      args.orderBy = {
        field: this._state.orderBy.column,
        order: this._state.orderBy.ascending ? 'asc' : 'desc',
      }
    }

    if (this._state.limitCount) {
      args.limit = this._state.limitCount
    }

    if (this._state.selectColumns !== '*') {
      args.fields = this._state.selectColumns.split(',').map(s => s.trim())
    }

    return args
  }

  select(columns?: string, options?: { count?: 'exact' | 'estimated' | 'planned'; head?: boolean }): QueryBuilder<T> {
    this._state.operation = 'select'
    this._state.selectColumns = columns || '*'
    if (options?.count) {
      this._state.countOption = options.count
    }
    return this
  }

  insert(data: Partial<T> | Partial<T>[]): QueryBuilder<T> {
    this._state.operation = 'insert'
    this._state.data = data
    return this
  }

  update(data: Partial<T>): QueryBuilder<T> {
    this._state.operation = 'update'
    this._state.data = data
    return this
  }

  upsert(data: Partial<T> | Partial<T>[], _options?: { onConflict?: string }): QueryBuilder<T> {
    this._state.operation = 'upsert'
    this._state.data = data
    return this
  }

  delete(): QueryBuilder<T> {
    this._state.operation = 'delete'
    return this
  }

  eq(column: string, value: unknown): QueryBuilder<T> {
    this._state.filters.push({ column, op: 'eq', value })
    return this
  }

  neq(column: string, value: unknown): QueryBuilder<T> {
    this._state.filters.push({ column, op: 'neq', value })
    return this
  }

  gt(column: string, value: unknown): QueryBuilder<T> {
    this._state.filters.push({ column, op: 'gt', value })
    return this
  }

  gte(column: string, value: unknown): QueryBuilder<T> {
    this._state.filters.push({ column, op: 'gte', value })
    return this
  }

  lt(column: string, value: unknown): QueryBuilder<T> {
    this._state.filters.push({ column, op: 'lt', value })
    return this
  }

  lte(column: string, value: unknown): QueryBuilder<T> {
    this._state.filters.push({ column, op: 'lte', value })
    return this
  }

  in(column: string, values: unknown[]): QueryBuilder<T> {
    this._state.filters.push({ column, op: 'in', value: values })
    return this
  }

  is(column: string, value: null | boolean): QueryBuilder<T> {
    this._state.filters.push({ column, op: 'is', value })
    return this
  }

  not(column: string, operator: string, value: unknown): QueryBuilder<T> {
    this._state.filters.push({ column, op: `not.${operator}`, value })
    return this
  }

  or(filters: string): QueryBuilder<T> {
    const orFilters = this.parseOrFilters(filters)
    this._state.orFilters.push(...orFilters)
    return this
  }

  private parseOrFilters(filterString: string): Filter[] {
    const filters: Filter[] = []
    const parts = filterString.split(',')
    
    for (const part of parts) {
      const ilikeSplit = part.split('.ilike.')
      if (ilikeSplit.length === 2) {
        filters.push({
          column: ilikeSplit[0].trim(),
          op: 'ilike',
          value: ilikeSplit[1].trim(),
        })
        continue
      }
      
      const eqSplit = part.split('.eq.')
      if (eqSplit.length === 2) {
        filters.push({
          column: eqSplit[0].trim(),
          op: 'eq',
          value: eqSplit[1].trim(),
        })
      }
    }
    
    return filters
  }

  order(column: string, options?: { ascending?: boolean }): QueryBuilder<T> {
    this._state.orderBy = { column, ascending: options?.ascending ?? true }
    return this
  }

  limit(count: number): QueryBuilder<T> {
    this._state.limitCount = count
    return this
  }

  range(_from: number, _to: number): QueryBuilder<T> {
    return this
  }

  async single(): Promise<QueryResult<T>> {
    const table = this.getConvexTable()
    
    if (this._state.operation === 'select') {
      const args = this.buildQueryArgs()
      args.limit = 1
      const result = await this.executeConvexQuery<T[]>(`${table}:list`, args)
      if (result && result.length > 0) {
        return { data: result[0], error: null }
      }
      return { data: null, error: null }
    }

    if (this._state.operation === 'insert') {
      const insertArgs = {
        ...(this._state.data as Record<string, unknown>),
      }
      const result = await this.executeConvexMutation<T>(`${table}:create`, insertArgs)
      return { data: result, error: null }
    }

    if (this._state.operation === 'update') {
      const idFilter = this._state.filters.find(f => f.column === 'id' && f.op === 'eq')
      if (idFilter) {
        const updateArgs = {
          id: idFilter.value,
          ...(this._state.data as Record<string, unknown>),
        }
        const result = await this.executeConvexMutation<T>(`${table}:update`, updateArgs)
        return { data: result, error: null }
      }
    }

    return { data: null, error: null }
  }

  async maybeSingle(): Promise<QueryResult<T | null>> {
    return this.single()
  }

  async then<TResult>(
    onfulfilled?: (value: QueryResult<T[]>) => TResult
  ): Promise<TResult> {
    const table = this.getConvexTable()
    
    if (this._state.operation === 'select') {
      const args = this.buildQueryArgs()
      const result = await this.executeConvexQuery<T[]>(`${table}:list`, args)
      const queryResult: QueryResult<T[]> = { 
        data: result || [], 
        error: null, 
        count: result?.length || 0 
      }
      return onfulfilled ? onfulfilled(queryResult) : (queryResult as unknown as TResult)
    }

    if (this._state.operation === 'insert') {
      const dataArray = Array.isArray(this._state.data) ? this._state.data : [this._state.data]
      const results: T[] = []
      for (const item of dataArray) {
        const result = await this.executeConvexMutation<T>(`${table}:create`, item as Record<string, unknown>)
        if (result) results.push(result)
      }
      const queryResult: QueryResult<T[]> = { data: results, error: null }
      return onfulfilled ? onfulfilled(queryResult) : (queryResult as unknown as TResult)
    }

    if (this._state.operation === 'update') {
      const idFilter = this._state.filters.find(f => f.column === 'id' && f.op === 'eq')
      if (idFilter) {
        const updateArgs = {
          id: idFilter.value,
          ...(this._state.data as Record<string, unknown>),
        }
        const result = await this.executeConvexMutation<T>(`${table}:update`, updateArgs)
        const queryResult: QueryResult<T[]> = { data: result ? [result] : [], error: null }
        return onfulfilled ? onfulfilled(queryResult) : (queryResult as unknown as TResult)
      }
    }

    if (this._state.operation === 'delete') {
      const idFilter = this._state.filters.find(f => f.column === 'id' && f.op === 'eq')
      if (idFilter) {
        await this.executeConvexMutation(`${table}:remove`, { id: idFilter.value })
      }
      const queryResult: QueryResult<T[]> = { data: [], error: null }
      return onfulfilled ? onfulfilled(queryResult) : (queryResult as unknown as TResult)
    }

    const queryResult: QueryResult<T[]> = { data: [], error: null, count: 0 }
    return onfulfilled ? onfulfilled(queryResult) : (queryResult as unknown as TResult)
  }
}

export interface SupabaseClient {
  from: <T = Record<string, unknown>>(table: string) => QueryBuilder<T>
  rpc: <T = unknown>(functionName: string, params?: Record<string, unknown>) => Promise<QueryResult<T>>
  auth: {
    getUser: (token: string) => Promise<{ data: { user: unknown } | null; error: unknown }>
  }
}

class ConvexSupabaseAdapter implements SupabaseClient {
  private _env: Env

  constructor(env: Env) {
    this._env = env
  }

  from<T = Record<string, unknown>>(table: string): QueryBuilder<T> {
    return new ConvexQueryBuilder<T>(this._env, table)
  }

  async rpc<T = unknown>(functionName: string, params?: Record<string, unknown>): Promise<QueryResult<T>> {
    const convexUrl = this._env.CONVEX_URL
    if (!convexUrl) {
      console.warn('[Convex] CONVEX_URL not configured')
      return { data: null, error: null }
    }

    try {
      const response = await fetch(`${convexUrl}/api/mutation`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(this._env.CONVEX_DEPLOY_KEY && { 'Authorization': `Convex ${this._env.CONVEX_DEPLOY_KEY}` })
        },
        body: JSON.stringify({
          path: `rpc:${functionName}`,
          args: params || {},
          format: 'json',
        })
      })

      if (!response.ok) {
        const errorText = await response.text()
        return { data: null, error: { message: errorText } }
      }

      const result = await response.json() as { value: T }
      return { data: result.value, error: null }
    } catch (error) {
      return { data: null, error: { message: String(error) } }
    }
  }

  get auth() {
    return {
      getUser: async (token: string) => {
        const convexUrl = this._env.CONVEX_URL
        if (!convexUrl) {
          return { data: null, error: null }
        }

        try {
          const response = await fetch(`${convexUrl}/api/query`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`,
            },
            body: JSON.stringify({
              path: 'users:getByToken',
              args: { token },
              format: 'json',
            })
          })

          if (!response.ok) {
            return { data: null, error: { message: 'Auth failed' } }
          }

          const result = await response.json() as { value: unknown }
          return { data: { user: result.value }, error: null }
        } catch (error) {
          return { data: null, error: { message: String(error) } }
        }
      },
    }
  }
}

let cachedClient: ConvexSupabaseAdapter | null = null
let cachedEnv: Env | null = null

export function getSupabaseClient(env: Env, _useServiceRole: boolean = false): SupabaseClient {
  if (cachedClient && cachedEnv === env) {
    return cachedClient
  }
  cachedClient = new ConvexSupabaseAdapter(env)
  cachedEnv = env
  return cachedClient
}

export function createSupabaseClient(env: Env, _useServiceRole: boolean = false): SupabaseClient {
  return new ConvexSupabaseAdapter(env)
}

export async function testDatabaseConnection(env: Env): Promise<boolean> {
  if (!env.CONVEX_URL) {
    return false
  }
  
  try {
    const response = await fetch(`${env.CONVEX_URL}/api/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        path: 'users:list',
        args: { limit: 1 },
        format: 'json',
      })
    })
    return response.ok
  } catch {
    return false
  }
}

export type { Env }
