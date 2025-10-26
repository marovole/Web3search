/**
 * 项目监控列表管理 Hook
 * 使用 localStorage 持久化存储
 */

import { useState, useEffect, useCallback } from 'react'
import type { WatchlistItem, UseWatchlistReturn } from '../types/watchlist'

const STORAGE_KEY = 'web3search_watchlist'
const MAX_WATCHLIST_ITEMS = 20

export const useWatchlist = (): UseWatchlistReturn => {
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([])

  // 从 localStorage 加载监控列表
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        const parsed = JSON.parse(stored) as WatchlistItem[]
        // 按添加时间倒序排序
        const sorted = parsed.sort(
          (a, b) => new Date(b.addedAt).getTime() - new Date(a.addedAt).getTime()
        )
        setWatchlist(sorted)
      }
    } catch (error) {
      console.error('Failed to load watchlist:', error)
    }
  }, [])

  // 保存监控列表到 localStorage
  const saveWatchlist = useCallback((items: WatchlistItem[]) => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(items))
      setWatchlist(items)
    } catch (error) {
      console.error('Failed to save watchlist:', error)
    }
  }, [])

  // 添加到监控列表
  const addToWatchlist = useCallback(
    (item: Omit<WatchlistItem, 'addedAt'>) => {
      // 检查是否已存在
      const exists = watchlist.some((w) => w.symbol === item.symbol)
      if (exists) {
        console.warn(`${item.symbol} is already in watchlist`)
        return
      }

      // 检查是否超过最大数量
      if (watchlist.length >= MAX_WATCHLIST_ITEMS) {
        console.warn(`Watchlist is full (max ${MAX_WATCHLIST_ITEMS} items)`)
        return
      }

      const newItem: WatchlistItem = {
        ...item,
        addedAt: new Date().toISOString(),
      }

      const newWatchlist = [newItem, ...watchlist]
      saveWatchlist(newWatchlist)
    },
    [watchlist, saveWatchlist]
  )

  // 从监控列表移除
  const removeFromWatchlist = useCallback(
    (symbol: string) => {
      const newWatchlist = watchlist.filter((item) => item.symbol !== symbol)
      saveWatchlist(newWatchlist)
    },
    [watchlist, saveWatchlist]
  )

  // 检查是否在监控列表中
  const isInWatchlist = useCallback(
    (symbol: string): boolean => {
      return watchlist.some((item) => item.symbol === symbol)
    },
    [watchlist]
  )

  // 清空监控列表
  const clearWatchlist = useCallback(() => {
    saveWatchlist([])
  }, [saveWatchlist])

  return {
    watchlist,
    addToWatchlist,
    removeFromWatchlist,
    isInWatchlist,
    clearWatchlist,
  }
}
