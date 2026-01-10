/**
 * GitHub Search Routes
 * Search GitHub repositories, commits, and issues with AI-generated summaries
 */

import { Hono } from 'hono'
import type { Env } from '../types/env'

const github = new Hono<{ Bindings: Env }>()

interface GitHubSearchResult {
  id: number
  name: string
  full_name: string
  description: string | null
  html_url: string
  language: string | null
  stargazers_count: number
  forks_count: number
  watchers_count: number
  created_at: string
  updated_at: string
  pushed_at: string
  owner: {
    login: string
    avatar_url: string
  }
}

interface GitHubAPIResponse {
  total_count: number
  incomplete_results: boolean
  items: GitHubSearchResult[]
}

/**
 * Generate AI summary for search results
 */
function generateSummary(items: GitHubSearchResult[], query: string, searchType: string) {
  const languages: Record<string, number> = {}
  const topRepos: string[] = []

  items.forEach((item) => {
    if (item.language) {
      languages[item.language] = (languages[item.language] || 0) + 1
    }
    if (topRepos.length < 5 && item.stargazers_count > 100) {
      topRepos.push(item.full_name)
    }
  })

  const languageList = Object.entries(languages)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)
    .map(([name, count]) => ({ name, count }))

  const keyInsights: string[] = []

  if (items.length > 0) {
    keyInsights.push(`找到 ${items.length} 个与 "${query}" 相关的${searchType === 'repositories' ? '仓库' : searchType === 'commits' ? '提交' : '议题'}`)

    if (languageList.length > 0) {
      keyInsights.push(`主要编程语言: ${languageList.slice(0, 3).map(l => l.name).join(', ')}`)
    }

    const avgStars = Math.round(items.reduce((sum, item) => sum + item.stargazers_count, 0) / items.length)
    if (avgStars > 0) {
      keyInsights.push(`平均 Star 数: ${avgStars}`)
    }

    if (topRepos.length > 0) {
      keyInsights.push(`热门项目: ${topRepos.slice(0, 3).join(', ')}`)
    }
  }

  return {
    total_results: items.length,
    result_types: { [searchType]: items.length },
    key_insights: keyInsights,
    top_repositories: topRepos,
    languages: languageList,
  }
}

/**
 * GET /search
 * Search GitHub repositories, commits, or issues
 */
github.get('/search', async (c) => {
  const query = c.req.query('query')?.trim()
  const searchType = c.req.query('search_type') || 'repositories'
  const page = parseInt(c.req.query('page') || '1', 10)
  const perPage = Math.min(parseInt(c.req.query('per_page') || '10', 10), 100)

  // Optional filters
  const language = c.req.query('language')
  const starsMin = c.req.query('stars_min')
  const starsMax = c.req.query('stars_max')
  const updatedAfter = c.req.query('updated_after')
  const sort = c.req.query('sort') || 'best-match'

  if (!query) {
    return c.json(
      {
        success: false,
        error: {
          code: 'MISSING_QUERY',
          message: 'Query parameter is required',
        },
      },
      400
    )
  }

  const startTime = Date.now()

  try {
    // Build GitHub search query
    let searchQuery = query

    if (language) {
      const langs = language.split(',').map(l => `language:${l.trim()}`).join(' ')
      searchQuery += ` ${langs}`
    }

    if (starsMin || starsMax) {
      const min = starsMin || '0'
      const max = starsMax || '*'
      searchQuery += ` stars:${min}..${max}`
    }

    if (updatedAfter) {
      searchQuery += ` pushed:>=${updatedAfter}`
    }

    // Map search type to GitHub API endpoint
    const typeMap: Record<string, string> = {
      repositories: 'repositories',
      commits: 'commits',
      issues: 'issues',
    }
    const apiType = typeMap[searchType] || 'repositories'

    // Map sort parameter
    const sortMap: Record<string, string> = {
      'relevance': '',
      'stars': 'stars',
      'forks': 'forks',
      'updated': 'updated',
    }
    const sortParam = sortMap[sort] || ''

    // Build GitHub API URL
    const githubUrl = new URL(`https://api.github.com/search/${apiType}`)
    githubUrl.searchParams.append('q', searchQuery)
    githubUrl.searchParams.append('page', page.toString())
    githubUrl.searchParams.append('per_page', perPage.toString())
    if (sortParam) {
      githubUrl.searchParams.append('sort', sortParam)
      githubUrl.searchParams.append('order', 'desc')
    }

    // Prepare headers
    const headers: Record<string, string> = {
      'Accept': 'application/vnd.github.v3+json',
      'User-Agent': 'Web3search-API/1.0',
    }

    // Use GitHub token if available
    if (c.env.GITHUB_TOKEN) {
      headers['Authorization'] = `Bearer ${c.env.GITHUB_TOKEN}`
    }

    const response = await fetch(githubUrl.toString(), { headers })

    if (!response.ok) {
      const errorText = await response.text()
      console.error('GitHub API error:', response.status, errorText)

      if (response.status === 403) {
        return c.json(
          {
            success: false,
            error: {
              code: 'RATE_LIMITED',
              message: 'GitHub API rate limit exceeded. Please try again later.',
            },
          },
          429
        )
      }

      return c.json(
        {
          success: false,
          error: {
            code: 'GITHUB_API_ERROR',
            message: `GitHub API error: ${response.statusText}`,
          },
        },
        response.status as 400 | 401 | 403 | 404 | 500
      )
    }

    const data: GitHubAPIResponse = await response.json()
    const executionTime = Date.now() - startTime

    // Generate AI summary
    const summary = generateSummary(data.items, query, searchType)

    return c.json({
      success: true,
      data: {
        total_count: data.total_count,
        items: data.items,
        page,
        per_page: perPage,
      },
      summary,
      query,
      search_type: searchType,
      execution_time_ms: executionTime,
    })
  } catch (error) {
    console.error('GitHub search error:', error)
    return c.json(
      {
        success: false,
        error: {
          code: 'INTERNAL_ERROR',
          message: error instanceof Error ? error.message : 'An internal error occurred',
        },
      },
      500
    )
  }
})

export default github
