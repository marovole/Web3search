"""
应用配置管理模块
使用 pydantic-settings 从环境变量加载配置

本模块实现了：
1. 基于Pydantic的强类型配置管理
2. 自动验证URL格式、端口范围等
3. 多环境配置支持（dev/staging/prod）
4. 敏感信息脱敏（日志安全）
5. 配置热加载（开发环境）
"""
import os
import logging
from typing import List, Optional, Any
from urllib.parse import urlparse
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import (
    Field,
    field_validator,
    model_validator,
    HttpUrl,
    RedisDsn,
    PostgresDsn
)


class Settings(BaseSettings):
    """应用配置类

    提供完整的配置管理和验证：
    - 自动从环境变量加载
    - 支持.env文件（.env.dev/.env.staging/.env.prod）
    - 强类型验证和格式检查
    - 敏感信息脱敏
    """

    # ================================
    # 基础配置
    # ================================
    ENVIRONMENT: str = Field(
        default="development",
        description="运行环境: development, staging, production"
    )
    DEBUG: bool = Field(
        default=True,
        description="调试模式（生产环境应为False）"
    )
    LOG_LEVEL: str = Field(
        default="INFO",
        description="日志级别: DEBUG, INFO, WARNING, ERROR, CRITICAL"
    )

    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """验证运行环境"""
        allowed = ["development", "dev", "staging", "stage", "production", "prod"]
        if v.lower() not in allowed:
            raise ValueError(f"ENVIRONMENT必须是以下之一: {', '.join(allowed)}")
        return v.lower()

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """验证日志级别"""
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in allowed:
            raise ValueError(f"LOG_LEVEL必须是以下之一: {', '.join(allowed)}")
        return v_upper

    # ================================
    # API配置
    # ================================
    API_V1_PREFIX: str = Field(default="/api/v1", description="API v1前缀")
    API_TITLE: str = Field(default="Web3 Search API", description="API标题")
    API_VERSION: str = Field(default="1.0.0", description="API版本")

    # CORS配置
    CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:5173,https://web3search.vercel.app",
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

    # 连接池配置
    DATABASE_POOL_MIN_SIZE: int = Field(
        default=10,
        ge=1,
        le=100,
        description="数据库连接池最小连接数（范围: 1-100）"
    )
    DATABASE_POOL_MAX_SIZE: int = Field(
        default=50,
        ge=1,
        le=200,
        description="数据库连接池最大连接数（范围: 1-200）"
    )
    DATABASE_POOL_MAX_QUERIES: int = Field(
        default=50000,
        ge=1000,
        description="单个连接最大查询数（之后回收，最小1000）"
    )
    DATABASE_POOL_MAX_INACTIVE_CONNECTION_LIFETIME: float = Field(
        default=300.0,
        ge=10.0,
        description="空闲连接最大存活时间（秒，最小10秒）"
    )
    DATABASE_POOL_TIMEOUT: float = Field(
        default=10.0,
        ge=1.0,
        le=60.0,
        description="获取连接超时时间（秒，范围: 1-60）"
    )
    DATABASE_COMMAND_TIMEOUT: float = Field(
        default=60.0,
        ge=1.0,
        le=300.0,
        description="SQL命令执行超时时间（秒，范围: 1-300）"
    )
    DATABASE_ECHO: bool = Field(
        default=False,
        description="是否输出SQL日志（生产环境应为False）"
    )
    DATABASE_POOL_RECYCLE: int = Field(
        default=3600,
        ge=300,
        description="连接回收时间（秒，最小300秒）"
    )

    @model_validator(mode='after')
    def validate_database_pool(self) -> 'Settings':
        """验证数据库连接池配置的合理性"""
        if self.DATABASE_POOL_MIN_SIZE > self.DATABASE_POOL_MAX_SIZE:
            raise ValueError(
                f"DATABASE_POOL_MIN_SIZE ({self.DATABASE_POOL_MIN_SIZE}) "
                f"不能大于 DATABASE_POOL_MAX_SIZE ({self.DATABASE_POOL_MAX_SIZE})"
            )
        return self

    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis连接字符串"
    )

    # ================================
    # OpenRouter API
    # ================================
    OPENROUTER_API_KEY: str = Field(
        default="",
        min_length=0,
        description="OpenRouter API密钥（生产环境必填）"
    )
    OPENROUTER_BASE_URL: str = Field(
        default="https://openrouter.ai/api/v1",
        description="OpenRouter API基础URL"
    )

    @field_validator("OPENROUTER_BASE_URL")
    @classmethod
    def validate_openrouter_url(cls, v: str) -> str:
        """验证OpenRouter URL格式"""
        if not v.startswith(("http://", "https://")):
            raise ValueError("OPENROUTER_BASE_URL必须以http://或https://开头")
        return v.rstrip("/")

    # ================================
    # 数据源API
    # ================================
    # CoinGecko
    COINGECKO_API_KEY: str = Field(
        default="",
        description="CoinGecko API密钥（可选）"
    )
    COINGECKO_BASE_URL: str = Field(
        default="https://api.coingecko.com/api/v3",
        description="CoinGecko API基础URL"
    )

    # Etherscan
    ETHERSCAN_API_KEY: str = Field(
        default="",
        description="Etherscan API密钥（可选）"
    )
    ETHERSCAN_BASE_URL: str = Field(
        default="https://api.etherscan.io/api",
        description="Etherscan API基础URL"
    )

    # BSCScan
    BSCSCAN_API_KEY: str = Field(
        default="",
        description="BSCScan API密钥（可选）"
    )
    BSCSCAN_BASE_URL: str = Field(
        default="https://api.bscscan.com/api",
        description="BSCScan API基础URL"
    )

    # Twitter
    TWITTER_BEARER_TOKEN: str = Field(
        default="",
        description="Twitter Bearer Token（可选）"
    )

    # Reddit
    REDDIT_CLIENT_ID: str = Field(
        default="",
        description="Reddit Client ID（可选）"
    )
    REDDIT_CLIENT_SECRET: str = Field(
        default="",
        description="Reddit Client Secret（可选）"
    )
    REDDIT_USER_AGENT: str = Field(
        default="Web3Search/1.0",
        min_length=1,
        description="Reddit User Agent"
    )

    # CryptoPanic
    CRYPTOPANIC_API_KEY: str = Field(
        default="",
        description="CryptoPanic API密钥（可选）"
    )
    CRYPTOPANIC_BASE_URL: str = Field(
        default="https://cryptopanic.com/api/v1",
        description="CryptoPanic API基础URL"
    )

    @field_validator(
        "COINGECKO_BASE_URL",
        "ETHERSCAN_BASE_URL",
        "BSCSCAN_BASE_URL",
        "CRYPTOPANIC_BASE_URL"
    )
    @classmethod
    def validate_base_urls(cls, v: str) -> str:
        """验证所有API base URL格式"""
        if not v.startswith(("http://", "https://")):
            raise ValueError("API Base URL必须以http://或https://开头")
        return v.rstrip("/")

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
    CACHE_TTL_PRICE: int = Field(
        default=60,
        ge=10,
        le=3600,
        description="价格数据缓存时间（秒，范围: 10-3600）"
    )
    CACHE_TTL_PROJECT: int = Field(
        default=3600,
        ge=300,
        le=86400,
        description="项目信息缓存时间（秒，范围: 300-86400）"
    )
    CACHE_TTL_REPORT: int = Field(
        default=86400,
        ge=3600,
        le=604800,
        description="报告缓存时间（秒，范围: 3600-604800）"
    )

    # ================================
    # 外部服务（可选）
    # ================================
    SENTRY_DSN: str = Field(default="", description="Sentry DSN")
    RAILWAY_ENVIRONMENT: str = Field(default="", description="Railway环境")
    VERCEL_ENV: str = Field(default="", description="Vercel环境")

    # ================================
    # 辅助方法
    # ================================
    def mask_sensitive(self, value: str) -> str:
        """脱敏处理敏感信息（用于日志输出）

        Args:
            value: 需要脱敏的字符串

        Returns:
            脱敏后的字符串，只显示前4位和后4位

        Example:
            >>> settings.mask_sensitive("sk_1234567890abcdef")
            'sk_1...cdef'
        """
        if not value or len(value) <= 8:
            return "***"
        return f"{value[:4]}...{value[-4:]}"

    def get_safe_config(self) -> dict:
        """获取安全的配置字典（敏感信息已脱敏）

        用于日志记录或调试输出，所有包含'KEY'、'TOKEN'、'SECRET'、'PASSWORD'的字段会被脱敏

        Returns:
            脱敏后的配置字典
        """
        config = {}
        sensitive_keywords = ['KEY', 'TOKEN', 'SECRET', 'PASSWORD', 'DSN']

        for field_name, field_value in self.model_dump().items():
            # 检查字段名是否包含敏感关键词
            is_sensitive = any(keyword in field_name.upper() for keyword in sensitive_keywords)

            if is_sensitive and isinstance(field_value, str) and field_value:
                config[field_name] = self.mask_sensitive(field_value)
            else:
                config[field_name] = field_value

        return config

    @model_validator(mode='after')
    def validate_production_config(self) -> 'Settings':
        """验证生产环境必须配置的字段"""
        if self.ENVIRONMENT in ('production', 'prod'):
            # 生产环境必须关闭DEBUG
            if self.DEBUG:
                logging.warning("生产环境检测到DEBUG=True，强制设置为False")
                self.DEBUG = False

            # 生产环境必须配置OpenRouter API Key
            if not self.OPENROUTER_API_KEY:
                raise ValueError("生产环境必须配置OPENROUTER_API_KEY")

            # 生产环境不应该输出SQL日志
            if self.DATABASE_ECHO:
                logging.warning("生产环境检测到DATABASE_ECHO=True，强制设置为False")
                self.DATABASE_ECHO = False

        return self

    model_config = SettingsConfigDict(
        # 根据环境变量ENVIRONMENT动态选择.env文件
        # 优先级: .env.{environment} > .env
        env_file=('.env', f'.env.{os.getenv("ENVIRONMENT", "development")}'),
        env_file_encoding='utf-8',
        case_sensitive=True,
        extra='ignore',  # 忽略未定义的环境变量
        validate_default=True,  # 验证默认值
    )


# ================================
# 全局配置实例和辅助函数
# ================================

# 创建全局配置实例
settings = Settings()

# 配置加载日志
logger = logging.getLogger(__name__)
logger.info(f"配置已加载 - 环境: {settings.ENVIRONMENT}, 调试模式: {settings.DEBUG}")
logger.debug(f"安全配置: {settings.get_safe_config()}")


def reload_settings() -> Settings:
    """重新加载配置（仅开发环境）

    在开发环境下，可以调用此函数重新加载环境变量和.env文件，
    而无需重启应用。生产环境下此函数不执行任何操作。

    Returns:
        新的Settings实例（开发环境）或当前实例（生产环境）

    Example:
        >>> from app.core.config import reload_settings
        >>> new_settings = reload_settings()
    """
    global settings

    if is_development():
        logger.info("重新加载配置...")
        old_env = settings.ENVIRONMENT
        settings = Settings()
        logger.info(f"配置已重新加载 - 环境: {old_env} -> {settings.ENVIRONMENT}")
        return settings
    else:
        logger.warning("生产环境不支持配置热加载")
        return settings


def is_production() -> bool:
    """检查是否为生产环境

    Returns:
        True if production environment, False otherwise
    """
    return settings.ENVIRONMENT.lower() in ("production", "prod")


def is_development() -> bool:
    """检查是否为开发环境

    Returns:
        True if development environment, False otherwise
    """
    return settings.ENVIRONMENT.lower() in ("development", "dev")


def is_staging() -> bool:
    """检查是否为预发布环境

    Returns:
        True if staging environment, False otherwise
    """
    return settings.ENVIRONMENT.lower() in ("staging", "stage")


def get_database_url() -> str:
    """获取数据库连接URL

    Returns:
        数据库连接字符串
    """
    return settings.DATABASE_URL


def get_redis_url() -> str:
    """获取Redis连接URL

    Returns:
        Redis连接字符串
    """
    return settings.REDIS_URL
