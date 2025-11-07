/**
 * 导出工具函数
 * 支持 CSV 和 JSON 格式导出
 */

export interface ExportableItem {
  [key: string]: any
}

/**
 * 将对象数组转换为 CSV 格式字符串
 */
export function convertToCSV<T extends ExportableItem>(
  data: T[],
  headers?: string[]
): string {
  if (data.length === 0) return ''

  // 如果没有提供 headers，从第一个对象提取所有键
  const keys = headers || Object.keys(data[0])

  // CSV 头部
  const csvHeaders = keys.join(',')

  // CSV 数据行
  const csvRows = data.map(item => {
    return keys.map(key => {
      const value = item[key]
      // 处理嵌套对象和数组
      if (value === null || value === undefined) {
        return ''
      }
      if (typeof value === 'object') {
        return `"${JSON.stringify(value).replace(/"/g, '""')}"`
      }
      // 转义引号和换行符
      const stringValue = String(value).replace(/"/g, '""')
      if (stringValue.includes(',') || stringValue.includes('\n')) {
        return `"${stringValue}"`
      }
      return stringValue
    }).join(',')
  })

  return [csvHeaders, ...csvRows].join('\n')
}

/**
 * 将数据导出为 CSV 文件
 */
export function exportToCSV<T extends ExportableItem>(
  data: T[],
  filename: string,
  headers?: string[]
): void {
  const csv = convertToCSV(data, headers)
  const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${filename}.csv`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

/**
 * 将数据导出为 JSON 文件
 */
export function exportToJSON<T>(
  data: T,
  filename: string,
  pretty: boolean = true
): void {
  const json = pretty
    ? JSON.stringify(data, null, 2)
    : JSON.stringify(data)
  const blob = new Blob([json], { type: 'application/json;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${filename}.json`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

/**
 * GitHub 搜索结果专用的 CSV 导出
 */
export interface GitHubSearchResultForExport {
  id: number
  name: string
  full_name: string
  description: string
  html_url: string
  language: string
  stargazers_count: number
  forks_count: number
  watchers_count: number
  created_at: string
  updated_at: string
  pushed_at: string
  owner_login: string
  owner_avatar_url: string
}

/**
 * 将 GitHub 搜索结果转换为扁平化格式用于 CSV 导出
 */
export function flattenGitHubResults(
  results: Array<{
    id: number
    name: string
    full_name: string
    description: string
    html_url: string
    language: string
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
  }>
): GitHubSearchResultForExport[] {
  return results.map(item => ({
    id: item.id,
    name: item.name,
    full_name: item.full_name,
    description: item.description || '',
    html_url: item.html_url,
    language: item.language || '',
    stargazers_count: item.stargazers_count,
    forks_count: item.forks_count,
    watchers_count: item.watchers_count,
    created_at: item.created_at,
    updated_at: item.updated_at,
    pushed_at: item.pushed_at,
    owner_login: item.owner.login,
    owner_avatar_url: item.owner.avatar_url
  }))
}

/**
 * GitHub 搜索结果 CSV 导出的表头
 */
export const GITHUB_SEARCH_CSV_HEADERS = [
  'ID',
  '名称',
  '完整名称',
  '描述',
  'URL',
  '语言',
  'Stars',
  'Forks',
  'Watchers',
  '创建时间',
  '更新时间',
  '推送时间',
  '所有者',
  '所有者头像'
]

