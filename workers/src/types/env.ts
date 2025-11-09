/**
 * Cloudflare Workers 运行时环境变量类型定义
 * 需要与 wrangler.toml 保持同步
 */
export interface Env {
  /**
   * Supabase 项目 URL
   * 例如: https://hxxnkbxyjhhorfeodiji.supabase.co
   */
  SUPABASE_URL: string

  /**
   * Supabase 匿名密钥（用于只读操作）
   */
  SUPABASE_ANON_KEY: string

  /**
   * Supabase 服务角色密钥（用于管理员操作，需保密）
   */
  SUPABASE_SERVICE_ROLE_KEY?: string

  /**
   * 健康检查使用的表名
   * 默认: 'projects'
   */
  SUPABASE_HEALTH_TABLE?: string

  /**
   * CORS 允许的来源列表（逗号分隔）
   * 例如: "https://web3search.pages.dev,https://web3search.vercel.app"
   */
  CORS_ORIGINS?: string

  /**
   * 应用版本号（用于健康检查响应）
   */
  APP_VERSION?: string

  /**
   * 环境标识
   */
  ENVIRONMENT?: 'production' | 'development'

  /**
   * OpenRouter API Key（用于 AI 聊天）
   */
  OPENROUTER_API_KEY: string

  /**
   * Cloudflare KV 命名空间（用于缓存和速率限制）
   */
  CACHE?: KVNamespace
}
