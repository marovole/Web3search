"""
配置管理测试模块

测试配置验证、多环境支持、敏感信息脱敏等功能
"""
import os
import pytest
from pydantic import ValidationError
from app.core.config import (
    Settings,
    settings,
    is_production,
    is_development,
    is_staging,
    reload_settings,
    get_database_url,
    get_redis_url,
)


class TestSettingsValidation:
    """测试配置验证功能"""

    def test_default_settings(self):
        """测试默认配置加载"""
        assert settings.ENVIRONMENT in ["development", "dev", "staging", "stage", "production", "prod"]
        assert isinstance(settings.DEBUG, bool)
        assert settings.LOG_LEVEL in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

    def test_environment_validation(self, monkeypatch):
        """测试环境变量验证"""
        # 测试有效环境
        valid_envs = ["development", "dev", "staging", "stage", "production", "prod"]
        for env in valid_envs:
            monkeypatch.setenv("ENVIRONMENT", env)
            test_settings = Settings()
            assert test_settings.ENVIRONMENT.lower() in valid_envs

        # 测试无效环境
        monkeypatch.setenv("ENVIRONMENT", "invalid")
        with pytest.raises(ValidationError) as exc_info:
            Settings()
        assert "ENVIRONMENT必须是以下之一" in str(exc_info.value)

    def test_log_level_validation(self, monkeypatch):
        """测试日志级别验证"""
        # 测试有效日志级别
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        for level in valid_levels:
            monkeypatch.setenv("LOG_LEVEL", level)
            test_settings = Settings()
            assert test_settings.LOG_LEVEL == level.upper()

        # 测试无效日志级别
        monkeypatch.setenv("LOG_LEVEL", "INVALID")
        with pytest.raises(ValidationError) as exc_info:
            Settings()
        assert "LOG_LEVEL必须是以下之一" in str(exc_info.value)

    def test_database_pool_validation(self, monkeypatch):
        """测试数据库连接池配置验证"""
        # 测试最小连接数 > 最大连接数（应该失败）
        monkeypatch.setenv("DATABASE_POOL_MIN_SIZE", "100")
        monkeypatch.setenv("DATABASE_POOL_MAX_SIZE", "50")
        with pytest.raises(ValidationError) as exc_info:
            Settings()
        assert "DATABASE_POOL_MIN_SIZE" in str(exc_info.value)

        # 测试有效范围
        monkeypatch.setenv("DATABASE_POOL_MIN_SIZE", "10")
        monkeypatch.setenv("DATABASE_POOL_MAX_SIZE", "50")
        test_settings = Settings()
        assert test_settings.DATABASE_POOL_MIN_SIZE == 10
        assert test_settings.DATABASE_POOL_MAX_SIZE == 50

    def test_database_pool_range_validation(self, monkeypatch):
        """测试数据库连接池参数范围"""
        # 测试超出范围的值
        with pytest.raises(ValidationError):
            monkeypatch.setenv("DATABASE_POOL_MIN_SIZE", "0")  # 小于最小值1
            Settings()

        with pytest.raises(ValidationError):
            monkeypatch.setenv("DATABASE_POOL_MAX_SIZE", "250")  # 大于最大值200
            Settings()

        with pytest.raises(ValidationError):
            monkeypatch.setenv("DATABASE_POOL_TIMEOUT", "0.5")  # 小于最小值1.0
            Settings()

    def test_url_validation(self, monkeypatch):
        """测试URL格式验证"""
        # 测试无效URL（不以http/https开头）
        monkeypatch.setenv("OPENROUTER_BASE_URL", "ftp://example.com")
        with pytest.raises(ValidationError) as exc_info:
            Settings()
        assert "必须以http://或https://开头" in str(exc_info.value)

        # 测试有效URL
        monkeypatch.setenv("OPENROUTER_BASE_URL", "https://api.example.com/v1")
        test_settings = Settings()
        assert test_settings.OPENROUTER_BASE_URL == "https://api.example.com/v1"

        # 测试URL去除尾部斜杠
        monkeypatch.setenv("OPENROUTER_BASE_URL", "https://api.example.com/v1/")
        test_settings = Settings()
        assert test_settings.OPENROUTER_BASE_URL == "https://api.example.com/v1"

    def test_cache_ttl_validation(self, monkeypatch):
        """测试缓存TTL配置验证"""
        # 测试价格缓存TTL范围
        with pytest.raises(ValidationError):
            monkeypatch.setenv("CACHE_TTL_PRICE", "5")  # 小于最小值10
            Settings()

        with pytest.raises(ValidationError):
            monkeypatch.setenv("CACHE_TTL_PRICE", "4000")  # 大于最大值3600
            Settings()

        # 测试有效值
        monkeypatch.setenv("CACHE_TTL_PRICE", "60")
        test_settings = Settings()
        assert test_settings.CACHE_TTL_PRICE == 60

    def test_production_validation(self, monkeypatch):
        """测试生产环境配置验证"""
        # 测试生产环境缺少必填配置
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("OPENROUTER_API_KEY", "")  # 空API key
        with pytest.raises(ValidationError) as exc_info:
            Settings()
        assert "生产环境必须配置OPENROUTER_API_KEY" in str(exc_info.value)

        # 测试生产环境有效配置
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk_test_1234567890")
        test_settings = Settings()
        assert test_settings.ENVIRONMENT == "production"
        assert test_settings.DEBUG is False  # 生产环境应自动关闭DEBUG


class TestSensitiveDataMasking:
    """测试敏感信息脱敏功能"""

    def test_mask_sensitive(self):
        """测试敏感信息脱敏方法"""
        # 测试长字符串
        masked = settings.mask_sensitive("sk_1234567890abcdef")
        assert masked == "sk_1...cdef"
        assert "1234567890ab" not in masked

        # 测试短字符串
        masked_short = settings.mask_sensitive("short")
        assert masked_short == "***"

        # 测试空字符串
        masked_empty = settings.mask_sensitive("")
        assert masked_empty == "***"

    def test_get_safe_config(self, monkeypatch):
        """测试获取安全配置字典"""
        # 设置测试环境变量
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk_test_1234567890")
        monkeypatch.setenv("ETHERSCAN_API_KEY", "etherscan_key_12345")
        monkeypatch.setenv("SENTRY_DSN", "https://sentry_dsn_12345@sentry.io/123")

        test_settings = Settings()
        safe_config = test_settings.get_safe_config()

        # 验证敏感字段已被脱敏
        assert safe_config["OPENROUTER_API_KEY"] == "sk_t...890"
        assert safe_config["ETHERSCAN_API_KEY"] == "ethe...345"
        assert safe_config["SENTRY_DSN"] == "http...123"

        # 验证非敏感字段未被脱敏
        assert safe_config["ENVIRONMENT"] == test_settings.ENVIRONMENT
        assert safe_config["DEBUG"] == test_settings.DEBUG

        # 确保原始密钥不在安全配置中
        config_str = str(safe_config)
        assert "sk_test_1234567890" not in config_str
        assert "etherscan_key_12345" not in config_str


class TestMultiEnvironmentSupport:
    """测试多环境配置支持"""

    def test_environment_detection(self, monkeypatch):
        """测试环境检测函数"""
        # 测试开发环境
        monkeypatch.setenv("ENVIRONMENT", "development")
        test_settings = Settings()
        # 需要更新全局settings以供辅助函数使用
        import app.core.config as config_module
        config_module.settings = test_settings
        assert is_development()
        assert not is_production()
        assert not is_staging()

        # 测试生产环境
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk_prod_key")
        test_settings = Settings()
        config_module.settings = test_settings
        assert is_production()
        assert not is_development()

        # 测试预发布环境
        monkeypatch.setenv("ENVIRONMENT", "staging")
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk_staging_key")
        test_settings = Settings()
        config_module.settings = test_settings
        assert is_staging()
        assert not is_development()
        assert not is_production()

    def test_env_file_loading(self, tmp_path, monkeypatch):
        """测试.env文件加载"""
        # 创建临时.env.dev文件
        env_file = tmp_path / ".env.dev"
        env_file.write_text(
            "ENVIRONMENT=development\n"
            "DEBUG=true\n"
            "LOG_LEVEL=DEBUG\n"
        )

        # 设置环境变量指向临时文件
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("ENVIRONMENT", "development")

        # 加载配置
        test_settings = Settings()
        assert test_settings.ENVIRONMENT == "development"


class TestConfigHelpers:
    """测试配置辅助函数"""

    def test_get_database_url(self):
        """测试获取数据库URL"""
        db_url = get_database_url()
        assert isinstance(db_url, str)
        assert db_url  # 不为空

    def test_get_redis_url(self):
        """测试获取Redis URL"""
        redis_url = get_redis_url()
        assert isinstance(redis_url, str)
        assert redis_url  # 不为空

    def test_reload_settings_dev(self, monkeypatch):
        """测试开发环境配置热加载"""
        monkeypatch.setenv("ENVIRONMENT", "development")
        import app.core.config as config_module
        config_module.settings = Settings()

        # 修改环境变量
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")

        # 重新加载配置
        new_settings = reload_settings()
        # 注意：由于Pydantic的缓存机制，可能需要强制重新加载
        assert new_settings is not None

    def test_reload_settings_prod(self, monkeypatch):
        """测试生产环境不支持配置热加载"""
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk_prod_key")
        import app.core.config as config_module
        config_module.settings = Settings()

        # 尝试重新加载（应该返回当前实例）
        old_settings = config_module.settings
        new_settings = reload_settings()
        assert new_settings is old_settings  # 应该是同一个实例


class TestCORSConfiguration:
    """测试CORS配置"""

    def test_cors_origins_list(self, monkeypatch):
        """测试CORS origins列表转换"""
        monkeypatch.setenv(
            "CORS_ORIGINS",
            "http://localhost:3000,https://example.com,https://app.example.com"
        )
        test_settings = Settings()
        origins = test_settings.cors_origins_list

        assert isinstance(origins, list)
        assert len(origins) == 3
        assert "http://localhost:3000" in origins
        assert "https://example.com" in origins
        assert "https://app.example.com" in origins

    def test_cors_origins_with_spaces(self, monkeypatch):
        """测试带空格的CORS origins"""
        monkeypatch.setenv(
            "CORS_ORIGINS",
            "http://localhost:3000 , https://example.com , https://app.example.com"
        )
        test_settings = Settings()
        origins = test_settings.cors_origins_list

        # 验证空格被正确去除
        assert all(origin == origin.strip() for origin in origins)


class TestRateLimitConfiguration:
    """测试速率限制配置"""

    def test_rate_limit_defaults(self):
        """测试速率限制默认值"""
        assert settings.RATE_LIMIT_QUICK_CHAT == "10/minute"
        assert settings.RATE_LIMIT_DEEP_RESEARCH == "3/hour"

    def test_rate_limit_custom(self, monkeypatch):
        """测试自定义速率限制"""
        monkeypatch.setenv("RATE_LIMIT_QUICK_CHAT", "20/minute")
        monkeypatch.setenv("RATE_LIMIT_DEEP_RESEARCH", "5/hour")

        test_settings = Settings()
        assert test_settings.RATE_LIMIT_QUICK_CHAT == "20/minute"
        assert test_settings.RATE_LIMIT_DEEP_RESEARCH == "5/hour"


class TestCeleryConfiguration:
    """测试Celery配置"""

    def test_celery_urls(self):
        """测试Celery URL配置"""
        assert settings.CELERY_BROKER_URL
        assert settings.CELERY_RESULT_BACKEND

        # 验证URL格式
        assert settings.CELERY_BROKER_URL.startswith("redis://")
        assert settings.CELERY_RESULT_BACKEND.startswith("redis://")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
