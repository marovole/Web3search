"""
研究分析相关的数据模型
定义Deep Research引擎10个分析器的输出Schema
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime


# ================================
# 1. TL;DR Generator Schema
# ================================

class TLDRSchema(BaseModel):
    """TL;DR生成器输出"""
    one_sentence: str = Field(..., description="一句话总结")
    bull_case: List[str] = Field(..., description="看涨理由（3-5条）")
    bear_case: List[str] = Field(..., description="看跌理由（3-5条）")
    key_catalysts: List[str] = Field(..., description="关键催化剂（2-3个）")
    risk_level: str = Field(..., description="风险等级（低/中/高）")
    investment_horizon: str = Field(..., description="建议投资期限")
    summary: str = Field(..., description="综合摘要（2-3句）")
    error: bool = Field(False, description="是否有错误")
    message: Optional[str] = Field(None, description="错误信息")

    class Config:
        json_schema_extra = {
            "example": {
                "one_sentence": "Uniswap是去中心化交易所（DEX）赛道龙头，近期催化剂密集，基本面强劲",
                "bull_case": [
                    "DEX赛道龙头，市场份额50%+，护城河深厚",
                    "协议收入高速增长（+30% MoM），费用开关投票即将激活",
                    "V4版本即将上线，引入Hooks机制提升竞争力"
                ],
                "bear_case": [
                    "监管风险未消除，SEC可能将UNI定义为证券",
                    "Layer2原生DEX崛起，分流高频交易用户",
                    "代币价值捕获不足，当前无分红机制"
                ],
                "key_catalysts": [
                    "费用开关投票（预计Q1 2024）",
                    "V4版本上线（预计Q2 2024）"
                ],
                "risk_level": "中",
                "investment_horizon": "中长期（3-6月）",
                "summary": "Uniswap基本面强劲，但监管风险和代币价值捕获问题需关注。建议等待催化剂明确后再配置。",
                "error": False
            }
        }


# ================================
# 2. Timeframe Analyzer Schema
# ================================

class TimeframeMetrics(BaseModel):
    """时间窗指标"""
    price_change_pct: Optional[float] = Field(None, description="价格变化（%）")
    volume_change_pct: Optional[float] = Field(None, description="成交量变化（%）")
    market_cap_change_pct: Optional[float] = Field(None, description="市值变化（%）")
    holder_change_pct: Optional[float] = Field(None, description="持币地址变化（%）")
    sentiment_score: Optional[float] = Field(None, description="情绪得分（0-100）")


class TimeframeAnalysis(BaseModel):
    """单个时间窗分析"""
    timeframe: str = Field(..., description="时间窗（7天/30天/90天）")
    trend: str = Field(..., description="趋势（强烈上涨/上涨/横盘/下跌/强烈下跌）")
    metrics: TimeframeMetrics = Field(..., description="关键指标")
    key_events: List[str] = Field(..., description="关键事件")
    narrative: str = Field(..., description="叙述分析")


class TimeframeSchema(BaseModel):
    """时间窗分析器输出"""
    windows: List[TimeframeAnalysis] = Field(..., description="3个时间窗分析（7天/30天/90天）")
    overall_momentum: str = Field(..., description="整体动量（加速上涨/稳步上涨/横盘整理/稳步下跌/加速下跌）")
    regime_shift: bool = Field(..., description="是否发生趋势转折")
    regime_shift_description: Optional[str] = Field(None, description="趋势转折描述")
    summary: str = Field(..., description="综合分析")
    error: bool = Field(False, description="是否有错误")
    message: Optional[str] = Field(None, description="错误信息")

    class Config:
        json_schema_extra = {
            "example": {
                "windows": [
                    {
                        "timeframe": "7天",
                        "trend": "上涨",
                        "metrics": {
                            "price_change_pct": 8.5,
                            "volume_change_pct": 12.3,
                            "market_cap_change_pct": 8.2,
                            "holder_change_pct": 1.2,
                            "sentiment_score": 72
                        },
                        "key_events": ["费用开关投票通过", "V4测试网上线"],
                        "narrative": "过去一周UNI价格上涨8.5%，主要由费用开关投票通过驱动"
                    }
                ],
                "overall_momentum": "稳步上涨",
                "regime_shift": True,
                "regime_shift_description": "从横盘整理转为上涨趋势",
                "summary": "UNI近期呈现加速上涨态势，主要由费用开关和V4催化剂驱动",
                "error": False
            }
        }


# ================================
# 3. Sentiment Analyzer Schema
# ================================

class SocialMetrics(BaseModel):
    """社交媒体指标"""
    platform: str = Field(..., description="平台（Twitter/Reddit）")
    mention_count: int = Field(..., description="提及次数")
    sentiment_score: float = Field(..., description="情绪得分（-1到1）")
    engagement_rate: float = Field(..., description="互动率（%）")
    top_topics: List[str] = Field(..., description="热门话题（前3）")


class SentimentSchema(BaseModel):
    """情绪分析器输出"""
    overall_sentiment: str = Field(..., description="整体情绪（极度看涨/看涨/中性/看跌/极度看跌）")
    sentiment_score: float = Field(..., description="情绪得分（0-100）")
    social_metrics: List[SocialMetrics] = Field(..., description="社交媒体指标")
    sentiment_drivers: List[str] = Field(..., description="情绪驱动因素（3-5条）")
    sentiment_shift: str = Field(..., description="情绪变化（改善/稳定/恶化）")
    fomo_index: int = Field(..., description="FOMO指数（0-100）")
    fear_index: int = Field(..., description="恐慌指数（0-100）")
    summary: str = Field(..., description="综合分析")
    error: bool = Field(False, description="是否有错误")
    message: Optional[str] = Field(None, description="错误信息")

    class Config:
        json_schema_extra = {
            "example": {
                "overall_sentiment": "看涨",
                "sentiment_score": 72,
                "social_metrics": [
                    {
                        "platform": "Twitter",
                        "mention_count": 3456,
                        "sentiment_score": 0.65,
                        "engagement_rate": 4.2,
                        "top_topics": ["费用开关", "V4上线", "DeFi"]
                    }
                ],
                "sentiment_drivers": [
                    "费用开关投票通过，社区情绪高涨",
                    "V4测试网上线，技术进展获认可",
                    "DeFi Summer叙事回归，DEX板块受关注"
                ],
                "sentiment_shift": "改善",
                "fomo_index": 68,
                "fear_index": 25,
                "summary": "UNI社区情绪积极，主要由费用开关和V4催化剂驱动",
                "error": False
            }
        }


# ================================
# 4. Technical Analyzer Schema
# ================================

class PriceMetrics(BaseModel):
    """价格指标"""
    current_price: float = Field(..., description="当前价格")
    price_change_24h_pct: Optional[float] = Field(None, description="24小时涨跌（%）")
    high_24h: Optional[float] = Field(None, description="24小时最高")
    low_24h: Optional[float] = Field(None, description="24小时最低")
    all_time_high: Optional[float] = Field(None, description="历史最高")
    ath_distance_pct: Optional[float] = Field(None, description="距ATH（%）")


class TechnicalIndicators(BaseModel):
    """技术指标"""
    rsi: Optional[float] = Field(None, description="RSI指标（0-100）")
    macd_signal: Optional[str] = Field(None, description="MACD信号（买入/卖出/中性）")
    moving_averages: Optional[Dict[str, str]] = Field(None, description="均线状态")
    support_levels: Optional[List[float]] = Field(None, description="支撑位")
    resistance_levels: Optional[List[float]] = Field(None, description="阻力位")


class TechnicalSchema(BaseModel):
    """技术面分析器输出"""
    price_metrics: PriceMetrics = Field(..., description="价格指标")
    technical_indicators: TechnicalIndicators = Field(..., description="技术指标")
    trend_analysis: str = Field(..., description="趋势分析")
    key_levels: Dict[str, List[float]] = Field(..., description="关键价位（支撑/阻力）")
    trading_signals: List[str] = Field(..., description="交易信号（3-5条）")
    technical_outlook: str = Field(..., description="技术面展望（看涨/中性/看跌）")
    summary: str = Field(..., description="综合分析")
    error: bool = Field(False, description="是否有错误")
    message: Optional[str] = Field(None, description="错误信息")

    class Config:
        json_schema_extra = {
            "example": {
                "price_metrics": {
                    "current_price": 12.34,
                    "price_change_24h_pct": 2.5,
                    "high_24h": 12.56,
                    "low_24h": 11.98,
                    "all_time_high": 44.92,
                    "ath_distance_pct": -72.5
                },
                "technical_indicators": {
                    "rsi": 65,
                    "macd_signal": "买入",
                    "moving_averages": {
                        "ma50": "上穿",
                        "ma200": "下穿"
                    },
                    "support_levels": [11.5, 10.8],
                    "resistance_levels": [13.2, 14.5]
                },
                "trend_analysis": "短期上涨趋势，MA50上穿MA200形成金叉",
                "key_levels": {
                    "support": [11.5, 10.8],
                    "resistance": [13.2, 14.5]
                },
                "trading_signals": [
                    "RSI 65处于强势区间但未超买",
                    "MACD金叉，买入信号",
                    "突破$12.5阻力位，上涨动能强劲"
                ],
                "technical_outlook": "看涨",
                "summary": "UNI技术面强劲，短期上涨趋势明确",
                "error": False
            }
        }


# ================================
# 5. Onchain Analyzer Schema
# ================================

class HolderDistribution(BaseModel):
    """持币分布"""
    total_holders: int = Field(..., description="总持币地址数")
    whale_holders: int = Field(..., description="巨鲸数量（>1%）")
    retail_holders: int = Field(..., description="散户数量（<0.01%）")
    top10_concentration_pct: float = Field(..., description="Top 10持币占比（%）")


class OnchainMetrics(BaseModel):
    """链上指标"""
    active_addresses_24h: Optional[int] = Field(None, description="24h活跃地址")
    transaction_count_24h: Optional[int] = Field(None, description="24h交易数")
    transaction_volume_24h: Optional[float] = Field(None, description="24h交易量（USD）")
    exchange_inflow_24h: Optional[float] = Field(None, description="24h交易所流入")
    exchange_outflow_24h: Optional[float] = Field(None, description="24h交易所流出")


class OnchainSchema(BaseModel):
    """链上分析器输出"""
    holder_distribution: HolderDistribution = Field(..., description="持币分布")
    onchain_metrics: OnchainMetrics = Field(..., description="链上活动指标")
    whale_movements: List[str] = Field(..., description="巨鲸动向（3-5条）")
    exchange_flows: str = Field(..., description="交易所流向分析")
    accumulation_signal: str = Field(..., description="筹码集中度（积累/分发/中性）")
    onchain_health: str = Field(..., description="链上健康度（健康/一般/警惕）")
    summary: str = Field(..., description="综合分析")
    error: bool = Field(False, description="是否有错误")
    message: Optional[str] = Field(None, description="错误信息")

    class Config:
        json_schema_extra = {
            "example": {
                "holder_distribution": {
                    "total_holders": 456789,
                    "whale_holders": 234,
                    "retail_holders": 398765,
                    "top10_concentration_pct": 48.5
                },
                "onchain_metrics": {
                    "active_addresses_24h": 12345,
                    "transaction_count_24h": 23456,
                    "transaction_volume_24h": 234567890,
                    "exchange_inflow_24h": 5678900,
                    "exchange_outflow_24h": 8901234
                },
                "whale_movements": [
                    "过去24h有5个巨鲸地址新增UNI持仓",
                    "交易所净流出350万UNI，显示持有意愿强烈",
                    "Top 10地址持币占比从47%升至48.5%"
                ],
                "exchange_flows": "交易所净流出，显示持币信心增强",
                "accumulation_signal": "积累",
                "onchain_health": "健康",
                "summary": "UNI链上数据健康，巨鲸积累信号明显",
                "error": False
            }
        }


# ================================
# 6. Competitor Analyzer Schema
# ================================

class CompetitorMetrics(BaseModel):
    """竞品指标"""
    name: str = Field(..., description="竞品名称")
    symbol: str = Field(..., description="代币符号")
    market_cap: Optional[float] = Field(None, description="市值（USD）")
    tvl: Optional[float] = Field(None, description="TVL（USD）")
    daily_volume: Optional[float] = Field(None, description="24h交易量（USD）")
    user_count: Optional[int] = Field(None, description="用户数")
    revenue_30d: Optional[float] = Field(None, description="30天收入（USD）")


class ValuationMultiples(BaseModel):
    """估值倍数"""
    ps_ratio: Optional[float] = Field(None, description="P/S比率")
    fdv_revenue: Optional[float] = Field(None, description="FDV/Revenue")
    fdv_tvl: Optional[float] = Field(None, description="FDV/TVL")
    pe_ratio: Optional[float] = Field(None, description="P/E比率")


class CompetitorSchema(BaseModel):
    """竞品分析器输出"""
    competitors: List[CompetitorMetrics] = Field(..., description="竞品列表（3-5个）")
    market_position: str = Field(..., description="市场地位（龙头/前三/中游/后进）")
    market_share_pct: Optional[float] = Field(None, description="市场份额（%）")
    valuation_multiples: ValuationMultiples = Field(..., description="估值倍数")
    sector_median_multiples: ValuationMultiples = Field(..., description="赛道中位数倍数")
    competitive_advantages: List[str] = Field(..., description="竞争优势（3-5条）")
    competitive_threats: List[str] = Field(..., description="竞争威胁（3-5条）")
    valuation_assessment: str = Field(..., description="估值评估（高估/合理/低估）")
    summary: str = Field(..., description="综合分析")
    error: bool = Field(False, description="是否有错误")
    message: Optional[str] = Field(None, description="错误信息")

    class Config:
        json_schema_extra = {
            "example": {
                "competitors": [
                    {
                        "name": "PancakeSwap",
                        "symbol": "CAKE",
                        "market_cap": 500000000,
                        "tvl": 2000000000,
                        "daily_volume": 300000000,
                        "user_count": 1200000,
                        "revenue_30d": 15000000
                    }
                ],
                "market_position": "龙头",
                "market_share_pct": 52.3,
                "valuation_multiples": {
                    "ps_ratio": 8.3,
                    "fdv_revenue": 10.5,
                    "fdv_tvl": 1.2,
                    "pe_ratio": None
                },
                "sector_median_multiples": {
                    "ps_ratio": 12.0,
                    "fdv_revenue": 18.0,
                    "fdv_tvl": 2.5,
                    "pe_ratio": None
                },
                "competitive_advantages": [
                    "品牌认知度最高，先发优势明显",
                    "流动性深度最好，滑点最低",
                    "V3集中流动性技术领先"
                ],
                "competitive_threats": [
                    "Layer2原生DEX技术性能更优",
                    "CAKE等竞品推出激进激励计划",
                    "监管不确定性可能削弱竞争力"
                ],
                "valuation_assessment": "低估",
                "summary": "Uniswap是DEX龙头，估值被低估，竞争优势明显",
                "error": False
            }
        }


# ================================
# 7. Tokenomics Analyzer Schema
# ================================

class SupplyStructure(BaseModel):
    """供应结构"""
    total_supply: float = Field(..., description="总供应量")
    circulating_supply: float = Field(..., description="流通供应量")
    circulating_ratio_pct: float = Field(..., description="流通率（%）")
    allocation: Dict[str, float] = Field(..., description="分配明细（%）")


class UnlockScheduleItem(BaseModel):
    """解锁时间表项"""
    date: str = Field(..., description="解锁日期")
    amount: float = Field(..., description="解锁数量")
    beneficiary: str = Field(..., description="受益方")


class ValueCapture(BaseModel):
    """价值捕获机制"""
    governance: str = Field(..., description="治理权描述")
    staking: Optional[str] = Field(None, description="质押机制")
    buyback_burn: Optional[str] = Field(None, description="回购销毁")
    revenue_share: Optional[str] = Field(None, description="收益分成")


class TokenomicsSchema(BaseModel):
    """代币经济学分析器输出"""
    supply_structure: SupplyStructure = Field(..., description="供应结构")
    unlock_schedule: List[UnlockScheduleItem] = Field(..., description="解锁时间表（未来6-12月）")
    unlock_pressure: str = Field(..., description="解锁抛压（高/中/低）")
    value_capture: ValueCapture = Field(..., description="价值捕获路径")
    tokenomics_rating: str = Field(..., description="代币经济学评级（优秀/良好/一般/差）")
    flywheel_effect: str = Field(..., description="飞轮效应描述")
    summary: str = Field(..., description="综合分析")
    error: bool = Field(False, description="是否有错误")
    message: Optional[str] = Field(None, description="错误信息")

    class Config:
        json_schema_extra = {
            "example": {
                "supply_structure": {
                    "total_supply": 1000000000,
                    "circulating_supply": 600000000,
                    "circulating_ratio_pct": 60.0,
                    "allocation": {
                        "团队": 21.51,
                        "投资人": 17.80,
                        "社区": 60.69
                    }
                },
                "unlock_schedule": [
                    {
                        "date": "2024-03-15",
                        "amount": 5000000,
                        "beneficiary": "团队"
                    }
                ],
                "unlock_pressure": "中",
                "value_capture": {
                    "governance": "持有者可投票决定协议参数",
                    "staking": None,
                    "buyback_burn": None,
                    "revenue_share": "费用开关激活后可分享协议收入"
                },
                "tokenomics_rating": "良好",
                "flywheel_effect": "交易量增加→流动性提升→滑点降低→用户增长→交易量增加",
                "summary": "UNI代币经济学设计合理，费用开关是关键催化剂",
                "error": False
            }
        }


# ================================
# 8. Risk Assessor Schema
# ================================

class CatalystItem(BaseModel):
    """催化剂项"""
    event: str = Field(..., description="事件描述")
    timeframe: str = Field(..., description="时间窗（2-4周/1-2月/3-6月）")
    impact: str = Field(..., description="影响（高/中/低）")
    probability: str = Field(..., description="概率（高/中/低）")
    description: str = Field(..., description="详细描述")
    price_impact: str = Field(..., description="价格影响预估")


class RiskItem(BaseModel):
    """风险项"""
    risk: str = Field(..., description="风险名称")
    severity: str = Field(..., description="严重程度（高/中/低）")
    probability: str = Field(..., description="概率（高/中/低）")
    timeframe: str = Field(..., description="时间窗")
    impact_description: str = Field(..., description="影响描述")
    price_impact: str = Field(..., description="价格影响预估")
    mitigation: str = Field(..., description="缓解措施")


class RiskRewardAnalysis(BaseModel):
    """风险收益分析"""
    upside_potential: str = Field(..., description="上行潜力")
    downside_risk: str = Field(..., description="下行风险")
    risk_reward_ratio: float = Field(..., description="风险收益比")
    asymmetry: str = Field(..., description="不对称性（正向/负向/对称）")


class ScenarioAnalysisItem(BaseModel):
    """情景分析项"""
    scenario: str = Field(..., description="情景（牛市/基准/熊市）")
    probability: int = Field(..., description="概率（%）")
    price_target: str = Field(..., description="价格目标")
    triggers: List[str] = Field(..., description="触发条件")
    narrative: str = Field(..., description="叙述")


class CalendarEvent(BaseModel):
    """日历事件"""
    date: str = Field(..., description="日期")
    event: str = Field(..., description="事件")
    impact: str = Field(..., description="影响（高/中/低）")
    description: str = Field(..., description="描述")


class RiskSchema(BaseModel):
    """风险评估器输出"""
    catalysts: Dict[str, List[CatalystItem]] = Field(..., description="催化剂（短期/中期/长期）")
    risks: Dict[str, List[RiskItem]] = Field(..., description="风险（监管/技术/竞争/市场/代币经济学）")
    risk_reward_analysis: RiskRewardAnalysis = Field(..., description="风险收益分析")
    tail_risks: List[str] = Field(..., description="尾部风险（极端低概率高影响事件）")
    scenario_analysis: List[ScenarioAnalysisItem] = Field(..., description="情景分析（牛市/基准/熊市）")
    overall_risk_rating: str = Field(..., description="整体风险评级（低/中/高）")
    overall_risk_score: int = Field(..., description="整体风险分数（0-10）")
    risk_adjusted_recommendation: str = Field(..., description="风险调整后建议")
    catalyst_calendar: List[CalendarEvent] = Field(..., description="催化剂日历")
    summary: str = Field(..., description="综合分析")
    error: bool = Field(False, description="是否有错误")
    message: Optional[str] = Field(None, description="错误信息")

    class Config:
        json_schema_extra = {
            "example": {
                "catalysts": {
                    "short_term": [
                        {
                            "event": "费用开关投票",
                            "timeframe": "2-4周",
                            "impact": "高",
                            "probability": "高",
                            "description": "社区投票决定是否激活费用开关",
                            "price_impact": "+10-15%"
                        }
                    ],
                    "medium_term": [],
                    "long_term": []
                },
                "risks": {
                    "regulatory": [
                        {
                            "risk": "SEC执法行动",
                            "severity": "高",
                            "probability": "中",
                            "timeframe": "1-3月",
                            "impact_description": "可能被定义为证券",
                            "price_impact": "-30-50%",
                            "mitigation": "团队积极沟通监管机构"
                        }
                    ],
                    "technical": [],
                    "competitive": [],
                    "market": [],
                    "tokenomics": []
                },
                "risk_reward_analysis": {
                    "upside_potential": "+50-80%",
                    "downside_risk": "-30-50%",
                    "risk_reward_ratio": 1.5,
                    "asymmetry": "正向不对称"
                },
                "tail_risks": ["SEC将UNI定义为证券并要求下架"],
                "scenario_analysis": [
                    {
                        "scenario": "牛市",
                        "probability": 40,
                        "price_target": "$25-30",
                        "triggers": ["费用开关激活", "V4成功上线", "DeFi Summer 2.0"],
                        "narrative": "催化剂全部兑现，估值回归合理水平"
                    }
                ],
                "overall_risk_rating": "中",
                "overall_risk_score": 5,
                "risk_adjusted_recommendation": "建议配置10-15%仓位，等待催化剂明确后加仓",
                "catalyst_calendar": [
                    {
                        "date": "2024-02-15",
                        "event": "费用开关投票",
                        "impact": "高",
                        "description": "决定是否激活协议收入分成"
                    }
                ],
                "summary": "UNI风险收益比有吸引力，短期催化剂密集",
                "error": False
            }
        }


# ================================
# 9. Conclusion Synthesizer Schema
# ================================

class ExecutiveSummary(BaseModel):
    """执行摘要"""
    one_sentence_thesis: str = Field(..., description="一句话投资论点")
    bull_thesis: List[str] = Field(..., description="看涨论点（3-5条）")
    bear_thesis: List[str] = Field(..., description="看跌论点（3-5条）")
    key_assumptions: List[str] = Field(..., description="关键假设（2-3条）")
    invalidation_triggers: List[str] = Field(..., description="失效触发器（2-3条）")


class InvestmentOutlookPeriod(BaseModel):
    """投资展望期间"""
    timeframe: str = Field(..., description="时间框架")
    view: str = Field(..., description="观点（强烈看涨/看涨/中性/看跌/强烈看跌）")
    price_target: str = Field(..., description="价格目标")
    key_events: List[str] = Field(..., description="关键事件")
    rationale: str = Field(..., description="理由")


class InvestmentOutlook(BaseModel):
    """投资展望"""
    short_term: InvestmentOutlookPeriod = Field(..., description="短期（1-2周）")
    medium_term: InvestmentOutlookPeriod = Field(..., description="中期（1-2月）")


class KeyMetric(BaseModel):
    """关键指标"""
    metric: str = Field(..., description="指标名称")
    current_value: str = Field(..., description="当前值")
    target: str = Field(..., description="目标值")
    importance: str = Field(..., description="重要性（高/中/低）")
    rationale: str = Field(..., description="理由")


class ConfidenceAssessment(BaseModel):
    """置信度评估"""
    overall_confidence: int = Field(..., description="整体置信度（0-100）", ge=0, le=100)
    confidence_level: str = Field(..., description="置信度等级（高/中/低）")
    data_quality: str = Field(..., description="数据质量（优秀/良好/一般/差）")
    analysis_completeness: str = Field(..., description="分析完整性（完整/大部分完整/部分缺失/严重缺失）")
    uncertainty_factors: List[str] = Field(..., description="不确定性因素")
    confidence_rationale: str = Field(..., description="置信度理由")


class InvestmentRecommendation(BaseModel):
    """投资建议"""
    rating: str = Field(..., description="评级（强烈看涨/看涨/中性/看跌/强烈看跌）")
    action: str = Field(..., description="行动（买入/增持/持有/减持/卖出）")
    position_sizing: str = Field(..., description="仓位建议（%）")
    entry_strategy: str = Field(..., description="进场策略")
    exit_strategy: str = Field(..., description="出场策略")
    risk_management: List[str] = Field(..., description="风险管理措施")
    suitable_for: str = Field(..., description="适合人群")
    not_suitable_for: str = Field(..., description="不适合人群")


class ComparativeAnalysis(BaseModel):
    """对比分析"""
    vs_competitors: str = Field(..., description="vs 竞品")
    vs_sector: str = Field(..., description="vs 赛道")
    vs_market: str = Field(..., description="vs 大盘")


class FinalVerdict(BaseModel):
    """最终结论"""
    verdict: str = Field(..., description="结论（强烈看涨/看涨/中性/看跌/强烈看跌）")
    conviction_level: str = Field(..., description="确信度（高/中/低）")
    time_horizon: str = Field(..., description="时间期限")
    expected_return: str = Field(..., description="预期收益")
    max_drawdown_risk: str = Field(..., description="最大回撤风险")
    risk_reward_ratio: float = Field(..., description="风险收益比", ge=0)
    summary: str = Field(..., description="总结")


class ConclusionSchema(BaseModel):
    """结论综合器输出"""
    executive_summary: ExecutiveSummary = Field(..., description="执行摘要")
    investment_outlook: InvestmentOutlook = Field(..., description="投资展望")
    key_metrics_to_watch: List[KeyMetric] = Field(..., description="关键跟踪指标（5个）")
    confidence_assessment: ConfidenceAssessment = Field(..., description="置信度评估")
    investment_recommendation: InvestmentRecommendation = Field(..., description="投资建议")
    catalyst_calendar: List[CalendarEvent] = Field(..., description="催化剂日历")
    comparative_analysis: ComparativeAnalysis = Field(..., description="对比分析")
    final_verdict: FinalVerdict = Field(..., description="最终结论")
    error: bool = Field(False, description="是否有错误")
    message: Optional[str] = Field(None, description="错误信息")

    class Config:
        json_schema_extra = {
            "example": {
                "executive_summary": {
                    "one_sentence_thesis": "Uniswap是DEX龙头，近期催化剂密集，基本面强劲，估值被低估，建议积极配置",
                    "bull_thesis": [
                        "协议收入高速增长（+30% MoM），年化收入达$540M",
                        "技术领先优势明显（V3集中流动性，V4 Hooks机制）",
                        "估值被低估（P/S 8.3 vs 赛道中位数12）"
                    ],
                    "bear_thesis": [
                        "监管风险未消除，SEC可能将UNI定义为证券",
                        "Layer2原生DEX崛起，技术性能更优"
                    ],
                    "key_assumptions": [
                        "费用开关将在Q1 2024激活",
                        "V4将在Q2 2024成功上线"
                    ],
                    "invalidation_triggers": [
                        "SEC明确将UNI定义为证券",
                        "V4上线延期超过6个月"
                    ]
                },
                "investment_outlook": {
                    "short_term": {
                        "timeframe": "1-2周",
                        "view": "看涨",
                        "price_target": "$13.5-15.0",
                        "key_events": ["费用开关投票"],
                        "rationale": "费用开关投票通过概率高"
                    },
                    "medium_term": {
                        "timeframe": "1-2月",
                        "view": "看涨",
                        "price_target": "$16-20",
                        "key_events": ["V4测试网上线", "费用开关激活"],
                        "rationale": "多个催化剂兑现"
                    }
                },
                "key_metrics_to_watch": [
                    {
                        "metric": "协议收入（月度）",
                        "current_value": "$45M",
                        "target": "$50M+",
                        "importance": "高",
                        "rationale": "反映DEX市场份额和增长趋势"
                    }
                ],
                "confidence_assessment": {
                    "overall_confidence": 75,
                    "confidence_level": "高",
                    "data_quality": "优秀",
                    "analysis_completeness": "完整",
                    "uncertainty_factors": ["监管风险", "V4上线时间"],
                    "confidence_rationale": "数据充分，分析全面，但监管风险需持续关注"
                },
                "investment_recommendation": {
                    "rating": "看涨",
                    "action": "买入",
                    "position_sizing": "10-15%",
                    "entry_strategy": "分批建仓，等待回调至$11.5-12.0区间加仓",
                    "exit_strategy": "设置止盈$18（+50%），止损$10（-20%）",
                    "risk_management": [
                        "仓位不超过15%",
                        "设置止损",
                        "关注监管新闻"
                    ],
                    "suitable_for": "风险偏好中等的中长期投资者",
                    "not_suitable_for": "风险厌恶型投资者、短线交易者"
                },
                "catalyst_calendar": [
                    {
                        "date": "2024-02-15",
                        "event": "费用开关投票",
                        "impact": "高",
                        "description": "决定是否激活协议收入分成"
                    }
                ],
                "comparative_analysis": {
                    "vs_competitors": "优于CAKE、SUSHI等竞品，护城河深厚",
                    "vs_sector": "DEX赛道整体向好，UNI受益最大",
                    "vs_market": "Beta系数1.2，市场上涨时弹性更大"
                },
                "final_verdict": {
                    "verdict": "看涨",
                    "conviction_level": "高",
                    "time_horizon": "1-2月",
                    "expected_return": "+50-80%",
                    "max_drawdown_risk": "-20-30%",
                    "risk_reward_ratio": 2.5,
                    "summary": "Uniswap基本面强劲，催化剂密集，估值被低估，建议积极配置"
                },
                "error": False
            }
        }


# ================================
# 10. Full Report Schema
# ================================

class FullReportSchema(BaseModel):
    """完整研究报告"""
    symbol: str = Field(..., description="代币符号")
    query: str = Field(..., description="用户查询")
    timestamp: datetime = Field(..., description="生成时间")

    # 10个分析器的输出
    tldr: TLDRSchema = Field(..., description="TL;DR生成器输出")
    timeframe: TimeframeSchema = Field(..., description="时间窗分析器输出")
    sentiment: SentimentSchema = Field(..., description="情绪分析器输出")
    technical: TechnicalSchema = Field(..., description="技术面分析器输出")
    onchain: OnchainSchema = Field(..., description="链上分析器输出")
    competitor: CompetitorSchema = Field(..., description="竞品分析器输出")
    tokenomics: TokenomicsSchema = Field(..., description="代币经济学分析器输出")
    risk: RiskSchema = Field(..., description="风险评估器输出")
    conclusion: ConclusionSchema = Field(..., description="结论综合器输出")

    # 元数据
    data_sources: List[str] = Field(..., description="数据来源")
    models_used: Dict[str, str] = Field(..., description="使用的模型")
    generation_time: float = Field(..., description="生成耗时（秒）")
    quality_score: int = Field(..., description="质量得分（0-100）", ge=0, le=100)

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "UNI",
                "query": "请帮我深度分析Uniswap",
                "timestamp": "2025-01-25T10:30:00Z",
                "tldr": {},
                "timeframe": {},
                "sentiment": {},
                "technical": {},
                "onchain": {},
                "competitor": {},
                "tokenomics": {},
                "risk": {},
                "conclusion": {},
                "data_sources": ["CoinGecko", "Etherscan", "Twitter", "Reddit", "CryptoPanic"],
                "models_used": {
                    "tldr": "meta-llama/llama-3.3-70b-instruct:free",
                    "conclusion": "meta-llama/llama-3.3-70b-instruct:free"
                },
                "generation_time": 45.6,
                "quality_score": 85
            }
        }
