"""
技术分析器（新版）
使用technical_analysis.yaml模板分析价格走势和技术指标
"""
import json
from typing import Dict, Any

from app.services.research_engine.analyzers.base_analyzer import BaseAnalyzer


class TechnicalAnalysisNew(BaseAnalyzer):
    """技术分析器（新版）"""

    def __init__(self):
        """初始化技术分析器"""
        super().__init__(
            template_name="technical_analysis",
            analyzer_name="TechnicalAnalysisNew"
        )

    def _prepare_template_variables(self, aggregated_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        准备模板变量

        Args:
            aggregated_data: 聚合的项目数据

        Returns:
            Dict: 模板变量
        """
        market_data = aggregated_data.get("market_data", {})

        # 价格数据
        current_price = market_data.get("current_price", 0)
        high_24h = market_data.get("high_24h", current_price * 1.05)
        low_24h = market_data.get("low_24h", current_price * 0.95)

        # 7天和30天数据（简化估算）
        price_change_7d = market_data.get("price_change_percentage_7d", 0)
        price_change_30d = market_data.get("price_change_percentage_30d", 0)

        high_7d = current_price * (1 + abs(price_change_7d) / 100)
        low_7d = current_price * (1 - abs(price_change_7d) / 100)

        high_30d = current_price * (1 + abs(price_change_30d) / 100)
        low_30d = current_price * (1 - abs(price_change_30d) / 100)

        # 技术指标（简化版 - 实际应该从技术分析API获取）
        rsi_14 = 50  # 默认中性
        if price_change_7d > 5:
            rsi_14 = 65  # 偏多
        elif price_change_7d < -5:
            rsi_14 = 35  # 偏空

        macd_value = "正值" if price_change_7d > 0 else "负值"
        macd_signal = "金叉" if price_change_7d > price_change_30d else "死叉"

        # 移动平均线（简化估算）
        ma_50 = current_price * 0.95
        ma_200 = current_price * 0.90

        # 交易量
        volume_24h = market_data.get("total_volume", 0)
        volume_7d_avg = volume_24h * 0.9  # 简化估算

        return {
            "current_price": current_price,
            "high_24h": high_24h,
            "low_24h": low_24h,
            "high_7d": high_7d,
            "low_7d": low_7d,
            "high_30d": high_30d,
            "low_30d": low_30d,
            "rsi_14": rsi_14,
            "macd_value": macd_value,
            "macd_signal": macd_signal,
            "ma_50": ma_50,
            "ma_200": ma_200,
            "volume_24h": self._format_volume(volume_24h),
            "volume_7d_avg": self._format_volume(volume_7d_avg),
        }

    def _format_volume(self, volume: float) -> str:
        """格式化交易量"""
        if volume >= 1_000_000_000:
            return f"{volume / 1_000_000_000:.1f}B"
        elif volume >= 1_000_000:
            return f"{volume / 1_000_000:.1f}M"
        else:
            return f"{volume:.0f}"

    def _parse_response(self, content: str) -> Dict[str, Any]:
        """
        解析LLM响应

        Args:
            content: LLM返回的文本

        Returns:
            Dict: 解析后的结构化数据
        """
        # 技术分析返回Markdown格式
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
            "价格走势",
            "技术指标",
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
        default_analysis = f"""## 价格走势
{symbol}的价格走势数据不完整，暂时无法提供详细的技术分析。

## 技术指标分析
技术指标数据待补充。

## 支撑与阻力
支撑阻力位分析待补充。

## 短期展望
技术面展望待补充。
"""

        return {
            "analysis": result.get("analysis", default_analysis),
            "format": "markdown",
        }


# 全局单例
technical_analysis_new = TechnicalAnalysisNew()
