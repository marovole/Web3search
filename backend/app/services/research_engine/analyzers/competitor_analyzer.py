"""
Competitor Analyzer
竞品对比分析器 - 识别竞品、对比关键指标、评估市场定位
"""
import yaml
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from app.services.llm import llm_client
from app.services.research_engine.analyzers.analyzer_output import (
    AnalyzerOutput,
    create_analyzer_output,
    create_error_output,
    create_competitor_table_hint,
)


class CompetitorAnalyzer:
    """竞品对比分析器"""

    # 赛道竞品映射表
    SECTOR_COMPETITORS = {
        "DEX": ["UNI", "CAKE", "SUSHI", "CRV", "BAL", "DYDX"],
        "借贷协议": ["AAVE", "COMP", "MKR", "JUP", "VENUS"],
        "Layer1": ["ETH", "SOL", "ADA", "AVAX", "DOT", "NEAR"],
        "Layer2": ["ARB", "OP", "MATIC", "IMX", "STRK"],
        "NFT市场": ["BLUR", "LOOKS", "X2Y2"],
        "衍生品交易所": ["DYDX", "GMX", "GNS", "PERP"],
        "跨链桥": ["ACROSS", "HOP", "STARGATE"],
        "稳定币": ["USDT", "USDC", "DAI", "FRAX", "LUSD"],
        "流动性质押": ["LDO", "RPL", "FXS", "ANKR"],
        "收益聚合器": ["YFI", "CVX", "BTRFLY"],
    }

    def __init__(self):
        """初始化竞品分析器"""
        self._load_prompts()
        self.llm_client = llm_client

    def _load_prompts(self):
        """加载 prompt 模板"""
        from app.core.config import settings
        prompt_path = settings.BASE_DIR / "prompts" / "deep_research" / "competitor.yaml"

        with open(prompt_path, 'r', encoding='utf-8') as f:
            prompts = yaml.safe_load(f)

        self.system_prompt = prompts["system_prompt"]
        self.user_prompt_template = prompts["user_prompt_template"]
        self.output_format = prompts["output_format"]
        self.validation_rules = prompts["validation_rules"]
        self.model_config = prompts["model_config"]

    def _identify_competitors(self, category: str, symbol: str) -> List[str]:
        """
        识别竞品

        Args:
            category: 项目类别
            symbol: 目标项目代币符号

        Returns:
            竞品符号列表（最多5个）
        """
        # 标准化类别名称
        category_map = {
            "dex": "DEX",
            "decentralized exchange": "DEX",
            "lending": "借贷协议",
            "lending protocol": "借贷协议",
            "layer 1": "Layer1",
            "layer 2": "Layer2",
            "nft marketplace": "NFT市场",
            "derivatives": "衍生品交易所",
            "bridge": "跨链桥",
            "stablecoin": "稳定币",
            "liquid staking": "流动性质押",
            "yield aggregator": "收益聚合器",
        }

        normalized_category = category_map.get(category.lower(), category)

        # 从映射表获取竞品
        competitors = self.SECTOR_COMPETITORS.get(normalized_category, [])

        # 排除自身
        competitors = [c for c in competitors if c.upper() != symbol.upper()]

        # 最多返回5个竞品
        return competitors[:5]

    def _extract_competitor_data(self, aggregated_data: Dict) -> List[Dict]:
        """
        提取竞品数据

        Args:
            aggregated_data: 聚合数据

        Returns:
            竞品数据列表
        """
        competitors_raw = aggregated_data.get("competitors", [])
        competitors = []

        for comp in competitors_raw:
            competitor = {
                "name": comp.get("name", "Unknown"),
                "symbol": comp.get("symbol", ""),
                "market_cap": comp.get("market_cap", 0),
                "tvl": comp.get("tvl", 0),
                "active_users_24h": comp.get("active_users_24h", 0),
                "volume_24h": comp.get("volume_24h", 0),
                "protocol_revenue_30d": comp.get("protocol_revenue_30d", 0),
                "market_share": comp.get("market_share", "N/A"),
                "differentiation": comp.get("differentiation", "")
            }
            competitors.append(competitor)

        return competitors

    def _format_competitors_data(self, competitors: List[Dict]) -> str:
        """
        格式化竞品数据为文本

        Args:
            competitors: 竞品数据列表

        Returns:
            格式化的竞品数据文本
        """
        if not competitors:
            return "暂无竞品数据"

        lines = []
        for i, comp in enumerate(competitors, 1):
            name = comp.get("name", "Unknown")
            symbol = comp.get("symbol", "")
            market_cap = comp.get("market_cap", 0)
            tvl = comp.get("tvl", 0)
            users = comp.get("active_users_24h", 0)
            volume = comp.get("volume_24h", 0)
            revenue = comp.get("protocol_revenue_30d", 0)

            line = (
                f"竞品{i}: {name} ({symbol}) - "
                f"市值${market_cap/1e6:.0f}M, "
                f"TVL${tvl/1e9:.1f}B, "
                f"日活{users/1e3:.0f}K, "
                f"日交易量${volume/1e6:.0f}M, "
                f"月收入${revenue/1e6:.0f}M"
            )
            lines.append(line)

        return "\n".join(lines)

    def _build_comparison_table(
        self,
        target_data: Dict,
        competitors: List[Dict]
    ) -> Dict:
        """
        构建对比表格

        Args:
            target_data: 目标项目数据
            competitors: 竞品数据列表

        Returns:
            对比表格字典
        """
        metrics = ["市值", "TVL", "日活用户", "日交易量", "月收入"]

        target_values = [
            target_data.get("market_cap", 0),
            target_data.get("tvl", 0),
            target_data.get("active_users_24h", 0),
            target_data.get("volume_24h", 0),
            target_data.get("protocol_revenue_30d", 0)
        ]

        competitor_entries = []
        for comp in competitors:
            comp_values = [
                comp.get("market_cap", 0),
                comp.get("tvl", 0),
                comp.get("active_users_24h", 0),
                comp.get("volume_24h", 0),
                comp.get("protocol_revenue_30d", 0)
            ]
            competitor_entries.append({
                "name": comp.get("name", "Unknown"),
                "values": comp_values
            })

        return {
            "metrics": metrics,
            "target_project": {
                "name": target_data.get("symbol", "Target"),
                "values": target_values
            },
            "competitors": competitor_entries
        }

    def _calculate_valuation_multiples(
        self,
        target_data: Dict,
        competitors: List[Dict]
    ) -> Dict:
        """
        计算估值倍数

        Args:
            target_data: 目标项目数据
            competitors: 竞品数据列表

        Returns:
            估值倍数字典
        """
        # 目标项目估值倍数
        market_cap = target_data.get("market_cap", 0)
        tvl = target_data.get("tvl", 0)
        revenue_30d = target_data.get("protocol_revenue_30d", 0)
        annualized_revenue = revenue_30d * 12

        target_multiples = {
            "ps_ratio": round(market_cap / annualized_revenue, 2) if annualized_revenue > 0 else 0,
            "fdv_to_revenue": round(market_cap / annualized_revenue, 2) if annualized_revenue > 0 else 0,
            "fdv_to_tvl": round(market_cap / tvl, 2) if tvl > 0 else 0,
            "pe_ratio": 0  # P/E 需要净利润数据，暂时设为0
        }

        # 计算赛道中位数
        if competitors:
            ps_ratios = []
            fdv_to_revenues = []
            fdv_to_tvls = []

            for comp in competitors:
                comp_market_cap = comp.get("market_cap", 0)
                comp_tvl = comp.get("tvl", 0)
                comp_revenue = comp.get("protocol_revenue_30d", 0) * 12

                if comp_revenue > 0:
                    ps_ratios.append(comp_market_cap / comp_revenue)
                    fdv_to_revenues.append(comp_market_cap / comp_revenue)

                if comp_tvl > 0:
                    fdv_to_tvls.append(comp_market_cap / comp_tvl)

            sector_median = {
                "ps_ratio": round(self._median(ps_ratios), 2) if ps_ratios else 0,
                "fdv_to_revenue": round(self._median(fdv_to_revenues), 2) if fdv_to_revenues else 0,
                "fdv_to_tvl": round(self._median(fdv_to_tvls), 2) if fdv_to_tvls else 0,
                "pe_ratio": 0
            }
        else:
            sector_median = {
                "ps_ratio": 0,
                "fdv_to_revenue": 0,
                "fdv_to_tvl": 0,
                "pe_ratio": 0
            }

        # 估值评估
        if sector_median["fdv_to_revenue"] > 0:
            ratio = target_multiples["fdv_to_revenue"] / sector_median["fdv_to_revenue"]
            if ratio < 0.7:
                assessment = "被低估"
                rationale = f"估值倍数为赛道中位数的{ratio:.1%}，显著被低估"
            elif ratio > 1.3:
                assessment = "被高估"
                rationale = f"估值倍数为赛道中位数的{ratio:.1%}，存在高估风险"
            else:
                assessment = "合理估值"
                rationale = f"估值倍数为赛道中位数的{ratio:.1%}，估值合理"
        else:
            assessment = "数据不足"
            rationale = "缺乏足够的赛道数据进行估值比较"

        return {
            "target_project": target_multiples,
            "sector_median": sector_median,
            "valuation_assessment": assessment,
            "rationale": rationale
        }

    def _median(self, values: List[float]) -> float:
        """计算中位数"""
        if not values:
            return 0
        sorted_values = sorted(values)
        n = len(sorted_values)
        if n % 2 == 0:
            return (sorted_values[n//2 - 1] + sorted_values[n//2]) / 2
        else:
            return sorted_values[n//2]

    def _format_prompt(self, aggregated_data: Dict) -> str:
        """
        格式化 prompt

        Args:
            aggregated_data: 聚合数据

        Returns:
            格式化的 prompt
        """
        # 提取目标项目数据
        symbol = aggregated_data.get("symbol", "Unknown")
        market_data = aggregated_data.get("market_data", {})
        onchain_data = aggregated_data.get("onchain_data", {})
        social_data = aggregated_data.get("social_data", {})

        name = market_data.get("name", symbol)
        category = market_data.get("category", "Unknown")
        market_cap = market_data.get("market_cap", 0)
        tvl = onchain_data.get("tvl", 0)
        active_users_24h = onchain_data.get("active_addresses_24h", 0)
        volume_24h = market_data.get("volume_24h", 0)
        protocol_revenue_30d = onchain_data.get("protocol_revenue_30d", 0)

        # 提取并格式化竞品数据
        competitors = self._extract_competitor_data(aggregated_data)
        competitors_data = self._format_competitors_data(competitors)

        # 填充模板
        prompt = self.user_prompt_template.format(
            symbol=symbol,
            name=name,
            category=category,
            market_cap=market_cap,
            tvl=tvl,
            active_users_24h=active_users_24h,
            volume_24h=volume_24h,
            protocol_revenue_30d=protocol_revenue_30d,
            competitors_data=competitors_data
        )

        return prompt

    async def analyze(self, aggregated_data: Dict) -> AnalyzerOutput:
        """
        执行竞品对比分析

        Args:
            aggregated_data: 聚合数据

        Returns:
            AnalyzerOutput: 包含竞品分析数据、元数据和可视化提示
        """
        start_time = time.time()
        symbol = aggregated_data.get("symbol", "Unknown")

        try:
            # 格式化 prompt
            user_prompt = self._format_prompt(aggregated_data)

            # 调用 LLM（返回 result, model_used, fallback_used 三元组）
            result, model_used, fallback_used = await self._call_llm(user_prompt)

            if result is None:
                return self._create_error_response("LLM 调用失败", model_used)

            # 验证输出
            is_valid, errors = self._validate_output(result)

            validation_warnings = []
            if not is_valid:
                # 尝试修复
                validation_warnings.append(f"输出验证失败: {', '.join(errors)}")
                result = self._fix_invalid_output(result, errors)

            # 计算生成时间
            generation_time_ms = int((time.time() - start_time) * 1000)

            # 创建竞品对比表格可视化提示
            visualization_hints = []
            if "comparison_table" in result and result["comparison_table"]:
                # 提取表格数据
                competitors_data = result["comparison_table"].get("data", [])
                metrics = result["comparison_table"].get("metrics", [])
                if competitors_data and metrics:
                    visualization_hints.append(
                        create_competitor_table_hint(competitors_data, metrics)
                    )

            # 包装为AnalyzerOutput
            return create_analyzer_output(
                data=result,
                analyzer_name="CompetitorAnalyzer",
                model_used=model_used,
                fallback_used=fallback_used,
                generation_time_ms=generation_time_ms,
                confidence=result.get("market_position", {}).get("confidence_score"),
                data_sources=["CoinGecko", "DeFi Llama"],
                visualization_hints=visualization_hints,
                validation_passed=len(validation_warnings) == 0,
                validation_warnings=validation_warnings,
            )

        except Exception as e:
            return self._create_error_response(f"分析过程出错: {str(e)}", self.model_config.get("primary_model", "unknown"))

    async def _call_llm(self, user_prompt: str) -> Tuple[Optional[Dict], str, bool]:
        """
        调用 LLM

        Args:
            user_prompt: 用户 prompt

        Returns:
            三元组: (LLM响应字典, 使用的模型, 是否使用fallback)
        """
        model_used = self.model_config["primary_model"]
        fallback_used = False

        try:
            # 主模型
            response = await self.llm_client.chat_completion(
                model=model_used,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.model_config["temperature"],
                max_tokens=self.model_config["max_tokens"]
            )

            if response and "choices" in response:
                content = response["choices"][0]["message"]["content"]
                # 提取 JSON
                json_start = content.find("{")
                json_end = content.rfind("}") + 1
                if json_start != -1 and json_end > json_start:
                    json_str = content[json_start:json_end]
                    return json.loads(json_str), model_used, fallback_used

        except Exception as e:
            print(f"Primary model failed: {e}")

        # Fallback 模型
        model_used = self.model_config["fallback_model"]
        fallback_used = True

        try:
            response = await self.llm_client.chat_completion(
                model=model_used,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.model_config["temperature"],
                max_tokens=self.model_config["max_tokens"]
            )

            if response and "choices" in response:
                content = response["choices"][0]["message"]["content"]
                json_start = content.find("{")
                json_end = content.rfind("}") + 1
                if json_start != -1 and json_end > json_start:
                    json_str = content[json_start:json_end]
                    return json.loads(json_str), model_used, fallback_used

        except Exception as e:
            print(f"Fallback model failed: {e}")

        return None, model_used, fallback_used

    def _validate_output(self, output: Dict) -> Tuple[bool, List[str]]:
        """
        验证输出

        Args:
            output: LLM 输出

        Returns:
            (是否有效, 错误列表)
        """
        errors = []

        # 检查必需字段
        required_fields = self.validation_rules["required_fields"]
        for field in required_fields:
            if field not in output:
                errors.append(f"Missing required field: {field}")

        # 验证 competitive_landscape
        if "competitive_landscape" in output:
            landscape = output["competitive_landscape"]
            valid_sectors = ["DEX", "借贷协议", "Layer1", "Layer2", "NFT市场", "衍生品交易所", "跨链桥", "稳定币", "其他"]
            if landscape.get("sector") not in valid_sectors:
                errors.append(f"Invalid sector: {landscape.get('sector')}")

        # 验证 competitors
        if "competitors" in output:
            competitors = output["competitors"]
            if not isinstance(competitors, list):
                errors.append("competitors must be a list")
            elif len(competitors) < 2 or len(competitors) > 5:
                errors.append(f"competitors must have 2-5 items, got {len(competitors)}")

        # 验证 valuation_multiples
        if "valuation_multiples" in output:
            vm = output["valuation_multiples"]
            if "valuation_assessment" in vm:
                valid_assessments = ["被低估", "合理估值", "被高估", "数据不足"]
                if vm["valuation_assessment"] not in valid_assessments:
                    errors.append(f"Invalid valuation_assessment: {vm['valuation_assessment']}")

        # 验证 competitive_advantages
        if "competitive_advantages" in output:
            ca = output["competitive_advantages"]
            if "moat_score" in ca:
                score = ca["moat_score"]
                if not isinstance(score, (int, float)) or score < 0 or score > 10:
                    errors.append(f"moat_score must be 0-10, got {score}")

        # 验证 market_position
        if "market_position" in output:
            mp = output["market_position"]
            valid_positions = ["领导者", "挑战者", "跟随者", "创新者"]
            if mp.get("position_type") not in valid_positions:
                errors.append(f"Invalid position_type: {mp.get('position_type')}")

        return (len(errors) == 0, errors)

    def _fix_invalid_output(self, output: Dict, errors: List[str]) -> Dict:
        """
        修复无效输出

        Args:
            output: 无效输出
            errors: 错误列表

        Returns:
            修复后的输出
        """
        # 补充缺失字段
        if "competitive_landscape" not in output:
            output["competitive_landscape"] = {
                "sector": "其他",
                "market_size": "数据不足",
                "growth_trend": "数据不足",
                "key_trends": [],
                "competition_intensity": "中等"
            }

        if "competitors" not in output:
            output["competitors"] = []

        if "comparison_table" not in output:
            output["comparison_table"] = {
                "metrics": [],
                "target_project": {},
                "competitors": []
            }

        if "valuation_multiples" not in output:
            output["valuation_multiples"] = {
                "target_project": {},
                "sector_median": {},
                "valuation_assessment": "数据不足",
                "rationale": "缺乏足够数据进行估值分析"
            }

        if "competitive_advantages" not in output:
            output["competitive_advantages"] = {
                "strengths": [],
                "moat_score": 5,
                "moat_types": []
            }

        if "competitive_risks" not in output:
            output["competitive_risks"] = {
                "threats": [],
                "risk_level": "中"
            }

        if "market_position" not in output:
            output["market_position"] = {
                "ranking": "数据不足",
                "position_type": "跟随者",
                "market_share_trend": "数据不足",
                "strategic_recommendation": "谨慎观望"
            }

        if "summary" not in output:
            output["summary"] = "竞品分析数据不足，无法给出明确结论"

        # 修复 moat_score
        if "competitive_advantages" in output:
            ca = output["competitive_advantages"]
            if "moat_score" in ca:
                score = ca["moat_score"]
                if not isinstance(score, (int, float)):
                    ca["moat_score"] = 5
                elif score < 0:
                    ca["moat_score"] = 0
                elif score > 10:
                    ca["moat_score"] = 10

        return output

    def _create_error_response(self, error_message: str, model_used: str) -> AnalyzerOutput:
        """
        创建错误响应

        Args:
            error_message: 错误消息
            model_used: 尝试使用的模型

        Returns:
            AnalyzerOutput: 错误响应
        """
        return create_error_output(
            analyzer_name="CompetitorAnalyzer",
            error_msg=f"竞品分析失败: {error_message}",
            model_used=model_used,
        )


# 创建全局单例
competitor_analyzer = CompetitorAnalyzer()
