/**
 * Unified Pagination Utilities
 * Eliminates duplicated pagination logic across routes
 */

export interface PaginationParams {
  page?: number
  limit?: number
  maxLimit?: number
}

export interface PaginationMeta {
  page: number
  limit: number
  offset: number
  hasMore: boolean
  total?: number
}

export interface PaginatedResponse<T> {
  data: T[]
  pagination: PaginationMeta
}

const DEFAULT_PAGE = 1
const DEFAULT_LIMIT = 20
const DEFAULT_MAX_LIMIT = 100

export function parsePaginationParams(params: PaginationParams): {
  page: number
  limit: number
  offset: number
} {
  const { maxLimit = DEFAULT_MAX_LIMIT } = params

  const page = Math.max(1, Number(params.page) || DEFAULT_PAGE)
  const limit = Math.min(
    maxLimit,
    Math.max(1, Number(params.limit) || DEFAULT_LIMIT)
  )
  const offset = (page - 1) * limit

  return { page, limit, offset }
}

export function applyPagination<T extends { range: (start: number, end: number) => T }>(
  query: T,
  params: PaginationParams
): { query: T; pagination: { page: number; limit: number; offset: number } } {
  const { page, limit, offset } = parsePaginationParams(params)

  const paginatedQuery = query.range(offset, offset + limit - 1) as T

  return {
    query: paginatedQuery,
    pagination: { page, limit, offset },
  }
}

export function buildPaginationMeta<T>(
  data: T[],
  pagination: { page: number; limit: number; offset: number },
  total?: number
): PaginationMeta {
  return {
    page: pagination.page,
    limit: pagination.limit,
    offset: pagination.offset,
    hasMore: data.length === pagination.limit,
    ...(total !== undefined && { total }),
  }
}

export function paginatedResult<T>(
  data: T[],
  pagination: { page: number; limit: number; offset: number },
  total?: number
): PaginatedResponse<T> {
  return {
    data,
    pagination: buildPaginationMeta(data, pagination, total),
  }
}

export function parseQueryPagination(
  query: URLSearchParams,
  defaults?: { limit?: number; maxLimit?: number }
): PaginationParams {
  return {
    page: Number(query.get('page')) || undefined,
    limit: Number(query.get('limit')) || defaults?.limit,
    maxLimit: defaults?.maxLimit,
  }
}

export default {
  parsePaginationParams,
  applyPagination,
  buildPaginationMeta,
  paginatedResult,
  parseQueryPagination,
}
