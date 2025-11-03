#!/usr/bin/env python3
"""
安全漏洞扫描脚本
执行自动化安全检查和漏洞扫描
"""
import asyncio
import sys
import os
import re
import subprocess
from pathlib import Path
from typing import List, Dict, Any
import argparse

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.security_validator import SecurityValidator
from app.core.config import settings


class SecurityScanner:
    """安全漏洞扫描器"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.results: List[Dict] = []

    async def run_all_scans(self) -> Dict:
        """运行所有安全扫描"""
        print("🔍 开始执行安全扫描...")
        print("=" * 60)

        # 1. 配置安全检查
        await self._scan_configuration_security()

        # 2. 代码安全扫描
        await self._scan_code_security()

        # 3. 依赖安全扫描
        await self._scan_dependencies()

        # 4. 文件权限扫描
        await self._scan_file_permissions()

        # 5. 敏感信息扫描
        await self._scan_sensitive_information()

        # 6. API安全扫描
        await self._scan_api_security()

        # 生成报告
        return self._generate_report()

    async def _scan_configuration_security(self):
        """扫描配置安全"""
        print("\n📋 扫描配置安全...")

        try:
            validator = SecurityValidator()
            config_report = await validator.validate_all()

            self.results.append({
                "category": "配置安全",
                "status": "PASS" if config_report["overall_status"] == "PASS" else "FAIL",
                "score": config_report["summary"]["score"],
                "issues": config_report["summary"]["failed"],
                "details": config_report["checks"]
            })

            print(f"   配置安全扫描完成，得分：{config_report['summary']['score']}%")
            if config_report["summary"]["failed"] > 0:
                print(f"   发现 {config_report['summary']['failed']} 个问题")

        except Exception as e:
            print(f"   ❌ 配置安全扫描失败：{e}")
            self.results.append({
                "category": "配置安全",
                "status": "ERROR",
                "score": 0,
                "issues": 1,
                "details": [{"error": str(e)}]
            })

    async def _scan_code_security(self):
        """扫描代码安全问题"""
        print("\n🔍 扫描代码安全...")

        issues = []

        # 扫描Python文件中的安全问题
        python_files = list(self.project_root.rglob("*.py"))
        for py_file in python_files:
            if "tests/" in str(py_file) or "venv" in str(py_file):
                continue

            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    line_number = 0

                    for line in content.split('\n'):
                        line_number += 1

                        # 检查硬编码密钥
                        if self._contains_hardcoded_secrets(line):
                            issues.append({
                                "file": str(py_file),
                                "line": line_number,
                                "type": "hardcoded_secret",
                                "content": line.strip()
                            })

                        # 检查SQL注入风险
                        if self._contains_sql_injection_risk(line):
                            issues.append({
                                "file": str(py_file),
                                "line": line_number,
                                "type": "sql_injection_risk",
                                "content": line.strip()
                            })

                        # 检查不安全的随机数生成
                        if self._contains_insecure_random(line):
                            issues.append({
                                "file": str(py_file),
                                "line": line_number,
                                "type": "insecure_random",
                                "content": line.strip()
                            })

            except Exception as e:
                print(f"   ⚠️ 扫描文件 {py_file} 时出错：{e}")

        score = max(0, 100 - len(issues) * 5)
        status = "PASS" if len(issues) == 0 else "FAIL"

        self.results.append({
            "category": "代码安全",
            "status": status,
            "score": score,
            "issues": len(issues),
            "details": issues
        })

        print(f"   代码安全扫描完成，发现 {len(issues)} 个潜在问题")

    async def _scan_dependencies(self):
        """扫描依赖安全"""
        print("\n📦 扫描依赖安全...")

        issues = []

        # 检查requirements.txt中的已知漏洞包
        requirements_file = self.project_root / "requirements.txt"
        if requirements_file.exists():
            try:
                with open(requirements_file, 'r') as f:
                    requirements = f.read()

                # 已知有安全问题的包版本
                vulnerable_packages = {
                    "urllib3": ["<1.26.5"],
                    "requests": ["<2.25.1"],
                    "pillow": ["<8.2.0"],
                    "jinja2": ["<2.11.3"],
                    "django": ["<3.2.0"],
                    "flask": ["<1.1.2"],
                }

                for line in requirements.split('\n'):
                    if '==' in line and not line.startswith('#'):
                        package, version = line.split('==', 1)
                        package = package.strip().lower()
                        version = version.strip()

                        if package in vulnerable_packages:
                            vulnerable_versions = vulnerable_packages[package]
                            for vuln_version in vulnerable_versions:
                                if self._version_matches(version, vuln_version):
                                    issues.append({
                                        "package": package,
                                        "version": version,
                                        "vulnerability": f"版本 {version} 存在已知安全漏洞"
                                    })

            except Exception as e:
                print(f"   ⚠️ 读取requirements.txt时出错：{e}")

        # 尝试运行safety扫描
        try:
            result = subprocess.run(
                [sys.executable, "-m", "safety", "check", "--json"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                # safety扫描通过
                print("   ✅ Safety扫描：未发现依赖漏洞")
            else:
                print("   ⚠️ Safety扫描发现依赖问题")
                # 这里可以解析JSON输出获取详细信息

        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("   ⚠️ Safety扫描未执行（工具未安装）")

        score = max(0, 100 - len(issues) * 10)
        status = "PASS" if len(issues) == 0 else "FAIL"

        self.results.append({
            "category": "依赖安全",
            "status": status,
            "score": score,
            "issues": len(issues),
            "details": issues
        })

        print(f"   依赖安全扫描完成，发现 {len(issues)} 个问题")

    async def _scan_file_permissions(self):
        """扫描文件权限"""
        print("\n🔒 扫描文件权限...")

        issues = []

        # 检查敏感文件的权限
        sensitive_files = [
            ".env*",
            "*key*",
            "*secret*",
            "config.*",
            "*.pem",
            "*.key",
            "*.p12"
        ]

        for pattern in sensitive_files:
            for file_path in self.project_root.glob(pattern):
                if file_path.is_file():
                    try:
                        stat = file_path.stat()
                        mode = oct(stat.st_mode)[-3:]

                        # 检查是否对其他用户可读
                        if mode[2] in ['4', '5', '6', '7']:  # others have read permission
                            issues.append({
                                "file": str(file_path),
                                "permissions": mode,
                                "issue": "文件对其他用户可读"
                            })

                    except Exception as e:
                        print(f"   ⚠️ 检查文件权限 {file_path} 时出错：{e}")

        score = max(0, 100 - len(issues) * 15)
        status = "PASS" if len(issues) == 0 else "FAIL"

        self.results.append({
            "category": "文件权限",
            "status": status,
            "score": score,
            "issues": len(issues),
            "details": issues
        })

        print(f"   文件权限扫描完成，发现 {len(issues)} 个权限问题")

    async def _scan_sensitive_information(self):
        """扫描敏感信息泄露"""
        print("\n🕵️ 扫描敏感信息泄露...")

        issues = []

        # 敏感信息模式
        sensitive_patterns = [
            (r'password\s*=\s*["\'][^"\']+["\']', "硬编码密码"),
            (r'secret\s*=\s*["\'][^"\']+["\']', "硬编码密钥"),
            (r'api_key\s*=\s*["\'][^"\']+["\']', "硬编码API密钥"),
            (r'token\s*=\s*["\'][^"\']+["\']', "硬编码令牌"),
            (r'sk-[a-zA-Z0-9]{20,}', "可能的OpenAI API密钥"),
            (r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', "邮箱地址"),
            (r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', "信用卡号"),
        ]

        # 扫描代码文件
        code_extensions = ['.py', '.js', '.ts', '.yaml', '.yml', '.json', '.env', '.ini']
        for ext in code_extensions:
            for file_path in self.project_root.rglob(f"*{ext}"):
                if "venv" in str(file_path) or ".git" in str(file_path):
                    continue

                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        line_number = 0

                        for line in content.split('\n'):
                            line_number += 1

                            for pattern, description in sensitive_patterns:
                                if re.search(pattern, line, re.IGNORECASE):
                                    issues.append({
                                        "file": str(file_path),
                                        "line": line_number,
                                        "type": description,
                                        "content": line.strip()[:100] + "..." if len(line.strip()) > 100 else line.strip()
                                    })

                except Exception:
                    continue

        score = max(0, 100 - len(issues) * 3)
        status = "PASS" if len(issues) == 0 else "WARNING"

        self.results.append({
            "category": "敏感信息",
            "status": status,
            "score": score,
            "issues": len(issues),
            "details": issues
        })

        print(f"   敏感信息扫描完成，发现 {len(issues)} 个潜在泄露")

    async def _scan_api_security(self):
        """扫描API安全"""
        print("\n🌐 扫描API安全...")

        issues = []

        # 检查API路由定义
        api_files = list(self.project_root.glob("app/api/**/*.py"))
        for api_file in api_files:
            try:
                with open(api_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 检查是否有未保护的端点
                if '@router.get' in content or '@router.post' in content:
                    # 检查是否有认证依赖
                    if 'Depends(' not in content and 'auth' not in content.lower():
                        issues.append({
                            "file": str(api_file),
                            "type": "unprotected_endpoint",
                            "issue": "可能存在未保护的API端点"
                        })

            except Exception:
                continue

        score = max(0, 100 - len(issues) * 10)
        status = "PASS" if len(issues) == 0 else "FAIL"

        self.results.append({
            "category": "API安全",
            "status": status,
            "score": score,
            "issues": len(issues),
            "details": issues
        })

        print(f"   API安全扫描完成，发现 {len(issues)} 个问题")

    def _contains_hardcoded_secrets(self, line: str) -> bool:
        """检查是否包含硬编码密钥"""
        secret_patterns = [
            r'password\s*=\s*["\'][^"\']{8,}["\']',
            r'secret\s*=\s*["\'][^"\']{16,}["\']',
            r'key\s*=\s*["\'][^"\']{16,}["\']',
        ]
        return any(re.search(pattern, line, re.IGNORECASE) for pattern in secret_patterns)

    def _contains_sql_injection_risk(self, line: str) -> bool:
        """检查SQL注入风险"""
        risky_patterns = [
            r'execute\s*\(\s*["\'].*\+.*["\']',
            r'execute\s*\(\s*f["\'].*{.*}.*["\']',
            r'query\s*\(\s*["\'].*\+.*["\']',
        ]
        return any(re.search(pattern, line, re.IGNORECASE) for pattern in risky_patterns)

    def _contains_insecure_random(self, line: str) -> bool:
        """检查不安全的随机数生成"""
        insecure_patterns = [
            r'random\.random\(\)',
            r'random\.randint\(',
            r'random\.choice\(',
        ]
        return any(re.search(pattern, line) for pattern in insecure_patterns)

    def _version_matches(self, version: str, pattern: str) -> bool:
        """简单版本匹配检查"""
        if pattern.startswith('<'):
            try:
                return tuple(map(int, version.split('.'))) < tuple(map(int, pattern[1:].split('.')))
            except:
                return False
        return False

    def _generate_report(self) -> Dict:
        """生成扫描报告"""
        total_issues = sum(result["issues"] for result in self.results)
        total_score = sum(result["score"] for result in self.results) / len(self.results) if self.results else 0

        # 计算整体状态
        critical_failures = sum(
            1 for result in self.results
            if result["status"] == "FAIL" and result["issues"] > 0
        )

        overall_status = "PASS"
        if critical_failures > 0:
            overall_status = "FAIL"
        elif total_issues > 0:
            overall_status = "WARNING"

        return {
            "timestamp": "2024-01-01T00:00:00Z",  # 实际应用中应该使用当前时间
            "summary": {
                "total_scans": len(self.results),
                "total_issues": total_issues,
                "average_score": round(total_score, 1),
                "overall_status": overall_status
            },
            "categories": self.results,
            "recommendations": self._generate_recommendations()
        }

    def _generate_recommendations(self) -> List[str]:
        """生成安全建议"""
        recommendations = []

        for result in self.results:
            if result["status"] in ["FAIL", "WARNING"]:
                category = result["category"]

                if category == "配置安全":
                    recommendations.append("检查并修复安全配置问题，确保生产环境使用强密钥和安全设置")
                elif category == "代码安全":
                    recommendations.append("审查代码安全问题，移除硬编码密钥和不安全的代码模式")
                elif category == "依赖安全":
                    recommendations.append("更新存在安全漏洞的依赖包到最新安全版本")
                elif category == "文件权限":
                    recommendations.append("修复敏感文件的权限设置，限制不必要的访问权限")
                elif category == "敏感信息":
                    recommendations.append("移除代码中的硬编码敏感信息，使用环境变量管理")
                elif category == "API安全":
                    recommendations.append("为API端点添加适当的认证和授权机制")

        if not recommendations:
            recommendations.append("未发现明显的安全问题，建议定期进行安全扫描")

        return recommendations


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="安全漏洞扫描工具")
    parser.add_argument("--output", "-o", help="输出报告文件路径")
    parser.add_argument("--category", "-c", help="只扫描指定类别（配置/代码/依赖/权限/敏感信息/API）")
    args = parser.parse_args()

    scanner = SecurityScanner()

    try:
        report = await scanner.run_all_scans()

        # 打印摘要
        print("\n" + "=" * 60)
        print("📊 安全扫描报告")
        print("=" * 60)
        print(f"整体状态：{report['summary']['overall_status']}")
        print(f"扫描项目：{report['summary']['total_scans']}")
        print(f"发现问题：{report['summary']['total_issues']}")
        print(f"安全评分：{report['summary']['average_score']}%")

        # 打印各类别结果
        print("\n📋 分类结果：")
        for category in report['categories']:
            status_icon = "✅" if category['status'] == 'PASS' else "❌" if category['status'] == 'FAIL' else "⚠️"
            print(f"   {status_icon} {category['category']}：{category['status']} ({category['score']}分, {category['issues']}个问题)")

        # 打印建议
        if report['recommendations']:
            print("\n💡 安全建议：")
            for i, rec in enumerate(report['recommendations'], 1):
                print(f"   {i}. {rec}")

        # 输出报告文件
        if args.output:
            import json
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"\n📄 详细报告已保存到：{args.output}")

        # 根据扫描结果设置退出码
        if report['summary']['overall_status'] == 'FAIL':
            sys.exit(1)
        else:
            sys.exit(0)

    except KeyboardInterrupt:
        print("\n⚠️ 扫描被用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ 扫描过程中出错：{e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())