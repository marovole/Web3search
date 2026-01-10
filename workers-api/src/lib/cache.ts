/**
 * KV Cache Utility
 * Provides type-safe caching with TTL support for external API data
 */

import type { Env } from '../types/env'

export interface CacheOptions {
  /** Time-to-live in seconds */
  ttl: number
  /** Optional namespace prefix for cache keys */
  namespace?: string
}

export interface CachedValue<T> {
  data: T
  cachedAt: number
  expiresAt: number
}

/**
 * Default TTL values for different data types (in seconds)
 */
export const CACHE_TTL = {
  /** Price data: 1 minute (frequent updates needed) */
  PRICE: 60,
  /** Market data: 5 minutes */
  MARKET: 300,
  /** User preferences: 10 minutes */
  PREFERENCES: 600,
  /** News data: 15 minutes */
  NEWS: 900,
  /** Token metadata: 1 hour (rarely changes) */
  TOKEN_META: 3600,
  /** Static content: 24 hours */
  STATIC: 86400,
} as const

/**
 * Build a cache key with optional namespace
 */
export function buildCacheKey(key: string, namespace?: string): string {
  const sanitizedKey = key.replace(/[^a-zA-Z0-9_-]/g, '_')
  return namespace ? `${namespace}:${sanitizedKey}` : sanitizedKey
}

/**
 * Get a value from cache
 * Returns null if not found or expired
 */
export async function cacheGet<T>(
  env: Env,
  key: string,
  namespace?: string
): Promise<T | null> {
  if (!env.CACHE) {
    return null
  }

  try {
    const cacheKey = buildCacheKey(key, namespace)
    const cached = await env.CACHE.get(cacheKey, 'json')

    if (!cached) {
      return null
    }

    const { data, expiresAt } = cached as CachedValue<T>

    // Check if expired (double-check since KV TTL might not be exact)
    if (Date.now() > expiresAt) {
      // Async delete, don't await
      env.CACHE.delete(cacheKey).catch(() => {})
      return null
    }

    return data
  } catch (error) {
    console.warn('[Cache] Get error:', error)
    return null
  }
}

/**
 * Set a value in cache with TTL
 */
export async function cacheSet<T>(
  env: Env,
  key: string,
  data: T,
  options: CacheOptions
): Promise<boolean> {
  if (!env.CACHE) {
    return false
  }

  try {
    const cacheKey = buildCacheKey(key, options.namespace)
    const now = Date.now()

    const value: CachedValue<T> = {
      data,
      cachedAt: now,
      expiresAt: now + options.ttl * 1000,
    }

    await env.CACHE.put(cacheKey, JSON.stringify(value), {
      expirationTtl: options.ttl,
    })

    return true
  } catch (error) {
    console.warn('[Cache] Set error:', error)
    return false
  }
}

/**
 * Delete a value from cache
 */
export async function cacheDelete(
  env: Env,
  key: string,
  namespace?: string
): Promise<boolean> {
  if (!env.CACHE) {
    return false
  }

  try {
    const cacheKey = buildCacheKey(key, namespace)
    await env.CACHE.delete(cacheKey)
    return true
  } catch (error) {
    console.warn('[Cache] Delete error:', error)
    return false
  }
}

/**
 * Get or set pattern - fetch from cache or compute and cache
 */
export async function cacheGetOrSet<T>(
  env: Env,
  key: string,
  fetcher: () => Promise<T>,
  options: CacheOptions
): Promise<T> {
  // Try cache first
  const cached = await cacheGet<T>(env, key, options.namespace)
  if (cached !== null) {
    return cached
  }

  // Fetch fresh data
  const data = await fetcher()

  // Cache the result (async, don't block)
  cacheSet(env, key, data, options).catch(() => {})

  return data
}

/**
 * Batch get multiple keys
 */
export async function cacheBatchGet<T>(
  env: Env,
  keys: string[],
  namespace?: string
): Promise<Map<string, T>> {
  const results = new Map<string, T>()

  if (!env.CACHE || keys.length === 0) {
    return results
  }

  // KV doesn't support batch get, so we parallelize
  const promises = keys.map(async (key) => {
    const value = await cacheGet<T>(env, key, namespace)
    if (value !== null) {
      results.set(key, value)
    }
  })

  await Promise.all(promises)
  return results
}

/**
 * Batch set multiple keys
 */
export async function cacheBatchSet<T>(
  env: Env,
  entries: Array<{ key: string; data: T }>,
  options: CacheOptions
): Promise<void> {
  if (!env.CACHE || entries.length === 0) {
    return
  }

  const promises = entries.map(({ key, data }) => cacheSet(env, key, data, options))

  await Promise.all(promises)
}

// Cache namespace constants
export const CACHE_NS = {
  PRICE: 'price',
  MARKET: 'market',
  NEWS: 'news',
  USER: 'user',
  TOKEN: 'token',
} as const
