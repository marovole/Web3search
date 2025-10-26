/**
 * 报告历史记录管理 Hook
 * 使用 localStorage 持久化存储
 */

import { useState, useEffect, useCallback } from 'react'
import type { ReportHistoryItem, UseReportHistoryReturn } from '../types/history'

const STORAGE_KEY = 'web3search_report_history'
const MAX_HISTORY_ITEMS = 50

export const useReportHistory = (): UseReportHistoryReturn => {
  const [history, setHistory] = useState<ReportHistoryItem[]>([])

  // 从 localStorage 加载历史记录
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        const parsed = JSON.parse(stored) as ReportHistoryItem[]
        // 按时间倒序排序
        const sorted = parsed.sort(
          (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
        )
        setHistory(sorted)
      }
    } catch (error) {
      console.error('Failed to load report history:', error)
    }
  }, [])

  // 保存历史记录到 localStorage
  const saveHistory = useCallback((items: ReportHistoryItem[]) => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(items))
      setHistory(items)
    } catch (error) {
      console.error('Failed to save report history:', error)
    }
  }, [])

  // 添加历史记录
  const addToHistory = useCallback(
    (item: Omit<ReportHistoryItem, 'timestamp'>) => {
      const newItem: ReportHistoryItem = {
        ...item,
        timestamp: new Date().toISOString(),
      }

      // 检查是否已存在相同的记录（相同symbol和reportType）
      const existingIndex = history.findIndex(
        (h) => h.symbol === item.symbol && h.reportType === item.reportType
      )

      let newHistory: ReportHistoryItem[]
      if (existingIndex !== -1) {
        // 更新现有记录的时间戳
        newHistory = [...history]
        newHistory[existingIndex] = newItem
      } else {
        // 添加新记录
        newHistory = [newItem, ...history]
      }

      // 限制最多50条记录
      if (newHistory.length > MAX_HISTORY_ITEMS) {
        newHistory = newHistory.slice(0, MAX_HISTORY_ITEMS)
      }

      // 按时间倒序排序
      newHistory.sort(
        (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
      )

      saveHistory(newHistory)
    },
    [history, saveHistory]
  )

  // 删除单条记录
  const removeFromHistory = useCallback(
    (timestamp: string) => {
      const newHistory = history.filter((item) => item.timestamp !== timestamp)
      saveHistory(newHistory)
    },
    [history, saveHistory]
  )

  // 清空历史记录
  const clearHistory = useCallback(() => {
    saveHistory([])
  }, [saveHistory])

  return {
    history,
    addToHistory,
    removeFromHistory,
    clearHistory,
  }
}
