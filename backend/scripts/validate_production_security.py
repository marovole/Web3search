#!/usr/bin/env python3
"""
生产环境安全配置验证脚本
验证所有生产环境安全配置是否正确设置
"""
import os
import sys
import yaml
import json
from pathlib import Path
from typing import Dict, List, Any


class ProductionSecurityValidator:
    """生产环境安全验证器"""

    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path(__file__).parent.parent
        self.results: List[Dict] = []

    def validate_all(self) -> Dict:
        """验证所有生产环境安全配置"""
        print("🔒 开始验证生产环境安全配置...")
        print("=" * 60)

        # 1. 验证render.yaml配置
        self._validate_render_yaml()

        # 2. 验证环境变量配置
        self._validate_environment_variables()

        # 3. 验证安全中间件配置
        self._validate_security_middleware()

        # 4. 验证CORS配置
        self._validate_cors_config()

        # 5. 验证安全头配置
        self._validate_security_headers()

        # 6. 验证认证配置
        self._validate_authentication()

        return self._generate_report()

    def _validate_render_yaml(self):
        """验证render.yaml配置"""
        print("\n📄 验证render.yaml配置...")

        render_file = self.project_root / "render.yaml"
        if not render_file.exists():
            self.results.append({
                "category": "render.yaml",
                "status": "FAIL",
                "message": "render.yaml文件不存在",
                "details": []
            })
            return

        try:
            with open(render_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            issues = []
            checks_passed = 0

            # 检查必需的环境变量
            web_service = self._find_web_service(config)
            if web_service:
                env_vars = web_service.get('envVars', [])

                # 检查JWT密钥配置
                jwt_config = next((var for var in env_vars if var.get('key') == 'JWT_SECRET_KEY'), None)
                if jwt_config and jwt_config.get('sync') == False:
                    checks_passed += 1
                else:
                    issues.append("JWT_SECRET_KEY未正确配置sync: false")

                # 检查签名密钥配置
                signature_config = next((var for var in env_vars if var.get('key') == 'SIGNATURE_SECRET_KEY'), None)
                if signature_config and signature_config.get('sync') == False:
                    checks_passed += 1
                else:
                    issues.append("SIGNATURE_SECRET_KEY未正确配置")

                # 检查签名验证启用
                sig_verify_config = next((var for var in env_vars if var.get('key') == 'ENABLE_SIGNATURE_VERIFICATION'), None)
                if sig_verify_config and sig_verify_config.get('value') == 'true':
                    checks_passed += 1
                else:
                    issues.append("ENABLE_SIGNATURE_VERIFICATION未启用")

                # 检查CORS配置
                cors_config = next((var for var in env_vars if var.get('key') == 'CORS_ORIGINS'), None)
                if cors_config:
                    cors_origins = cors_config.get('value', '')
                    if 'web3search.ai' in cors_origins:
                        checks_passed += 1
                    else:
                        issues.append(f"CORS_ORIGINS未配置生产域名：{cors_origins}")
                else:
                    issues.append("CORS_ORIGINS未配置")

                # 检查安全头配置
                headers = web_service.get('headers', [])
                required_headers = [
                    'X-Content-Type-Options',
                    'X-Frame-Options',
                    'Strict-Transport-Security',
                    'Content-Security-Policy',
                    'Referrer-Policy',
                    'Permissions-Policy'
                ]

                configured_headers = [h.get('name') for h in headers]
                for header in required_headers:
                    if header in configured_headers:
                        checks_passed += 1
                    else:
                        issues.append(f"缺少安全头：{header}")

            # 检查生产环境配置
            env_config = next((var for var in env_vars if var.get('key') == 'ENVIRONMENT'), None)
            if env_config and env_config.get('value') == 'production':
                checks_passed += 1
            else:
                issues.append("ENVIRONMENT未设置为production")

            debug_config = next((var for var in env_vars if var.get('key') == 'DEBUG'), None)
            if debug_config and debug_config.get('value') == 'false':
                checks_passed += 1
            else:
                issues.append("DEBUG未设置为false")

            total_checks = checks_passed + len(issues)
            status = "PASS" if len(issues) == 0 else "FAIL"

            self.results.append({
                "category": "render.yaml",
                "status": status,
                "message": f"通过 {checks_passed}/{total_checks} 项检查",
                "details": issues,
                "checks_passed": checks_passed,
                "total_checks": total_checks
            })

            print(f"   render.yaml验证完成，通过 {checks_passed}/{total_checks} 项检查")
            if issues:
                print(f"   发现 {len(issues)} 个问题")

        except Exception as e:
            self.results.append({
                "category": "render.yaml",
                "status": "ERROR",
                "message": f"验证失败：{e}",
                "details": []
            })
            print(f"   ❌ render.yaml验证失败：{e}")

    def _validate_environment_variables(self):
        """验证环境变量配置"""
        print("\n🌍 验证环境变量配置...")

        issues = []
        checks_passed = 0

        # 检查.env文件
        env_files = ['.env.production', '.env']
        for env_file in env_files:
            env_path = self.project_root / env_file
            if env_path.exists():
                try:
                    with open(env_path, 'r') as f:
                        content = f.read()

                    # 检查必需的环境变量
                    required_vars = ['JWT_SECRET_KEY', 'SIGNATURE_SECRET_KEY']
                    for var in required_vars:
                        if f'{var}=' in content:
                            # 检查是否包含默认值或示例值
                            if any(bad_value in content.lower() for bad_value in ['change-me', 'default', 'example', 'temp']):
                                issues.append(f"{env_file}中{var}包含默认值")
                            else:
                                checks_passed += 1
                        else:
                            issues.append(f"{env_file}中缺少{var}")

                except Exception as e:
                    issues.append(f"读取{env_file}失败：{e}")

        total_checks = checks_passed + len(issues)
        status = "PASS" if len(issues) == 0 else "FAIL"

        self.results.append({
            "category": "环境变量",
            "status": status,
            "message": f"通过 {checks_passed}/{total_checks} 项检查",
            "details": issues,
            "checks_passed": checks_passed,
            "total_checks": total_checks
        })

        print(f"   环境变量验证完成，通过 {checks_passed}/{total_checks} 项检查")

    def _validate_security_middleware(self):
        """验证安全中间件配置"""
        print("\n🛡️ 验证安全中间件配置...")

        issues = []
        checks_passed = 0

        # 检查主应用文件中的中间件配置
        main_file = self.project_root / "app" / "main.py"
        if main_file.exists():
            try:
                with open(main_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 检查强制认证中间件
                if 'RequiredAuthMiddleware' in content:
                    checks_passed += 1
                    # 检查是否在生产环境启用
                    if 'if settings.ENVIRONMENT in (\'production\', \'prod\')' in content:
                        checks_passed += 1
                    else:
                        issues.append("强制认证中间件未配置为仅在生产环境启用")
                else:
                    issues.append("未找到RequiredAuthMiddleware配置")

                # 检查签名验证中间件
                if 'RequestSignatureMiddleware' in content:
                    checks_passed += 1
                    if 'ENABLE_SIGNATURE_VERIFICATION' in content:
                        checks_passed += 1
                    else:
                        issues.append("签名验证中间件未与配置关联")
                else:
                    issues.append("未找到RequestSignatureMiddleware配置")

                # 检查安全验证器
                if 'security_validator' in content:
                    checks_passed += 1
                    if 'validate_all' in content:
                        checks_passed += 1
                    else:
                        issues.append("安全验证器未在启动时执行")
                else:
                    issues.append("未找到安全验证器配置")

            except Exception as e:
                issues.append(f"读取main.py失败：{e}")

        total_checks = checks_passed + len(issues)
        status = "PASS" if len(issues) == 0 else "FAIL"

        self.results.append({
            "category": "安全中间件",
            "status": status,
            "message": f"通过 {checks_passed}/{total_checks} 项检查",
            "details": issues,
            "checks_passed": checks_passed,
            "total_checks": total_checks
        })

        print(f"   安全中间件验证完成，通过 {checks_passed}/{total_checks} 项检查")

    def _validate_cors_config(self):
        """验证CORS配置"""
        print("\n🌐 验证CORS配置...")

        issues = []
        checks_passed = 0

        # 检查CORS配置文件
        config_file = self.project_root / "app" / "core" / "config.py"
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 检查CORS验证逻辑
                if 'cors_origins_list' in content and 'def cors_origins_list' in content:
                    checks_passed += 1

                    # 检查生产环境CORS验证
                    if 'production' in content and 'dangerous_patterns' in content:
                        checks_passed += 1
                    else:
                        issues.append("CORS配置缺少生产环境安全检查")
                else:
                    issues.append("未找到CORS配置")

                # 检查默认CORS配置
                if 'localhost:3000' in content:
                    checks_passed += 1  # 开发环境配置
                else:
                    issues.append("缺少开发环境CORS配置")

            except Exception as e:
                issues.append(f"读取CORS配置失败：{e}")

        total_checks = checks_passed + len(issues)
        status = "PASS" if len(issues) == 0 else "FAIL"

        self.results.append({
            "category": "CORS配置",
            "status": status,
            "message": f"通过 {checks_passed}/{total_checks} 项检查",
            "details": issues,
            "checks_passed": checks_passed,
            "total_checks": total_checks
        })

        print(f"   CORS配置验证完成，通过 {checks_passed}/{total_checks} 项检查")

    def _validate_security_headers(self):
        """验证安全头配置"""
        print("\n🔒 验证安全头配置...")

        issues = []
        checks_passed = 0

        # 检查render.yaml中的安全头
        render_file = self.project_root / "render.yaml"
        if render_file.exists():
            try:
                with open(render_file, 'r') as f:
                    config = yaml.safe_load(f)

                web_service = self._find_web_service(config)
                if web_service:
                    headers = web_service.get('headers', [])

                    required_headers = {
                        'X-Content-Type-Options': 'nosniff',
                        'X-Frame-Options': 'DENY',
                        'X-XSS-Protection': '1; mode=block',
                        'Strict-Transport-Security': 'max-age=31536000',
                        'Referrer-Policy': 'strict-origin-when-cross-origin',
                        'Permissions-Policy': 'camera=(), microphone=()'
                    }

                    configured_headers = {h.get('name'): h.get('value') for h in headers}

                    for header_name, expected_value in required_headers.items():
                        header_config = next(
                            (h for h in headers if h.get('name') == header_name),
                            None
                        )

                        if header_config:
                            if header_name == 'Strict-Transport-Security':
                                # HSTS包含必需的属性
                                if 'max-age=31536000' in header_config.get('value', ''):
                                    checks_passed += 1
                                else:
                                    issues.append(f"{header_name}配置不正确")
                            elif header_name == 'Content-Security-Policy':
                                # CSP配置
                                if 'default-src' in header_config.get('value', ''):
                                    checks_passed += 1
                                else:
                                    issues.append(f"{header_name}缺少default-src")
                            else:
                                checks_passed += 1
                        else:
                            issues.append(f"缺少安全头：{header_name}")

            except Exception as e:
                issues.append(f"读取render.yaml失败：{e}")

        total_checks = checks_passed + len(issues)
        status = "PASS" if len(issues) == 0 else "FAIL"

        self.results.append({
            "category": "安全头",
            "status": status,
            "message": f"通过 {checks_passed}/{total_checks} 项检查",
            "details": issues,
            "checks_passed": checks_passed,
            "total_checks": total_checks
        })

        print(f"   安全头验证完成，通过 {checks_passed}/{total_checks} 项检查")

    def _validate_authentication(self):
        """验证认证配置"""
        print("\n🔑 验证认证配置...")

        issues = []
        checks_passed = 0

        # 检查JWT配置
        config_file = self.project_root / "app" / "core" / "config.py"
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 检查JWT强制配置
                if 'JWT_SECRET_KEY.*Field.*\.\.\.' in content or 'JWT_SECRET_KEY.*Ellipsis' in content:
                    checks_passed += 1  # 强制配置
                else:
                    issues.append("JWT_SECRET_KEY未设置为强制配置")

                # 检查JWT验证逻辑
                if 'validate_production_config' in content:
                    checks_passed += 1

                    # 检查生产环境验证
                    if 'forbidden_keys' in content and 'temp_development_key' in content:
                        checks_passed += 1
                    else:
                        issues.append("JWT生产环境验证不完整")
                else:
                    issues.append("未找到生产环境配置验证")

                # 检查签名验证配置
                if 'SIGNATURE_SECRET_KEY' in content:
                    checks_passed += 1

                if 'ENABLE_SIGNATURE_VERIFICATION' in content:
                    checks_passed += 1

            except Exception as e:
                issues.append(f"读取配置文件失败：{e}")

        # 检查RBAC配置
        rbac_files = [
            self.project_root / "app" / "models" / "rbac.py",
            self.project_root / "app" / "services" / "rbac_service.py"
        ]

        for rbac_file in rbac_files:
            if rbac_file.exists():
                checks_passed += 1

        total_checks = checks_passed + len(issues)
        status = "PASS" if len(issues) == 0 else "FAIL"

        self.results.append({
            "category": "认证配置",
            "status": status,
            "message": f"通过 {checks_passed}/{total_checks} 项检查",
            "details": issues,
            "checks_passed": checks_passed,
            "total_checks": total_checks
        })

        print(f"   认证配置验证完成，通过 {checks_passed}/{total_checks} 项检查")

    def _find_web_service(self, config: Dict) -> Dict:
        """查找web服务配置"""
        services = config.get('services', [])
        for service in services:
            if service.get('type') == 'web':
                return service
        return {}

    def _generate_report(self) -> Dict:
        """生成验证报告"""
        total_checks = sum(result.get("checks_passed", 0) for result in self.results)
        total_possible = sum(result.get("total_checks", 0) for result in self.results)
        failed_categories = sum(
            1 for result in self.results
            if result["status"] == "FAIL"
        )

        success_rate = (total_checks / total_possible * 100) if total_possible > 0 else 0
        overall_status = "PASS" if failed_categories == 0 and success_rate >= 90 else "FAIL"

        return {
            "timestamp": "2024-01-01T00:00:00Z",
            "summary": {
                "total_checks": total_possible,
                "passed_checks": total_checks,
                "success_rate": round(success_rate, 1),
                "failed_categories": failed_categories,
                "overall_status": overall_status
            },
            "categories": self.results,
            "recommendations": self._generate_recommendations(),
            "deployment_ready": overall_status == "PASS"
        }

    def _generate_recommendations(self) -> List[str]:
        """生成部署建议"""
        recommendations = []

        for result in self.results:
            if result["status"] == "FAIL":
                category = result["category"]
                recommendations.append(f"修复{category}配置问题：{result['message']}")

                for detail in result.get("details", [])[:3]:  # 只显示前3个问题
                    recommendations.append(f"  - {detail}")

        if not recommendations:
            recommendations.append("✅ 所有生产环境安全配置验证通过，系统已准备好部署")

        return recommendations


def main():
    """主函数"""
    validator = ProductionSecurityValidator()

    try:
        report = validator.validate_all()

        # 打印摘要
        print("\n" + "=" * 60)
        print("📊 生产环境安全配置验证报告")
        print("=" * 60)
        print(f"整体状态：{report['summary']['overall_status']}")
        print(f"验证通过：{report['summary']['passed_checks']}/{report['summary']['total_checks']}")
        print(f"成功率：{report['summary']['success_rate']}%")
        print(f"部署就绪：{'是' if report['deployment_ready'] else '否'}")

        # 打印各类别结果
        print("\n📋 分类结果：")
        for category in report['categories']:
            status_icon = "✅" if category['status'] == 'PASS' else "❌" if category['status'] == 'FAIL' else "⚠️"
            print(f"   {status_icon} {category['category']}：{category['message']}")

        # 打印建议
        if report['recommendations']:
            print("\n💡 部署建议：")
            for i, rec in enumerate(report['recommendations'], 1):
                print(f"   {i}. {rec}")

        # 保存报告
        report_file = Path("production_security_validation.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\n📄 详细报告已保存到：{report_file}")

        # 根据验证结果设置退出码
        if report['deployment_ready']:
            print("\n✅ 生产环境安全配置验证通过，系统已准备好部署")
            sys.exit(0)
        else:
            print("\n❌ 生产环境安全配置验证失败，请修复问题后重新验证")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n⚠️ 验证被用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ 验证过程中出错：{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()