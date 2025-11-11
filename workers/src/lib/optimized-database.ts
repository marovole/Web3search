/**
 * 优化的数据库查询工具
 * 解决N+1查询问题，提高性能
 */

import { createClient, SupabaseClient } from '@supabase/supabase-js'

interface QueryOptions {
  useCache?: boolean
  cacheTTL?: number
  maxRetries?: number
}

interface CacheEntry<T> {
  data: T
  timestamp: number
  ttl: number
}

class OptimizedDatabase {
  private supabase: SupabaseClient
  private cache: Map<string, CacheEntry<any>> = new Map()
  private defaultOptions: QueryOptions = {
    useCache: true,
    cacheTTL: 5 * 60 * 1000, // 5分钟
    maxRetries: 3
  }

  constructor(supabase: SupabaseClient) {
    this.supabase = supabase
  }

  /**
   * 生成缓存键
   */
  private getCacheKey(table: string, query: any): string {
    return `${table}:${JSON.stringify(query)}`
  }

  /**
   * 检查缓存是否有效
   */
  private isCacheValid<T>(entry: CacheEntry<T>): boolean {
    return Date.now() - entry.timestamp < entry.ttl
  }

  /**
   * 清理过期缓存
   */
  private cleanExpiredCache(): void {
    const now = Date.now()
    for (const [key, entry] of this.cache.entries()) {
      if (now - entry.timestamp >= entry.ttl) {
        this.cache.delete(key)
      }
    }
  }

  /**
   * 优化的对话查询 - 解决N+1问题
   */
  async getConversationWithMessages(
    conversationId: string,
    userId: string,
    options: QueryOptions = {}
  ) {
    const opts = { ...this.defaultOptions, ...options }
    const cacheKey = this.getCacheKey('conversation_with_messages', { 
      conversationId, 
      userId 
    })

    // 检查缓存
    if (opts.useCache) {
      this.cleanExpiredCache()
      const cached = this.cache.get(cacheKey)
      if (cached && this.isCacheValid(cached)) {
        return cached.data
      }
    }

    try {
      // 使用单次查询获取对话和消息，避免N+1问题
      const { data, error } = await this.supabase
        .from('conversations')
        .select(`
          id,
          title,
          created_at,
          updated_at,
          user_id,
          messages (
            id,
            role,
            content,
            created_at,
            metadata
          )
        `)
        .eq('id', conversationId)
        .eq('user_id', userId)
        .single()

      if (error) {
        throw error
      }

      // 缓存结果
      if (opts.useCache) {
        this.cache.set(cacheKey, {
          data,
          timestamp: Date.now(),
          ttl: opts.cacheTTL!
        })
      }

      return data
    } catch (error) {
      console.error('Failed to get conversation with messages:', error)
      throw error
    }
  }

  /**
   * 批量获取用户对话列表
   */
  async getUserConversations(
    userId: string,
    page: number = 1,
    pageSize: number = 20,
    options: QueryOptions = {}
  ) {
    const opts = { ...this.defaultOptions, ...options }
    const cacheKey = this.getCacheKey('user_conversations', { 
      userId, 
      page, 
      pageSize 
    })

    if (opts.useCache) {
      this.cleanExpiredCache()
      const cached = this.cache.get(cacheKey)
      if (cached && this.isCacheValid(cached)) {
        return cached.data
      }
    }

    try {
      const offset = (page - 1) * pageSize

      // 优化的查询：包含最新消息预览和消息计数
      const { data, error } = await this.supabase
        .from('conversations')
        .select(`
          id,
          title,
          created_at,
          updated_at,
          messages_count: messages(count),
          latest_message: messages (
            role,
            content,
            created_at
          ).order(created_at, { ascending: false }).limit(1)
        `)
        .eq('user_id', userId)
        .is('deleted_at', null)
        .order('updated_at', { ascending: false })
        .range(offset, offset + pageSize - 1)

      if (error) {
        throw error
      }

      // 缓存结果
      if (opts.useCache) {
        this.cache.set(cacheKey, {
          data,
          timestamp: Date.now(),
          ttl: opts.cacheTTL!
        })
      }

      return data
    } catch (error) {
      console.error('Failed to get user conversations:', error)
      throw error
    }
  }

  /**
   * 优化的消息历史查询
   */
  async getConversationMessages(
    conversationId: string,
    userId: string,
    limit: number = 50,
    offset: number = 0,
    options: QueryOptions = {}
  ) {
    const opts = { ...this.defaultOptions, ...options }
    const cacheKey = this.getCacheKey('conversation_messages', { 
      conversationId, 
      userId, 
      limit, 
      offset 
    })

    if (opts.useCache) {
      this.cleanExpiredCache()
      const cached = this.cache.get(cacheKey)
      if (cached && this.isCacheValid(cached)) {
        return cached.data
      }
    }

    try {
      // 验证用户权限并获取消息
      const { data, error } = await this.supabase
        .from('messages')
        .select(`
          id,
          role,
          content,
          created_at,
          metadata,
          conversation!inner (
            user_id
          )
        `)
        .eq('conversation_id', conversationId)
        .eq('conversation.user_id', userId)
        .order('created_at', { ascending: true })
        .range(offset, offset + limit - 1)

      if (error) {
        throw error
      }

      // 缓存结果
      if (opts.useCache) {
        this.cache.set(cacheKey, {
          data,
          timestamp: Date.now(),
          ttl: opts.cacheTTL!
        })
      }

      return data
    } catch (error) {
      console.error('Failed to get conversation messages:', error)
      throw error
    }
  }

  /**
   * 批量插入消息
   */
  async insertMessages(messages: Array<{
    conversation_id: string
    role: string
    content: string
    metadata?: any
  }>) {
    try {
      const { data, error } = await this.supabase
        .from('messages')
        .insert(messages)
        .select()

      if (error) {
        throw error
      }

      // 清理相关缓存
      this.invalidateCachePattern('conversation_')
      this.invalidateCachePattern('user_conversations')

      return data
    } catch (error) {
      console.error('Failed to insert messages:', error)
      throw error
    }
  }

  /**
   * 清理匹配模式的缓存
   */
  private invalidateCachePattern(pattern: string): void {
    for (const key of this.cache.keys()) {
      if (key.startsWith(pattern)) {
        this.cache.delete(key)
      }
    }
  }

  /**
   * 手动清理缓存
   */
  clearCache(): void {
    this.cache.clear()
  }

  /**
   * 获取缓存统计信息
   */
  getCacheStats() {
    const now = Date.now()
    let validCount = 0
    let expiredCount = 0

    for (const entry of this.cache.values()) {
      if (now - entry.timestamp < entry.ttl) {
        validCount++
      } else {
        expiredCount++
      }
    }

    return {
      total: this.cache.size,
      valid: validCount,
      expired: expiredCount
    }
  }
}

/**
 * 创建优化的数据库实例
 */
export function createOptimizedDatabase(supabase: SupabaseClient) {
  return new OptimizedDatabase(supabase)
}

export { OptimizedDatabase }