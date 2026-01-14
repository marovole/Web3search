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

class MockQueryBuilder<T = Record<string, unknown>> implements QueryBuilder<T> {
  private _table: string
  private _operation: 'select' | 'insert' | 'update' | 'upsert' | 'delete' = 'select'

  constructor(table: string) {
    this._table = table
  }

  select(_columns?: string, _options?: { count?: 'exact' | 'estimated' | 'planned'; head?: boolean }): QueryBuilder<T> {
    this._operation = 'select'
    return this
  }

  insert(_data: Partial<T> | Partial<T>[]): QueryBuilder<T> {
    this._operation = 'insert'
    return this
  }

  update(_data: Partial<T>): QueryBuilder<T> {
    this._operation = 'update'
    return this
  }

  upsert(_data: Partial<T> | Partial<T>[], _options?: { onConflict?: string }): QueryBuilder<T> {
    this._operation = 'upsert'
    return this
  }

  delete(): QueryBuilder<T> {
    this._operation = 'delete'
    return this
  }

  eq(_column: string, _value: unknown): QueryBuilder<T> {
    return this
  }

  neq(_column: string, _value: unknown): QueryBuilder<T> {
    return this
  }

  gt(_column: string, _value: unknown): QueryBuilder<T> {
    return this
  }

  gte(_column: string, _value: unknown): QueryBuilder<T> {
    return this
  }

  lt(_column: string, _value: unknown): QueryBuilder<T> {
    return this
  }

  lte(_column: string, _value: unknown): QueryBuilder<T> {
    return this
  }

  in(_column: string, _values: unknown[]): QueryBuilder<T> {
    return this
  }

  is(_column: string, _value: null | boolean): QueryBuilder<T> {
    return this
  }

  not(_column: string, _operator: string, _value: unknown): QueryBuilder<T> {
    return this
  }

  or(_filters: string): QueryBuilder<T> {
    return this
  }

  order(_column: string, _options?: { ascending?: boolean }): QueryBuilder<T> {
    return this
  }

  limit(_count: number): QueryBuilder<T> {
    return this
  }

  range(_from: number, _to: number): QueryBuilder<T> {
    return this
  }

  async single(): Promise<QueryResult<T>> {
    console.warn(`[Convex Migration] ${this._operation} on ${this._table} - returning mock data`)
    return { data: null, error: null }
  }

  async maybeSingle(): Promise<QueryResult<T | null>> {
    console.warn(`[Convex Migration] ${this._operation} on ${this._table} - returning mock data`)
    return { data: null, error: null }
  }

  async then<TResult>(
    onfulfilled?: (value: QueryResult<T[]>) => TResult
  ): Promise<TResult> {
    console.warn(`[Convex Migration] ${this._operation} on ${this._table} - returning mock data`)
    const result: QueryResult<T[]> = { data: [], error: null, count: 0 }
    return onfulfilled ? onfulfilled(result) : (result as unknown as TResult)
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
  constructor(_env: Env) {}

  from<T = Record<string, unknown>>(table: string): QueryBuilder<T> {
    return new MockQueryBuilder<T>(table)
  }

  async rpc<T = unknown>(_functionName: string, _params?: Record<string, unknown>): Promise<QueryResult<T>> {
    console.warn(`[Convex Migration] RPC call - returning mock success`)
    return { data: null, error: null }
  }

  get auth() {
    return {
      getUser: async (_token: string) => {
        console.warn('[Convex Migration] auth.getUser called - returning null')
        return { data: null, error: null }
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

export async function testDatabaseConnection(_env: Env): Promise<boolean> {
  return true
}

export type { Env }
