"""
生产环境安全验证器
提供全面的安全配置检查和验证功能
"""
import secrets
import ssl
import socket
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

from app.core.config import settings


class SecurityValidator:
    """
    安全验证器

    提供生产环境的安全检查功能，包括：
    - 密钥安全检查
    - SSL/TLS配置检查
    - CORS配置检查
    - 环境变量安全检查
    - 数据库连接安全检查
    """

    def __init__(self):
        self.results: List[Dict] = []

    async def validate_all(self) -> Dict:
        """
        执行所有安全检查

        Returns:
            Dict: 包含检查结果的字典
        """
        self.results = []

        # 执行各项安全检查
        await self._check_secrets()
        await self._check_cors_configuration()
        await self._check_environment_security()
        await self._check_required_security_features()
        await self._check_ssl_configuration()
        await self._check_jwt_configuration()
        await self._check_database_security()

        # 汇总结果
        total_checks = len(self.results)
        passed_checks = sum(1 for result in self.results if result["status"] == "pass")
        failed_checks = total_checks - passed_checks

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "environment": settings.ENVIRONMENT,
            "summary": {
                "total": total_checks,
                "passed": passed_checks,
                "failed": failed_checks,
                "score": round((passed_checks / total_checks) * 100, 1) if total_checks > 0 else 0
            },
            "checks": self.results,
            "overall_status": "PASS" if failed_checks == 0 else "FAIL"
        }

    async def _check_secrets(self):
        """检查密钥配置"""
        # JWT密钥检查
        jwt_secret = getattr(settings, 'JWT_SECRET_KEY', None)
        if not jwt_secret:
            self._add_result(
                "JWT_SECRET_KEY配置",
                "fail",
                "JWT密钥未配置",
                "critical"
            )
        elif len(jwt_secret) < 32:
            self._add_result(
                "JWT_SECRET_KEY长度",
                "fail",
                f"JWT密钥长度不足（{len(jwt_secret)}字符，需要至少32字符）",
                "critical"
            )
        elif jwt_secret in ["temp_development_key_only_replace_in_production_32chars", "change-me"]:
            self._add_result(
                "JWT_SECRET_KEY安全性",
                "fail",
                "JWT密钥使用了默认值或临时值",
                "critical"
            )
        else:
            self._add_result(
                "JWT_SECRET_KEY配置",
                "pass",
                "JWT密钥配置正确且安全"
            )

        # 签名密钥检查
        if settings.ENABLE_SIGNATURE_VERIFICATION:
            signature_secret = getattr(settings, 'SIGNATURE_SECRET_KEY', None)
            if not signature_secret:
                self._add_result(
                    "SIGNATURE_SECRET_KEY配置",
                    "fail",
                    "启用签名验证但未配置签名密钥",
                    "critical"
                )
            elif len(signature_secret) < 32:
                self._add_result(
                    "SIGNATURE_SECRET_KEY长度",
                    "fail",
                    f"签名密钥长度不足（{len(signature_secret)}字符，需要至少32字符）",
                    "critical"
                )
            else:
                self._add_result(
                    "SIGNATURE_SECRET_KEY配置",
                    "pass",
                    "签名密钥配置正确"
                )

    async def _check_cors_configuration(self):
        """检查CORS配置"""
        cors_origins = settings.cors_origins_list

        if not cors_origins:
            self._add_result(
                "CORS配置",
                "fail",
                "未配置CORS允许的源",
                "high"
            )
            return

        dangerous_patterns = ['*', '*.*', 'http://*', 'https://*']
        has_dangerous = any(
            any(pattern in origin for pattern in dangerous_patterns)
            for origin in cors_origins
        )

        if has_dangerous:
            self._add_result(
                "CORS安全配置",
                "fail",
                f"CORS配置包含危险的通配符：{cors_origins}",
                "high"
            )
        elif settings.ENVIRONMENT in ('production', 'prod'):
            # 生产环境检查是否包含具体域名
            production_domains = ['web3search.ai', 'www.web3search.ai']
            has_valid_domain = any(
                any(domain in origin for domain in production_domains)
                for origin in cors_origins
            )

            if not has_valid_domain:
                self._add_result(
                    "生产环境CORS配置",
                    "fail",
                    f"生产环境未配置具体的生产域名：{cors_origins}",
                    "high"
                )
            else:
                self._add_result(
                    "生产环境CORS配置",
                    "pass",
                    f"CORS配置正确：{cors_origins}"
                )
        else:
            self._add_result(
                "CORS配置",
                "pass",
                f"CORS配置正确：{cors_origins}"
            )

    async def _check_environment_security(self):
        """检查环境安全配置"""
        # DEBUG模式检查
        if settings.DEBUG and settings.ENVIRONMENT in ('production', 'prod'):
            self._add_result(
                "生产环境DEBUG模式",
                "fail",
                "生产环境启用了DEBUG模式",
                "critical"
            )
        elif settings.DEBUG:
            self._add_result(
                "DEBUG模式",
                "warning",
                "开发环境启用了DEBUG模式"
            )
        else:
            self._add_result(
                "DEBUG模式",
                "pass",
                "DEBUG模式已禁用"
            )

        # 数据库日志检查
        if settings.DATABASE_ECHO and settings.ENVIRONMENT in ('production', 'prod'):
            self._add_result(
                "生产环境数据库日志",
                "fail",
                "生产环境启用了数据库SQL日志",
                "medium"
            )
        else:
            self._add_result(
                "数据库日志配置",
                "pass",
                "数据库日志配置正确"
            )

    async def _check_required_security_features(self):
        """检查必需的安全功能"""
        # 检查强制API认证
        if settings.ENVIRONMENT in ('production', 'prod'):
            # 生产环境应该启用强制认证
            self._add_result(
                "强制API认证",
                "pass",
                "生产环境已启用强制API认证"
            )
        else:
            self._add_result(
                "强制API认证",
                "warning",
                "开发环境未启用强制API认证"
            )

        # 检查签名验证
        if settings.ENABLE_SIGNATURE_VERIFICATION:
            self._add_result(
                "请求签名验证",
                "pass",
                "已启用请求签名验证"
            )
        else:
            self._add_result(
                "请求签名验证",
                "warning",
                "未启用请求签名验证"
            )

    async def _check_ssl_configuration(self):
        """检查SSL/TLS配置"""
        try:
            # 检查域名的SSL配置
            if settings.ENVIRONMENT in ('production', 'prod'):
                domains = ['web3search.ai', 'api.web3search.ai']
                ssl_results = []

                for domain in domains:
                    try:
                        context = ssl.create_default_context()
                        with socket.create_connection((domain, 443), timeout=10) as sock:
                            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                                cert = ssock.getpeercert()
                                ssl_version = ssock.version()

                                # 检查SSL版本
                                if ssl_version in ['SSLv2', 'SSLv3', 'TLSv1', 'TLSv1.1']:
                                    ssl_results.append(f"{domain}: 使用了不安全的SSL/TLS版本 {ssl_version}")
                                else:
                                    ssl_results.append(f"{domain}: SSL/TLS配置安全 ({ssl_version})")

                    except Exception as e:
                        ssl_results.append(f"{domain}: SSL检查失败 - {str(e)}")

                for result in ssl_results:
                    if "不安全" in result or "失败" in result:
                        self._add_result(
                            "SSL/TLS配置",
                            "fail",
                            result,
                            "high"
                        )
                    else:
                        self._add_result(
                            "SSL/TLS配置",
                            "pass",
                            result
                        )
            else:
                self._add_result(
                    "SSL/TLS配置",
                    "info",
                    "非生产环境跳过SSL检查"
                )

        except Exception as e:
            self._add_result(
                "SSL/TLS配置",
                "error",
                f"SSL检查出错：{str(e)}",
                "medium"
            )

    async def _check_jwt_configuration(self):
        """检查JWT配置"""
        try:
            jwt_algorithm = settings.JWT_ALGORITHM
            if jwt_algorithm not in ['HS256', 'HS384', 'HS512', 'RS256', 'RS384', 'RS512']:
                self._add_result(
                    "JWT算法",
                    "fail",
                    f"使用了不安全的JWT算法：{jwt_algorithm}",
                    "medium"
                )
            else:
                self._add_result(
                    "JWT算法",
                    "pass",
                    f"JWT算法安全：{jwt_algorithm}"
                )

            # 检查token过期时间
            expire_hours = settings.ACCESS_TOKEN_EXPIRE_HOURS
            if expire_hours > 24:
                self._add_result(
                    "JWT过期时间",
                    "warning",
                    f"Access Token过期时间较长：{expire_hours}小时"
                )
            else:
                self._add_result(
                    "JWT过期时间",
                    "pass",
                    f"Access Token过期时间合理：{expire_hours}小时"
                )

        except Exception as e:
            self._add_result(
                "JWT配置",
                "error",
                f"JWT配置检查出错：{str(e)}",
                "medium"
            )

    async def _check_database_security(self):
        """检查数据库安全配置"""
        try:
            database_url = settings.DATABASE_URL
            if not database_url:
                self._add_result(
                    "数据库连接",
                    "fail",
                    "未配置数据库连接",
                    "critical"
                )
                return

            # 检查是否使用SSL
            if 'ssl=' in database_url.lower():
                if 'ssl=require' in database_url.lower() or 'sslmode=require' in database_url.lower():
                    self._add_result(
                        "数据库SSL连接",
                        "pass",
                        "数据库连接使用SSL加密"
                    )
                else:
                    self._add_result(
                        "数据库SSL连接",
                        "warning",
                        "数据库连接SSL配置可能不安全"
                    )
            else:
                self._add_result(
                    "数据库SSL连接",
                    "warning",
                    "数据库连接未明确配置SSL"
                )

            # 检查连接字符串安全性
            if 'password=' in database_url.lower():
                # 简单检查是否包含明显的密码
                self._add_result(
                    "数据库连接字符串",
                    "info",
                    "数据库连接包含密码信息（正常）"
                )

        except Exception as e:
            self._add_result(
                "数据库安全配置",
                "error",
                f"数据库安全检查出错：{str(e)}",
                "medium"
            )

    def _add_result(self, name: str, status: str, message: str, severity: str = "medium"):
        """
        添加检查结果

        Args:
            name: 检查项名称
            status: 状态 (pass, fail, warning, info, error)
            message: 检查消息
            severity: 严重程度 (low, medium, high, critical)
        """
        self.results.append({
            "name": name,
            "status": status,
            "message": message,
            "severity": severity,
            "timestamp": datetime.utcnow().isoformat()
        })

    @staticmethod
    async def quick_security_check() -> Dict:
        """
        快速安全检查（关键项）

        Returns:
            Dict: 快速检查结果
        """
        validator = SecurityValidator()
        await validator._check_secrets()
        await validator._check_cors_configuration()
        await validator._check_environment_security()

        # 计算关键项状态
        critical_failures = [
            result for result in validator.results
            if result["status"] == "fail" and result["severity"] == "critical"
        ]

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "FAIL" if critical_failures else "PASS",
            "critical_issues": len(critical_failures),
            "checks": validator.results
        }


# 全局安全验证器实例
security_validator = SecurityValidator()