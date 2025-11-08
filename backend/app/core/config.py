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
from pathlib import Path
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
    # 项目路径配置
    # ================================
    BASE_DIR: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parent.parent.parent.parent,
        description="项目根目录（Web3search目录）"
    )

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
        default="http://localhost:3000,http://localhost:5173",
        description="允许的跨域来源（逗号分隔，生产环境必须指定具体域名）"
    )

    @property
    def cors_origins_list(self) -> List[str]:
        """将CORS_ORIGINS字符串转换为列表并进行安全验证"""
        origins = [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

        # 生产环境安全检查
        if self.ENVIRONMENT in ('production', 'prod'):
            # 检查是否有危险的通配符
            dangerous_patterns = ['*', '.*', '*.*']
            for origin in origins:
                for pattern in dangerous_patterns:
                    if pattern in origin:
                        raise ValueError(f"生产环境不允许使用不安全的CORS配置: {origin}")

            # 检查是否包含具体的生产域名（包括所有部署平台）
            production_domains = [
                'web3search.ai',           # 主域名
                'www.web3search.ai',       # WWW 子域名
                'api.web3search.ai',       # API 子域名
                'web3search.vercel.app',   # Vercel 前端部署域名
                'web3search.pages.dev',    # Cloudflare Pages 前端部署域名
                'web3-search.netlify.app'  # Netlify 前端部署域名
            ]
            has_valid_domain = any(domain in origin for origin in origins for domain in production_domains)

            if not has_valid_domain:
                raise ValueError(f"生产环境必须配置具体的生产域名，当前配置: {origins}")

        return origins

    # ================================
    # 数据库配置
    # ================================
    DATABASE_URL: str = Field(
        default="",
        description="PostgreSQL数据库连接字符串（必须通过环境变量设置）"
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

    @field_validator("REDIS_URL")
    @classmethod
    def validate_redis_url(cls, v: str) -> str:
        """验证Redis URL格式"""
        if not v:
            # 空字符串表示禁用 Redis
            logging.warning("REDIS_URL 为空，Redis 功能将被禁用")
            return v

        # 允许 disabled:// 前缀来显式禁用 Redis
        if v.startswith("disabled://"):
            logging.info("Redis 已通过 disabled:// 前缀显式禁用")
            return v

        # 验证 Redis URL 必须以正确的 scheme 开头
        if not v.startswith(("redis://", "rediss://", "unix://")):
            raise ValueError(
                f"REDIS_URL 必须以 redis://、rediss:// 或 unix:// 开头，当前值: {v[:50]}..."
            )

        return v

    # ================================
    # JWT认证配置
    # ================================
    JWT_SECRET_KEY: str = Field(
        ...,
        min_length=32,
        description="JWT Secret Key（必须通过环境变量设置，不允许默认值）"
    )
    JWT_ALGORITHM: str = Field(
        default="HS256",
        description="JWT算法"
    )

    # API签名验证配置
    SIGNATURE_SECRET_KEY: str = Field(
        ...,
        min_length=32,
        description="API签名验证密钥（必须通过环境变量设置）"
    )
    ENABLE_SIGNATURE_VERIFICATION: bool = Field(
        default=False,
        description="是否启用API请求签名验证（生产环境建议启用）"
    )
    ACCESS_TOKEN_EXPIRE_HOURS: int = Field(
        default=24,
        ge=1,
        le=168,  # 最大7天
        description="Access Token过期时间（小时）"
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=30,
        ge=1,
        le=90,  # 最大90天
        description="Refresh Token过期时间（天）"
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

    # GitHub
    GITHUB_TOKEN: str = Field(
        default="",
        description="GitHub个人访问令牌（PAT），从 https://github.com/settings/tokens 获取（必须通过环境变量设置）"
    )
    GITHUB_BASE_URL: str = Field(
        default="https://api.github.com",
        description="GitHub API基础URL"
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

    # PolygonScan
    POLYGONSCAN_API_KEY: str = Field(
        default="",
        description="PolygonScan API密钥（可选）"
    )

    # Arbiscan
    ARBISCAN_API_KEY: str = Field(
        default="",
        description="Arbiscan API密钥（可选）"
    )

    # Twitter
    TWITTER_BEARER_TOKEN: str = Field(
        default="",
        description="Twitter Bearer Token（可选）"
    )

    # Telegram
    TELEGRAM_BOT_TOKEN: str = Field(
        default="",
        description="Telegram Bot Token（可选）"
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

    # CoinMarketCap（CoinGecko的fallback）
    COINMARKETCAP_API_KEY: str = Field(
        default="",
        description="CoinMarketCap API密钥（Pro API）"
    )
    COINMARKETCAP_BASE_URL: str = Field(
        default="https://pro-api.coinmarketcap.com/v2",
        description="CoinMarketCap API基础URL"
    )

    # Blockchair（Etherscan的fallback）
    BLOCKCHAIR_API_KEY: str = Field(
        default="",
        description="Blockchair API密钥（可选）"
    )
    BLOCKCHAIR_BASE_URL: str = Field(
        default="https://api.blockchair.com",
        description="Blockchair API基础URL"
    )

    # Nitter（Twitter的fallback）
    NITTER_INSTANCE_URL: str = Field(
        default="https://nitter.net",
        description="Nitter实例URL"
    )

    # Pushshift（Reddit的fallback）
    PUSHSHIFT_BASE_URL: str = Field(
        default="https://api.pushshift.io",
        description="Pushshift API基础URL"
    )

    @field_validator(
        "COINGECKO_BASE_URL",
        "ETHERSCAN_BASE_URL",
        "BSCSCAN_BASE_URL",
        "CRYPTOPANIC_BASE_URL",
        "COINMARKETCAP_BASE_URL",
        "BLOCKCHAIR_BASE_URL",
        "NITTER_INSTANCE_URL",
        "PUSHSHIFT_BASE_URL"
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
    # 重试策略配置（任务5.2）
    # ================================
    API_RETRY_MAX_ATTEMPTS: int = Field(
        default=3,
        ge=1,
        le=10,
        description="API调用最大重试次数（范围: 1-10）"
    )
    API_RETRY_DELAYS: str = Field(
        default="1.0,2.0,4.0",
        description="重试延迟序列，逗号分隔（秒），如: 1.0,2.0,4.0"
    )
    API_RETRY_SINGLE_TIMEOUT: float = Field(
        default=10.0,
        ge=1.0,
        le=60.0,
        description="单次API请求超时时间（秒，范围: 1-60）"
    )
    API_RETRY_TOTAL_TIMEOUT: float = Field(
        default=30.0,
        ge=5.0,
        le=120.0,
        description="API调用总计超时时间（秒，范围: 5-120）"
    )

    @property
    def api_retry_delays_list(self) -> List[float]:
        """将API_RETRY_DELAYS字符串转换为浮点数列表"""
        try:
            return [float(x.strip()) for x in self.API_RETRY_DELAYS.split(",")]
        except ValueError as e:
            logger.warning(f"Invalid API_RETRY_DELAYS format: {self.API_RETRY_DELAYS}, using default [1.0, 2.0, 4.0]")
            return [1.0, 2.0, 4.0]

    @model_validator(mode='after')
    def validate_retry_config(self) -> 'Settings':
        """验证重试配置的合理性（任务5.2）"""
        # 验证单次超时不能大于总超时
        if self.API_RETRY_SINGLE_TIMEOUT > self.API_RETRY_TOTAL_TIMEOUT:
            raise ValueError(
                f"API_RETRY_SINGLE_TIMEOUT ({self.API_RETRY_SINGLE_TIMEOUT}s) "
                f"不能大于 API_RETRY_TOTAL_TIMEOUT ({self.API_RETRY_TOTAL_TIMEOUT}s)"
            )

        # 验证延迟序列长度与重试次数匹配
        delays = self.api_retry_delays_list
        if len(delays) < self.API_RETRY_MAX_ATTEMPTS:
            logger.warning(
                f"API_RETRY_DELAYS 长度 ({len(delays)}) 少于 API_RETRY_MAX_ATTEMPTS ({self.API_RETRY_MAX_ATTEMPTS}), "
                f"将重复使用最后一个延迟值"
            )

        # 验证延迟值合理性（不超过30秒）
        for i, delay in enumerate(delays):
            if delay < 0:
                raise ValueError(f"重试延迟不能为负数: delays[{i}] = {delay}")
            if delay > 30.0:
                logger.warning(f"重试延迟过长: delays[{i}] = {delay}s, 建议不超过30秒")

        return self

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
    SLACK_WEBHOOK_URL: str = Field(default="", description="Slack Webhook URL (用于告警通知)")
    SLACK_ALERTS_CHANNEL: str = Field(default="#alerts", description="Slack告警频道")
    RAILWAY_ENVIRONMENT: str = Field(default="", description="Railway环境")
    VERCEL_ENV: str = Field(default="", description="Vercel环境")

    # ================================
    # Loki 日志聚合配置（可选）
    # ================================
    LOKI_URL: str = Field(
        default="http://localhost:3100",
        description="Loki 服务URL（默认: http://localhost:3100）"
    )
    LOKI_USERNAME: str = Field(
        default="",
        description="Loki 认证用户名（可选）"
    )
    LOKI_PASSWORD: str = Field(
        default="",
        description="Loki 认证密码（可选）"
    )

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
        """验证生产环境必须配置的字段和格式"""
        if self.ENVIRONMENT in ('production', 'prod'):
            # 生产环境必须关闭DEBUG
            if self.DEBUG:
                logging.warning("生产环境检测到DEBUG=True，强制设置为False")
                self.DEBUG = False

            # 生产环境必须配置OpenRouter API Key
            if not self.OPENROUTER_API_KEY:
                raise ValueError("生产环境必须配置OPENROUTER_API_KEY")
            
            # 验证OpenRouter API Key格式
            if self.OPENROUTER_API_KEY and not self.OPENROUTER_API_KEY.startswith(('sk-or-v1-', 'sk-or-')):
                logging.warning("OPENROUTER_API_KEY格式可能不正确，应以'sk-or-v1-'或'sk-or-'开头")

            # 生产环境必须配置安全的JWT密钥
            forbidden_keys = [
                "temp_development_key_only_replace_in_production_32chars",
                "change-me",
                "default_secret_key_change_me",
                "your-secret-key-here",
                "your_github_token_here",  # GitHub token默认值
            ]

            if not self.JWT_SECRET_KEY or len(self.JWT_SECRET_KEY) < 32:
                raise ValueError("生产环境必须通过环境变量设置安全的JWT_SECRET_KEY，长度至少32位")

            if self.JWT_SECRET_KEY in forbidden_keys:
                raise ValueError("生产环境不能使用默认或临时JWT密钥，请设置安全的JWT_SECRET_KEY环境变量")
            
            # 验证JWT密钥强度（至少包含字母和数字）
            if len(self.JWT_SECRET_KEY) < 32 or not any(c.isalnum() for c in self.JWT_SECRET_KEY):
                raise ValueError("JWT_SECRET_KEY强度不足，应包含字母和数字，长度至少32位")

            # 生产环境必须配置签名密钥
            if not self.SIGNATURE_SECRET_KEY or len(self.SIGNATURE_SECRET_KEY) < 32:
                raise ValueError("生产环境必须通过环境变量设置SIGNATURE_SECRET_KEY，长度至少32位")
            
            if self.SIGNATURE_SECRET_KEY in forbidden_keys:
                raise ValueError("生产环境不能使用默认或临时签名密钥")

            # 生产环境必须配置数据库连接
            if not self.DATABASE_URL:
                raise ValueError("生产环境必须通过环境变量设置DATABASE_URL")
            
            # 验证数据库URL格式
            if self.DATABASE_URL and not self.DATABASE_URL.startswith(('postgresql://', 'postgresql+asyncpg://')):
                raise ValueError("DATABASE_URL格式不正确，应以postgresql://或postgresql+asyncpg://开头")
            
            # 验证数据库URL不包含默认凭据
            if 'postgres:postgres@' in self.DATABASE_URL or ':postgres@' in self.DATABASE_URL:
                logging.warning("检测到数据库URL可能包含默认凭据，建议使用强密码")

            # 生产环境必须配置CORS来源
            if not self.CORS_ORIGINS or self.CORS_ORIGINS.strip() == '':
                raise ValueError("生产环境必须配置CORS_ORIGINS，指定允许的前端域名")
            
            # 验证CORS配置不包含通配符
            if '*' in self.CORS_ORIGINS:
                raise ValueError("生产环境CORS_ORIGINS不能包含通配符'*'，必须指定具体域名")

            # 生产环境不应该输出SQL日志
            if self.DATABASE_ECHO:
                logging.warning("生产环境检测到DATABASE_ECHO=True，强制设置为False")
                self.DATABASE_ECHO = False
            
            # 验证日志级别（生产环境不应使用DEBUG）
            if self.LOG_LEVEL == "DEBUG":
                logging.warning("生产环境检测到LOG_LEVEL=DEBUG，建议使用INFO或WARNING")
                # 不强制修改，但给出警告
            
            # 验证GitHub Token（如果配置了）
            if self.GITHUB_TOKEN and self.GITHUB_TOKEN == "your_github_token_here":
                raise ValueError("生产环境不能使用默认GitHub Token，请设置有效的GITHUB_TOKEN环境变量")
            
            # 验证GitHub Token格式（如果配置了）
            if self.GITHUB_TOKEN and not self.GITHUB_TOKEN.startswith(('ghp_', 'gho_', 'ghu_', 'ghs_', 'ghr_')):
                logging.warning("GITHUB_TOKEN格式可能不正确，应以'ghp_', 'gho_', 'ghu_', 'ghs_'或'ghr_'开头")

        else:
            # 开发环境友好提示
            development_warnings = []
            missing_configs = []

            # JWT密钥在所有环境都是必需的
            if not self.JWT_SECRET_KEY or len(self.JWT_SECRET_KEY) < 32:
                development_warnings.append("⚠️ JWT_SECRET_KEY未设置或长度不足32位")
                development_warnings.append("   请设置安全的JWT_SECRET_KEY环境变量")

            if not self.DATABASE_URL:
                missing_configs.append("DATABASE_URL")
            if not self.OPENROUTER_API_KEY:
                missing_configs.append("OPENROUTER_API_KEY")

            if missing_configs:
                development_warnings.append(f"缺少配置: {', '.join(missing_configs)}")

            if development_warnings:
                logging.warning("=" * 60)
                logging.warning("🔧 开发环境配置提醒")
                for warning in development_warnings:
                    logging.warning(warning)
                logging.warning("📖 完整配置指南: DEPLOYMENT_FIX_GUIDE.md")
                logging.warning("=" * 60)

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
