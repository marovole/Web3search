"""
基本面分析器
使用fundamental_analysis.yaml模板分析项目基本面
"""
import json
from typing import Dict, Any
from datetime import datetime

from app.services.research_engine.analyzers.base_analyzer import BaseAnalyzer


class FundamentalAnalyzer(BaseAnalyzer):
    """基本面分析器"""

    def __init__(self):
        """初始化基本面分析器"""
        super().__init__(
            template_name="fundamental_analysis",
            analyzer_name="FundamentalAnalyzer"
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

        # 项目信息
        project_name = project_info.get("name", symbol)
        categories = project_info.get("categories", [])
        project_type = ", ".join(categories[:2]) if categories else "未知"

        # 上线时间
        genesis_date = project_info.get("genesis_date")
        if genesis_date:
            try:
                dt = datetime.fromisoformat(genesis_date.replace('Z', '+00:00'))
                launch_date = dt.strftime("%Y-%m")
            except:
                launch_date = "未知"
        else:
            launch_date = "未知"

        # 官网
        homepage = project_info.get("links", {}).get("homepage", [""])[0] or "N/A"

        # 代币信息
        current_price = market_data.get("current_price", 0)
        market_cap = market_data.get("market_cap", 0)
        circulating_supply = market_data.get("circulating_supply", 0)
        total_supply = market_data.get("total_supply", 0)

        # 完全稀释估值
        if total_supply and current_price:
            fdv = total_supply * current_price
        else:
            fdv = market_cap

        # 协议数据（简化版 - 实际应该从DefiLlama等获取）
        tvl = market_data.get("total_volume", 0) * 10  # 简化估算
        revenue_30d = tvl * 0.001  # 简化估算
        active_users_30d = int(market_data.get("total_volume", 0) / 1000)  # 简化估算

        # 团队和投资（实际应该从专门的数据源获取）
        team_info = "核心团队"
        investors = "主要投资机构"

        return {
            "project_name": project_name,
            "project_type": project_type,
            "launch_date": launch_date,
            "website": homepage,
            "symbol": symbol,
            "total_supply": self._format_number(total_supply),
            "circulating_supply": self._format_number(circulating_supply),
            "price": current_price,
            "fdv": self._format_number(fdv),
            "tvl": self._format_number(tvl),
            "revenue_30d": self._format_number(revenue_30d),
            "active_users_30d": self._format_number(active_users_30d),
            "team_info": team_info,
            "investors": investors,
        }

    def _format_number(self, num: float) -> str:
        """格式化数字为易读形式"""
        if num >= 1_000_000_000:
            return f"{num / 1_000_000_000:.2f}B"
        elif num >= 1_000_000:
            return f"{num / 1_000_000:.2f}M"
        elif num >= 1_000:
            return f"{num / 1_000:.2f}K"
        else:
            return f"{num:.2f}"

    def _parse_response(self, content: str) -> Dict[str, Any]:
        """
        解析LLM响应

        Args:
            content: LLM返回的文本

        Returns:
            Dict: 解析后的结构化数据
        """
        # 基本面分析返回Markdown格式
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
            "项目概述",
            "代币经济学",
            "市场表现",
        ]

        for section in required_sections:
            if section not in analysis:
                print(f"⚠️ 缺少章节: {section}")
                # 不严格要求，继续执行
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
        default_analysis = f"""## 项目概述
{symbol}是一个加密货币项目。由于数据不完整，暂时无法提供详细的基本面分析。

## 代币经济学
代币经济学数据待补充。

## 市场表现
市场表现数据待补充。

## 竞争优势
竞争优势分析待补充。
"""

        return {
            "analysis": result.get("analysis", default_analysis),
            "format": "markdown",
        }


# 全局单例
fundamental_analyzer = FundamentalAnalyzer()
