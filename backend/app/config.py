"""
Application Configuration
Manages environment variables and application settings using Pydantic
"""

from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application metadata
    project_name: str = Field(default="Web3search Backend API", description="Project name")
    version: str = Field(default="1.0.0", description="API version")
    api_prefix: str = Field(default="/api/v1", description="API URL prefix")

    # Server configuration
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    debug: bool = Field(default=False, description="Debug mode")

    # Request size limiter configuration
    request_size_limit_enabled: bool = Field(
        default=True,
        description="Enable request size limiting middleware"
    )
    request_max_size: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        description="Maximum request size in bytes"
    )
    request_max_upload_size: int = Field(
        default=50 * 1024 * 1024,  # 50MB
        description="Maximum file upload size in bytes"
    )
    ip_block_duration: int = Field(
        default=300,  # 5 minutes
        description="IP block duration in seconds after violations"
    )

    # SQL injection protection configuration
    sql_injection_protection_enabled: bool = Field(
        default=True,
        description="Enable SQL injection protection middleware"
    )
    sql_injection_log_only: bool = Field(
        default=False,
        description="Only log SQL injection attempts without blocking (for staging)"
    )
    sql_injection_skip_paths: List[str] = Field(
        default_factory=lambda: ["/health", "/docs", "/openapi.json"],
        description="Paths to skip SQL injection detection"
    )

    # CORS configuration
    cors_allow_origins: List[str] = Field(
        default_factory=lambda: [
            "https://web3search.pages.dev",
            "https://*.web3search.pages.dev",
            "http://localhost:*",
            "http://127.0.0.1:*",
        ],
        description="Allowed CORS origins"
    )
    cors_allow_methods: List[str] = Field(
        default_factory=lambda: ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        description="Allowed HTTP methods"
    )
    cors_allow_headers: List[str] = Field(
        default_factory=lambda: ["*"],
        description="Allowed request headers"
    )
    cors_allow_credentials: bool = Field(
        default=True,
        description="Allow credentials in CORS requests"
    )
    cors_max_age: int = Field(
        default=86400,  # 24 hours
        description="CORS preflight cache duration in seconds"
    )

    # Logging configuration
    logging_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )

    # Database configuration (if needed for analytics/reports)
    database_url: str = Field(
        default="",
        description="Database connection URL"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
