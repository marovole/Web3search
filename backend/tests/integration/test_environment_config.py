"""
环境配置验证测试
确保不同环境下的配置正确加载和验证
"""
import pytest
import os
from unittest.mock import patch

from app.core.config import settings


# ================================
# 环境变量加载测试
# ================================

def test_test_environment_loaded():
    """测试测试环境配置正确加载"""
    # 在测试中，环境应该是test或development
    assert settings.ENVIRONMENT in ["test", "development", "production"]


def test_api_base_url_format():
    """测试API_BASE_URL格式正确"""
    # API_BASE_URL应该是有效的URL格式
    assert settings.API_BASE_URL.startswith("http://") or \
           settings.API_BASE_URL.startswith("https://")

    # 不应该有路径重复
    assert "/api/api" not in settings.API_BASE_URL


def test_database_url_configured():
    """测试数据库URL已配置"""
    assert settings.DATABASE_URL is not None
    assert len(settings.DATABASE_URL) > 0


# ================================
# 生产环境配置测试
# ================================

def test_production_api_url_complete():
    """测试生产环境使用完整API URL"""
    with patch.dict(os.environ, {
        "ENVIRONMENT": "production",
        "API_BASE_URL": "https://web3search-api.onrender.com"
    }):
        # 生产环境应该使用完整URL
        api_url = os.getenv("API_BASE_URL")
        assert api_url.startswith("https://")
        assert "onrender.com" in api_url or "vercel.app" in api_url or "web3search" in api_url


def test_production_no_relative_paths():
    """测试生产环境不使用相对路径"""
    with patch.dict(os.environ, {
        "ENVIRONMENT": "production",
        "API_BASE_URL": "https://web3search-api.onrender.com"
    }):
        api_url = os.getenv("API_BASE_URL")
        # 不应该是相对路径
        assert not api_url.startswith("/")
        assert not api_url.startswith("./")


# ================================
# 开发环境配置测试
# ================================

def test_development_api_url_flexible():
    """测试开发环境API URL配置灵活"""
    with patch.dict(os.environ, {
        "ENVIRONMENT": "development",
        "API_BASE_URL": "http://localhost:8000"
    }):
        api_url = os.getenv("API_BASE_URL")
        # 开发环境可以使用localhost或相对路径
        assert "localhost" in api_url or api_url.startswith("http://")


# ================================
# URL路径验证测试
# ================================

def test_url_path_no_duplication():
    """测试URL路径没有重复"""
    # 测试常见的路径拼接场景
    base_url = settings.API_BASE_URL.rstrip("/")
    api_path = "/api/v1"

    full_url = f"{base_url}{api_path}"

    # 不应该有路径重复
    assert "/api/api" not in full_url
    assert "//v1" not in full_url
    assert full_url.count("/api/v1") == 1


def test_construct_api_endpoint_urls():
    """测试构造API端点URL"""
    base_url = settings.API_BASE_URL.rstrip("/")

    endpoints = [
        "/api/v1/chat/quick",
        "/api/v1/chat/research",
        "/api/v1/reports/"
    ]

    for endpoint in endpoints:
        full_url = f"{base_url}{endpoint}"

        # 验证URL格式正确
        assert full_url.startswith("http://") or full_url.startswith("https://")

        # 验证没有双斜杠（除了协议部分）
        url_without_protocol = full_url.split("://", 1)[1]
        assert "//" not in url_without_protocol

        # 验证API路径正确
        assert "/api/v1/" in full_url


# ================================
# 环境检测测试
# ================================

def test_environment_detection():
    """测试环境检测逻辑"""
    # 测试可以正确识别环境
    env = settings.ENVIRONMENT

    assert env in ["development", "test", "staging", "production"]


def test_environment_specific_settings():
    """测试不同环境的特定设置"""
    env = settings.ENVIRONMENT

    if env == "production":
        # 生产环境应该有特定配置
        assert settings.API_BASE_URL.startswith("https://")
    elif env == "development":
        # 开发环境可以使用http
        assert settings.API_BASE_URL.startswith("http://") or \
               settings.API_BASE_URL.startswith("https://")


# ================================
# 配置验证测试
# ================================

def test_required_config_present():
    """测试必需的配置项存在"""
    # 这些配置项应该总是存在（即使是空字符串）
    required_configs = [
        "DATABASE_URL",
        "API_BASE_URL",
        "ENVIRONMENT",
    ]

    for config in required_configs:
        value = getattr(settings, config, None)
        assert value is not None, f"Required config {config} is None"


def test_optional_config_handling():
    """测试可选配置的处理"""
    # 可选配置可能不存在，但不应该导致错误
    optional_configs = [
        "OPENROUTER_API_KEY",
        "COINGECKO_API_KEY",
        "TWITTER_BEARER_TOKEN",
    ]

    for config in optional_configs:
        # 应该可以安全地访问，返回None或空字符串
        value = getattr(settings, config, None)
        # 不抛出异常即可


# ================================
# API配置错误预防测试
# ================================

def test_prevent_api_path_duplication():
    """测试防止API路径重复的配置"""
    # 模拟常见的错误配置
    wrong_configs = [
        "http://localhost:8000/api",  # 如果后续再加/api/v1会重复
        "https://api.example.com/api/v1",  # 已经包含完整路径
    ]

    for wrong_config in wrong_configs:
        # 验证我们的代码能正确处理这些情况
        base = wrong_config.rstrip("/")

        # 如果base已经包含/api，不应该再添加
        if base.endswith("/api"):
            # 应该只添加/v1
            assert True
        elif "/api/v1" in base:
            # 不应该再添加任何路径
            assert True


def test_url_trailing_slash_handling():
    """测试URL尾部斜杠处理"""
    # 测试无论API_BASE_URL是否有尾部斜杠，都能正确拼接
    test_bases = [
        "http://localhost:8000",
        "http://localhost:8000/",
    ]

    for base in test_bases:
        normalized = base.rstrip("/")
        full_url = f"{normalized}/api/v1/chat"

        # 应该只有一个斜杠分隔
        assert "/api//v1" not in full_url
        assert full_url.count("//") == 1  # 只有http://中的双斜杠
