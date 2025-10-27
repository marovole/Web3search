"""
Prompt质量报告生成器（任务 12.8）

功能：
1. 综合质量报告
2. 监控数据汇总
3. 评估结果分析
4. A/B测试总结
5. 优化建议生成
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
from pathlib import Path

from app.services.prompt_monitor import prompt_monitor, AggregatedMetrics
from app.services.prompt_evaluator import PromptEvaluator
from app.services.ab_testing import ABTestResult
from app.services.prompt_version import PromptVersionControl


# ================================
# 报告数据类
# ================================

@dataclass
class QualityReport:
    """质量报告"""
    prompt_name: str
    report_period: str  # 报告周期
    generated_at: datetime

    # 监控数据
    monitoring_summary: Dict[str, Any] = field(default_factory=dict)

    # 评估数据
    evaluation_summary: Dict[str, Any] = field(default_factory=dict)

    # A/B测试
    ab_test_results: List[Dict[str, Any]] = field(default_factory=list)

    # 版本历史
    version_history: List[Dict[str, Any]] = field(default_factory=list)

    # 优化建议
    recommendations: List[str] = field(default_factory=list)

    # 问题列表
    issues: List[Dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "prompt_name": self.prompt_name,
            "report_period": self.report_period,
            "generated_at": self.generated_at.isoformat(),
            "monitoring_summary": self.monitoring_summary,
            "evaluation_summary": self.evaluation_summary,
            "ab_test_results": self.ab_test_results,
            "version_history": self.version_history,
            "recommendations": self.recommendations,
            "issues": self.issues
        }


# ================================
# 报告生成器
# ================================

class QualityReportGenerator:
    """质量报告生成器（任务12.8）"""

    def __init__(self):
        self.evaluator = PromptEvaluator()

    def generate_report(
        self,
        prompt_name: str,
        time_window: str = "24h",
        include_version_history: bool = True,
        include_recommendations: bool = True
    ) -> QualityReport:
        """
        生成质量报告（任务12.8）

        Args:
            prompt_name: Prompt名称
            time_window: 时间窗口（"1h", "24h", "7d"）
            include_version_history: 是否包含版本历史
            include_recommendations: 是否包含优化建议

        Returns:
            QualityReport: 质量报告
        """
        report = QualityReport(
            prompt_name=prompt_name,
            report_period=time_window,
            generated_at=datetime.utcnow()
        )

        # 1. 收集监控数据
        report.monitoring_summary = self._collect_monitoring_data(
            prompt_name,
            time_window
        )

        # 2. 收集评估数据（如果有）
        report.evaluation_summary = self._collect_evaluation_data(prompt_name)

        # 3. 版本历史
        if include_version_history:
            report.version_history = self._collect_version_history(prompt_name)

        # 4. 分析问题
        report.issues = self._analyze_issues(report)

        # 5. 生成建议
        if include_recommendations:
            report.recommendations = self._generate_recommendations(report)

        return report

    def _collect_monitoring_data(
        self,
        prompt_name: str,
        time_window: str
    ) -> Dict[str, Any]:
        """收集监控数据"""
        try:
            metrics = prompt_monitor.get_metrics(
                prompt_name=prompt_name,
                time_window=time_window
            )

            return {
                "total_requests": metrics.total_requests,
                "successful_requests": metrics.successful_requests,
                "failed_requests": metrics.failed_requests,
                "error_rate": metrics.error_rate,
                "avg_quality_score": metrics.avg_quality_score,
                "avg_token_count": metrics.avg_token_count,
                "avg_response_time_ms": metrics.avg_response_time_ms,
                "p50_response_time_ms": metrics.p50_response_time_ms,
                "p95_response_time_ms": metrics.p95_response_time_ms,
                "p99_response_time_ms": metrics.p99_response_time_ms
            }
        except Exception as e:
            return {"error": str(e)}

    def _collect_evaluation_data(self, prompt_name: str) -> Dict[str, Any]:
        """收集评估数据"""
        # 注意：实际应该从数据库或缓存中读取历史评估结果
        # 这里返回占位数据
        return {
            "note": "评估数据需要从实际运行的评估任务中收集",
            "avg_bleu": 0.0,
            "avg_rouge": 0.0,
            "avg_semantic": 0.0
        }

    def _collect_version_history(self, prompt_name: str) -> List[Dict[str, Any]]:
        """收集版本历史"""
        try:
            vc = PromptVersionControl(prompt_name)
            versions = vc.list_versions()

            # 最近5个版本
            recent_versions = versions[-5:] if len(versions) > 5 else versions

            return [
                {
                    "version": v.version,
                    "author": v.author,
                    "created_at": v.created_at.isoformat(),
                    "changelog": v.changelog
                }
                for v in recent_versions
            ]
        except Exception as e:
            return [{"error": str(e)}]

    def _analyze_issues(self, report: QualityReport) -> List[Dict[str, str]]:
        """分析问题"""
        issues = []
        monitoring = report.monitoring_summary

        if not monitoring or "error" in monitoring:
            return issues

        # 检查错误率
        if monitoring.get("error_rate", 0) > 0.05:
            issues.append({
                "severity": "high",
                "category": "reliability",
                "description": f"错误率过高：{monitoring['error_rate']:.1%}",
                "recommendation": "检查Prompt逻辑，增加输入验证"
            })

        # 检查响应时间
        if monitoring.get("p95_response_time_ms", 0) > 3000:
            issues.append({
                "severity": "medium",
                "category": "performance",
                "description": f"P95响应时间过长：{monitoring['p95_response_time_ms']:.0f}ms",
                "recommendation": "优化Prompt长度，使用缓存"
            })

        # 检查质量得分
        if 0 < monitoring.get("avg_quality_score", 1.0) < 0.6:
            issues.append({
                "severity": "high",
                "category": "quality",
                "description": f"平均质量得分偏低：{monitoring['avg_quality_score']:.2f}",
                "recommendation": "改进Prompt结构，增加Few-shot示例"
            })

        # 检查Token消耗
        if monitoring.get("avg_token_count", 0) > 2000:
            issues.append({
                "severity": "medium",
                "category": "cost",
                "description": f"Token消耗过高：{monitoring['avg_token_count']:.0f} tokens/请求",
                "recommendation": "精简Prompt，移除冗余内容"
            })

        return issues

    def _generate_recommendations(self, report: QualityReport) -> List[str]:
        """生成优化建议"""
        recommendations = []
        monitoring = report.monitoring_summary

        if not monitoring or "error" in monitoring:
            return ["无足够数据生成建议"]

        # 基于问题生成建议
        if report.issues:
            recommendations.append(f"发现 {len(report.issues)} 个问题需要处理")

        # 基于监控数据
        if monitoring.get("total_requests", 0) > 100:
            if monitoring.get("avg_quality_score", 0) > 0.8:
                recommendations.append("质量表现优秀，建议保持当前版本")
            elif monitoring.get("avg_quality_score", 0) > 0.6:
                recommendations.append("质量良好，可考虑小幅优化")
            else:
                recommendations.append("质量需要改进，建议参考优化指南")

        # Token优化
        if monitoring.get("avg_token_count", 0) > 1000:
            recommendations.append("考虑优化Prompt长度以降低成本")

        # 性能优化
        if monitoring.get("p95_response_time_ms", 0) > 2000:
            recommendations.append("考虑实现缓存策略以提升响应速度")

        # 样本量
        if monitoring.get("total_requests", 0) < 30:
            recommendations.append("样本量较少，建议积累更多数据后再优化")

        return recommendations

    def generate_markdown_report(self, report: QualityReport) -> str:
        """
        生成Markdown格式报告（任务12.8）

        Args:
            report: 质量报告

        Returns:
            str: Markdown文本
        """
        md = []

        # 标题
        md.append(f"# Prompt质量报告：{report.prompt_name}")
        md.append("")
        md.append(f"**报告周期**: {report.report_period}")
        md.append(f"**生成时间**: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        md.append("")

        # 执行摘要
        md.append("## 执行摘要")
        md.append("")

        monitoring = report.monitoring_summary
        if monitoring and "error" not in monitoring:
            md.append(f"- **总请求数**: {monitoring.get('total_requests', 0)}")
            md.append(f"- **成功率**: {(1 - monitoring.get('error_rate', 0)):.1%}")
            md.append(f"- **平均质量得分**: {monitoring.get('avg_quality_score', 0):.3f}/1.0")
            md.append(f"- **平均响应时间**: {monitoring.get('avg_response_time_ms', 0):.0f}ms")
            md.append(f"- **P95响应时间**: {monitoring.get('p95_response_time_ms', 0):.0f}ms")
            md.append(f"- **平均Token消耗**: {monitoring.get('avg_token_count', 0):.0f} tokens")
        else:
            md.append("*暂无监控数据*")

        md.append("")

        # 问题列表
        if report.issues:
            md.append("## ⚠️ 发现的问题")
            md.append("")

            for issue in report.issues:
                severity_emoji = {
                    "high": "🔴",
                    "medium": "🟡",
                    "low": "🟢"
                }.get(issue["severity"], "⚪")

                md.append(f"### {severity_emoji} {issue['category'].upper()}")
                md.append(f"**问题**: {issue['description']}")
                md.append(f"**建议**: {issue['recommendation']}")
                md.append("")
        else:
            md.append("## ✅ 未发现问题")
            md.append("")

        # 监控详情
        md.append("## 监控指标详情")
        md.append("")

        if monitoring and "error" not in monitoring:
            md.append("### 请求统计")
            md.append("")
            md.append(f"- 总请求: {monitoring.get('total_requests', 0)}")
            md.append(f"- 成功请求: {monitoring.get('successful_requests', 0)}")
            md.append(f"- 失败请求: {monitoring.get('failed_requests', 0)}")
            md.append(f"- 错误率: {monitoring.get('error_rate', 0):.1%}")
            md.append("")

            md.append("### 性能指标")
            md.append("")
            md.append(f"- 平均响应时间: {monitoring.get('avg_response_time_ms', 0):.0f}ms")
            md.append(f"- P50响应时间: {monitoring.get('p50_response_time_ms', 0):.0f}ms")
            md.append(f"- P95响应时间: {monitoring.get('p95_response_time_ms', 0):.0f}ms")
            md.append(f"- P99响应时间: {monitoring.get('p99_response_time_ms', 0):.0f}ms")
            md.append("")

            md.append("### 质量指标")
            md.append("")
            md.append(f"- 平均质量得分: {monitoring.get('avg_quality_score', 0):.3f}/1.0")
            md.append("")

            md.append("### 成本指标")
            md.append("")
            md.append(f"- 平均Token消耗: {monitoring.get('avg_token_count', 0):.0f} tokens")
            md.append("")

        # 版本历史
        if report.version_history:
            md.append("## 版本历史")
            md.append("")

            for v in reversed(report.version_history):
                if "error" not in v:
                    md.append(f"### {v['version']}")
                    md.append(f"- **作者**: {v['author']}")
                    md.append(f"- **时间**: {v['created_at']}")
                    if v.get('changelog'):
                        md.append(f"- **变更**: {v['changelog']}")
                    md.append("")

        # 优化建议
        if report.recommendations:
            md.append("## 💡 优化建议")
            md.append("")

            for i, rec in enumerate(report.recommendations, 1):
                md.append(f"{i}. {rec}")

            md.append("")

        # 参考资源
        md.append("## 参考资源")
        md.append("")
        md.append("- [Prompt优化指南](app/docs/PROMPT_OPTIMIZATION_GUIDE.md)")
        md.append("- [Few-shot示例库](app/services/few_shot_library.py)")
        md.append("- [评估工具](app/services/prompt_evaluator.py)")
        md.append("")

        # 页脚
        md.append("---")
        md.append("")
        md.append(f"*报告由Prompt质量报告生成器自动生成*")

        return "\n".join(md)

    def save_report(
        self,
        report: QualityReport,
        output_dir: Optional[Path] = None,
        format: str = "markdown"
    ) -> Path:
        """
        保存报告到文件（任务12.8）

        Args:
            report: 质量报告
            output_dir: 输出目录
            format: 格式（"markdown" 或 "json"）

        Returns:
            Path: 保存的文件路径
        """
        if output_dir is None:
            output_dir = Path(__file__).parent.parent / "data" / "reports"

        output_dir.mkdir(parents=True, exist_ok=True)

        # 文件名：prompt_name_YYYYMMDD_HHMMSS
        timestamp = report.generated_at.strftime("%Y%m%d_%H%M%S")
        filename = f"{report.prompt_name}_{timestamp}"

        if format == "markdown":
            file_path = output_dir / f"{filename}.md"
            content = self.generate_markdown_report(report)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
        elif format == "json":
            file_path = output_dir / f"{filename}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)
        else:
            raise ValueError(f"不支持的格式: {format}")

        return file_path


# ================================
# 全局实例
# ================================

quality_report_generator = QualityReportGenerator()


# ================================
# 便捷函数
# ================================

def generate_quality_report(
    prompt_name: str,
    time_window: str = "24h",
    save_to_file: bool = True,
    format: str = "markdown"
) -> QualityReport:
    """
    便捷函数：生成质量报告（任务12.8）

    Args:
        prompt_name: Prompt名称
        time_window: 时间窗口
        save_to_file: 是否保存到文件
        format: 文件格式

    Returns:
        QualityReport: 质量报告
    """
    report = quality_report_generator.generate_report(
        prompt_name=prompt_name,
        time_window=time_window
    )

    if save_to_file:
        file_path = quality_report_generator.save_report(report, format=format)
        report.monitoring_summary["report_file"] = str(file_path)

    return report


def generate_all_reports(time_window: str = "24h") -> List[QualityReport]:
    """
    便捷函数：为所有Prompt生成报告

    Args:
        time_window: 时间窗口

    Returns:
        List[QualityReport]: 报告列表
    """
    # 获取所有被监控的prompt
    prompt_names = list(prompt_monitor.prompt_windows.keys())

    reports = []
    for prompt_name in prompt_names:
        try:
            report = generate_quality_report(
                prompt_name=prompt_name,
                time_window=time_window
            )
            reports.append(report)
        except Exception as e:
            # 记录错误但继续处理其他prompt
            print(f"生成报告失败 ({prompt_name}): {e}")

    return reports
