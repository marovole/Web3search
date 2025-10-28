"""
Deep Research 引擎
生成15-30秒的深度研究报告
"""
import asyncio
from typing import Dict, Any, Optional, Callable, Awaitable, List
from datetime import datetime

from app.services.llm import llm_client, ModelConfig
from app.services.data_aggregator import data_aggregator
from app.services.prompt_manager import prompt_manager

# 导入9个Analyzer和统一输出接口
from app.services.research_engine.analyzers.analyzer_output import (
    AnalyzerOutput,
    VisualizationHint,
    create_error_output,
)
from app.services.research_engine.analyzers.tldr_generator import tldr_generator
from app.services.research_engine.analyzers.timeframe_analyzer import timeframe_analyzer
from app.services.research_engine.analyzers.sentiment_analyzer import sentiment_analyzer
from app.services.research_engine.analyzers.technical_analyzer import technical_analyzer
from app.services.research_engine.analyzers.onchain_analyzer import onchain_analyzer
from app.services.research_engine.analyzers.competitor_analyzer import competitor_analyzer
from app.services.research_engine.analyzers.tokenomics_analyzer import tokenomics_analyzer
from app.services.research_engine.analyzers.risk_assessor import risk_assessor
from app.services.research_engine.analyzers.conclusion_synthesizer import conclusion_synthesizer


class DeepResearchEngine:
    """
    Deep Research 引擎
    生成全面深入的加密货币项目分析报告
    """

    def __init__(self):
        """初始化Deep Research引擎"""
        self.llm_client = llm_client
        self.data_aggregator = data_aggregator
        self.prompt_manager = prompt_manager

        # 初始化9个Analyzer（使用全局单例）
        self.tldr_generator = tldr_generator
        self.timeframe_analyzer = timeframe_analyzer
        self.sentiment_analyzer = sentiment_analyzer
        self.technical_analyzer = technical_analyzer
        self.onchain_analyzer = onchain_analyzer
        self.competitor_analyzer = competitor_analyzer
        self.tokenomics_analyzer = tokenomics_analyzer
        self.risk_assessor = risk_assessor
        self.conclusion_synthesizer = conclusion_synthesizer

    async def research(
        self,
        query: str,
        symbol: Optional[str] = None,
        progress_callback: Optional[Callable[[str, int], Awaitable[None]]] = None,
    ) -> Dict[str, Any]:
        """
        执行深度研究（任务 8.2 - 添加进度提示）

        Args:
            query: 用户查询
            symbol: 币种符号（可选，会从query中提取）
            progress_callback: 进度回调函数，接收(message: str, progress: int)

        Returns:
            Dict: 研究报告数据
        """
        start_time = datetime.utcnow()

        # 提取币种符号
        if not symbol:
            symbol = self._extract_symbol(query)

        print(f"🔍 开始深度研究: {symbol}")

        # 发送进度：开始
        if progress_callback:
            await progress_callback("🔍 开始深度研究分析...", 0)

        # 步骤1: 聚合数据（并行获取）
        print("  📊 采集数据...")
        if progress_callback:
            await progress_callback("📊 正在收集市场数据、链上数据和社交媒体数据...", 25)

        aggregated_data = await self.data_aggregator.aggregate_project_data(symbol)

        if "error" in aggregated_data:
            return {
                "error": aggregated_data["error"],
                "symbol": symbol,
            }

        # 步骤2: 格式化数据为LLM可读格式
        formatted_data = self.data_aggregator.format_for_llm(aggregated_data)

        # 步骤3: 三阶段分析
        print("  🤖 生成分析...")
        if progress_callback:
            await progress_callback("🤖 正在进行深度分析（生成摘要、技术分析、市场分析等）...", 50)

        # 阶段1: 生成TL;DR（使用TldrGenerator）
        tldr_result = await self._generate_tldr(query, symbol, aggregated_data)
        tldr_data = tldr_result.get("data", {})
        tldr_summary = tldr_data.get("summary", "⚠️ TL;DR生成失败")

        # 阶段2: 七维度分析（并行调用7个analyzer）
        sections_result = await self._generate_sections(query, symbol, formatted_data, aggregated_data)

        # 提取结果
        analyzer_outputs = sections_result["analyzer_outputs"]
        # 添加tldr到analyzer_outputs
        analyzer_outputs["tldr"] = tldr_result
        sections = sections_result["sections"]
        visualization_hints = sections_result["visualization_hints"]

        # 发送进度：分析完成，生成报告
        if progress_callback:
            await progress_callback("📝 正在生成研究报告和投资建议...", 75)

        # 结论已经在_generate_sections()中生成，直接使用
        conclusion_result = analyzer_outputs.get("conclusion")
        if not conclusion_result:
            # 如果conclusion生成失败，创建错误输出
            conclusion_result = create_error_output("conclusion", "结论生成失败")
            analyzer_outputs["conclusion"] = conclusion_result

        # 组装完整报告
        end_time = datetime.utcnow()
        generation_time = (end_time - start_time).total_seconds()

        # 收集所有使用的模型
        models_used = {}
        for key, output in analyzer_outputs.items():
            metadata = output.get("metadata", {})
            if "model_used" in metadata:
                models_used[key] = metadata["model_used"]

        # 收集所有数据源
        data_sources = set()
        for key, output in analyzer_outputs.items():
            metadata = output.get("metadata", {})
            if "data_sources" in metadata:
                data_sources.update(metadata.get("data_sources", []))

        report = {
            "symbol": symbol,
            "query": query,
            # 向后兼容的文本字段
            "tldr": tldr_summary,
            "sections": sections,
            "conclusion": conclusion_summary,
            # 新的结构化数据字段
            "analyzer_outputs": analyzer_outputs,
            "visualization_hints": visualization_hints,
            # 元数据
            "data_sources": list(data_sources) if data_sources else [
                "CoinGecko",
                "Etherscan/BSCScan",
                "Twitter",
                "Reddit",
                "CryptoPanic",
            ],
            "models_used": models_used,
            "generation_time": generation_time,
            "timestamp": datetime.utcnow().isoformat(),
        }

        print(f"✅ 研究完成，耗时 {generation_time:.2f} 秒")

        # 发送进度：完成
        if progress_callback:
            await progress_callback(f"✅ 研究报告生成完成！（耗时 {generation_time:.1f} 秒）", 100)

        return report

    def _extract_symbol(self, query: str) -> str:
        """从查询中提取币种符号"""
        # 简单实现，与QuickChat相同
        common_symbols = {
            "比特币": "BTC",
            "以太坊": "ETH",
            "币安币": "BNB",
        }

        query_lower = query.lower()
        for name, symbol in common_symbols.items():
            if name in query_lower:
                return symbol

        # 检查大写符号
        words = query.split()
        for word in words:
            word_upper = word.upper()
            if len(word_upper) >= 2 and len(word_upper) <= 10:
                if word_upper in ["BTC", "ETH", "BNB", "XRP", "DOGE", "SOL"]:
                    return word_upper

        return "BTC"

    async def _generate_tldr(
        self,
        query: str,
        symbol: str,
        aggregated_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        生成TL;DR摘要（使用TldrGenerator）

        Args:
            query: 用户查询
            symbol: 代币符号
            aggregated_data: 聚合数据

        Returns:
            Dict[str, Any]: 包含data（tldr数据）和metadata的字典
        """
        print("  📝 生成TL;DR摘要...")

        # 调用TldrGenerator
        tldr_output = await self.tldr_generator.generate_tldr(
            query=query,
            symbol=symbol,
            aggregated_data=aggregated_data,
        )

        if isinstance(tldr_output, Exception):
            print(f"  ⚠️ TL;DR生成失败: {str(tldr_output)}")
            return {
                "data": {"summary": f"⚠️ TL;DR生成失败: {str(tldr_output)}"},
                "metadata": {"analyzer_name": "TldrGenerator", "error": True},
            }

        if isinstance(tldr_output, AnalyzerOutput):
            return {
                "data": tldr_output.data,
                "metadata": tldr_output.metadata.model_dump(),
                "error": tldr_output.error,
            }

        # 意外类型
        print(f"  ⚠️ TL;DR返回了意外的类型: {type(tldr_output)}")
        return {
            "data": {"summary": "⚠️ TL;DR返回格式不正确"},
            "metadata": {"analyzer_name": "TldrGenerator", "error": True},
        }

    async def _generate_sections(
        self,
        query: str,
        symbol: str,
        formatted_data: Dict[str, str],
        raw_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        并行调用8个Analyzer生成分析内容（不包括tldr，包括conclusion）

        Args:
            query: 用户查询
            symbol: 代币符号
            formatted_data: 格式化数据
            raw_data: 原始数据

        Returns:
            Dict[str, Any]: 包含analyzer_outputs（AnalyzerOutput对象）和sections（文本内容）
        """
        print("  🔬 并行调用8个Analyzer...")

        # 准备各analyzer所需的数据
        market_data = raw_data.get("market_data", {})
        social_data = raw_data.get("social_data", {})
        onchain_data = raw_data.get("onchain_data", {})
        project_info = raw_data.get("project_info", {})

        # 提取竞品信息
        categories = project_info.get("categories", [])
        competitors_str = ", ".join(categories) if categories else "加密货币"

        # 提取代币经济学数据
        tokenomics_data = {
            "total_supply": market_data.get("total_supply"),
            "circulating_supply": market_data.get("circulating_supply"),
            "max_supply": market_data.get("max_supply"),
        }

        # 并行调用8个analyzer（包括conclusion）
        (
            timeframe_output,
            sentiment_output,
            technical_output,
            onchain_output,
            competitor_output,
            tokenomics_output,
            risk_output,
            conclusion_output,
        ) = await asyncio.gather(
            self.timeframe_analyzer.analyze(symbol, query, market_data),
            self.sentiment_analyzer.analyze(symbol, social_data),
            self.technical_analyzer.analyze(symbol, market_data),
            self.onchain_analyzer.analyze(symbol, onchain_data),
            self.competitor_analyzer.analyze(symbol, competitors_str),
            self.tokenomics_analyzer.analyze(symbol, tokenomics_data),
            self.risk_assessor.analyze(symbol, raw_data),
            self.conclusion_synthesizer.synthesize(symbol, query, raw_data),
            return_exceptions=True,
        )

        # 收集analyzer输出和降级处理
        analyzer_outputs = {}
        visualization_hints: List[VisualizationHint] = []

        # 处理每个analyzer的输出
        analyzers_data = [
            ("timeframe", timeframe_output, "时间窗分析"),
            ("sentiment", sentiment_output, "情绪分析"),
            ("technical", technical_output, "技术分析"),
            ("onchain", onchain_output, "链上分析"),
            ("competitor", competitor_output, "竞品分析"),
            ("tokenomics", tokenomics_output, "代币经济学"),
            ("risk", risk_output, "风险评估"),
            ("conclusion", conclusion_output, "结论合成"),
        ]

        # 处理每个analyzer的输出并统计失败情况
        failed_analyzers = []
        successful_analyzers = []

        for key, output, name in analyzers_data:
            if isinstance(output, Exception):
                print(f"  ⚠️ {name}失败: {str(output)}")
                # 使用统一的错误输出创建函数
                analyzer_outputs[key] = create_error_output(key, str(output))
                failed_analyzers.append((key, name, str(output)))
            elif isinstance(output, AnalyzerOutput):
                if output.error:
                    # AnalyzerOutput对象但包含错误
                    print(f"  ⚠️ {name}失败: {output.error}")
                    failed_analyzers.append((key, name, output.error))
                else:
                    # 正常输出
                    analyzer_outputs[key] = output
                    successful_analyzers.append((key, name))
                    # 收集可视化提示
                    visualization_hints.extend(output.visualization_hints)
            else:
                print(f"  ⚠️ {name}返回了意外的类型: {type(output)}")
                analyzer_outputs[key] = create_error_output(
                    key, f"返回类型错误: {type(output)}"
                )
                failed_analyzers.append((key, name, f"返回类型错误: {type(output)}"))

        # 应用智能降级策略
        self._apply_fallback_strategy(analyzer_outputs, failed_analyzers, successful_analyzers, symbol)

        # 构建向后兼容的sections字典（提取文本内容）
        sections = {
            "timeframe": self._extract_summary(analyzer_outputs.get("timeframe")),
            "sentiment": self._extract_summary(analyzer_outputs.get("sentiment")),
            "technical_analysis": self._extract_summary(analyzer_outputs.get("technical")),
            "onchain_analysis": self._extract_summary(analyzer_outputs.get("onchain")),
            "competitor_analysis": self._extract_summary(analyzer_outputs.get("competitor")),
            "tokenomics": self._extract_summary(analyzer_outputs.get("tokenomics")),
            "risk_assessment": self._extract_summary(analyzer_outputs.get("risk")),
            "conclusion": self._extract_summary(analyzer_outputs.get("conclusion")),
        }

        return {
            "analyzer_outputs": analyzer_outputs,
            "sections": sections,
            "visualization_hints": visualization_hints,
        }

    def _extract_summary(self, analyzer_output: Optional[AnalyzerOutput]) -> str:
        """从analyzer输出中提取摘要文本（用于向后兼容）"""
        if not analyzer_output:
            return "⚠️ 分析数据不可用"

        if isinstance(analyzer_output, AnalyzerOutput):
            # 处理新的AnalyzerOutput对象
            if analyzer_output.error:
                return f"⚠️ {analyzer_output.error}"

            # 尝试提取summary字段
            data = analyzer_output.data
            if "summary" in data:
                return data["summary"]
            elif "judgment" in data:  # TL;DR 使用judgment字段
                return data["judgment"]
            else:
                # 如果没有summary，返回第一个字符串字段
                for key, value in data.items():
                    if isinstance(value, str) and value.strip():
                        return value
                return "✅ 分析完成"

        # 向后兼容：处理旧的字典格式
        elif isinstance(analyzer_output, dict):
            data = analyzer_output.get("data", {})
            if analyzer_output.get("error"):
                return f"⚠️ {data.get('summary', '生成失败')}"

            if "summary" in data:
                return data["summary"]
            elif "judgment" in data:
                return data["judgment"]

        return "⚠️ 分析数据不可用"

    def _apply_fallback_strategy(
        self,
        analyzer_outputs: Dict[str, AnalyzerOutput],
        failed_analyzers: list,
        successful_analyzers: list,
        symbol: str
    ) -> None:
        """
        应用智能降级策略，当多个analyzers失败时提供有意义的反馈

        Args:
            analyzer_outputs: 所有analyzer的输出字典
            failed_analyzers: 失败的analyzer列表 [(key, name, error), ...]
            successful_analyzers: 成功的analyzer列表 [(key, name), ...]
            symbol: 代币符号
        """
        failure_rate = len(failed_analyzers) / 8.0  # 8个analyzer

        # 记录失败情况
        if failed_analyzers:
            failed_names = [name for _, name, _ in failed_analyzers]
            print(f"  📊 分析完成: {len(successful_analyzers)}/8 个模块成功")
            if len(successful_analyzers) > 0:
                successful_names = [name for _, name in successful_analyzers]
                print(f"  ✅ 成功模块: {', '.join(successful_names)}")
            if len(failed_analyzers) > 0:
                print(f"  ⚠️ 失败模块: {', '.join(failed_names)}")

        # 根据失败率应用不同的降级策略
        if failure_rate >= 0.75:  # 75%以上失败
            print(f"  🚨 严重失败率 ({failure_rate:.1%})，应用紧急降级策略")
            self._emergency_fallback(analyzer_outputs, symbol, failed_analyzers)
        elif failure_rate >= 0.5:  # 50%以上失败
            print(f"  ⚠️ 高失败率 ({failure_rate:.1%})，应用部分降级策略")
            self._partial_fallback(analyzer_outputs, symbol, failed_analyzers)
        elif failure_rate >= 0.25:  # 25%以上失败
            print(f"  📝 中等失败率 ({failure_rate:.1%})，应用温和降级策略")
            self._gentle_fallback(analyzer_outputs, symbol, failed_analyzers)
        # 低于25%失败率不需要特殊降级处理

    def _emergency_fallback(
        self,
        analyzer_outputs: Dict[str, AnalyzerOutput],
        symbol: str,
        failed_analyzers: list
    ) -> None:
        """紧急降级策略：当大部分analyzers失败时"""
        from app.services.research_engine.analyzers.analyzer_output import create_analyzer_output

        # 创建基础的市场信息
        fallback_data = {
            "summary": f"⚠️ {symbol} 分析服务遇到严重问题，仅提供基础信息",
            "fallback_level": "emergency",
            "basic_info": {
                "symbol": symbol,
                "status": "部分功能可用",
                "note": "建议稍后重试或联系技术支持"
            },
            "failed_analyzers": [name for _, name, _ in failed_analyzers]
        }

        # 更新关键的analyzers输出
        critical_analyzers = ["timeframe", "sentiment", "conclusion"]
        for analyzer_name in critical_analyzers:
            if analyzer_name in analyzer_outputs and analyzer_outputs[analyzer_name].error:
                analyzer_outputs[analyzer_name] = create_analyzer_output(
                    data=fallback_data,
                    analyzer_name=analyzer_name,
                    model_used="fallback_emergency",
                    confidence=0,
                    validation_passed=False,
                    validation_warnings=["Emergency fallback due to multiple analyzer failures"]
                )

    def _partial_fallback(
        self,
        analyzer_outputs: Dict[str, AnalyzerOutput],
        symbol: str,
        failed_analyzers: list
    ) -> None:
        """部分降级策略：当较多analyzers失败时"""
        from app.services.research_engine.analyzers.analyzer_output import create_analyzer_output

        # 为失败的analyzers提供有意义的降级信息
        fallback_templates = {
            "timeframe": {
                "summary": f"⚠️ {symbol} 时间窗分析暂时不可用，建议关注价格走势和市场情绪",
                "fallback_note": "基础市场信息获取失败"
            },
            "sentiment": {
                "summary": f"⚠️ {symbol} 社交情绪分析暂时不可用，请参考其他分析维度",
                "fallback_note": "社交媒体数据获取失败"
            },
            "technical": {
                "summary": f"⚠️ {symbol} 技术分析暂时不可用，建议关注基本面和市场表现",
                "fallback_note": "技术指标计算失败"
            },
            "onchain": {
                "summary": f"⚠️ {symbol} 链上数据分析暂时不可用，请参考价格和市场表现",
                "fallback_note": "区块链数据获取失败"
            },
            "competitor": {
                "summary": f"⚠️ {symbol} 竞品分析暂时不可用，建议关注项目本身基本面",
                "fallback_note": "竞品数据获取失败"
            },
            "tokenomics": {
                "summary": f"⚠️ {symbol} 代币经济学分析暂时不可用，建议关注市场表现",
                "fallback_note": "代币经济数据获取失败"
            },
            "risk": {
                "summary": f"⚠️ {symbol} 风险评估暂时不可用，请注意投资风险，建议谨慎决策",
                "fallback_note": "风险评估计算失败"
            },
            "conclusion": {
                "summary": f"⚠️ {symbol} 综合结论暂时无法生成，部分分析维度遇到技术问题，建议稍后重试",
                "fallback_note": "综合分析失败"
            }
        }

        for analyzer_name, _, _ in failed_analyzers:
            if analyzer_name in fallback_templates:
                template = fallback_templates[analyzer_name]
                analyzer_outputs[analyzer_name] = create_analyzer_output(
                    data=template,
                    analyzer_name=analyzer_name,
                    model_used="fallback_partial",
                    confidence=20,  # 低置信度
                    validation_passed=False,
                    validation_warnings=["Partial fallback due to analyzer failure"]
                )

    def _gentle_fallback(
        self,
        analyzer_outputs: Dict[str, AnalyzerOutput],
        symbol: str,
        failed_analyzers: list
    ) -> None:
        """温和降级策略：当少数analyzers失败时"""
        # 只记录警告，不替换输出，让现有的错误输出保持原样
        failed_count = len(failed_analyzers)
        total_count = 8
        success_count = total_count - failed_count

        print(f"  📊 分析结果: {success_count}/{total_count} 个模块成功")
        print(f"  💡 提示: {failed_count} 个模块遇到问题，但不影响整体分析质量")


# ================================
# 全局实例
# ================================

deep_research_engine = DeepResearchEngine()
