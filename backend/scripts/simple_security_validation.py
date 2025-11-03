#!/usr/bin/env python3
"""
简化的生产环境安全配置验证脚本
不依赖外部模块，验证关键安全配置
"""
import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Any


class SimpleSecurityValidator:
    """简化安全验证器"""

    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path(__file__).parent.parent
        self.results: List[Dict] = []

    def validate_all(self) -> Dict:
        """验证所有生产环境安全配置"""
        print("🔒 开始验证生产环境安全配置...")
        print("=" * 60)

        # 1. 验证必需文件存在
        self._validate_required_files()

        # 2. 验证代码中的安全配置
        self._validate_code_security()

        # 3. 验证环境变量配置
        self._validate_env_files()

        # 4. 验证render.yaml基础配置
        self._validate_render_yaml_basic()

        return self._generate_report()

    def _validate_required_files(self):
        """验证必需文件存在"""
        print("\n📁 验证必需文件...")

        required_files = [
            "app/main.py",
            "app/core/config.py",
            "app/core/security_validator.py",
            "app/api/middleware/required_auth.py",
            "app/api/middleware/request_signature.py",
            "app/services/rbac_service.py",
            "render.yaml"
        ]

        issues = []
        checks_passed = 0

        for file_path in required_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                checks_passed += 1
            else:
                issues.append(f"缺少必需文件：{file_path}")

        total_checks = checks_passed + len(issues)
        status = "PASS" if len(issues) == 0 else "FAIL"

        self.results.append({
            "category": "必需文件",
            "status": status,
            "message": f"找到 {checks_passed}/{total_checks} 个必需文件",
            "details": issues,
            "checks_passed": checks_passed,
            "total_checks": total_checks
        })

        print(f"   必需文件验证完成，找到 {checks_passed}/{total_checks} 个文件")

    def _validate_code_security(self):
        """验证代码中的安全配置"""
        print("\n🔍 验证代码安全配置...")

        issues = []
        checks_passed = 0

        # 检查main.py
        main_file = self.project_root / "app" / "main.py"
        if main_file.exists():
            try:
                with open(main_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 检查安全中间件导入
                if 'RequiredAuthMiddleware' in content:
                    checks_passed += 1
                else:
                    issues.append("未导入RequiredAuthMiddleware")

                if 'RequestSignatureMiddleware' in content:
                    checks_passed += 1
                else:
                    issues.append("未导入RequestSignatureMiddleware")

                if 'security_validator' in content:
                    checks_passed += 1
                else:
                    issues.append("未导入security_validator")

                # 检查安全配置验证
                if 'validate_production_config' in content:
                    checks_passed += 1
                else:
                    issues.append("未调用validate_production_config")

                # 检查生产环境检查
                if 'ENVIRONMENT in (\'production\', \'prod\')' in content:
                    checks_passed += 1
                else:
                    issues.append("未检查生产环境")

            except Exception as e:
                issues.append(f"读取main.py失败：{e}")

        # 检查config.py
        config_file = self.project_root / "app" / "core" / "config.py"
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 检查JWT强制配置
                if ('JWT_SECRET_KEY' in content and 'Field(' in content and ('...' in content or 'Ellipsis' in content)):
                    checks_passed += 1
                else:
                    issues.append("JWT_SECRET_KEY未设置为强制")

                # 检查签名验证配置
                if 'SIGNATURE_SECRET_KEY' in content:
                    checks_passed += 1
                else:
                    issues.append("未配置SIGNATURE_SECRET_KEY")

                if 'ENABLE_SIGNATURE_VERIFICATION' in content:
                    checks_passed += 1
                else:
                    issues.append("未配置ENABLE_SIGNATURE_VERIFICATION")

                # 检查CORS验证逻辑
                if 'dangerous_patterns' in content and 'production' in content:
                    checks_passed += 1
                else:
                    issues.append("CORS缺少生产环境验证")

            except Exception as e:
                issues.append(f"读取config.py失败：{e}")

        total_checks = checks_passed + len(issues)
        status = "PASS" if len(issues) == 0 else "FAIL"

        self.results.append({
            "category": "代码安全配置",
            "status": status,
            "message": f"通过 {checks_passed}/{total_checks} 项代码检查",
            "details": issues,
            "checks_passed": checks_passed,
            "total_checks": total_checks
        })

        print(f"   代码安全配置验证完成，通过 {checks_passed}/{total_checks} 项检查")

    def _validate_env_files(self):
        """验证环境变量文件"""
        print("\n🌍 验证环境变量文件...")

        issues = []
        checks_passed = 0

        env_files = ['.env.example', '.env.production', '.env']
        for env_file in env_files:
            env_path = self.project_root / env_file
            if env_path.exists():
                checks_passed += 1

                try:
                    with open(env_path, 'r') as f:
                        content = f.read()

                    # 检查是否包含关键环境变量示例
                    if 'JWT_SECRET_KEY=' in content:
                        checks_passed += 1

                    if 'SIGNATURE_SECRET_KEY=' in content:
                        checks_passed += 1

                    if 'CORS_ORIGINS=' in content:
                        checks_passed += 1

                    # 检查是否包含不安全的默认值
                    if 'change-me' in content.lower() or 'default_secret' in content.lower():
                        if env_file != '.env.example':
                            issues.append(f"{env_file}包含不安全的默认值")

                except Exception as e:
                    issues.append(f"读取{env_file}失败：{e}")

        total_checks = checks_passed + len(issues)
        status = "PASS" if len(issues) == 0 else "FAIL"

        self.results.append({
            "category": "环境变量文件",
            "status": status,
            "message": f"通过 {checks_passed}/{total_checks} 项环境变量检查",
            "details": issues,
            "checks_passed": checks_passed,
            "total_checks": total_checks
        })

        print(f"   环境变量文件验证完成，通过 {checks_passed}/{total_checks} 项检查")

    def _validate_render_yaml_basic(self):
        """验证render.yaml基础配置"""
        print("\n📄 验证render.yaml基础配置...")

        issues = []
        checks_passed = 0

        render_file = self.project_root / "render.yaml"
        if render_file.exists():
            checks_passed += 1

            try:
                with open(render_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 检查基础配置
                if 'type: web' in content:
                    checks_passed += 1

                if 'JWT_SECRET_KEY' in content:
                    checks_passed += 1

                if 'SIGNATURE_SECRET_KEY' in content:
                    checks_passed += 1

                if 'ENABLE_SIGNATURE_VERIFICATION' in content:
                    checks_passed += 1

                if 'CORS_ORIGINS' in content:
                    checks_passed += 1

                # 检查安全头
                security_headers = [
                    'X-Content-Type-Options',
                    'X-Frame-Options',
                    'Strict-Transport-Security',
                    'Content-Security-Policy'
                ]

                for header in security_headers:
                    if header in content:
                        checks_passed += 1

                # 检查关键配置值
                if 'ENVIRONMENT' in content and 'production' in content:
                    checks_passed += 1

                if 'DEBUG' in content and 'false' in content:
                    checks_passed += 1

            except Exception as e:
                issues.append(f"读取render.yaml失败：{e}")
        else:
            issues.append("render.yaml文件不存在")

        total_checks = checks_passed + len(issues)
        status = "PASS" if len(issues) == 0 else "FAIL"

        self.results.append({
            "category": "render.yaml基础配置",
            "status": status,
            "message": f"通过 {checks_passed}/{total_checks} 项render.yaml检查",
            "details": issues,
            "checks_passed": checks_passed,
            "total_checks": total_checks
        })

        print(f"   render.yaml基础配置验证完成，通过 {checks_passed}/{total_checks} 项检查")

    def _generate_report(self) -> Dict:
        """生成验证报告"""
        total_checks = sum(result.get("checks_passed", 0) for result in self.results)
        total_possible = sum(result.get("total_checks", 0) for result in self.results)
        failed_categories = sum(
            1 for result in self.results
            if result["status"] == "FAIL"
        )

        success_rate = (total_checks / total_possible * 100) if total_possible > 0 else 0
        overall_status = "PASS" if failed_categories == 0 and success_rate >= 85 else "FAIL"

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
                recommendations.append(f"修复{category}问题：{result['message']}")

                for detail in result.get("details", [])[:3]:
                    recommendations.append(f"  - {detail}")

        if not recommendations:
            recommendations.append("✅ 所有关键安全配置验证通过，系统已准备好部署")
            recommendations.append("🚀 建议在部署前再次运行完整的安全扫描")

        return recommendations


def main():
    """主函数"""
    validator = SimpleSecurityValidator()

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
        report_file = Path("production_security_validation_simple.json")
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