#!/usr/bin/env python3
"""
生成综合测试报告
整合所有测试结果并生成Markdown格式的详细报告
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any


def load_json_report(filepath: str) -> Dict[str, Any]:
    """加载JSON测试报告"""
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def generate_markdown_report():
    """生成Markdown格式的综合测试报告"""
    
    # 加载测试报告
    api_report = load_json_report("production_test_report.json")
    frontend_report = load_json_report("frontend_ui_test_report.json")
    
    report_lines = []
    report_lines.append("# Web3search 生产环境功能测试报告")
    report_lines.append("")
    report_lines.append(f"**测试日期**: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}")
    report_lines.append(f"**测试环境**: 生产环境 (Vercel + Render)")
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")
    
    # 测试摘要
    report_lines.append("## 📋 测试摘要")
    report_lines.append("")
    
    if api_report:
        summary = api_report.get("summary", {})
        total = summary.get("total", 0)
        passed = summary.get("passed", 0)
        failed = summary.get("failed", 0)
        warning = summary.get("warning", 0)
        pass_rate = summary.get("pass_rate", 0)
        
        report_lines.append("### 后端API测试结果")
        report_lines.append("")
        report_lines.append(f"- **总计**: {total} 个测试")
        report_lines.append(f"- **✅ 通过**: {passed}")
        report_lines.append(f"- **❌ 失败**: {failed}")
        report_lines.append(f"- **⚠️  警告**: {warning}")
        report_lines.append(f"- **通过率**: {pass_rate}%")
        report_lines.append("")
    
    if frontend_report:
        summary = frontend_report.get("summary", {})
        total = summary.get("total", 0)
        passed = summary.get("passed", 0)
        failed = summary.get("failed", 0)
        warning = summary.get("warning", 0)
        pass_rate = summary.get("pass_rate", 0)
        
        report_lines.append("### 前端UI测试结果")
        report_lines.append("")
        report_lines.append(f"- **总计**: {total} 个测试")
        report_lines.append(f"- **✅ 通过**: {passed}")
        report_lines.append(f"- **❌ 失败**: {failed}")
        report_lines.append(f"- **⚠️  警告**: {warning}")
        report_lines.append(f"- **通过率**: {pass_rate}%")
        report_lines.append("")
    
    report_lines.append("---")
    report_lines.append("")
    
    # 详细测试结果
    report_lines.append("## 🔍 详细测试结果")
    report_lines.append("")
    
    if api_report:
        report_lines.append("### 1. 后端API功能测试")
        report_lines.append("")
        
        results = api_report.get("results", [])
        
        # 按状态分组
        passed_tests = [r for r in results if r.get("status") == "passed"]
        failed_tests = [r for r in results if r.get("status") == "failed"]
        warning_tests = [r for r in results if r.get("status") == "warning"]
        
        if passed_tests:
            report_lines.append("#### ✅ 通过的测试")
            report_lines.append("")
            for test in passed_tests:
                response_time = test.get("response_time")
                time_str = f", 响应时间: {response_time:.0f}ms" if response_time else ""
                report_lines.append(f"- **{test.get('name')}**: {test.get('details')}{time_str}")
            report_lines.append("")
        
        if failed_tests:
            report_lines.append("#### ❌ 失败的测试")
            report_lines.append("")
            for test in failed_tests:
                report_lines.append(f"- **{test.get('name')}**")
                report_lines.append(f"  - 详情: {test.get('details')}")
                if test.get('error'):
                    error_msg = test.get('error', '')[:200]
                    report_lines.append(f"  - 错误: `{error_msg}`")
            report_lines.append("")
        
        if warning_tests:
            report_lines.append("#### ⚠️  警告的测试")
            report_lines.append("")
            for test in warning_tests:
                report_lines.append(f"- **{test.get('name')}**: {test.get('details')}")
            report_lines.append("")
    
    if frontend_report:
        report_lines.append("### 2. 前端UI功能测试")
        report_lines.append("")
        
        results = frontend_report.get("results", [])
        
        passed_tests = [r for r in results if r.get("status") == "passed"]
        failed_tests = [r for r in results if r.get("status") == "failed"]
        warning_tests = [r for r in results if r.get("status") == "warning"]
        
        if passed_tests:
            report_lines.append("#### ✅ 通过的测试")
            report_lines.append("")
            for test in passed_tests:
                report_lines.append(f"- **{test.get('name')}**: {test.get('details')}")
            report_lines.append("")
        
        if failed_tests:
            report_lines.append("#### ❌ 失败的测试")
            report_lines.append("")
            for test in failed_tests:
                report_lines.append(f"- **{test.get('name')}**: {test.get('details')}")
                if test.get('error'):
                    report_lines.append(f"  - 错误: `{test.get('error')[:200]}`")
            report_lines.append("")
    
    report_lines.append("---")
    report_lines.append("")
    
    # 性能指标
    report_lines.append("## ⚡ 性能指标")
    report_lines.append("")
    
    if api_report:
        results = api_report.get("results", [])
        response_times = [r.get("response_time") for r in results if r.get("response_time")]
        
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            max_time = max(response_times)
            min_time = min(response_times)
            
            report_lines.append("### API响应时间统计")
            report_lines.append("")
            report_lines.append(f"- **平均响应时间**: {avg_time:.0f}ms")
            report_lines.append(f"- **最大响应时间**: {max_time:.0f}ms")
            report_lines.append(f"- **最小响应时间**: {min_time:.0f}ms")
            report_lines.append("")
            
            # 性能评估
            report_lines.append("### 性能评估")
            report_lines.append("")
            if avg_time < 1000:
                report_lines.append("- ✅ **优秀**: 平均响应时间 < 1秒")
            elif avg_time < 3000:
                report_lines.append("- ⚠️  **良好**: 平均响应时间 < 3秒")
            else:
                report_lines.append("- ❌ **需改进**: 平均响应时间 > 3秒")
            report_lines.append("")
    
    report_lines.append("---")
    report_lines.append("")
    
    # 发现的问题
    report_lines.append("## 🚨 发现的问题")
    report_lines.append("")
    
    if api_report:
        failed_tests = [r for r in api_report.get("results", []) if r.get("status") == "failed"]
        
        if failed_tests:
            # 按优先级分类
            critical_issues = []
            high_issues = []
            medium_issues = []
            
            for test in failed_tests:
                name = test.get("name", "")
                if "前端" in name or "Deep Research" in name:
                    critical_issues.append(test)
                elif "报告" in name or "搜索" in name:
                    high_issues.append(test)
                else:
                    medium_issues.append(test)
            
            if critical_issues:
                report_lines.append("### 🔴 关键问题 (P0)")
                report_lines.append("")
                for test in critical_issues:
                    report_lines.append(f"1. **{test.get('name')}**")
                    report_lines.append(f"   - 问题: {test.get('details')}")
                    report_lines.append(f"   - 影响: 核心功能无法使用")
                    report_lines.append("")
            
            if high_issues:
                report_lines.append("### 🟠 高优先级问题 (P1)")
                report_lines.append("")
                for test in high_issues:
                    report_lines.append(f"1. **{test.get('name')}**")
                    report_lines.append(f"   - 问题: {test.get('details')}")
                    report_lines.append("")
            
            if medium_issues:
                report_lines.append("### 🟡 中优先级问题 (P2)")
                report_lines.append("")
                for test in medium_issues:
                    report_lines.append(f"1. **{test.get('name')}**")
                    report_lines.append(f"   - 问题: {test.get('details')}")
                    report_lines.append("")
    
    report_lines.append("---")
    report_lines.append("")
    
    # 修复建议
    report_lines.append("## 🔧 修复建议")
    report_lines.append("")
    
    if api_report:
        failed_tests = [r for r in api_report.get("results", []) if r.get("status") == "failed"]
        
        if failed_tests:
            report_lines.append("### 立即修复 (P0)")
            report_lines.append("")
            
            for test in failed_tests:
                name = test.get("name", "")
                if "前端" in name:
                    report_lines.append("1. **修复前端部署**")
                    report_lines.append("   - 检查Vercel部署配置")
                    report_lines.append("   - 验证构建流程")
                    report_lines.append("   - 确认域名设置")
                    report_lines.append("")
                elif "Deep Research" in name:
                    report_lines.append("2. **修复Deep Research功能**")
                    report_lines.append("   - 检查服务器日志")
                    report_lines.append("   - 验证数据库连接")
                    report_lines.append("   - 检查外部API依赖")
                    report_lines.append("")
            
            report_lines.append("### 短期修复 (P1)")
            report_lines.append("")
            report_lines.append("1. **修复报告列表API**")
            report_lines.append("   - 检查数据库查询")
            report_lines.append("   - 验证权限配置")
            report_lines.append("")
            report_lines.append("2. **修复搜索和热点API**")
            report_lines.append("   - 检查外部数据源连接")
            report_lines.append("   - 验证API密钥配置")
            report_lines.append("")
    
    report_lines.append("---")
    report_lines.append("")
    
    # 总体评估
    report_lines.append("## 🎯 总体评估")
    report_lines.append("")
    
    if api_report:
        summary = api_report.get("summary", {})
        pass_rate = summary.get("pass_rate", 0)
        
        if pass_rate >= 80:
            report_lines.append("### ✅ 系统状态: 良好")
            report_lines.append("")
            report_lines.append("大部分功能正常运行，系统整体稳定。")
        elif pass_rate >= 50:
            report_lines.append("### ⚠️  系统状态: 需改进")
            report_lines.append("")
            report_lines.append("部分核心功能存在问题，需要尽快修复。")
        else:
            report_lines.append("### ❌ 系统状态: 严重问题")
            report_lines.append("")
            report_lines.append("多个核心功能无法正常工作，需要立即修复。")
        report_lines.append("")
    
    report_lines.append("---")
    report_lines.append("")
    report_lines.append(f"**报告生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")
    
    # 保存报告
    report_content = "\n".join(report_lines)
    report_file = "PRODUCTION_TEST_REPORT.md"
    
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report_content)
    
    print(f"✅ 综合测试报告已生成: {report_file}")
    print(f"📊 报告包含 {len(report_lines)} 行内容")
    
    return report_file


if __name__ == "__main__":
    generate_markdown_report()

