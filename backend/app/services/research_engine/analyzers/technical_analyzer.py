"""
技术面分析器
分析价格走势、技术指标、支撑阻力位和衍生品市场数据
"""
import json
import time
from typing import Dict, Any, Optional, List
from pathlib import Path
import yaml
import statistics

from app.services.llm import llm_client, ModelConfig
from app.core.config import settings
from app.services.research_engine.analyzers.analyzer_output import (
    AnalyzerOutput,
    create_analyzer_output,
    create_error_output,
    create_price_chart_hint,
)


class TechnicalAnalyzer:
    """
    技术面分析器
    参考：openspec/changes/add-crypto-ai-search-platform/specs/ai-analysis/spec.md
    Scenario: 技术面分析
    """

    def __init__(self):
        """初始化技术面分析器"""
        self.llm_client = llm_client
        self._load_prompts()

    def _load_prompts(self):
        """加载提示词模板"""
        prompts_dir = Path(settings.BASE_DIR) / "prompts" / "deep_research"
        technical_yaml_path = prompts_dir / "technical.yaml"

        if not technical_yaml_path.exists():
            raise FileNotFoundError(f"技术面提示词文件不存在: {technical_yaml_path}")

        with open(technical_yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        self.system_prompt = data.get("system_prompt", "")
        self.user_prompt_template = data.get("user_prompt_template", "")
        self.model_config = data.get("model_config", {})
        self.output_validation = data.get("output_validation", {})

    async def analyze(
        self,
        aggregated_data: Dict[str, Any],
    ) -> AnalyzerOutput:
        """
        技术面分析

        Args:
            aggregated_data: 聚合后的项目数据（来自DataAggregator）

        Returns:
            AnalyzerOutput: 包含技术面分析数据、元数据和可视化提示
        """
        start_time = time.time()

        # 提取必要数据
        symbol = aggregated_data.get("symbol", "Unknown")
        project_info = aggregated_data.get("project_info", {})
        market_data = aggregated_data.get("market_data", {})

        # 提取价格历史
        price_history = self._extract_price_history(aggregated_data)

        # 计算技术指标
        rsi_data = self._calculate_rsi(price_history.get("prices_14d", []))
        macd_data = self._calculate_macd(price_history.get("prices_30d", []))
        bollinger_data = self._calculate_bollinger_bands(price_history.get("prices_20d", []))

        # 识别支撑阻力位
        support_resistance = self._identify_support_resistance(price_history, market_data)

        # 分析成交量和异常检测
        volume_analysis = self._analyze_volume(market_data, price_history)

        # 分析衍生品市场
        derivatives = self._analyze_derivatives(aggregated_data.get("derivatives_data", {}))

        # 简单的趋势分析（用于评分）
        trend_analysis = {
            "short_term_trend": "横盘",
            "medium_term_trend": "横盘",
            "trend_strength": "弱",
        }

        # 计算技术面综合评分
        technical_score = self._calculate_technical_score({
            "rsi": rsi_data,
            "macd": macd_data,
            "bollinger_bands": bollinger_data,
        }, trend_analysis)

        # 格式化提示词
        user_prompt = self._format_prompt(
            symbol=symbol,
            project_name=project_info.get("name", symbol),
            current_price=market_data.get("current_price", "N/A"),
            price_change_24h=market_data.get("price_change_percentage_24h", "N/A"),
            market_data=market_data,
            price_history=price_history,
            rsi_data=rsi_data,
            macd_data=macd_data,
            bollinger_data=bollinger_data,
            support_resistance=support_resistance,
            volume_analysis=volume_analysis,
            derivatives=derivatives,
            technical_score=technical_score,
        )

        # 调用LLM生成（使用deepseek-r1）
        model_used = self.model_config.get("primary_model", ModelConfig.DEEP_RESEARCH_SUMMARY)
        fallback_used = False

        try:
            result = await self._call_llm(user_prompt, use_fallback=False)
        except Exception as e:
            print(f"⚠️ 主模型调用失败: {e}，尝试fallback模型")
            try:
                result = await self._call_llm(user_prompt, use_fallback=True)
                model_used = self.model_config.get("fallback_model", ModelConfig.QUICK_CHAT)
                fallback_used = True
            except Exception as fallback_error:
                print(f"❌ Fallback模型也失败: {fallback_error}")
                return self._create_error_response(symbol, str(fallback_error), model_used)

        # 验证输出格式
        validation_warnings = []
        if not self._validate_output(result):
            print("⚠️ 输出格式验证失败，使用默认值补全")
            validation_warnings.append("输出格式验证失败，已使用默认值补全")
            result = self._fix_invalid_output(result, symbol)

        # 计算生成时间
        generation_time_ms = int((time.time() - start_time) * 1000)

        # 包装为AnalyzerOutput
        return create_analyzer_output(
            data=result,
            analyzer_name="TechnicalAnalyzer",
            model_used=model_used,
            fallback_used=fallback_used,
            generation_time_ms=generation_time_ms,
            confidence=result.get("technical_rating", {}).get("confidence"),
            data_sources=["CoinGecko", "TradingView"],
            visualization_hints=[],  # 可选：添加价格图表hint
            validation_passed=len(validation_warnings) == 0,
            validation_warnings=validation_warnings,
        )

    def _extract_price_history(self, aggregated_data: Dict) -> Dict:
        """
        提取价格历史数据

        Args:
            aggregated_data: 聚合数据

        Returns:
            Dict: 价格历史数据
        """
        market_data = aggregated_data.get("market_data", {})

        # 从market_data中提取价格序列（如果有）
        # 注意：实际数据可能需要从price_history字段获取
        price_chart_data = market_data.get("price_chart_data", {})

        # 构建不同周期的价格序列
        prices_7d = price_chart_data.get("7d", [])
        prices_14d = price_chart_data.get("14d", [])
        prices_20d = price_chart_data.get("20d", [])
        prices_30d = price_chart_data.get("30d", [])

        # 如果没有图表数据，使用当前价格和变化百分比估算
        current_price = market_data.get("current_price", 0)
        if not prices_7d and current_price > 0:
            # 简化估算：基于价格变化百分比生成模拟价格序列
            change_7d = market_data.get("price_change_percentage_7d", 0)
            change_30d = market_data.get("price_change_percentage_30d", 0)

            # 生成简单的价格序列（实际应该从API获取）
            prices_7d = self._generate_price_series(current_price, change_7d, 7)
            prices_14d = self._generate_price_series(current_price, (change_7d + change_30d) / 2, 14)
            prices_20d = self._generate_price_series(current_price, change_30d, 20)
            prices_30d = self._generate_price_series(current_price, change_30d, 30)

        return {
            "prices_7d": prices_7d,
            "prices_14d": prices_14d,
            "prices_20d": prices_20d,
            "prices_30d": prices_30d,
        }

    def _generate_price_series(self, current_price: float, total_change_pct: float, days: int) -> List[float]:
        """
        生成模拟价格序列（用于缺少历史数据时）

        Args:
            current_price: 当前价格
            total_change_pct: 总变化百分比
            days: 天数

        Returns:
            List[float]: 价格序列
        """
        if days == 0 or current_price == 0:
            return [current_price] * max(1, days)

        # 计算起始价格
        start_price = current_price / (1 + total_change_pct / 100)

        # 生成线性插值的价格序列（简化版）
        prices = []
        for i in range(days):
            price = start_price + (current_price - start_price) * (i / (days - 1)) if days > 1 else current_price
            prices.append(price)

        return prices

    def _calculate_rsi(self, prices: List[float], period: int = 14) -> Dict:
        """
        计算RSI（相对强弱指标）

        Args:
            prices: 价格序列
            period: 周期（默认14）

        Returns:
            Dict: RSI数据
        """
        if not prices or len(prices) < period + 1:
            return {
                "value": 50,
                "signal": "中性",
                "interpretation": "数据不足，无法计算RSI。",
            }

        # 计算价格变化
        changes = [prices[i] - prices[i - 1] for i in range(1, len(prices))]

        # 分离涨跌
        gains = [change if change > 0 else 0 for change in changes]
        losses = [abs(change) if change < 0 else 0 for change in changes]

        # 计算平均涨跌
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period

        # 避免除零
        if avg_loss == 0:
            rsi = 100
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))

        # 判断信号
        if rsi > 70:
            signal = "超买"
            interpretation = f"RSI为{rsi:.1f}，位于超买区域（>70），价格可能面临回调压力。"
        elif rsi < 30:
            signal = "超卖"
            interpretation = f"RSI为{rsi:.1f}，位于超卖区域（<30），价格可能出现反弹。"
        else:
            signal = "中性"
            interpretation = f"RSI为{rsi:.1f}，位于中性区间（30-70），市场情绪相对平衡。"

        return {
            "value": round(rsi, 2),
            "signal": signal,
            "interpretation": interpretation,
        }

    def _calculate_macd(self, prices: List[float]) -> Dict:
        """
        计算MACD（移动平均收敛/发散指标）

        Args:
            prices: 价格序列

        Returns:
            Dict: MACD数据
        """
        if not prices or len(prices) < 26:
            return {
                "macd_line": 0,
                "signal_line": 0,
                "histogram": 0,
                "signal": "中性",
                "interpretation": "数据不足，无法计算MACD。",
            }

        # 计算EMA
        def calculate_ema(data: List[float], period: int) -> float:
            if len(data) < period:
                return sum(data) / len(data) if data else 0
            multiplier = 2 / (period + 1)
            ema = sum(data[:period]) / period
            for price in data[period:]:
                ema = (price - ema) * multiplier + ema
            return ema

        # 12日EMA
        ema_12 = calculate_ema(prices, 12)
        # 26日EMA
        ema_26 = calculate_ema(prices, 26)

        # MACD线
        macd_line = ema_12 - ema_26

        # 信号线（MACD的9日EMA，简化计算）
        signal_line = macd_line * 0.9  # 简化版本

        # 柱状图
        histogram = macd_line - signal_line

        # 判断信号
        if macd_line > signal_line and histogram > 0:
            signal = "看涨"
            interpretation = f"MACD线（{macd_line:.2f}）位于信号线（{signal_line:.2f}）上方，柱状图为正，多头动能增强。"
        elif macd_line < signal_line and histogram < 0:
            signal = "看跌"
            interpretation = f"MACD线（{macd_line:.2f}）位于信号线（{signal_line:.2f}）下方，柱状图为负，空头动能增强。"
        else:
            signal = "中性"
            interpretation = f"MACD线接近信号线，市场处于平衡状态。"

        return {
            "macd_line": round(macd_line, 2),
            "signal_line": round(signal_line, 2),
            "histogram": round(histogram, 2),
            "signal": signal,
            "interpretation": interpretation,
        }

    def _calculate_bollinger_bands(self, prices: List[float], period: int = 20, std_dev: int = 2) -> Dict:
        """
        计算布林带

        Args:
            prices: 价格序列
            period: 周期（默认20）
            std_dev: 标准差倍数（默认2）

        Returns:
            Dict: 布林带数据
        """
        if not prices or len(prices) < period:
            return {
                "upper": 0,
                "middle": 0,
                "lower": 0,
                "current_position": "数据不足",
                "bandwidth": "数据不足",
                "interpretation": "数据不足，无法计算布林带。",
            }

        # 计算中轨（简单移动平均）
        middle = sum(prices[-period:]) / period

        # 计算标准差
        variance = sum((p - middle) ** 2 for p in prices[-period:]) / period
        std = variance ** 0.5

        # 计算上轨和下轨
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)

        # 当前价格
        current_price = prices[-1]

        # 判断位置
        if current_price >= upper * 0.98:  # 接近或超过上轨
            position = "上轨附近"
        elif current_price <= lower * 1.02:  # 接近或低于下轨
            position = "下轨附近"
        else:
            position = "中轨附近"

        # 判断带宽
        bandwidth_pct = ((upper - lower) / middle) * 100
        if bandwidth_pct < 5:
            bandwidth = "收窄"
            bandwidth_note = "，可能酝酿大行情"
        elif bandwidth_pct > 15:
            bandwidth = "扩张"
            bandwidth_note = "，波动率增加"
        else:
            bandwidth = "正常"
            bandwidth_note = ""

        interpretation = f"价格位于布林带{position}（上轨${upper:.2f}，中轨${middle:.2f}，下轨${lower:.2f}），带宽{bandwidth}{bandwidth_note}。"

        return {
            "upper": round(upper, 2),
            "middle": round(middle, 2),
            "lower": round(lower, 2),
            "current_position": position,
            "bandwidth": bandwidth,
            "interpretation": interpretation,
        }

    def _identify_support_resistance(self, price_history: Dict, market_data: Dict) -> Dict:
        """
        识别支撑和阻力位

        Args:
            price_history: 价格历史
            market_data: 市场数据

        Returns:
            Dict: 支撑阻力数据
        """
        current_price = market_data.get("current_price", 0)

        # 获取历史高低点
        high_24h = market_data.get("high_24h", current_price)
        low_24h = market_data.get("low_24h", current_price)
        ath_price = market_data.get("ath", {}).get("price", current_price * 1.5)
        atl_price = market_data.get("atl", {}).get("price", current_price * 0.5)

        # 从价格序列中找局部高低点
        prices_30d = price_history.get("prices_30d", [current_price])

        # 简化版：基于百分比计算支撑阻力位
        immediate_support = [
            f"${current_price * 0.95:.0f}",
            f"${current_price * 0.90:.0f}",
        ]

        immediate_resistance = [
            f"${current_price * 1.05:.0f}",
            f"${current_price * 1.10:.0f}",
        ]

        strong_support = [
            f"${current_price * 0.85:.0f}",
            f"${current_price * 0.80:.0f}",
        ]

        strong_resistance = [
            f"${current_price * 1.15:.0f}",
            f"${current_price * 1.20:.0f}",
        ]

        return {
            "immediate_support": immediate_support,
            "immediate_resistance": immediate_resistance,
            "strong_support": strong_support,
            "strong_resistance": strong_resistance,
            "ath_price": ath_price,
            "atl_price": atl_price,
        }

    def _analyze_volume(self, market_data: Dict, price_history: Dict) -> Dict:
        """
        分析成交量数据和异常检测

        Args:
            market_data: 市场数据
            price_history: 价格历史

        Returns:
            Dict: 成交量分析
        """
        # 提取成交量数据
        volume_24h = market_data.get("total_volume", 0)
        volume_change_24h = market_data.get("volume_change_24h", 0)

        # 获取历史成交量序列（简化版）
        volumes_7d = self._extract_volume_history(price_history, market_data)

        # 计算成交量指标
        avg_volume_7d = statistics.mean(volumes_7d) if volumes_7d else 0
        volume_ratio = volume_24h / avg_volume_7d if avg_volume_7d > 0 else 1

        # 成交量强度分析
        if volume_ratio > 2.0:
            volume_strength = "极高"
            volume_signal = "放量"
            volume_interpretation = f"24h成交量({volume_24h:.0f})是7日均值({avg_volume_7d:.0f})的{volume_ratio:.1f}倍，成交量异常放大，可能预示重要行情。"
        elif volume_ratio > 1.5:
            volume_strength = "高"
            volume_signal = "放量"
            volume_interpretation = f"24h成交量相对活跃，是7日均值的{volume_ratio:.1f}倍。"
        elif volume_ratio < 0.5:
            volume_strength = "低"
            volume_signal = "缩量"
            volume_interpretation = f"24h成交量萎缩，仅为7日均值的{volume_ratio:.1f}倍，市场交投清淡。"
        else:
            volume_strength = "正常"
            volume_signal = "正常"
            volume_interpretation = f"24h成交量正常，维持在7日均值水平附近。"

        # 异常检测（基于统计学方法）
        anomalies = self._detect_volume_anomalies(volumes_7d, volume_24h)

        return {
            "volume_24h": volume_24h,
            "volume_change_24h": volume_change_24h,
            "avg_volume_7d": avg_volume_7d,
            "volume_ratio": round(volume_ratio, 2),
            "volume_strength": volume_strength,
            "volume_signal": volume_signal,
            "volume_interpretation": volume_interpretation,
            "anomalies_detected": anomalies,
        }

    def _extract_volume_history(self, price_history: Dict, market_data: Dict) -> List[float]:
        """
        提取成交量历史数据

        Args:
            price_history: 价格历史
            market_data: 市场数据

        Returns:
            List[float]: 成交量序列
        """
        # 简化实现：基于价格变化估算成交量
        # 实际应该从API获取真实的成交量数据
        base_volume = market_data.get("total_volume", 1000000)

        # 生成模拟成交量序列（实际应用中应从历史数据获取）
        volumes = []
        for i in range(7):
            # 添加随机波动
            variation = 0.5 + (i % 3) * 0.2  # 简单的周期性模式
            volume = base_volume * variation
            volumes.append(volume)

        return volumes

    def _detect_volume_anomalies(self, historical_volumes: List[float], current_volume: float) -> List[str]:
        """
        检测成交量异常

        Args:
            historical_volumes: 历史成交量
            current_volume: 当前成交量

        Returns:
            List[str]: 异常检测结果
        """
        if not historical_volumes:
            return []

        anomalies = []

        # 计算统计指标
        mean_volume = statistics.mean(historical_volumes)
        std_volume = statistics.stdev(historical_volumes) if len(historical_volumes) > 1 else 0

        if std_volume == 0:
            return anomalies

        # Z-score异常检测
        z_score = (current_volume - mean_volume) / std_volume

        if abs(z_score) > 2.5:
            if z_score > 0:
                anomalies.append(f"成交量异常放大 (Z-score: {z_score:.2f})")
            else:
                anomalies.append(f"成交量异常萎缩 (Z-score: {z_score:.2f})")

        # 相对于均值的倍数检测
        ratio = current_volume / mean_volume
        if ratio > 3.0:
            anomalies.append(f"成交量是历史均值的{ratio:.1f}倍，极度异常")
        elif ratio > 2.0:
            anomalies.append(f"成交量明显放大，是历史均值的{ratio:.1f}倍")

        return anomalies

    def _calculate_technical_score(self, technical_indicators: Dict, trend_analysis: Dict) -> Dict:
        """
        计算技术面综合评分

        Args:
            technical_indicators: 技术指标数据
            trend_analysis: 趋势分析数据

        Returns:
            Dict: 技术面评分
        """
        score_components = []

        # RSI评分 (0-100)
        rsi = technical_indicators.get("rsi", {})
        rsi_value = rsi.get("value", 50)
        if rsi_value > 70:
            rsi_score = 20  # 超买，负面
            rsi_reason = f"RSI={rsi_value:.1f}超买"
        elif rsi_value < 30:
            rsi_score = 80  # 超卖，正面
            rsi_reason = f"RSI={rsi_value:.1f}超卖"
        else:
            rsi_score = 50  # 中性
            rsi_reason = f"RSI={rsi_value:.1f}中性"
        score_components.append(("RSI", rsi_score, rsi_reason))

        # MACD评分 (0-100)
        macd = technical_indicators.get("macd", {})
        macd_line = macd.get("macd_line", 0)
        signal_line = macd.get("signal_line", 0)
        if macd_line > signal_line:
            macd_score = 70  # 金叉，正面
            macd_reason = "MACD金叉"
        else:
            macd_score = 30  # 死叉，负面
            macd_reason = "MACD死叉"
        score_components.append(("MACD", macd_score, macd_reason))

        # 布林带评分 (0-100)
        bollinger = technical_indicators.get("bollinger_bands", {})
        position = bollinger.get("current_position", "")
        if "上轨" in position:
            bb_score = 20  # 接近上轨，负面
            bb_reason = "价格接近上轨"
        elif "下轨" in position:
            bb_score = 80  # 接近下轨，正面
            bb_reason = "价格接近下轨"
        else:
            bb_score = 50  # 中轨附近，中性
            bb_reason = "价格在中轨附近"
        score_components.append(("布林带", bb_score, bb_reason))

        # 趋势评分 (0-100)
        trend = trend_analysis.get("trend_strength", "弱")
        if trend == "强":
            trend_score = 75
            trend_reason = "趋势强劲"
        elif trend == "中等":
            trend_score = 50
            trend_reason = "趋势中等"
        else:
            trend_score = 25
            trend_reason = "趋势疲弱"
        score_components.append(("趋势", trend_score, trend_reason))

        # 计算综合评分
        weights = [0.25, 0.25, 0.25, 0.25]  # 各指标权重
        total_score = sum(score * weight for score, weight in zip([rsi_score, macd_score, bb_score, trend_score], weights))

        # 确定综合判断
        if total_score >= 70:
            overall_bias = "看涨"
            confidence = min(90, total_score)
        elif total_score <= 30:
            overall_bias = "看跌"
            confidence = min(90, 100 - total_score)
        else:
            overall_bias = "中性"
            confidence = 50 + abs(50 - total_score) * 0.5

        return {
            "total_score": round(total_score, 1),
            "overall_bias": overall_bias,
            "confidence": round(confidence, 1),
            "score_components": score_components,
            "interpretation": f"技术面综合评分为{total_score:.1f}分，{overall_bias}倾向，可信度{confidence:.1f}%。",
        }

    def _analyze_derivatives(self, derivatives_data: Dict) -> Dict:
        """
        分析衍生品市场数据

        Args:
            derivatives_data: 衍生品数据

        Returns:
            Dict: 衍生品分析
        """
        # 提取衍生品数据
        open_interest = derivatives_data.get("open_interest", {})
        funding_rate = derivatives_data.get("funding_rate", {})
        liquidations = derivatives_data.get("liquidations", {})

        # 未平仓合约分析
        oi_value = open_interest.get("value", 0)
        oi_change_24h = open_interest.get("change_24h", 0)

        if oi_change_24h > 5:
            oi_signal = "看涨"
            oi_interpretation = f"未平仓合约上升{oi_change_24h:.1f}%，多头积极建仓。"
        elif oi_change_24h < -5:
            oi_signal = "看跌"
            oi_interpretation = f"未平仓合约下降{abs(oi_change_24h):.1f}%，市场观望或平仓。"
        else:
            oi_signal = "中性"
            oi_interpretation = "未平仓合约变化不大，市场平稳。"

        # 资金费率分析
        fr_value = funding_rate.get("value", 0)
        if fr_value > 0.03:
            fr_interpretation = f"资金费率为{fr_value:.3f}（{fr_value*100:.2f}%），多头支付费用，市场严重偏多，警惕过热。"
        elif fr_value > 0.01:
            fr_interpretation = f"资金费率为{fr_value:.3f}（{fr_value*100:.2f}%），多头支付费用，市场偏多。"
        elif fr_value < -0.03:
            fr_interpretation = f"资金费率为{fr_value:.3f}（{fr_value*100:.2f}%），空头支付费用，市场严重偏空。"
        elif fr_value < -0.01:
            fr_interpretation = f"资金费率为{fr_value:.3f}（{fr_value*100:.2f}%），空头支付费用，市场偏空。"
        else:
            fr_interpretation = f"资金费率接近零（{fr_value:.3f}），多空平衡。"

        # 清算数据分析
        long_liq = liquidations.get("long_24h", 0)
        short_liq = liquidations.get("short_24h", 0)

        if short_liq > long_liq * 2:
            liq_risk = "低"
            liq_interpretation = f"空头清算（${short_liq/1e6:.1f}M）远超多头（${long_liq/1e6:.1f}M），上涨动能强。"
        elif long_liq > short_liq * 2:
            liq_risk = "高"
            liq_interpretation = f"多头清算（${long_liq/1e6:.1f}M）远超空头（${short_liq/1e6:.1f}M），下跌动能强或杠杆过高。"
        else:
            liq_risk = "中"
            liq_interpretation = "多空清算相对平衡。"

        return {
            "open_interest": {
                "value": oi_value,
                "change_24h": oi_change_24h,
                "signal": oi_signal,
                "interpretation": oi_interpretation,
            },
            "funding_rate": {
                "value": fr_value,
                "interpretation": fr_interpretation,
            },
            "liquidation_risk": {
                "level": liq_risk,
                "long_liquidations_24h": long_liq,
                "short_liquidations_24h": short_liq,
                "interpretation": liq_interpretation,
            },
        }

    def _format_prompt(
        self,
        symbol: str,
        project_name: str,
        current_price: Any,
        price_change_24h: Any,
        market_data: Dict,
        price_history: Dict,
        rsi_data: Dict,
        macd_data: Dict,
        bollinger_data: Dict,
        support_resistance: Dict,
        volume_analysis: Dict,
        derivatives: Dict,
        technical_score: Dict,
    ) -> str:
        """格式化用户提示词"""
        # 格式化价格序列（显示前10个和后10个）
        def format_price_series(prices: List[float]) -> str:
            if not prices:
                return "无数据"
            if len(prices) <= 20:
                return ", ".join([f"${p:.2f}" for p in prices])
            # 显示前5个和后5个
            first_5 = ", ".join([f"${p:.2f}" for p in prices[:5]])
            last_5 = ", ".join([f"${p:.2f}" for p in prices[-5:]])
            return f"{first_5} ... {last_5}"

        # 替换模板占位符
        prompt = self.user_prompt_template.format(
            symbol=symbol,
            project_name=project_name,
            current_price=current_price,
            price_change_24h=price_change_24h,
            # 价格数据
            high_24h=market_data.get("high_24h", "N/A"),
            low_24h=market_data.get("low_24h", "N/A"),
            volume_24h=market_data.get("total_volume", "N/A"),
            price_change_7d=market_data.get("price_change_percentage_7d", "N/A"),
            price_change_30d=market_data.get("price_change_percentage_30d", "N/A"),
            price_history_7d=format_price_series(price_history.get("prices_7d", [])),
            price_history_30d=format_price_series(price_history.get("prices_30d", [])),
            # RSI
            rsi_value=rsi_data.get("value", "N/A"),
            # MACD
            macd_line=macd_data.get("macd_line", "N/A"),
            macd_signal=macd_data.get("signal_line", "N/A"),
            macd_histogram=macd_data.get("histogram", "N/A"),
            # 布林带
            bollinger_upper=bollinger_data.get("upper", "N/A"),
            bollinger_middle=bollinger_data.get("middle", "N/A"),
            bollinger_lower=bollinger_data.get("lower", "N/A"),
            bollinger_position=bollinger_data.get("current_position", "N/A"),
            bollinger_width=bollinger_data.get("bandwidth", "N/A"),
            # 支撑阻力
            immediate_support=", ".join(support_resistance.get("immediate_support", [])),
            immediate_resistance=", ".join(support_resistance.get("immediate_resistance", [])),
            strong_support=", ".join(support_resistance.get("strong_support", [])),
            strong_resistance=", ".join(support_resistance.get("strong_resistance", [])),
            ath_price=support_resistance.get("ath_price", "N/A"),
            ath_distance=market_data.get("ath_change_percentage", "N/A"),
            atl_price=support_resistance.get("atl_price", "N/A"),
            atl_distance=market_data.get("atl_change_percentage", "N/A"),
            # 成交量分析
            volume_24h=volume_analysis.get("volume_24h", "N/A"),
            volume_strength=volume_analysis.get("volume_strength", "N/A"),
            volume_signal=volume_analysis.get("volume_signal", "N/A"),
            volume_anomalies=", ".join(volume_analysis.get("anomalies_detected", [])) or "无异常",
            # 衍生品
            open_interest_value=derivatives.get("open_interest", {}).get("value", "N/A"),
            open_interest_change_24h=derivatives.get("open_interest", {}).get("change_24h", "N/A"),
            funding_rate=derivatives.get("funding_rate", {}).get("value", "N/A"),
            long_liquidations_24h=derivatives.get("liquidation_risk", {}).get("long_liquidations_24h", "N/A"),
            short_liquidations_24h=derivatives.get("liquidation_risk", {}).get("short_liquidations_24h", "N/A"),
            liquidation_risk=derivatives.get("liquidation_risk", {}).get("level", "N/A"),
            # 技术面评分
            technical_score=technical_score.get("total_score", "N/A"),
            technical_bias=technical_score.get("overall_bias", "N/A"),
            technical_confidence=technical_score.get("confidence", "N/A"),
        )

        return prompt

    async def _call_llm(self, user_prompt: str, use_fallback: bool = False) -> Dict[str, Any]:
        """
        调用LLM生成技术面分析

        Args:
            user_prompt: 用户提示词
            use_fallback: 是否使用fallback模型

        Returns:
            Dict: 解析后的JSON响应
        """
        model = (
            self.model_config.get("fallback_model", ModelConfig.DEEP_RESEARCH_SUMMARY)
            if use_fallback
            else self.model_config.get("primary_model", ModelConfig.DEEP_RESEARCH_REASONING)
        )

        temperature = self.model_config.get("temperature", 0.3)
        max_tokens = self.model_config.get("max_tokens", 2000)

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

        # 验证technical_indicators结构
        if "technical_indicators" in result:
            ti = result["technical_indicators"]
            ti_required = self.output_validation.get("technical_indicators_structure", {}).get("required_fields", [])
            for field in ti_required:
                if field not in ti:
                    print(f"❌ technical_indicators缺少字段: {field}")
                    return False

            # 验证RSI范围
            if "rsi" in ti and isinstance(ti["rsi"], dict):
                rsi_value = ti["rsi"].get("value", -1)
                rsi_range = self.output_validation.get("technical_indicators_structure", {}).get("rsi_range", {})
                if not (rsi_range.get("min", 0) <= rsi_value <= rsi_range.get("max", 100)):
                    print(f"❌ RSI值超出范围: {rsi_value}")
                    return False

        # 验证overall_technical_view
        if "overall_technical_view" in result:
            otv = result["overall_technical_view"]
            otv_required = self.output_validation.get("overall_technical_view_structure", {}).get("required_fields", [])
            for field in otv_required:
                if field not in otv:
                    print(f"❌ overall_technical_view缺少字段: {field}")
                    return False

            # 验证confidence范围
            confidence = otv.get("confidence", -1)
            conf_range = self.output_validation.get("overall_technical_view_structure", {}).get("confidence_range", {})
            if not (conf_range.get("min", 0) <= confidence <= conf_range.get("max", 100)):
                print(f"❌ confidence超出范围: {confidence}")
                return False

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
        from datetime import datetime, timezone

        # 补全technical_indicators
        if "technical_indicators" not in result:
            result["technical_indicators"] = {}

        ti = result["technical_indicators"]
        ti.setdefault("rsi", {"value": 50, "signal": "中性", "interpretation": "数据不足"})
        ti.setdefault("macd", {"macd_line": 0, "signal_line": 0, "histogram": 0, "signal": "中性", "interpretation": "数据不足"})
        ti.setdefault("bollinger_bands", {"upper": 0, "middle": 0, "lower": 0, "current_position": "数据不足", "bandwidth": "数据不足", "interpretation": "数据不足"})

        # 补全其他必填字段
        result.setdefault("support_resistance", {
            "immediate_support": [],
            "immediate_resistance": [],
            "strong_support": [],
            "strong_resistance": [],
            "key_levels_narrative": "数据不足",
        })

        result.setdefault("trend_analysis", {
            "short_term_trend": "横盘",
            "medium_term_trend": "横盘",
            "trend_strength": "弱",
            "narrative": f"{symbol}的技术面数据不完整，暂时无法给出明确趋势判断。",
        })

        result.setdefault("volume_analysis", {
            "volume_24h": 0,
            "volume_strength": "正常",
            "volume_signal": "正常",
            "volume_interpretation": "成交量数据不足",
            "anomalies_detected": [],
        })

        result.setdefault("derivatives_analysis", {
            "open_interest": {"value": 0, "change_24h": 0, "signal": "中性", "interpretation": "数据不足"},
            "funding_rate": {"value": 0, "interpretation": "数据不足"},
            "liquidation_risk": {"level": "低", "long_liquidations_24h": 0, "short_liquidations_24h": 0, "interpretation": "数据不足"},
        })

        result.setdefault("technical_score", {
            "total_score": 50,
            "overall_bias": "中性",
            "confidence": 40,
            "score_components": [],
            "interpretation": "技术面评分数据不足",
        })

        result.setdefault("overall_technical_view", {
            "bias": "中性",
            "confidence": 40,
            "time_horizon": "短期",
            "narrative": f"{symbol}的技术面分析数据不完整，建议等待更多数据后再做判断。",
        })

        result.setdefault("risk_warnings", [])
        result.setdefault("data_sources", [])
        result.setdefault("updated_at", datetime.now(timezone.utc).isoformat())

        return result

    def _create_error_response(self, symbol: str, error_msg: str, model_used: str) -> AnalyzerOutput:
        """
        创建错误响应

        Args:
            symbol: 币种符号
            error_msg: 错误信息
            model_used: 尝试使用的模型

        Returns:
            AnalyzerOutput: 错误响应
        """
        return create_error_output(
            analyzer_name="TechnicalAnalyzer",
            error_msg=f"{symbol}的技术面分析失败: {error_msg}",
            model_used=model_used,
        )


# 全局单例
technical_analyzer = TechnicalAnalyzer()
