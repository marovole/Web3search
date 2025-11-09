import { Hono } from 'hono'
import { getSupabaseClient } from '../lib/supabase'
import type { Env } from '../types/env'

const router = new Hono<{ Bindings: Env }>()

/**
 * 搜索自动完成响应接口
 */
interface AutocompleteResult {
  id: number
  symbol: string
  name: string
  coingecko_id?: string
  categories?: string[]
}

/**
 * 计算搜索匹配分数
 * 分数越高，匹配相关性越强
 */
function calculateMatchScore(
  project: { symbol: string; name: string },
  searchTerm: string
): number {
  const termLower = searchTerm.toLowerCase()
  const symbolLower = project.symbol.toLowerCase()
  const nameLower = project.name.toLowerCase()

  // 完全匹配得分最高
  if (symbolLower === termLower) return 100
  if (nameLower === termLower) return 90

  // 前缀匹配次高
  if (symbolLower.startsWith(termLower)) return 80
  if (nameLower.startsWith(termLower)) return 70

  // 包含匹配最低
  if (symbolLower.includes(termLower)) return 60
  if (nameLower.includes(termLower)) return 50

  return 0
}

/**
 * 搜索自动完成端点
 * GET /search/autocomplete?q={query}&limit={limit}
 *
 * 根据用户输入的查询字符串，返回匹配的项目建议列表
 * 搜索字段：symbol (代币符号), name (项目名称)
 *
 * Query 参数：
 * - q: 搜索查询字符串 (必需)
 * - limit: 返回结果数量限制 (可选，默认 10，最大 50)
 */
router.get('/autocomplete', async (c) => {
  const query = c.req.query('q')
  const limitParam = c.req.query('limit')

  // 验证查询参数
  if (!query || query.trim().length === 0) {
    return c.json(
      {
        error: 'Bad Request',
        message: 'Query parameter "q" is required and cannot be empty',
      },
      400
    )
  }

  // 解析并验证 limit 参数
  const limit = Math.min(
    Math.max(parseInt(limitParam ?? '10', 10) || 10, 1),
    50
  )

  // 转义 PostgreSQL ILIKE 特殊字符 (%, _)
  const searchTerm = query.trim().replace(/[%_]/g, '\\$&')

  try {
    const client = getSupabaseClient(c.env)
    const queryStart = performance.now()

    // 使用 PostgreSQL 的 ILIKE 进行不区分大小写的前缀搜索
    // 搜索策略：
    // 1. symbol 前缀匹配 (可以利用索引 ix_projects_symbol_name)
    // 2. name 前缀匹配 (可以利用索引 ix_projects_symbol_name)
    // 性能优化：使用前缀匹配而非包含匹配，显著提升查询速度
    const { data, error } = await client
      .from('projects')
      .select('id, symbol, name, coingecko_id, categories')
      .or(`symbol.ilike.${searchTerm}%,name.ilike.${searchTerm}%`)
      .limit(limit * 2) // 获取更多结果用于客户端排序

    const queryTime = Math.round(performance.now() - queryStart)

    if (error) {
      console.error('Supabase autocomplete query error:', {
        error: error.message,
        code: error.code,
        details: error.details,
        query: searchTerm,
        queryTime,
      })

      return c.json(
        {
          error: 'Internal Server Error',
          message: 'Failed to fetch autocomplete suggestions',
        },
        500
      )
    }

    // 应用智能排序：按匹配相关性排序
    const sortedData = (data ?? [])
      .map((project) => ({
        ...project,
        matchScore: calculateMatchScore(project, searchTerm),
      }))
      .sort((a, b) => b.matchScore - a.matchScore)
      .slice(0, limit) // 应用用户请求的 limit

    // 转换数据格式
    const results: AutocompleteResult[] = sortedData.map((project) => ({
      id: project.id,
      symbol: project.symbol,
      name: project.name,
      coingecko_id: project.coingecko_id ?? undefined,
      categories: Array.isArray(project.categories) ? project.categories : undefined,
    }))

    // 性能监控日志
    console.log('Search autocomplete performance:', {
      query: searchTerm,
      limit,
      queryTime,
      resultCount: results.length,
      rawResultCount: data?.length ?? 0,
    })

    return c.json(
      {
        query: searchTerm,
        count: results.length,
        results,
      },
      200,
      {
        'Cache-Control': 'public, max-age=300', // 缓存 5 分钟
      }
    )
  } catch (error) {
    console.error('Unexpected autocomplete error:', {
      error: error instanceof Error ? error.message : String(error),
      query: searchTerm,
    })

    return c.json(
      {
        error: 'Internal Server Error',
        message: 'An unexpected error occurred',
      },
      500
    )
  }
})

export default router
