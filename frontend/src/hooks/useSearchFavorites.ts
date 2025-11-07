/**
 * 搜索结果收藏 Hook
 * 便捷的 Hook 封装，提供收藏功能的常用操作
 */

import { useSearchFavorites as useSearchFavoritesContext } from '../contexts/SearchFavoritesContext'
import type { SearchFavorite } from '../contexts/SearchFavoritesContext'

export function useSearchFavorites() {
  const context = useSearchFavoritesContext()

  return {
    ...context,
    // 便捷方法：切换收藏状态
    toggleFavorite: (item: { id: number; type: SearchFavorite['type']; data: any; query?: string }) => {
      if (context.isFavorite(item.id, item.type)) {
        // 找到并删除
        const favorite = context.favorites.find(
          f => f.type === item.type && f.data.id === item.id
        )
        if (favorite) {
          context.removeFavorite(favorite.id)
        }
      } else {
        // 添加收藏
        context.addFavorite({
          type: item.type,
          data: item.data,
          query: item.query
        })
      }
    }
  }
}

export default useSearchFavorites

