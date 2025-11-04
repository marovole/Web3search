"""
风险分析器
使用risk_assessment.yaml模板评估项目风险
"""
import json
from typing import Dict, Any

from app.services.research_engine.analyzers.base_analyzer import BaseAnalyzer


class RiskAnalyzer(BaseAnalyzer):
    """风险分析器"""

    def __init__(self):
        """初始化风险分析器"""
        super().__init__(
            template_name="risk_assessment",
            analyzer_name="RiskAnalyzer"
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

        # 提取项目信息
        project_name = project_info.get("name", symbol)
        categories = project_info.get("categories", [])
        project_type = categories[0] if categories else "未知"

        # 计算运行时长
        genesis_date = project_info.get("genesis_date")
        if genesis_date:
            from datetime import datetime
            try:
                genesis = datetime.fromisoformat(genesis_date.replace('Z', '+00:00'))
                days = (datetime.now() - genesis).days
                if days > 365:
                    running_time = f"{days // 365}年"
                else:
                    running_time = f"{days}天"
            except:
                running_time = "未知"
        else:
            running_time = "未知"

        # 审计状态（简化版）
        audit_status = "未知"
        # 实际应该从链上数据或项目信息中获取

        # 监管合规
        regulatory_status = "去中心化，无注册实体"

        # 市场竞争
        market_cap = market_data.get("market_cap", 0)
        if market_cap > 10_000_000_000:  # 100亿美元
            competition_level = "高（市场份额大，竞争激烈）"
        elif market_cap > 1_000_000_000:  # 10亿美元
            competition_level = "中等"
        else:
            competition_level = "低（市场份额小）"

        # 代币集中度（简化版）
        token_concentration = "中等"

        # 流动性
        volume_24h = market_data.get("total_volume", 0)
        if volume_24h > 100_000_000:  # 1亿美元
            liquidity_level = "高"
        elif volume_24h > 10_000_000:  # 1000万美元
            liquidity_level = "中等"
        else:
            liquidity_level = "低"

        return {
            "project_name": project_name,
            "project_type": project_type,
            "running_time": running_time,
            "audit_status": audit_status,
            "regulatory_status": regulatory_status,
            "competition_level": competition_level,
            "token_concentration": token_concentration,
            "liquidity_level": liquidity_level,
        }

    def _parse_response(self, content: str) -> Dict[str, Any]:
        """
        解析LLM响应

        Args:
            content: LLM返回的文本

        Returns:
            Dict: 解析后的结构化数据
        """
        # 风险评估返回Markdown格式，不需要JSON解析
        # 直接返回文本内容
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
        # 检查必要字段
        if "analysis" not in result:
            return False

        analysis = result["analysis"]

        # 检查是否包含关键章节
        required_sections = [
            "风险概述",
            "主要风险",
            "市场风险",
            "技术风险",
        ]

        for section in required_sections:
            if section not in analysis:
                print(f"⚠️ 缺少章节: {section}")
                return False

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
        # 提供默认的风险评估
        default_analysis = f"""## 风险概述
总体风险等级：**中**

{symbol}项目的风险评估数据不完整，无法给出详细的风险分析。

## 主要风险

### 市场风险 [中]
加密货币市场波动性较大，价格可能受到多种因素影响。

### 技术风险 [中]
技术实现的复杂性可能带来潜在的安全隐患。

### 监管风险 [中]
监管政策的变化可能对项目产生影响。

### 竞争风险 [中]
市场竞争激烈，新进入者可能分流市场份额。

## 风险缓释
建议关注项目的后续发展和风险控制措施。
"""

        return {
            "analysis": result.get("analysis", default_analysis),
            "format": "markdown",
        }


# 全局单例
risk_analyzer = RiskAnalyzer()
