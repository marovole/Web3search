"""
应用配置管理模块
使用 pydantic-settings 从环境变量加载配置
"""
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """应用配置类"""

    # ================================
    # 基础配置
    # ================================
    ENVIRONMENT: str = Field(default="development", description="运行环境")
    DEBUG: bool = Field(default=True, description="调试模式")
    LOG_LEVEL: str = Field(default="INFO", description="日志级别")

    # ================================
    # API配置
    # ================================
    API_V1_PREFIX: str = Field(default="/api/v1", description="API v1前缀")
    API_TITLE: str = Field(default="Web3 Search API", description="API标题")
    API_VERSION: str = Field(default="1.0.0", description="API版本")

    # CORS配置
    CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:5173",
        description="允许的跨域来源（逗号分隔）"
    )

    @property
    def cors_origins_list(self) -> List[str]:
        """将CORS_ORIGINS字符串转换为列表"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    # ================================
    # 数据库配置
    # ================================
    DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/web3search",
        description="PostgreSQL数据库连接字符串"
    )
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis连接字符串"
    )

    # ================================
    # OpenRouter API
    # ================================
    OPENROUTER_API_KEY: str = Field(
        default="",
        description="OpenRouter API密钥"
    )
    OPENROUTER_BASE_URL: str = Field(
        default="https://openrouter.ai/api/v1",
        description="OpenRouter API基础URL"
    )

    # ================================
    # 数据源API
    # ================================
    # CoinGecko
    COINGECKO_API_KEY: str = Field(default="", description="CoinGecko API密钥")
    COINGECKO_BASE_URL: str = Field(
        default="https://api.coingecko.com/api/v3",
        description="CoinGecko API基础URL"
    )

    # Etherscan
    ETHERSCAN_API_KEY: str = Field(default="", description="Etherscan API密钥")
    ETHERSCAN_BASE_URL: str = Field(
        default="https://api.etherscan.io/api",
        description="Etherscan API基础URL"
    )

    # BSCScan
    BSCSCAN_API_KEY: str = Field(default="", description="BSCScan API密钥")
    BSCSCAN_BASE_URL: str = Field(
        default="https://api.bscscan.com/api",
        description="BSCScan API基础URL"
    )

    # Twitter
    TWITTER_BEARER_TOKEN: str = Field(default="", description="Twitter Bearer Token")

    # Reddit
    REDDIT_CLIENT_ID: str = Field(default="", description="Reddit Client ID")
    REDDIT_CLIENT_SECRET: str = Field(default="", description="Reddit Client Secret")
    REDDIT_USER_AGENT: str = Field(default="Web3Search/1.0", description="Reddit User Agent")

    # CryptoPanic
    CRYPTOPANIC_API_KEY: str = Field(default="", description="CryptoPanic API密钥")
    CRYPTOPANIC_BASE_URL: str = Field(
        default="https://cryptopanic.com/api/v1",
        description="CryptoPanic API基础URL"
    )

    # ================================
    # 速率限制配置
    # ================================
    RATE_LIMIT_QUICK_CHAT: str = Field(default="10/minute", description="Quick Chat速率限制")
    RATE_LIMIT_DEEP_RESEARCH: str = Field(default="3/hour", description="Deep Research速率限制")

    # ================================
    # Celery配置
    # ================================
    CELERY_BROKER_URL: str = Field(
        default="redis://localhost:6379/1",
        description="Celery Broker URL"
    )
    CELERY_RESULT_BACKEND: str = Field(
        default="redis://localhost:6379/1",
        description="Celery Result Backend"
    )

    # ================================
    # 缓存TTL配置（秒）
    # ================================
    CACHE_TTL_PRICE: int = Field(default=60, description="价格数据缓存时间")
    CACHE_TTL_PROJECT: int = Field(default=3600, description="项目信息缓存时间")
    CACHE_TTL_REPORT: int = Field(default=86400, description="报告缓存时间")

    # ================================
    # 外部服务（可选）
    # ================================
    SENTRY_DSN: str = Field(default="", description="Sentry DSN")
    RAILWAY_ENVIRONMENT: str = Field(default="", description="Railway环境")
    VERCEL_ENV: str = Field(default="", description="Vercel环境")

    class Config:
        """Pydantic配置"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# 创建全局配置实例
settings = Settings()


# 辅助函数：检查是否为生产环境
def is_production() -> bool:
    """检查是否为生产环境"""
    return settings.ENVIRONMENT.lower() in ("production", "prod")


# 辅助函数：检查是否为开发环境
def is_development() -> bool:
    """检查是否为开发环境"""
    return settings.ENVIRONMENT.lower() in ("development", "dev")
