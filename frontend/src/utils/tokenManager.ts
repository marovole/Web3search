/**
 * 安全的令牌存储管理
 * 使用sessionStorage并添加额外的安全措施
 */

interface TokenData {
  token: string
  expiresAt: number
  refreshToken?: string
}

class TokenManager {
  private readonly TOKEN_KEY = 'web3search_auth_data'
  private readonly TOKEN_REFRESH_THRESHOLD = 5 * 60 * 1000 // 5分钟

  /**
   * 安全地存储令牌
   */
  setToken(token: string, expiresIn?: number, refreshToken?: string): void {
    try {
      const expiresAt = expiresIn 
        ? Date.now() + (expiresIn * 1000)
        : Date.now() + (24 * 60 * 60 * 1000) // 默认24小时

      const tokenData: TokenData = {
        token,
        expiresAt,
        refreshToken
      }

      // 使用sessionStorage而不是localStorage
      if (typeof window !== 'undefined' && window.sessionStorage) {
        sessionStorage.setItem(this.TOKEN_KEY, JSON.stringify(tokenData))
      }
    } catch (error) {
      console.error('Failed to store token:', error)
    }
  }

  /**
   * 获取有效的令牌
   */
  getToken(): string | null {
    try {
      if (typeof window === 'undefined' || !window.sessionStorage) {
        return null
      }

      const stored = sessionStorage.getItem(this.TOKEN_KEY)
      if (!stored) {
        return null
      }

      const tokenData: TokenData = JSON.parse(stored)
      
      // 检查令牌是否过期
      if (Date.now() >= tokenData.expiresAt) {
        this.clearToken()
        return null
      }

      // 检查是否需要刷新令牌
      if (this.shouldRefreshToken(tokenData.expiresAt)) {
        this.refreshTokenIfNeeded(tokenData.refreshToken)
      }

      return tokenData.token
    } catch (error) {
      console.error('Failed to get token:', error)
      this.clearToken()
      return null
    }
  }

  /**
   * 清除令牌
   */
  clearToken(): void {
    try {
      if (typeof window !== 'undefined' && window.sessionStorage) {
        sessionStorage.removeItem(this.TOKEN_KEY)
      }
    } catch (error) {
      console.error('Failed to clear token:', error)
    }
  }

  /**
   * 检查是否需要刷新令牌
   */
  private shouldRefreshToken(expiresAt: number): boolean {
    return Date.now() >= (expiresAt - this.TOKEN_REFRESH_THRESHOLD)
  }

  /**
   * 刷新令牌（如果需要）
   */
  private async refreshTokenIfNeeded(refreshToken?: string): Promise<void> {
    if (!refreshToken) {
      return
    }

    try {
      // 这里可以调用刷新令牌的API
      // const response = await fetch('/api/v1/auth/refresh', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify({ refresh_token: refreshToken })
      // })
      
      // const data = await response.json()
      // if (data.token) {
      //   this.setToken(data.token, data.expires_in, data.refresh_token)
      // }
    } catch (error) {
      console.error('Failed to refresh token:', error)
      this.clearToken()
    }
  }

  /**
   * 检查是否已认证
   */
  isAuthenticated(): boolean {
    return this.getToken() !== null
  }

  /**
   * 获取令牌剩余有效时间（毫秒）
   */
  getTokenRemainingTime(): number {
    try {
      if (typeof window === 'undefined' || !window.sessionStorage) {
        return 0
      }

      const stored = sessionStorage.getItem(this.TOKEN_KEY)
      if (!stored) {
        return 0
      }

      const tokenData: TokenData = JSON.parse(stored)
      return Math.max(0, tokenData.expiresAt - Date.now())
    } catch (error) {
      return 0
    }
  }
}

// 创建单例实例
const tokenManager = new TokenManager()

export default tokenManager