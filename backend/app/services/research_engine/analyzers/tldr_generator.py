"""
TL;DR 生成器
生成符合specs要求的TL;DR摘要（核心判断+置信度+总结）
"""
import json
from typing import Dict, Any, Optional
from pathlib import Path
import yaml

from app.services.llm import llm_client, ModelConfig
from app.core.config import settings


class TLDRGenerator:
    """
    TL;DR生成器
    参考：openspec/changes/add-crypto-ai-search-platform/specs/ai-analysis/spec.md
    Scenario: TL;DR生成符合标准格式
    """

    def __init__(self):
        """初始化TL;DR生成器"""
        self.llm_client = llm_client
        self._load_prompts()

    def _load_prompts(self):
        """加载提示词模板"""
        prompts_dir = Path(settings.BASE_DIR) / "prompts" / "deep_research"
        tldr_yaml_path = prompts_dir / "tldr.yaml"

        if not tldr_yaml_path.exists():
            raise FileNotFoundError(f"TL;DR提示词文件不存在: {tldr_yaml_path}")

        with open(tldr_yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        self.system_prompt = data.get("system_prompt", "")
        self.user_prompt_template = data.get("user_prompt_template", "")
        self.model_config = data.get("model_config", {})
        self.output_validation = data.get("output_validation", {})

    async def generate_tldr(
        self,
        query: str,
        aggregated_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        生成TL;DR摘要

        Args:
            query: 用户查询
            aggregated_data: 聚合后的项目数据（来自DataAggregator）

        Returns:
            Dict: TL;DR数据，格式：
            {
                "judgment": "BULL | NEUTRAL | BEAR",
                "judgment_emoji": "🟢 | 🟡 | 🔴",
                "confidence": 85,
                "confidence_level": "高",
                "summary": "一句话总结...",
                "key_metrics": {...},
                "reasoning": "判断理由..."
            }
        """
        # 提取必要数据
        symbol = aggregated_data.get("symbol", "Unknown")
        project_info = aggregated_data.get("project_info", {})
        market_data = aggregated_data.get("market_data", {})
        social_data = aggregated_data.get("social_data", {})
        onchain_data = aggregated_data.get("onchain_data", {})

        # 格式化提示词
        user_prompt = self._format_prompt(
            query=query,
            symbol=symbol,
            project_info=project_info,
            market_data=market_data,
            social_data=social_data,
            onchain_data=onchain_data,
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

    def _format_prompt(
        self,
        query: str,
        symbol: str,
        project_info: Dict,
        market_data: Dict,
        social_data: Dict,
        onchain_data: Dict,
    ) -> str:
        """格式化用户提示词"""
        # 安全提取数据（带默认值）
        current_price = market_data.get("current_price", "N/A")
        market_cap = market_data.get("market_cap", "N/A")
        market_rank = market_data.get("market_cap_rank", "N/A")
        price_change_24h = market_data.get("price_change_percentage_24h", "N/A")
        price_change_7d = market_data.get("price_change_percentage_7d", "N/A")
        price_change_30d = market_data.get("price_change_percentage_30d", "N/A")
        volume_24h = market_data.get("total_volume", "N/A")
        circulating_supply = market_data.get("circulating_supply", "N/A")
        total_supply = market_data.get("total_supply", "N/A")

        project_name = project_info.get("name", symbol)
        categories = ", ".join(project_info.get("categories", [])[:3]) or "N/A"
        description = project_info.get("description", {}).get("en", "N/A")
        if len(description) > 300:
            description = description[:297] + "..."

        twitter_followers = social_data.get("twitter", {}).get("followers", "N/A")
        reddit_subscribers = social_data.get("reddit", {}).get("subscribers", "N/A")
        social_sentiment = social_data.get("overall_sentiment", "N/A")
        discussion_heat = social_data.get("discussion_heat", "N/A")

        active_addresses = onchain_data.get("active_addresses", "N/A")
        holder_count = onchain_data.get("holder_count", "N/A")
        whale_activity = onchain_data.get("whale_activity", "N/A")

        # 替换模板占位符
        prompt = self.user_prompt_template.format(
            query=query,
            symbol=symbol,
            current_price=current_price,
            market_cap=market_cap,
            market_rank=market_rank,
            price_change_24h=price_change_24h,
            price_change_7d=price_change_7d,
            price_change_30d=price_change_30d,
            volume_24h=volume_24h,
            circulating_supply=circulating_supply,
            total_supply=total_supply,
            project_name=project_name,
            categories=categories,
            description=description,
            twitter_followers=twitter_followers,
            reddit_subscribers=reddit_subscribers,
            social_sentiment=social_sentiment,
            discussion_heat=discussion_heat,
            active_addresses=active_addresses,
            holder_count=holder_count,
            whale_activity=whale_activity,
        )

        return prompt

    async def _call_llm(self, user_prompt: str, use_fallback: bool = False) -> Dict[str, Any]:
        """
        调用LLM生成TL;DR

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

        temperature = self.model_config.get("temperature", 0.3)
        max_tokens = self.model_config.get("max_tokens", 800)

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

        # 验证judgment值
        valid_judgments = self.output_validation.get("judgment_values", [])
        if result.get("judgment") not in valid_judgments:
            print(f"❌ judgment值无效: {result.get('judgment')}")
            return False

        # 验证confidence范围
        confidence = result.get("confidence", -1)
        conf_range = self.output_validation.get("confidence_range", {})
        if not (conf_range.get("min", 0) <= confidence <= conf_range.get("max", 100)):
            print(f"❌ confidence超出范围: {confidence}")
            return False

        # 验证summary长度
        summary = result.get("summary", "")
        summary_length = self.output_validation.get("summary_length", {})
        if not (summary_length.get("min", 0) <= len(summary) <= summary_length.get("max", 300)):
            print(f"⚠️ summary长度不符合要求: {len(summary)}字")
            # 长度问题不算严重错误，只警告

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
        # 设置默认值
        fixed = {
            "judgment": result.get("judgment", "NEUTRAL"),
            "judgment_emoji": result.get("judgment_emoji", "🟡"),
            "confidence": result.get("confidence", 50),
            "confidence_level": result.get("confidence_level", "中等"),
            "summary": result.get("summary", f"{symbol}项目的数据不完整，暂时无法给出明确判断。"),
            "key_metrics": result.get("key_metrics", {}),
            "reasoning": result.get("reasoning", "数据不足，需要更多信息。"),
        }

        # 确保judgment和emoji匹配
        judgment_emoji_map = {
            "BULL": "🟢",
            "NEUTRAL": "🟡",
            "BEAR": "🔴",
        }
        fixed["judgment_emoji"] = judgment_emoji_map.get(
            fixed["judgment"], "🟡"
        )

        # 确保confidence在范围内
        fixed["confidence"] = max(0, min(100, fixed["confidence"]))

        return fixed

    def _create_error_response(self, symbol: str, error_msg: str) -> Dict[str, Any]:
        """
        创建错误响应

        Args:
            symbol: 币种符号
            error_msg: 错误信息

        Returns:
            Dict: 错误响应数据
        """
        return {
            "judgment": "NEUTRAL",
            "judgment_emoji": "🟡",
            "confidence": 30,
            "confidence_level": "低",
            "summary": f"{symbol}项目的TL;DR生成失败，可能是数据源问题或AI服务暂时不可用。",
            "key_metrics": {},
            "reasoning": f"生成失败: {error_msg}",
            "error": error_msg,
        }


# 全局单例
tldr_generator = TLDRGenerator()
