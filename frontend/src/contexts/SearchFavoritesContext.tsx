import React, { createContext, useContext, useState, useEffect, useCallback } from 'react'

export interface SearchFavorite {
  id: string
  type: 'repository' | 'commit' | 'issue'
  data: any
  favoritedAt: string
  query?: string
}

interface SearchFavoritesContextType {
  favorites: SearchFavorite[]
  addFavorite: (favorite: Omit<SearchFavorite, 'id' | 'favoritedAt'>) => void
  removeFavorite: (id: string) => void
  isFavorite: (id: number, type: SearchFavorite['type']) => boolean
  clearFavorites: () => void
  getFavoritesByType: (type: SearchFavorite['type']) => SearchFavorite[]
}

const STORAGE_KEY = 'web3search_search_favorites'
const MAX_FAVORITES = 100

const SearchFavoritesContext = createContext<SearchFavoritesContextType | undefined>(undefined)

interface SearchFavoritesProviderProps {
  children: React.ReactNode
}

/**
 * 搜索结果收藏上下文提供者
 */
export function SearchFavoritesProvider({ children }: SearchFavoritesProviderProps) {
  const [favorites, setFavorites] = useState<SearchFavorite[]>([])

  // 加载收藏
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        const parsed = JSON.parse(stored) as SearchFavorite[]
        setFavorites(parsed)
      }
    } catch (error) {
      console.error('加载收藏失败:', error)
    }
  }, [])

  // 保存收藏
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(favorites))
    } catch (error) {
      console.error('保存收藏失败:', error)
    }
  }, [favorites])

  // 添加收藏
  const addFavorite = useCallback((favorite: Omit<SearchFavorite, 'id' | 'favoritedAt'>) => {
    // 检查是否已存在（基于 type 和 data.id）
    const exists = favorites.some(
      f => f.type === favorite.type && f.data.id === favorite.data.id
    )

    if (exists) {
      console.warn('该结果已收藏')
      return
    }

    const newFavorite: SearchFavorite = {
      ...favorite,
      id: `${favorite.type}_${favorite.data.id}_${Date.now()}`,
      favoritedAt: new Date().toISOString()
    }

    setFavorites(prev => {
      const newFavorites = [newFavorite, ...prev]
      // 限制收藏数量
      return newFavorites.slice(0, MAX_FAVORITES)
    })
  }, [favorites])

  // 删除收藏
  const removeFavorite = useCallback((id: string) => {
    setFavorites(prev => prev.filter(f => f.id !== id))
  }, [])

  // 检查是否已收藏
  const isFavorite = useCallback((id: number, type: SearchFavorite['type']): boolean => {
    return favorites.some(f => f.type === type && f.data.id === id)
  }, [favorites])

  // 清空收藏
  const clearFavorites = useCallback(() => {
    setFavorites([])
    localStorage.removeItem(STORAGE_KEY)
  }, [])

  // 按类型获取收藏
  const getFavoritesByType = useCallback((type: SearchFavorite['type']): SearchFavorite[] => {
    return favorites.filter(f => f.type === type)
  }, [favorites])

  return (
    <SearchFavoritesContext.Provider
      value={{
        favorites,
        addFavorite,
        removeFavorite,
        isFavorite,
        clearFavorites,
        getFavoritesByType
      }}
    >
      {children}
    </SearchFavoritesContext.Provider>
  )
}

/**
 * 使用搜索结果收藏上下文
 */
export function useSearchFavorites() {
  const context = useContext(SearchFavoritesContext)
  if (!context) {
    throw new Error('useSearchFavorites must be used within SearchFavoritesProvider')
  }
  return context
}

