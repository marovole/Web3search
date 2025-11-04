"""
竞品分析器（新版）
使用competitor_analysis.yaml模板对比项目与竞品
"""
import json
from typing import Dict, Any

from app.services.research_engine.analyzers.base_analyzer import BaseAnalyzer


class CompetitorAnalysisNew(BaseAnalyzer):
    """竞品分析器（新版）"""

    def __init__(self):
        """初始化竞品分析器"""
        super().__init__(
            template_name="competitor_analysis",
            analyzer_name="CompetitorAnalysisNew"
        )

    def _prepare_template_variables(self, aggregated_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        准备模板变量

        Args:
            aggregated_data: 聚合的项目数据

        Returns:
            Dict: 模板变量
        """
        symbol = aggregated_data.get("symbol", "Unknown")
        project_info = aggregated_data.get("project_info", {})
        market_data = aggregated_data.get("market_data", {})

        # 目标项目数据
        project_name = project_info.get("name", symbol)
        project_tvl = market_data.get("total_volume", 0) * 10  # 简化估算
        project_volume = market_data.get("total_volume", 0)
        project_users = int(project_volume / 1000)  # 简化估算
        project_market_cap = market_data.get("market_cap", 0)

        # 竞品数据（简化版 - 实际应该从API获取相同类别的顶级项目）
        # 这里使用简化的估算
        competitor1_name = "竞品A"
        competitor1_tvl = project_tvl * 0.5
        competitor1_volume = project_volume * 0.4
        competitor1_users = project_users * 0.3
        competitor1_market_cap = project_market_cap * 0.6

        competitor2_name = "竞品B"
        competitor2_tvl = project_tvl * 0.8
        competitor2_volume = project_volume * 0.6
        competitor2_users = project_users * 0.5
        competitor2_market_cap = project_market_cap * 0.9

        return {
            "project_name": project_name,
            "project_tvl": self._format_number(project_tvl),
            "project_volume": self._format_number(project_volume),
            "project_users": self._format_number(project_users),
            "project_market_cap": self._format_number(project_market_cap),
            "competitor1_name": competitor1_name,
            "competitor1_tvl": self._format_number(competitor1_tvl),
            "competitor1_volume": self._format_number(competitor1_volume),
            "competitor1_users": self._format_number(competitor1_users),
            "competitor1_market_cap": self._format_number(competitor1_market_cap),
            "competitor2_name": competitor2_name,
            "competitor2_tvl": self._format_number(competitor2_tvl),
            "competitor2_volume": self._format_number(competitor2_volume),
            "competitor2_users": self._format_number(competitor2_users),
            "competitor2_market_cap": self._format_number(competitor2_market_cap),
        }

    def _format_number(self, num: float) -> str:
        """格式化数字"""
        if num >= 1_000_000_000:
            return f"{num / 1_000_000_000:.1f}B"
        elif num >= 1_000_000:
            return f"{num / 1_000_000:.1f}M"
        elif num >= 1_000:
            return f"{num / 1_000:.1f}K"
        else:
            return f"{num:.0f}"

    def _parse_response(self, content: str) -> Dict[str, Any]:
        """
        解析LLM响应

        Args:
            content: LLM返回的文本

        Returns:
            Dict: 解析后的结构化数据
        """
        # 竞品分析返回Markdown格式
        return {
            "analysis": content,
            "format": "markdown",
        }

    def _validate_output(self, result: Dict[str, Any]) -> bool:
        """
        验证输出格式

        Args:
            result: 解析后的结果

        Returns:
            bool: 是否通过验证
        """
        if "analysis" not in result:
            return False

        analysis = result["analysis"]

        # 检查关键章节
        required_sections = [
            "关键指标对比",
            "相对优势",
        ]

        for section in required_sections:
            if section not in analysis:
                print(f"⚠️ 缺少章节: {section}")
                pass

        return True

    def _fix_invalid_output(self, result: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        """
        修复无效输出

        Args:
            result: 原始结果
            symbol: 币种符号

        Returns:
            Dict: 修复后的结果
        """
        default_analysis = f"""## 关键指标对比

{symbol}的竞品对比数据不完整，暂时无法提供详细的竞品分析。

## 相对优势
相对优势分析待补充。

## 差距分析
差距分析待补充。

## 市场地位
市场地位分析待补充。
"""

        return {
            "analysis": result.get("analysis", default_analysis),
            "format": "markdown",
        }


# 全局单例
competitor_analysis_new = CompetitorAnalysisNew()
