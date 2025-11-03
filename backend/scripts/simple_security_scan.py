#!/usr/bin/env python3
"""
简化的安全漏洞扫描脚本
不依赖项目模块，执行基础安全检查
"""
import os
import re
import sys
import json
from pathlib import Path
from typing import List, Dict, Any


class SimpleSecurityScanner:
    """简化安全扫描器"""

    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path(__file__).parent.parent
        self.results: List[Dict] = []

    def scan_all(self) -> Dict:
        """执行所有安全扫描"""
        print("🔍 开始执行简化安全扫描...")
        print("=" * 60)

        # 1. 敏感信息扫描
        self._scan_sensitive_files()

        # 2. 硬编码密钥扫描
        self._scan_hardcoded_secrets()

        # 3. 配置文件安全扫描
        self._scan_config_security()

        # 4. Python代码安全扫描
        self._scan_python_security()

        # 5. 文件权限检查
        self._scan_file_permissions()

        return self._generate_report()

    def _scan_sensitive_files(self):
        """扫描敏感文件"""
        print("\n🕵️ 扫描敏感文件...")

        sensitive_patterns = [
            ".env*",
            "*key*",
            "*secret*",
            "*password*",
            "config.*",
            "*.pem",
            "*.key",
            "*.p12",
            "id_rsa*",
            "*.pfx"
        ]

        issues = []
        for pattern in sensitive_patterns:
            for file_path in self.project_root.glob(pattern):
                if file_path.is_file() and not file_path.name.startswith('.git'):
                    issues.append({
                        "file": str(file_path.relative_to(self.project_root)),
                        "type": "sensitive_file",
                        "size": file_path.stat().st_size
                    })

        self.results.append({
            "category": "敏感文件",
            "status": "INFO" if issues else "PASS",
            "issues": len(issues),
            "details": issues
        })

        print(f"   发现 {len(issues)} 个敏感文件")

    def _scan_hardcoded_secrets(self):
        """扫描硬编码密钥"""
        print("\n🔑 扫描硬编码密钥...")

        secret_patterns = [
            (r'password\s*=\s*["\'][^"\']+["\']', "硬编码密码"),
            (r'secret\s*=\s*["\'][^"\']+["\']', "硬编码密钥"),
            (r'api_key\s*=\s*["\'][^"\']+["\']', "硬编码API密钥"),
            (r'token\s*=\s*["\'][^"\']+["\']', "硬编码令牌"),
            (r'sk-[a-zA-Z0-9]{20,}', "OpenAI API密钥"),
            (r'AIza[A-Za-z0-9_-]{35}', "Google API密钥"),
        ]

        issues = []
        code_extensions = ['.py', '.js', '.ts', '.yaml', '.yml', '.json', '.env', '.ini']

        for ext in code_extensions:
            for file_path in self.project_root.rglob(f"*{ext}"):
                if self._should_skip_file(file_path):
                    continue

                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        line_number = 0

                        for line in content.split('\n'):
                            line_number += 1

                            for pattern, description in secret_patterns:
                                if re.search(pattern, line, re.IGNORECASE):
                                    issues.append({
                                        "file": str(file_path.relative_to(self.project_root)),
                                        "line": line_number,
                                        "type": description,
                                        "content": line.strip()[:80] + "..." if len(line.strip()) > 80 else line.strip()
                                    })

                except Exception:
                    continue

        self.results.append({
            "category": "硬编码密钥",
            "status": "FAIL" if issues else "PASS",
            "issues": len(issues),
            "details": issues
        })

        print(f"   发现 {len(issues)} 个硬编码密钥")

    def _scan_config_security(self):
        """扫描配置文件安全"""
        print("\n⚙️ 扫描配置文件安全...")

        issues = []

        # 检查render.yaml
        render_yaml = self.project_root / "render.yaml"
        if render_yaml.exists():
            try:
                with open(render_yaml, 'r') as f:
                    content = f.read()

                # 检查是否有sync: false的敏感配置
                if 'sync: false' not in content:
                    issues.append({
                        "file": "render.yaml",
                        "type": "missing_sync_false",
                        "issue": "敏感环境变量未设置sync: false"
                    })

                # 检查安全头配置
                if 'X-Content-Type-Options' not in content:
                    issues.append({
                        "file": "render.yaml",
                        "type": "missing_security_headers",
                        "issue": "缺少安全头配置"
                    })

            except Exception as e:
                issues.append({
                    "file": "render.yaml",
                    "type": "read_error",
                    "issue": f"读取文件失败：{e}"
                })

        # 检查.env文件
        env_files = list(self.project_root.glob(".env*"))
        for env_file in env_files:
            if env_file.name in ['.env.example', '.env.template']:
                continue

            try:
                with open(env_file, 'r') as f:
                    content = f.read()

                # 检查是否包含默认值
                if 'change-me' in content.lower() or 'default' in content.lower():
                    issues.append({
                        "file": str(env_file.relative_to(self.project_root)),
                        "type": "default_values",
                        "issue": "包含默认或示例值"
                    })

            except Exception:
                continue

        self.results.append({
            "category": "配置安全",
            "status": "FAIL" if issues else "PASS",
            "issues": len(issues),
            "details": issues
        })

        print(f"   发现 {len(issues)} 个配置安全问题")

    def _scan_python_security(self):
        """扫描Python代码安全问题"""
        print("\n🐍 扫描Python代码安全...")

        issues = []

        # 安全问题的模式
        security_patterns = [
            (r'eval\s*\(', "使用eval函数"),
            (r'exec\s*\(', "使用exec函数"),
            (r'pickle\.loads?\s*\(', "使用pickle反序列化"),
            (r'shell=True', "shell=True可能存在命令注入风险"),
            (r'os\.system\s*\(', "使用os.system"),
            (r'subprocess\.call\s*\([^)]*shell=True', "subprocess使用shell=True"),
            (r'random\.random\(\)', "使用不安全的随机数生成器"),
            (r'md5\s*\(', "使用不安全的MD5哈希"),
            (r'sha1\s*\(', "使用不安全的SHA1哈希"),
        ]

        for py_file in self.project_root.rglob("*.py"):
            if self._should_skip_file(py_file):
                continue

            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    line_number = 0

                for line in content.split('\n'):
                    line_number += 1

                    for pattern, description in security_patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            issues.append({
                                "file": str(py_file.relative_to(self.project_root)),
                                "line": line_number,
                                "type": description,
                                "content": line.strip()
                            })

            except Exception:
                continue

        self.results.append({
            "category": "Python代码安全",
            "status": "WARNING" if issues else "PASS",
            "issues": len(issues),
            "details": issues
        })

        print(f"   发现 {len(issues)} 个Python代码安全问题")

    def _scan_file_permissions(self):
        """扫描文件权限"""
        print("\n🔒 扫描文件权限...")

        issues = []

        # 检查敏感文件的权限
        sensitive_files = [
            ".env",
            ".env.production",
            "render.yaml",
            "*.key",
            "*.pem"
        ]

        for pattern in sensitive_files:
            for file_path in self.project_root.glob(pattern):
                if file_path.is_file():
                    try:
                        stat = file_path.stat()
                        mode = oct(stat.st_mode)[-3:]

                        # 检查是否对其他用户可读
                        if mode[2] in ['4', '5', '6', '7']:
                            issues.append({
                                "file": str(file_path.relative_to(self.project_root)),
                                "permissions": mode,
                                "issue": "文件对其他用户可读"
                            })

                    except Exception:
                        continue

        self.results.append({
            "category": "文件权限",
            "status": "FAIL" if issues else "PASS",
            "issues": len(issues),
            "details": issues
        })

        print(f"   发现 {len(issues)} 个权限问题")

    def _should_skip_file(self, file_path: Path) -> bool:
        """判断是否应该跳过文件"""
        skip_patterns = [
            "venv",
            ".git",
            "__pycache__",
            "node_modules",
            ".pytest_cache",
            "build",
            "dist"
        ]

        return any(pattern in str(file_path) for pattern in skip_patterns)

    def _generate_report(self) -> Dict:
        """生成扫描报告"""
        total_issues = sum(result["issues"] for result in self.results)
        failed_categories = sum(
            1 for result in self.results
            if result["status"] == "FAIL"
        )

        overall_status = "PASS"
        if failed_categories > 0:
            overall_status = "FAIL"
        elif total_issues > 0:
            overall_status = "WARNING"

        return {
            "timestamp": "2024-01-01T00:00:00Z",
            "summary": {
                "total_scans": len(self.results),
                "total_issues": total_issues,
                "failed_categories": failed_categories,
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

                if category == "硬编码密钥":
                    recommendations.append("移除代码中的硬编码密钥，使用环境变量管理敏感信息")
                elif category == "配置安全":
                    recommendations.append("修复配置文件中的安全问题，设置适当的同步和安全配置")
                elif category == "Python代码安全":
                    recommendations.append("审查Python代码中的安全问题，避免使用不安全的函数")
                elif category == "文件权限":
                    recommendations.append("修复敏感文件的权限设置，限制不必要的访问权限")
                elif category == "敏感文件":
                    recommendations.append("确保敏感文件不会意外提交到版本控制系统")

        if not recommendations:
            recommendations.append("未发现明显的安全问题，建议定期进行安全扫描")

        return recommendations


def main():
    """主函数"""
    scanner = SimpleSecurityScanner()

    try:
        report = scanner.scan_all()

        # 打印摘要
        print("\n" + "=" * 60)
        print("📊 安全扫描报告")
        print("=" * 60)
        print(f"整体状态：{report['summary']['overall_status']}")
        print(f"扫描项目：{report['summary']['total_scans']}")
        print(f"发现问题：{report['summary']['total_issues']}")
        print(f"失败类别：{report['summary']['failed_categories']}")

        # 打印各类别结果
        print("\n📋 分类结果：")
        for category in report['categories']:
            status_icon = "✅" if category['status'] == 'PASS' else "❌" if category['status'] == 'FAIL' else "⚠️"
            print(f"   {status_icon} {category['category']}：{category['status']} ({category['issues']}个问题)")

        # 打印详细问题
        if report['summary']['total_issues'] > 0:
            print("\n🔍 详细问题：")
            for category in report['categories']:
                if category['issues'] > 0:
                    print(f"\n{category['category']}:")
                    for issue in category['details'][:5]:  # 只显示前5个问题
                        if 'file' in issue:
                            print(f"   📁 {issue['file']}")
                        if 'line' in issue:
                            print(f"   📍 行 {issue['line']}")
                        if 'type' in issue:
                            print(f"   ⚠️ {issue['type']}")
                        if 'issue' in issue:
                            print(f"   📝 {issue['issue']}")
                        print("   " + "-" * 40)

        # 打印建议
        if report['recommendations']:
            print("\n💡 安全建议：")
            for i, rec in enumerate(report['recommendations'], 1):
                print(f"   {i}. {rec}")

        # 保存报告
        report_file = Path("security_scan_report.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\n📄 详细报告已保存到：{report_file}")

        # 根据扫描结果设置退出码
        if report['summary']['overall_status'] == 'FAIL':
            print("\n❌ 发现严重安全问题，请及时修复")
            sys.exit(1)
        else:
            print("\n✅ 安全扫描完成")
            sys.exit(0)

    except KeyboardInterrupt:
        print("\n⚠️ 扫描被用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ 扫描过程中出错：{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()