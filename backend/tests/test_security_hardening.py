"""
安全加固测试用例
测试所有安全增强功能的正确性
"""
import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import status

from app.main import app
from app.core.config import settings
from app.core.security_validator import SecurityValidator
from app.api.middleware.required_auth import RequiredAuthMiddleware
from app.api.middleware.request_signature import RequestSignatureMiddleware


class TestSecurityConfiguration:
    """测试安全配置"""

    def test_jwt_secret_required(self):
        """测试JWT密钥配置要求"""
        # 临时保存原始设置
        original_jwt_secret = getattr(settings, 'JWT_SECRET_KEY', None)

        try:
            # 测试未设置JWT密钥的情况
            with patch.object(settings, 'JWT_SECRET_KEY', None):
                with pytest.raises(ValueError, match="JWT_SECRET_KEY"):
                    settings.validate_production_config()

            # 测试JWT密钥长度不足
            with patch.object(settings, 'JWT_SECRET_KEY', "short"):
                with pytest.raises(ValueError, match="长度至少32位"):
                    settings.validate_production_config()

            # 测试JWT密钥使用默认值
            with patch.object(settings, 'JWT_SECRET_KEY', "temp_development_key_only_replace_in_production_32chars"):
                with pytest.raises(ValueError, match="不能使用默认或临时JWT密钥"):
                    settings.validate_production_config()

        finally:
            # 恢复原始设置
            if original_jwt_secret:
                settings.JWT_SECRET_KEY = original_jwt_secret

    def test_cors_security_configuration(self):
        """测试CORS安全配置"""
        # 测试危险通配符
        dangerous_origins = ["*", "*.*", "https://*", "http://*"]

        for dangerous_origin in dangerous_origins:
            with patch.object(settings, 'CORS_ORIGINS', dangerous_origin):
                with patch.object(settings, 'ENVIRONMENT', 'production'):
                    with pytest.raises(ValueError, match="不安全的CORS配置"):
                        _ = settings.cors_origins_list

        # 测试有效配置
        valid_origins = "https://web3search.ai,https://www.web3search.ai"
        with patch.object(settings, 'CORS_ORIGINS', valid_origins):
            origins = settings.cors_origins_list
            assert len(origins) == 2
            assert "https://web3search.ai" in origins

    def test_signature_secret_configuration(self):
        """测试签名密钥配置"""
        # 测试启用签名验证但未配置密钥
        with patch.object(settings, 'ENABLE_SIGNATURE_VERIFICATION', True):
            with patch.object(settings, 'SIGNATURE_SECRET_KEY', None):
                with pytest.raises(ValueError):
                    # 这里应该在实际的签名验证中抛出错误
                    pass  # 在实际实现中会检查


class TestRequiredAuthMiddleware:
    """测试强制认证中间件"""

    def test_middleware_blocks_unauthenticated_requests(self):
        """测试中间件阻止未认证请求"""
        # ��建测试客户端
        client = TestClient(app)

        # 模拟生产环境
        with patch.object(settings, 'ENVIRONMENT', 'production'):
            # 测试未认证的API请求应该被阻止
            response = client.get("/api/v1/search?q=test")
            assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_middleware_allows_health_check(self):
        """测试中间件允许健康检查请求"""
        client = TestClient(app)

        with patch.object(settings, 'ENVIRONMENT', 'production'):
            # 健康检查应该不需要认证
            response = client.get("/health")
            assert response.status_code == status.HTTP_200_OK

    def test_middleware_allows_auth_endpoints(self):
        """测试中间件允许认证端点"""
        client = TestClient(app)

        with patch.object(settings, 'ENVIRONMENT', 'production'):
            # 登录端点应该不需要认证
            response = client.post("/api/v1/auth/login", json={
                "email": "test@example.com",
                "password": "password"
            })
            # 应该返回401而不是404，说明端点存在但认证失败
            assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_422_UNPROCESSABLE_ENTITY]


class TestRequestSignatureMiddleware:
    """测试请求签名验证中间件"""

    def test_signature_validation(self):
        """测试签名验证逻辑"""
        # 这里需要模拟签名验证的逻辑
        # 由于签名验证比较复杂，这里只测试基本��构
        middleware = RequestSignatureMiddleware(app, enabled=True)

        # 测试跳过路径检查
        request_mock = AsyncMock()
        request_mock.url.path = "/health"
        assert middleware._should_skip_signature(request_mock) == True

        request_mock.url.path = "/api/v1/search"
        assert middleware._should_skip_signature(request_mock) == False

    def test_signature_calculation(self):
        """测试签名计算"""
        middleware = RequestSignatureMiddleware(app, enabled=True)

        # 测试签名字符串构造
        signature = middleware._calculate_signature(
            method="GET",
            path="/api/v1/search",
            query="q=test",
            body=b'',
            timestamp="1234567890",
            api_key="test_api_key"
        )

        assert isinstance(signature, str)
        assert len(signature) == 64  # SHA256 hex长度

    def test_api_key_format_validation(self):
        """测试API密钥格式验证"""
        from app.api.middleware.request_signature import APIKeyManager

        # 测试有效格式
        valid_key = "web3search_abc123def456"
        assert APIKeyManager.validate_api_key_format(valid_key) == True

        # 测试无效格式
        invalid_keys = [
            "invalid_key",
            "short",
            "web3search",
            "test_key_too_short"
        ]
        for invalid_key in invalid_keys:
            assert APIKeyManager.validate_api_key_format(invalid_key) == False


class TestRBACSystem:
    """测试基于角色的��问控制系统"""

    @pytest.mark.asyncio
    async def test_permission_checking(self):
        """测试权限检查"""
        from app.services.rbac_service import RBACService

        # 创建模拟数据库会话
        mock_db = AsyncMock()

        # 模拟超级用户检查
        mock_db.execute.return_value.scalar.return_value = True

        rbac_service = RBACService(mock_db)

        # 超级用户应该拥有所有权限
        has_permission = await rbac_service.check_permission("user_123", "user", "read")
        assert has_permission == True

    @pytest.mark.asyncio
    async def test_permission_name_parsing(self):
        """测试权限名称解析"""
        from app.services.rbac_service import RBACService

        # 测试正常格式
        resource, action = RBACService.parse_permission_name("user:read")
        assert resource == "user"
        assert action == "read"

        # 测试异常格式
        with pytest.raises(ValueError):
            RBACService.parse_permission_name("invalid_format")

    def test_permission_constants(self):
        """测试权限常量"""
        from app.api.middleware.permission_auth import Permissions, Roles

        # 测试权限常量格式
        assert Permissions.USER_READ == "user:read"
        assert Permissions.ADMIN_WRITE == "admin:write"

        # 测试角色常量
        assert Roles.ADMIN == "admin"
        assert Roles.USER == "user"


class TestSecurityValidator:
    """测试安全验证器"""

    @pytest.mark.asyncio
    async def test_jwt_secret_validation(self):
        """测试JWT密钥验证"""
        validator = SecurityValidator()

        # 测试有效JWT密钥
        with patch.object(settings, 'JWT_SECRET_KEY', 'a' * 32):
            await validator._check_secrets()
            jwt_result = next(r for r in validator.results if 'JWT_SECRET_KEY' in r['name'])
            assert jwt_result['status'] == 'pass'

        # 重置结果
        validator.results = []

        # 测试无效JWT密钥
        with patch.object(settings, 'JWT_SECRET_KEY', 'short'):
            await validator._check_secrets()
            jwt_result = next(r for r in validator.results if 'JWT_SECRET_KEY' in r['name'])
            assert jwt_result['status'] == 'fail'

    @pytest.mark.asyncio
    async def test_cors_validation(self):
        """测试CORS配置验证"""
        validator = SecurityValidator()

        # 测试安全配置
        safe_origins = "https://web3search.ai,https://www.web3search.ai"
        with patch.object(settings, 'cors_origins_list', safe_origins.split(',')):
            await validator._check_cors_configuration()
            cors_result = next(r for r in validator.results if 'CORS' in r['name'])
            assert cors_result['status'] == 'pass'

        # 重置结果
        validator.results = []

        # 测试危险配置
        dangerous_origins = ["*"]
        with patch.object(settings, 'cors_origins_list', dangerous_origins):
            await validator._check_cors_configuration()
            cors_result = next(r for r in validator.results if 'CORS' in r['name'])
            assert cors_result['status'] == 'fail'

    @pytest.mark.asyncio
    async def test_environment_security_validation(self):
        """测试环境安全验证"""
        validator = SecurityValidator()

        # 测试生产环境启用DEBUG
        with patch.object(settings, 'DEBUG', True):
            with patch.object(settings, 'ENVIRONMENT', 'production'):
                await validator._check_environment_security()
                debug_result = next(r for r in validator.results if 'DEBUG' in r['name'])
                assert debug_result['status'] == 'fail'

    @pytest.mark.asyncio
    async def test_quick_security_check(self):
        """测试快速安全检查"""
        report = await SecurityValidator.quick_security_check()

        assert 'status' in report
        assert 'critical_issues' in report
        assert 'checks' in report
        assert isinstance(report['critical_issues'], int)

    @pytest.mark.asyncio
    async def test_comprehensive_security_validation(self):
        """测试全面安全验证"""
        validator = SecurityValidator()

        # 模拟安全配置
        with patch.object(settings, 'JWT_SECRET_KEY', 'a' * 32):
            with patch.object(settings, 'cors_origins_list', ['https://web3search.ai']):
                with patch.object(settings, 'DEBUG', False):
                    with patch.object(settings, 'ENVIRONMENT', 'production'):
                        report = await validator.validate_all()

        assert 'summary' in report
        assert 'checks' in report
        assert 'overall_status' in report
        assert report['summary']['total'] > 0


class TestSecurityEndpoints:
    """测试安全API端点"""

    def test_security_health_endpoint(self):
        """测试安全健康检查端点"""
        client = TestClient(app)

        response = client.get("/api/v1/security/health")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert 'status' in data
        assert 'critical_issues' in data
        assert 'timestamp' in data

    def test_security_config_endpoint_requires_auth(self):
        """测试安全配置端点需要认证"""
        client = TestClient(app)

        response = client.get("/api/v1/security/config")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_full_security_scan_requires_permission(self):
        """测试全面安全扫描需要权限"""
        client = TestClient(app)

        # 即使有认证，没有权限也应该被拒绝
        headers = {"Authorization": "Bearer fake_token"}
        response = client.get("/api/v1/security/full-scan", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED  # 假的token


class TestSecurityHeaders:
    """测试安全头配置"""

    def test_security_headers_in_render_config(self):
        """测试render.yaml中的安全头配置"""
        import yaml

        # 读取render.yaml配置
        with open('render.yaml', 'r') as f:
            config = yaml.safe_load(f)

        # 检查web服务的headers配置
        web_service = next(s for s in config['services'] if s['type'] == 'web')
        headers = web_service.get('headers', [])

        # 必需的安全头
        required_headers = [
            'X-Content-Type-Options',
            'X-Frame-Options',
            'X-XSS-Protection',
            'Strict-Transport-Security',
            'Content-Security-Policy',
            'Referrer-Policy',
            'Permissions-Policy'
        ]

        configured_headers = [h['name'] for h in headers]
        for required_header in required_headers:
            assert required_header in configured_headers, f"Missing security header: {required_header}"

    def test_hsts_header_configuration(self):
        """测试HSTS头配置"""
        import yaml

        with open('render.yaml', 'r') as f:
            config = yaml.safe_load(f)

        web_service = next(s for s in config['services'] if s['type'] == 'web')
        hsts_header = next(
            (h for h in web_service.get('headers', []) if h['name'] == 'Strict-Transport-Security'),
            None
        )

        assert hsts_header is not None, "HSTS header not configured"
        assert 'max-age=31536000' in hsts_header['value'], "HSTS max-age should be 1 year"
        assert 'includeSubDomains' in hsts_header['value'], "HSTS should include subdomains"
        assert 'preload' in hsts_header['value'], "HSTS should include preload"


class TestSecurityIntegration:
    """集成测试"""

    @pytest.mark.asyncio
    async def test_startup_security_validation(self):
        """测试启动时安全验证"""
        # 模拟安全配置检查
        with patch.object(settings, 'JWT_SECRET_KEY', 'a' * 32):
            with patch.object(settings, 'cors_origins_list', ['https://web3search.ai']):
                with patch.object(settings, 'DEBUG', False):
                    with patch.object(settings, 'ENVIRONMENT', 'production'):
                        # 这里不应该抛出异常
                        try:
                            settings.validate_production_config()
                        except ValueError:
                            pytest.fail("Security validation should pass with correct configuration")

    def test_middleware_order(self):
        """测试中间件顺序"""
        client = TestClient(app)

        # 检查中间件是否正确安装
        # 这是一个间接测试，通过检查响应来验证中间件是否生效
        with patch.object(settings, 'ENVIRONMENT', 'production'):
            # 未认证请求应该被强制认证中间件阻止
            response = client.get("/api/v1/search?q=test")
            assert response.status_code == status.HTTP_401_UNAUTHORIZED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])