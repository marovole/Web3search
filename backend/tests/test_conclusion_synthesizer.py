"""
结论综合器测试
测试 ConclusionSynthesizer 类的所有功能
"""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.research_engine.analyzers.conclusion_synthesizer import (
    ConclusionSynthesizer,
    conclusion_synthesizer
)


class TestConclusionSynthesizerInit:
    """测试初始化"""

    def test_init_loads_prompts(self):
        """测试初始化加载 prompts"""
        synthesizer = ConclusionSynthesizer()

        assert hasattr(synthesizer, 'system_prompt')
        assert hasattr(synthesizer, 'user_prompt_template')
        assert hasattr(synthesizer, 'output_format')
        assert hasattr(synthesizer, 'validation_rules')
        assert hasattr(synthesizer, 'model_config')
        assert hasattr(synthesizer, 'llm_client')

        assert isinstance(synthesizer.system_prompt, str)
        assert isinstance(synthesizer.user_prompt_template, str)
        assert isinstance(synthesizer.output_format, dict)
        assert isinstance(synthesizer.validation_rules, dict)
        assert isinstance(synthesizer.model_config, dict)


class TestConclusionSynthesizerSingleton:
    """测试全局单例"""

    def test_singleton_exists(self):
        """测试全局单例存在"""
        assert conclusion_synthesizer is not None
        assert isinstance(conclusion_synthesizer, ConclusionSynthesizer)


class TestExtractSummary:
    """测试 _extract_summary 方法"""

    def test_extract_summary_with_summary_field(self):
        """测试提取带有 summary 字段的分析结果"""
        synthesizer = ConclusionSynthesizer()

        analysis = {
            "summary": "这是摘要内容",
            "other_field": "其他数据"
        }

        result = synthesizer._extract_summary(analysis, "summary")
        assert result == "这是摘要内容"

    def test_extract_summary_with_error(self):
        """测试提取有错误的分析结果"""
        synthesizer = ConclusionSynthesizer()

        analysis = {
            "error": True,
            "message": "分析失败"
        }

        result = synthesizer._extract_summary(analysis, "summary")
        assert result == "暂无数据"

    def test_extract_summary_with_none(self):
        """测试提取空分析结果"""
        synthesizer = ConclusionSynthesizer()

        result = synthesizer._extract_summary(None, "summary")
        assert result == "暂无数据"

    def test_extract_summary_with_empty_dict(self):
        """测试提取空字典"""
        synthesizer = ConclusionSynthesizer()

        result = synthesizer._extract_summary({}, "summary")
        assert result == "暂无数据"

    def test_extract_summary_with_custom_default(self):
        """测试使用自定义默认值"""
        synthesizer = ConclusionSynthesizer()

        result = synthesizer._extract_summary({}, "summary", "自定义默认值")
        assert result == "自定义默认值"


class TestFormatPrompt:
    """测试 _format_prompt 方法"""

    def test_format_prompt_with_complete_data(self):
        """测试使用完整数据格式化 prompt"""
        synthesizer = ConclusionSynthesizer()

        all_analyses = {
            "symbol": "UNI",
            "tldr": {"summary": "TL;DR摘要"},
            "timeframe": {"summary": "时间窗分析摘要"},
            "sentiment": {"summary": "情绪分析摘要"},
            "technical": {"summary": "技术面分析摘要"},
            "onchain": {"summary": "链上分析摘要"},
            "competitor": {"summary": "竞品分析摘要"},
            "tokenomics": {"summary": "代币经济学摘要"},
            "risk": {"summary": "风险评估摘要"}
        }

        result = synthesizer._format_prompt(all_analyses)

        assert isinstance(result, str)
        assert "UNI" in result
        assert "TL;DR摘要" in result
        assert "时间窗分析摘要" in result
        assert "情绪分析摘要" in result
        assert "技术面分析摘要" in result
        assert "链上分析摘要" in result
        assert "竞品分析摘要" in result
        assert "代币经济学摘要" in result
        assert "风险评估摘要" in result

    def test_format_prompt_with_missing_summaries(self):
        """测试缺少摘要时的格式化"""
        synthesizer = ConclusionSynthesizer()

        all_analyses = {
            "symbol": "BTC",
            "tldr": {"error": True},
            "timeframe": None,
            "sentiment": {}
        }

        result = synthesizer._format_prompt(all_analyses)

        assert isinstance(result, str)
        assert "BTC" in result
        assert "暂无数据" in result

    def test_format_prompt_with_unknown_symbol(self):
        """测试未知代币符号"""
        synthesizer = ConclusionSynthesizer()

        all_analyses = {}

        result = synthesizer._format_prompt(all_analyses)

        assert isinstance(result, str)
        assert "Unknown" in result


class TestValidateOutput:
    """测试 _validate_output 方法"""

    def test_validate_output_valid(self):
        """测试验证有效输出"""
        synthesizer = ConclusionSynthesizer()

        output = {
            "executive_summary": {
                "one_sentence_thesis": "投资论点",
                "bull_thesis": ["看涨理由1"],
                "bear_thesis": ["看跌理由1"],
                "key_assumptions": ["假设1"],
                "invalidation_triggers": ["失效触发器1"]
            },
            "investment_outlook": {
                "short_term": {
                    "timeframe": "1-2周",
                    "view": "看涨",
                    "price_target": "$100",
                    "key_events": [],
                    "rationale": "理由"
                },
                "medium_term": {
                    "timeframe": "1-2月",
                    "view": "中性",
                    "price_target": "$110",
                    "key_events": [],
                    "rationale": "理由"
                }
            },
            "key_metrics_to_watch": [
                {"metric": "指标1", "current_value": "100", "target": "120", "importance": "高", "rationale": "原因"}
                for _ in range(5)
            ],
            "confidence_assessment": {
                "overall_confidence": 75,
                "confidence_level": "高",
                "data_quality": "优秀",
                "analysis_completeness": "完整",
                "uncertainty_factors": [],
                "confidence_rationale": "原因"
            },
            "investment_recommendation": {
                "rating": "看涨",
                "action": "买入",
                "position_sizing": "10%",
                "entry_strategy": "分批建仓",
                "exit_strategy": "设置止盈",
                "risk_management": [],
                "suitable_for": "长期投资者",
                "not_suitable_for": "短线交易者"
            },
            "catalyst_calendar": [],
            "comparative_analysis": {
                "vs_competitors": "优于竞品",
                "vs_sector": "优于赛道",
                "vs_market": "优于大盘"
            },
            "final_verdict": {
                "verdict": "看涨",
                "conviction_level": "高",
                "time_horizon": "1-2月",
                "expected_return": "+20%",
                "max_drawdown_risk": "-15%",
                "risk_reward_ratio": 1.5,
                "summary": "总结"
            }
        }

        is_valid, errors = synthesizer._validate_output(output)

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_output_missing_required_fields(self):
        """测试缺少必需字段"""
        synthesizer = ConclusionSynthesizer()

        output = {}

        is_valid, errors = synthesizer._validate_output(output)

        assert is_valid is False
        assert len(errors) > 0
        assert any("Missing required field" in error for error in errors)

    def test_validate_output_invalid_confidence(self):
        """测试无效的置信度"""
        synthesizer = ConclusionSynthesizer()

        output = {
            "executive_summary": {},
            "investment_outlook": {},
            "key_metrics_to_watch": [{} for _ in range(5)],
            "confidence_assessment": {
                "overall_confidence": 150  # 超出范围
            },
            "investment_recommendation": {},
            "catalyst_calendar": [],
            "comparative_analysis": {},
            "final_verdict": {"risk_reward_ratio": 1.0}
        }

        is_valid, errors = synthesizer._validate_output(output)

        assert is_valid is False
        assert any("overall_confidence must be 0-100" in error for error in errors)

    def test_validate_output_invalid_metrics_count(self):
        """测试无效的关键指标数量"""
        synthesizer = ConclusionSynthesizer()

        output = {
            "executive_summary": {},
            "investment_outlook": {},
            "key_metrics_to_watch": [{"metric": "指标1"}],  # 只有1个，应该有5个
            "confidence_assessment": {"overall_confidence": 50},
            "investment_recommendation": {},
            "catalyst_calendar": [],
            "comparative_analysis": {},
            "final_verdict": {"risk_reward_ratio": 1.0}
        }

        is_valid, errors = synthesizer._validate_output(output)

        assert is_valid is False
        assert any("key_metrics_to_watch must have 5 items" in error for error in errors)

    def test_validate_output_invalid_risk_reward_ratio(self):
        """测试无效的风险收益比"""
        synthesizer = ConclusionSynthesizer()

        output = {
            "executive_summary": {},
            "investment_outlook": {},
            "key_metrics_to_watch": [{} for _ in range(5)],
            "confidence_assessment": {"overall_confidence": 50},
            "investment_recommendation": {},
            "catalyst_calendar": [],
            "comparative_analysis": {},
            "final_verdict": {
                "risk_reward_ratio": -1.5  # 负数无效
            }
        }

        is_valid, errors = synthesizer._validate_output(output)

        assert is_valid is False
        assert any("risk_reward_ratio must be a positive number" in error for error in errors)


class TestFixInvalidOutput:
    """测试 _fix_invalid_output 方法"""

    def test_fix_invalid_output_missing_executive_summary(self):
        """测试修复缺失的执行摘要"""
        synthesizer = ConclusionSynthesizer()

        output = {}
        errors = ["Missing required field: executive_summary"]

        result = synthesizer._fix_invalid_output(output, errors)

        assert "executive_summary" in result
        assert "one_sentence_thesis" in result["executive_summary"]
        assert "bull_thesis" in result["executive_summary"]
        assert "bear_thesis" in result["executive_summary"]

    def test_fix_invalid_output_missing_investment_outlook(self):
        """测试修复缺失的投资展望"""
        synthesizer = ConclusionSynthesizer()

        output = {}
        errors = ["Missing required field: investment_outlook"]

        result = synthesizer._fix_invalid_output(output, errors)

        assert "investment_outlook" in result
        assert "short_term" in result["investment_outlook"]
        assert "medium_term" in result["investment_outlook"]

    def test_fix_invalid_output_wrong_metrics_count(self):
        """测试修复错误的指标数量"""
        synthesizer = ConclusionSynthesizer()

        output = {
            "key_metrics_to_watch": [{"metric": "指标1"}]
        }
        errors = ["key_metrics_to_watch must have 5 items"]

        result = synthesizer._fix_invalid_output(output, errors)

        assert len(result["key_metrics_to_watch"]) == 5

    def test_fix_invalid_output_invalid_confidence(self):
        """测试修复无效的置信度"""
        synthesizer = ConclusionSynthesizer()

        output = {
            "confidence_assessment": {
                "overall_confidence": 150  # 超出范围
            }
        }
        errors = ["overall_confidence must be 0-100"]

        result = synthesizer._fix_invalid_output(output, errors)

        assert result["confidence_assessment"]["overall_confidence"] == 100

    def test_fix_invalid_output_negative_confidence(self):
        """测试修复负置信度"""
        synthesizer = ConclusionSynthesizer()

        output = {
            "confidence_assessment": {
                "overall_confidence": -50
            }
        }
        errors = []

        result = synthesizer._fix_invalid_output(output, errors)

        assert result["confidence_assessment"]["overall_confidence"] == 0

    def test_fix_invalid_output_invalid_risk_reward_ratio(self):
        """测试修复无效的风险收益比"""
        synthesizer = ConclusionSynthesizer()

        output = {
            "final_verdict": {
                "risk_reward_ratio": -1.5
            }
        }
        errors = ["risk_reward_ratio must be a positive number"]

        result = synthesizer._fix_invalid_output(output, errors)

        assert result["final_verdict"]["risk_reward_ratio"] == 1.0


class TestCreateErrorResponse:
    """测试 _create_error_response 方法"""

    def test_create_error_response(self):
        """测试创建错误响应"""
        synthesizer = ConclusionSynthesizer()

        error_message = "LLM 调用失败"

        result = synthesizer._create_error_response(error_message)

        assert result["error"] is True
        assert result["message"] == error_message
        assert "executive_summary" in result
        assert "investment_outlook" in result
        assert "key_metrics_to_watch" in result
        assert "confidence_assessment" in result
        assert "investment_recommendation" in result
        assert "catalyst_calendar" in result
        assert "comparative_analysis" in result
        assert "final_verdict" in result

        assert len(result["key_metrics_to_watch"]) == 5
        assert result["confidence_assessment"]["overall_confidence"] == 0


class TestCallLLM:
    """测试 _call_llm 方法"""

    @pytest.mark.asyncio
    async def test_call_llm_success_primary_model(self):
        """测试主模型成功调用"""
        synthesizer = ConclusionSynthesizer()

        mock_response = {
            "choices": [{
                "message": {
                    "content": '{"executive_summary": {"one_sentence_thesis": "测试论点"}}'
                }
            }]
        }

        with patch.object(synthesizer.llm_client, 'chat_completion', new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = mock_response

            result = await synthesizer._call_llm("test prompt")

            assert result is not None
            assert "executive_summary" in result
            mock_chat.assert_called_once()

    @pytest.mark.asyncio
    async def test_call_llm_fallback_model(self):
        """测试 fallback 模型调用"""
        synthesizer = ConclusionSynthesizer()

        mock_fallback_response = {
            "choices": [{
                "message": {
                    "content": '{"executive_summary": {"one_sentence_thesis": "fallback论点"}}'
                }
            }]
        }

        with patch.object(synthesizer.llm_client, 'chat_completion', new_callable=AsyncMock) as mock_chat:
            # 第一次调用失败，第二次成功
            mock_chat.side_effect = [Exception("Primary failed"), mock_fallback_response]

            result = await synthesizer._call_llm("test prompt")

            assert result is not None
            assert "executive_summary" in result
            assert mock_chat.call_count == 2

    @pytest.mark.asyncio
    async def test_call_llm_all_models_fail(self):
        """测试所有模型都失败"""
        synthesizer = ConclusionSynthesizer()

        with patch.object(synthesizer.llm_client, 'chat_completion', new_callable=AsyncMock) as mock_chat:
            mock_chat.side_effect = [Exception("Primary failed"), Exception("Fallback failed")]

            result = await synthesizer._call_llm("test prompt")

            assert result is None


class TestAnalyze:
    """测试 analyze 方法"""

    @pytest.mark.asyncio
    async def test_analyze_success(self):
        """测试成功分析"""
        synthesizer = ConclusionSynthesizer()

        all_analyses = {
            "symbol": "UNI",
            "tldr": {"summary": "TL;DR摘要"},
            "timeframe": {"summary": "时间窗摘要"},
            "sentiment": {"summary": "情绪摘要"},
            "technical": {"summary": "技术面摘要"},
            "onchain": {"summary": "链上摘要"},
            "competitor": {"summary": "竞品摘要"},
            "tokenomics": {"summary": "代币经济学摘要"},
            "risk": {"summary": "风险摘要"}
        }

        mock_llm_response = {
            "executive_summary": {
                "one_sentence_thesis": "投资论点",
                "bull_thesis": [],
                "bear_thesis": [],
                "key_assumptions": [],
                "invalidation_triggers": []
            },
            "investment_outlook": {
                "short_term": {"timeframe": "1-2周", "view": "看涨", "price_target": "$100", "key_events": [], "rationale": "原因"},
                "medium_term": {"timeframe": "1-2月", "view": "中性", "price_target": "$110", "key_events": [], "rationale": "原因"}
            },
            "key_metrics_to_watch": [
                {"metric": f"指标{i}", "current_value": "100", "target": "120", "importance": "高", "rationale": "原因"}
                for i in range(1, 6)
            ],
            "confidence_assessment": {
                "overall_confidence": 75,
                "confidence_level": "高",
                "data_quality": "优秀",
                "analysis_completeness": "完整",
                "uncertainty_factors": [],
                "confidence_rationale": "原因"
            },
            "investment_recommendation": {
                "rating": "看涨",
                "action": "买入",
                "position_sizing": "10%",
                "entry_strategy": "分批",
                "exit_strategy": "止盈",
                "risk_management": [],
                "suitable_for": "长期投资者",
                "not_suitable_for": "短线交易者"
            },
            "catalyst_calendar": [],
            "comparative_analysis": {
                "vs_competitors": "优于竞品",
                "vs_sector": "优于赛道",
                "vs_market": "优于大盘"
            },
            "final_verdict": {
                "verdict": "看涨",
                "conviction_level": "高",
                "time_horizon": "1-2月",
                "expected_return": "+20%",
                "max_drawdown_risk": "-15%",
                "risk_reward_ratio": 1.5,
                "summary": "总结"
            }
        }

        with patch.object(synthesizer, '_call_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_llm_response

            result = await synthesizer.analyze(all_analyses)

            assert result["error"] is False
            assert "executive_summary" in result
            assert "investment_outlook" in result
            assert "final_verdict" in result
            mock_llm.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_llm_failure(self):
        """测试 LLM 调用失败"""
        synthesizer = ConclusionSynthesizer()

        all_analyses = {
            "symbol": "BTC"
        }

        with patch.object(synthesizer, '_call_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = None

            result = await synthesizer.analyze(all_analyses)

            assert result["error"] is True
            assert "message" in result
            assert "LLM 调用失败" in result["message"]

    @pytest.mark.asyncio
    async def test_analyze_invalid_output_fixed(self):
        """测试无效输出被修复"""
        synthesizer = ConclusionSynthesizer()

        all_analyses = {
            "symbol": "ETH"
        }

        # 返回无效输出（缺少必需字段）
        mock_llm_response = {
            "executive_summary": {},
            "confidence_assessment": {
                "overall_confidence": 150  # 无效值
            }
        }

        with patch.object(synthesizer, '_call_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_llm_response

            result = await synthesizer.analyze(all_analyses)

            # 应该被修复
            assert result["error"] is False
            assert "executive_summary" in result
            assert result["confidence_assessment"]["overall_confidence"] == 100  # 被修复为100

    @pytest.mark.asyncio
    async def test_analyze_exception_handling(self):
        """测试异常处理"""
        synthesizer = ConclusionSynthesizer()

        all_analyses = {
            "symbol": "SOL"
        }

        with patch.object(synthesizer, '_format_prompt') as mock_format:
            mock_format.side_effect = Exception("Formatting error")

            result = await synthesizer.analyze(all_analyses)

            assert result["error"] is True
            assert "message" in result
            assert "分析过程出错" in result["message"]
