/**
 * 安全的数值格式化工具函数
 * 提供防御性编程的数值处理，防止 toFixed 等方法的运行时错误
 */

/**
 * 类型守卫：检查值是否为有限数值
 */
export const isFiniteNumber = (value: unknown): value is number => {
  return typeof value === 'number' && Number.isFinite(value)
}

/**
 * 类型守卫：检查值是否可转换为有限数值
 */
export const isConvertibleToNumber = (value: unknown): boolean => {
  if (isFiniteNumber(value)) return true
  if (typeof value === 'string') {
    const normalized = value.replace(/[, $%]/g, '').trim()
    return normalized.length > 0 && Number.isFinite(Number(normalized))
  }
  return false
}

/**
 * 安全转换：将值转换为有限数值或 null
 * 处理 undefined, null, NaN, Infinity, 字符串等多种情况
 */
export const coerceFiniteNumber = (value: unknown): number | null => {
  // 已经是有效的有限数值
  if (isFiniteNumber(value)) return value

  // 字符串转换
  if (typeof value === 'string') {
    const normalized = value.replace(/[, $%]/g, '').trim()
    if (!normalized) return null

    const parsed = Number(normalized)
    return Number.isFinite(parsed) ? parsed : null
  }

  // 其他类型无法转换
  return null
}

/**
 * 安全的 toFixed 格式化
 * 自动处理 undefined, null, NaN, Infinity 等边界情况
 */
export const safeToFixed = (
  value: unknown,
  digits: number = 2,
  fallback: string = 'N/A'
): string => {
  const num = coerceFiniteNumber(value)
  return num !== null ? num.toFixed(digits) : fallback
}

/**
 * 格式化价格
 * 根据价格大小自动选择合适的小数位数
 */
export const formatPrice = (price?: number | string | null): string => {
  const num = coerceFiniteNumber(price)
  if (num === null) return 'N/A'

  if (num < 0.01) return `$${num.toFixed(6)}`
  if (num < 1) return `$${num.toFixed(4)}`
  return `$${num.toFixed(2)}`
}

/**
 * 格式化价格变化（百分比）
 */
export const formatPriceChange = (change?: number | string | null): string => {
  const num = coerceFiniteNumber(change)
  if (num === null) return 'N/A'

  return `${num > 0 ? '+' : ''}${num.toFixed(2)}%`
}

/**
 * 格式化百分比
 */
export const formatPercentage = (
  value: unknown,
  digits: number = 1,
  fallback: string = 'N/A'
): string => {
  const num = coerceFiniteNumber(value)
  return num !== null ? `${num.toFixed(digits)}%` : fallback
}

/**
 * 格式化分数（0-100 或 0-1）
 */
export const formatScore = (
  value: unknown,
  digits: number = 2,
  fallback: string = 'N/A'
): string => {
  const num = coerceFiniteNumber(value)
  return num !== null ? num.toFixed(digits) : fallback
}

/**
 * 格式化时间戳或持续时间（秒）
 */
export const formatDuration = (
  seconds: unknown,
  fallback: string = 'N/A'
): string => {
  const num = coerceFiniteNumber(seconds)
  if (num === null) return fallback

  if (num < 60) return `${num.toFixed(1)}s`
  return `${(num / 60).toFixed(1)}m`
}

/**
 * 格式化文件大小（字节）
 */
export const formatFileSize = (bytes: unknown): string => {
  const num = coerceFiniteNumber(bytes)
  if (num === null || num < 0) return 'N/A'

  if (num === 0) return '0 B'

  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(num) / Math.log(k))

  return `${parseFloat((num / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`
}

/**
 * 格式化市场 cap（大数字）
 */
export const formatMarketCap = (value: unknown): string => {
  const num = coerceFiniteNumber(value)
  if (num === null) return 'N/A'

  if (num >= 1_000_000_000) return `$${(num / 1_000_000_000).toFixed(2)}B`
  if (num >= 1_000_000) return `$${(num / 1_000_000).toFixed(2)}M`
  if (num >= 1_000) return `$${(num / 1_000).toFixed(1)}K`
  return `$${num.toFixed(2)}`
}

/**
 * 判断数值是否有效（可用于过滤）
 */
export const isValidNumber = (value: unknown): boolean => {
  return coerceFiniteNumber(value) !== null
}

/**
 * 过滤数组中的有效数值项
 */
export const filterValidNumbers = <T extends Record<string, any>>(
  items: T[],
  key: keyof T
): T[] => {
  return items.filter((item) => isValidNumber(item[key]))
}
