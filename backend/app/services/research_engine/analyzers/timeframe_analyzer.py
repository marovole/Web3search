"""
时间窗分析器
分析项目在24小时、7天、30天三个时间窗口的表现
"""
import json
from typing import Dict, Any, Optional, List
from pathlib import Path
import yaml

from app.services.llm import llm_client, ModelConfig
from app.core.config import settings


class TimeframeAnalyzer:
    """
    时间窗分析器
    参考：openspec/changes/add-crypto-ai-search-platform/specs/ai-analysis/spec.md
    Scenario: 时间窗分析多维度输出
    """

    def __init__(self):
        """初始化时间窗分析器"""
        self.llm_client = llm_client
        self._load_prompts()

    def _load_prompts(self):
        """加载提示词模板"""
        prompts_dir = Path(settings.BASE_DIR) / "prompts" / "deep_research"
        timeframe_yaml_path = prompts_dir / "timeframe.yaml"

        if not timeframe_yaml_path.exists():
            raise FileNotFoundError(f"时间窗提示词文件不存在: {timeframe_yaml_path}")

        with open(timeframe_yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        self.system_prompt = data.get("system_prompt", "")
        self.user_prompt_template = data.get("user_prompt_template", "")
        self.model_config = data.get("model_config", {})
        self.output_validation = data.get("output_validation", {})

    async def analyze(
        self,
        aggregated_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        分析时间窗数据

        Args:
            aggregated_data: 聚合后的项目数据（来自DataAggregator）

        Returns:
            Dict: 时间窗分析数据，格式：
            {
                "timeframe_24h": {
                    "price_change": "+2.5%",
                    "volume_change": "+15.2%",
                    "key_events": [...],
                    "narrative": "...",
                    "trend": "上涨 | 下跌 | 横盘"
                },
                "timeframe_7d": {...},
                "timeframe_30d": {...},
                "cross_timeframe_analysis": {...},
                "data_sources": [...],
                "updated_at": "2025-10-25T14:30:00Z"
            }
        """
        # 提取必要数据
        symbol = aggregated_data.get("symbol", "Unknown")

        # 提取三个时间窗的数据
        data_24h = self._extract_24h_data(aggregated_data)
        data_7d = self._extract_7d_data(aggregated_data)
        data_30d = self._extract_30d_data(aggregated_data)

        # 格式化提示词
        user_prompt = self._format_prompt(
            symbol=symbol,
            data_24h=data_24h,
            data_7d=data_7d,
            data_30d=data_30d,
            project_info=aggregated_data.get("project_info", {}),
            market_data=aggregated_data.get("market_data", {}),
        )

        # 调用LLM生成
        try:
            # 使用qwen3-235b主模型
            result = await self._call_llm(user_prompt, use_fallback=False)
        except Exception as e:
            print(f"⚠️ 主模型调用失败: {e}，尝试fallback模型")
            try:
                # Fallback到qwen3-30b
                result = await self._call_llm(user_prompt, use_fallback=True)
            except Exception as fallback_error:
                # 如果两个模型都失败，返回默认响应
                print(f"❌ Fallback模型也失败: {fallback_error}")
                return self._create_error_response(symbol, str(fallback_error))

        # 验证输出格式
        if not self._validate_output(result):
            print("⚠️ 输出格式验证失败，使用默认值补全")
            result = self._fix_invalid_output(result, symbol)

        return result

    def _extract_24h_data(self, aggregated_data: Dict) -> Dict:
        """
        提取24小时窗口数据

        Args:
            aggregated_data: 聚合数据

        Returns:
            Dict: 24小时数据
        """
        market_data = aggregated_data.get("market_data", {})
        social_data = aggregated_data.get("social_data", {})
        onchain_data = aggregated_data.get("onchain_data", {})

        return {
            "price_change_24h": market_data.get("price_change_percentage_24h", "N/A"),
            "current_price": market_data.get("current_price", "N/A"),
            "volume_24h": market_data.get("total_volume", "N/A"),
            "volume_change_24h": market_data.get("volume_change_percentage_24h", "N/A"),
            "tx_count_24h": onchain_data.get("transactions_24h", "N/A"),
            "active_addresses_24h": onchain_data.get("active_addresses", "N/A"),
            "events_24h": social_data.get("recent_events_24h", []),
        }

    def _extract_7d_data(self, aggregated_data: Dict) -> Dict:
        """
        提取7天窗口数据

        Args:
            aggregated_data: 聚合数据

        Returns:
            Dict: 7天数据
        """
        market_data = aggregated_data.get("market_data", {})
        social_data = aggregated_data.get("social_data", {})

        return {
            "price_change_7d": market_data.get("price_change_percentage_7d", "N/A"),
            "high_7d": market_data.get("high_24h", "N/A"),  # 使用24h最高价作为近似
            "low_7d": market_data.get("low_24h", "N/A"),  # 使用24h最低价作为近似
            "avg_volume_7d": market_data.get("total_volume", "N/A"),
            "twitter_mentions_7d": social_data.get("twitter", {}).get("mentions_7d", "N/A"),
            "reddit_posts_7d": social_data.get("reddit", {}).get("posts_7d", "N/A"),
            "social_sentiment_7d": social_data.get("overall_sentiment", "N/A"),
            "events_7d": social_data.get("recent_events_7d", []),
        }

    def _extract_30d_data(self, aggregated_data: Dict) -> Dict:
        """
        提取30天窗口数据

        Args:
            aggregated_data: 聚合数据

        Returns:
            Dict: 30天数据
        """
        market_data = aggregated_data.get("market_data", {})
        onchain_data = aggregated_data.get("onchain_data", {})

        # 计算距离ATH/ATL的距离
        current_price = market_data.get("current_price", 0)
        ath_price = market_data.get("ath", {}).get("price", current_price)
        atl_price = market_data.get("atl", {}).get("price", current_price)

        ath_distance = "N/A"
        atl_distance = "N/A"
        if ath_price and current_price:
            ath_distance = f"{((current_price - ath_price) / ath_price * 100):.2f}"
        if atl_price and current_price:
            atl_distance = f"{((current_price - atl_price) / atl_price * 100):.2f}"

        return {
            "price_change_30d": market_data.get("price_change_percentage_30d", "N/A"),
            "ath_distance": ath_distance,
            "atl_distance": atl_distance,
            "market_cap_change_30d": market_data.get("market_cap_change_percentage_30d", "N/A"),
            "tvl_change_30d": onchain_data.get("tvl_change_30d", "N/A"),
            "user_growth_30d": onchain_data.get("user_growth_30d", "N/A"),
            "revenue_change_30d": onchain_data.get("revenue_change_30d", "N/A"),
            "events_30d": aggregated_data.get("social_data", {}).get("recent_events_30d", []),
        }

    def _format_prompt(
        self,
        symbol: str,
        data_24h: Dict,
        data_7d: Dict,
        data_30d: Dict,
        project_info: Dict,
        market_data: Dict,
    ) -> str:
        """格式化用户提示词"""
        # 安全提取基本信息
        project_name = project_info.get("name", symbol)
        current_price = market_data.get("current_price", "N/A")
        market_rank = market_data.get("market_cap_rank", "N/A")

        # 格式化事件列表
        def format_events(events: List) -> str:
            if not events or events == "N/A":
                return "暂无重要事件记录"
            if isinstance(events, list):
                return "\n".join([f"- {event}" for event in events[:5]])  # 最多5个事件
            return str(events)

        events_24h = format_events(data_24h.get("events_24h", []))
        events_7d = format_events(data_7d.get("events_7d", []))
        events_30d = format_events(data_30d.get("events_30d", []))

        # 替换模板占位符
        prompt = self.user_prompt_template.format(
            symbol=symbol,
            project_name=project_name,
            current_price=current_price,
            market_rank=market_rank,
            # 24h数据
            price_change_24h=data_24h.get("price_change_24h", "N/A"),
            volume_24h=data_24h.get("volume_24h", "N/A"),
            volume_change_24h=data_24h.get("volume_change_24h", "N/A"),
            tx_count_24h=data_24h.get("tx_count_24h", "N/A"),
            active_addresses_24h=data_24h.get("active_addresses_24h", "N/A"),
            events_24h=events_24h,
            # 7d数据
            price_change_7d=data_7d.get("price_change_7d", "N/A"),
            high_7d=data_7d.get("high_7d", "N/A"),
            low_7d=data_7d.get("low_7d", "N/A"),
            avg_volume_7d=data_7d.get("avg_volume_7d", "N/A"),
            twitter_mentions_7d=data_7d.get("twitter_mentions_7d", "N/A"),
            reddit_posts_7d=data_7d.get("reddit_posts_7d", "N/A"),
            social_sentiment_7d=data_7d.get("social_sentiment_7d", "N/A"),
            events_7d=events_7d,
            # 30d数据
            price_change_30d=data_30d.get("price_change_30d", "N/A"),
            ath_distance=data_30d.get("ath_distance", "N/A"),
            atl_distance=data_30d.get("atl_distance", "N/A"),
            market_cap_change_30d=data_30d.get("market_cap_change_30d", "N/A"),
            tvl_change_30d=data_30d.get("tvl_change_30d", "N/A"),
            user_growth_30d=data_30d.get("user_growth_30d", "N/A"),
            revenue_change_30d=data_30d.get("revenue_change_30d", "N/A"),
            events_30d=events_30d,
        )

        return prompt

    async def _call_llm(self, user_prompt: str, use_fallback: bool = False) -> Dict[str, Any]:
        """
        调用LLM生成时间窗分析

        Args:
            user_prompt: 用户提示词
            use_fallback: 是否使用fallback模型

        Returns:
            Dict: 解析后的JSON响应
        """
        model = (
            self.model_config.get("fallback_model", ModelConfig.QUICK_CHAT)
            if use_fallback
            else self.model_config.get("primary_model", ModelConfig.DEEP_RESEARCH_SUMMARY)
        )

        temperature = self.model_config.get("temperature", 0.4)
        max_tokens = self.model_config.get("max_tokens", 1500)

        # 调用LLM
        response = await self.llm_client.chat_completion(
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        content = response.get("content", "")

        # 尝试解析JSON
        try:
            # 移除可能的markdown代码块标记
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            result = json.loads(content)
            return result
        except json.JSONDecodeError as e:
            print(f"❌ JSON解析失败: {e}\n原始内容:\n{content}")
            raise ValueError(f"LLM返回了无效的JSON: {str(e)}")

    def _validate_output(self, result: Dict[str, Any]) -> bool:
        """
        验证输出格式

        Args:
            result: LLM生成的结果

        Returns:
            bool: 是否符合格式要求
        """
        required_fields = self.output_validation.get("required_fields", [])

        # 检查必填字段
        for field in required_fields:
            if field not in result:
                print(f"❌ 缺少必填字段: {field}")
                return False

        # 验证每个时间窗的必填字段
        timeframe_required = self.output_validation.get("timeframe_structure", {}).get("required_fields", [])
        for timeframe in ["timeframe_24h", "timeframe_7d", "timeframe_30d"]:
            if timeframe not in result:
                continue

            timeframe_data = result[timeframe]
            for field in timeframe_required:
                if field not in timeframe_data:
                    print(f"❌ {timeframe}缺少必填字段: {field}")
                    return False

            # 验证trend值
            trend = timeframe_data.get("trend", "")
            valid_trends = self.output_validation.get("trend_values", [])
            if trend not in valid_trends:
                print(f"⚠️ {timeframe}的trend值无效: {trend}")
                # 不算严重错误，只警告

            # 验证key_events数量
            key_events = timeframe_data.get("key_events", [])
            max_events = self.output_validation.get("key_events", {}).get("max_count", 3)
            if len(key_events) > max_events:
                print(f"⚠️ {timeframe}的key_events超过限制: {len(key_events)} > {max_events}")

            # 验证narrative长度
            narrative = timeframe_data.get("narrative", "")
            min_len = self.output_validation.get("narrative", {}).get("min_length", 50)
            max_len = self.output_validation.get("narrative", {}).get("max_length", 150)
            if not (min_len <= len(narrative) <= max_len):
                print(f"⚠️ {timeframe}的narrative长度不符合要求: {len(narrative)}字")

        # 验证cross_timeframe_analysis
        if "cross_timeframe_analysis" in result:
            cross_fields = self.output_validation.get("cross_timeframe_fields", [])
            for field in cross_fields:
                if field not in result["cross_timeframe_analysis"]:
                    print(f"⚠️ cross_timeframe_analysis缺少字段: {field}")

        return True

    def _fix_invalid_output(self, result: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        """
        修复无效输出（补全缺失字段）

        Args:
            result: 原始结果
            symbol: 币种符号

        Returns:
            Dict: 修复后的结果
        """
        # 默认时间窗结构
        default_timeframe = {
            "price_change": "N/A",
            "key_events": [],
            "narrative": f"{symbol}在该时间窗口的数据不完整，暂时无法给出详细分析。",
            "trend": "横盘",
        }

        # 修复三个时间窗
        for timeframe in ["timeframe_24h", "timeframe_7d", "timeframe_30d"]:
            if timeframe not in result:
                result[timeframe] = default_timeframe.copy()
            else:
                # 补全缺失字段
                for key, value in default_timeframe.items():
                    if key not in result[timeframe]:
                        result[timeframe][key] = value

        # 修复cross_timeframe_analysis
        if "cross_timeframe_analysis" not in result:
            result["cross_timeframe_analysis"] = {
                "consistency": "低",
                "momentum": "稳定",
                "risk_signal": "数据不足",
                "summary": f"{symbol}的跨时间窗分析数据不完整，需要更多信息。",
            }

        # 补全data_sources和updated_at
        if "data_sources" not in result:
            result["data_sources"] = ["CoinGecko"]

        if "updated_at" not in result:
            from datetime import datetime, timezone
            result["updated_at"] = datetime.now(timezone.utc).isoformat()

        return result

    def _create_error_response(self, symbol: str, error_msg: str) -> Dict[str, Any]:
        """
        创建错误响应

        Args:
            symbol: 币种符号
            error_msg: 错误信息

        Returns:
            Dict: 错误响应数据
        """
        from datetime import datetime, timezone

        default_timeframe = {
            "price_change": "N/A",
            "key_events": [],
            "narrative": f"{symbol}的时间窗分析生成失败，可能是数据源问题或AI服务暂时不可用。",
            "trend": "横盘",
        }

        return {
            "timeframe_24h": default_timeframe.copy(),
            "timeframe_7d": default_timeframe.copy(),
            "timeframe_30d": default_timeframe.copy(),
            "cross_timeframe_analysis": {
                "consistency": "低",
                "momentum": "无法判断",
                "risk_signal": "数据不足",
                "summary": f"{symbol}的时间窗分析失败: {error_msg}",
            },
            "data_sources": [],
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "error": error_msg,
        }


# 全局单例
timeframe_analyzer = TimeframeAnalyzer()
