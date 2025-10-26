"""
RiskAssessor 单元测试
测试风险评估器的所有功能
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.research_engine.analyzers.risk_assessor import RiskAssessor, risk_assessor


@pytest.fixture
def analyzer():
    """创建 RiskAssessor 实例"""
    return RiskAssessor()


@pytest.fixture
def sample_aggregated_data():
    """示例聚合数据"""
    return {
        "symbol": "UNI",
        "market_data": {
            "name": "Uniswap",
            "category": "DEX",
            "market_cap": 4500000000
        },
        "onchain_data": {
            "active_addresses_24h": 150000
        },
        "recent_events": [
            {"title": "V3上线", "date": "2024-01-15"},
            {"title": "费用开关投票", "date": "2024-02-01"},
            "社区金库分配提案"
        ],
        "competitors": [
            {"name": "PancakeSwap", "market_cap": 800000000},
            {"name": "SushiSwap", "market_cap": 300000000}
        ],
        "market_share": "60%",
        "competition_intensity": "激烈",
        "tokenomics": {
            "circulating_supply": 750000000,
            "unlock_schedule": [
                {
                    "date": "2025-03-01",
                    "amount": 10000000,
                    "beneficiary": "投资人"
                },
                {
                    "date": "2025-06-01",
                    "amount": 15000000,
                    "beneficiary": "团队"
                }
            ]
        },
        "tech_status": {
            "product_status": "稳定运行",
            "development": "V4开发中",
            "audits": "通过多次审计"
        },
        "regulatory": {
            "status": "不确定",
            "compliance": "未明确",
            "risk_level": "中等"
        }
    }


class TestRiskAssessorInit:
    """测试初始化"""

    def test_init_success(self, analyzer):
        """测试正常初始化"""
        assert analyzer.system_prompt is not None
        assert analyzer.user_prompt_template is not None
        assert analyzer.model_config is not None
        assert analyzer.validation_rules is not None
        assert "catalysts" in analyzer.validation_rules["required_fields"]
        assert "risks" in analyzer.validation_rules["required_fields"]

    def test_singleton_instance(self):
        """测试单例实例"""
        assert risk_assessor is not None
        assert isinstance(risk_assessor, RiskAssessor)


class TestFormatRecentEvents:
    """测试格式化近期事件"""

    def test_format_recent_events_complete(self, analyzer):
        """测试格式化完整近期事件"""
        data = {
            "recent_events": [
                {"title": "Event1", "date": "2024-01-01"},
                {"title": "Event2", "date": "2024-01-15"},
                "Event3 string format"
            ]
        }

        formatted = analyzer._format_recent_events(data)

        assert "Event1" in formatted
        assert "2024-01-01" in formatted
        assert "Event2" in formatted
        assert "Event3 string format" in formatted

    def test_format_recent_events_empty(self, analyzer):
        """测试格式化空事件列表"""
        formatted = analyzer._format_recent_events({})

        assert formatted == "暂无近期重要事件数据"

    def test_format_recent_events_max_five(self, analyzer):
        """测试最多格式化5个事件"""
        data = {
            "recent_events": [
                {"title": f"Event{i}", "date": f"2024-0{i}-01"}
                for i in range(1, 10)  # 9个事件
            ]
        }

        formatted = analyzer._format_recent_events(data)

        # 应该只包含前5个
        assert "Event1" in formatted
        assert "Event5" in formatted
        # 不应该包含第6个及以后
        lines = formatted.split("\n")
        assert len(lines) <= 5


class TestFormatCompetitionSummary:
    """测试格式化竞争总结"""

    def test_format_competition_summary_complete(self, analyzer):
        """测试格式化完整竞争总结"""
        data = {
            "competitors": [
                {"name": "Comp1"},
                {"name": "Comp2"},
                {"name": "Comp3"}
            ],
            "market_share": "60%",
            "competition_intensity": "激烈"
        }

        formatted = analyzer._format_competition_summary(data)

        assert "Comp1" in formatted
        assert "Comp2" in formatted
        assert "Comp3" in formatted
        assert "60%" in formatted
        assert "激烈" in formatted

    def test_format_competition_summary_empty(self, analyzer):
        """测试格式化空竞争数据"""
        formatted = analyzer._format_competition_summary({})

        assert formatted == "暂无竞争对手数据"

    def test_format_competition_summary_no_market_share(self, analyzer):
        """测试无市场份额的竞争总结"""
        data = {
            "competitors": [{"name": "Comp1"}],
            "competition_intensity": "中等"
        }

        formatted = analyzer._format_competition_summary(data)

        assert "Comp1" in formatted
        assert "中等" in formatted


class TestFormatUnlockSummary:
    """测试格式化解锁总结"""

    def test_format_unlock_summary_complete(self, analyzer):
        """测试格式化完整解锁总结"""
        data = {
            "tokenomics": {
                "circulating_supply": 750000000,
                "unlock_schedule": [
                    {
                        "date": "2025-03-01",
                        "amount": 10000000,
                        "beneficiary": "投资人"
                    },
                    {
                        "date": "2025-06-01",
                        "amount": 15000000,
                        "beneficiary": "团队"
                    }
                ]
            }
        }

        formatted = analyzer._format_unlock_summary(data)

        assert "25,000,000" in formatted  # 总解锁量
        assert "3.3%" in formatted or "3.4%" in formatted  # 占流通量百分比
        assert "2025-03-01" in formatted
        assert "投资人" in formatted

    def test_format_unlock_summary_empty(self, analyzer):
        """测试格式化空解锁数据"""
        formatted = analyzer._format_unlock_summary({})

        assert formatted == "暂无代币解锁数据"

    def test_format_unlock_summary_max_three(self, analyzer):
        """测试最多格式化3个解锁"""
        data = {
            "tokenomics": {
                "circulating_supply": 100000000,
                "unlock_schedule": [
                    {"date": f"2025-0{i}-01", "amount": 1000000, "beneficiary": "Test"}
                    for i in range(1, 6)  # 5个解锁
                ]
            }
        }

        formatted = analyzer._format_unlock_summary(data)

        # 应该包含总量行 + 最多3个解锁
        lines = formatted.split("\n")
        assert len(lines) <= 4  # 1行总量 + 3行具体解锁


class TestFormatTechStatus:
    """测试格式化技术状态"""

    def test_format_tech_status_complete(self, analyzer):
        """测试格式化完整技术状态"""
        data = {
            "tech_status": {
                "product_status": "稳定运行",
                "development": "V4开发中",
                "audits": "通过审计"
            }
        }

        formatted = analyzer._format_tech_status(data)

        assert "稳定运行" in formatted
        assert "V4开发中" in formatted
        assert "通过审计" in formatted

    def test_format_tech_status_empty(self, analyzer):
        """测试格式化空技术状态"""
        formatted = analyzer._format_tech_status({})

        # 应该有默认信息
        assert "产品运行稳定" in formatted or "稳定" in formatted

    def test_format_tech_status_partial(self, analyzer):
        """测试格式化部分技术状态"""
        data = {
            "tech_status": {
                "product_status": "测试中"
            }
        }

        formatted = analyzer._format_tech_status(data)

        assert "测试中" in formatted


class TestFormatRegulatoryEnvironment:
    """测试格式化监管环境"""

    def test_format_regulatory_environment_complete(self, analyzer):
        """测试格式化完整监管环境"""
        data = {
            "regulatory": {
                "status": "不确定",
                "compliance": "未明确",
                "risk_level": "中等"
            }
        }

        formatted = analyzer._format_regulatory_environment(data)

        assert "不确定" in formatted
        assert "未明确" in formatted
        assert "中等" in formatted

    def test_format_regulatory_environment_empty(self, analyzer):
        """测试格式化空监管环境"""
        formatted = analyzer._format_regulatory_environment({})

        # 应该有默认信息
        assert "监管" in formatted

    def test_format_regulatory_environment_partial(self, analyzer):
        """测试格式化部分监管环境"""
        data = {
            "regulatory": {
                "status": "合规"
            }
        }

        formatted = analyzer._format_regulatory_environment(data)

        assert "合规" in formatted


class TestFormatPrompt:
    """测试格式化 prompt"""

    def test_format_prompt_complete_data(self, analyzer, sample_aggregated_data):
        """测试完整数据的 prompt 格式化"""
        prompt = analyzer._format_prompt(sample_aggregated_data)

        assert "UNI" in prompt
        assert "Uniswap" in prompt
        assert "DEX" in prompt
        assert "4500000000" in prompt
        assert "V3上线" in prompt
        assert "PancakeSwap" in prompt

    def test_format_prompt_missing_data(self, analyzer):
        """测试缺失数据的 prompt 格式化"""
        data = {"symbol": "TEST"}
        prompt = analyzer._format_prompt(data)

        assert "TEST" in prompt


class TestOutputValidation:
    """测试输出验证"""

    def test_validate_output_valid(self, analyzer):
        """测试有效输出验证"""
        output = {
            "catalysts": {
                "short_term": [{"event": "Event1"}],
                "medium_term": [{"event": "Event2"}],
                "long_term": [{"event": "Event3"}]
            },
            "risks": {
                "regulatory": [{"risk": "Risk1"}],
                "technical": [{"risk": "Risk2"}],
                "competitive": [{"risk": "Risk3"}],
                "market": [{"risk": "Risk4"}],
                "tokenomics": [{"risk": "Risk5"}]
            },
            "risk_reward_analysis": {
                "risk_reward_ratio": 2.0
            },
            "tail_risks": [],
            "scenario_analysis": {},
            "overall_risk_rating": {
                "score": 5
            },
            "summary": "Summary"
        }

        is_valid, errors = analyzer._validate_output(output)
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_output_missing_required_fields(self, analyzer):
        """测试缺少必需字段"""
        output = {
            "catalysts": {}
        }

        is_valid, errors = analyzer._validate_output(output)
        assert is_valid is False
        assert len(errors) > 0

    def test_validate_output_invalid_catalysts(self, analyzer):
        """测试无效催化剂格式"""
        output = {
            "catalysts": {
                "short_term": "not a list"  # 应该是列表
            },
            "risks": {
                "regulatory": [], "technical": [], "competitive": [],
                "market": [], "tokenomics": []
            },
            "risk_reward_analysis": {"risk_reward_ratio": 1.0},
            "tail_risks": [],
            "scenario_analysis": {},
            "overall_risk_rating": {"score": 5},
            "summary": "test"
        }

        is_valid, errors = analyzer._validate_output(output)
        assert is_valid is False
        assert any("short_term" in error for error in errors)

    def test_validate_output_invalid_risk_reward_ratio(self, analyzer):
        """测试无效风险回报比"""
        output = {
            "catalysts": {
                "short_term": [], "medium_term": [], "long_term": []
            },
            "risks": {
                "regulatory": [], "technical": [], "competitive": [],
                "market": [], "tokenomics": []
            },
            "risk_reward_analysis": {
                "risk_reward_ratio": -1.0  # 负数
            },
            "tail_risks": [],
            "scenario_analysis": {},
            "overall_risk_rating": {"score": 5},
            "summary": "test"
        }

        is_valid, errors = analyzer._validate_output(output)
        assert is_valid is False
        assert any("risk_reward_ratio" in error for error in errors)

    def test_validate_output_invalid_risk_score(self, analyzer):
        """测试无效风险分数"""
        output = {
            "catalysts": {
                "short_term": [], "medium_term": [], "long_term": []
            },
            "risks": {
                "regulatory": [], "technical": [], "competitive": [],
                "market": [], "tokenomics": []
            },
            "risk_reward_analysis": {"risk_reward_ratio": 1.0},
            "tail_risks": [],
            "scenario_analysis": {},
            "overall_risk_rating": {
                "score": 15  # 超过10
            },
            "summary": "test"
        }

        is_valid, errors = analyzer._validate_output(output)
        assert is_valid is False
        assert any("score" in error for error in errors)


class TestFixInvalidOutput:
    """测试修复无效输出"""

    def test_fix_invalid_output_missing_fields(self, analyzer):
        """测试修复缺少字段的输出"""
        invalid_output = {
            "catalysts": {}
        }

        fixed = analyzer._fix_invalid_output(invalid_output, ["Missing fields"])

        assert "risks" in fixed
        assert "risk_reward_analysis" in fixed
        assert "tail_risks" in fixed
        assert "scenario_analysis" in fixed
        assert "overall_risk_rating" in fixed
        assert "summary" in fixed

    def test_fix_invalid_output_invalid_ratio(self, analyzer):
        """测试修复无效风险回报比"""
        invalid_output = {
            "risk_reward_analysis": {
                "risk_reward_ratio": -1.0
            }
        }

        fixed = analyzer._fix_invalid_output(invalid_output, ["Invalid ratio"])

        assert fixed["risk_reward_analysis"]["risk_reward_ratio"] == 1.0

    def test_fix_invalid_output_invalid_score(self, analyzer):
        """测试修复无效风险分数"""
        invalid_output = {
            "overall_risk_rating": {
                "score": 15
            }
        }

        fixed = analyzer._fix_invalid_output(invalid_output, ["Invalid score"])

        assert fixed["overall_risk_rating"]["score"] == 10

    def test_fix_invalid_output_negative_score(self, analyzer):
        """测试修复负数风险分数"""
        invalid_output = {
            "overall_risk_rating": {
                "score": -5
            }
        }

        fixed = analyzer._fix_invalid_output(invalid_output, ["Negative score"])

        assert fixed["overall_risk_rating"]["score"] == 0


class TestErrorResponse:
    """测试错误响应"""

    def test_create_error_response(self, analyzer):
        """测试创建错误响应"""
        error_msg = "LLM 调用失败"
        response = analyzer._create_error_response(error_msg)

        assert response["error"] is True
        assert error_msg in response["message"]
        assert "catalysts" in response
        assert "risks" in response
        assert response["overall_risk_rating"]["score"] == 0


class TestAnalyze:
    """测试 analyze 主函数"""

    @pytest.mark.asyncio
    async def test_analyze_success(self, analyzer, sample_aggregated_data):
        """测试成功分析"""
        mock_response = {
            "catalysts": {
                "short_term": [
                    {
                        "event": "V4上线",
                        "timeframe": "2-4周",
                        "impact": "高",
                        "probability": "高"
                    }
                ],
                "medium_term": [
                    {
                        "event": "费用开关",
                        "timeframe": "1-2月",
                        "impact": "高",
                        "probability": "中"
                    }
                ],
                "long_term": []
            },
            "risks": {
                "regulatory": [{"risk": "SEC执法"}],
                "technical": [{"risk": "合约漏洞"}],
                "competitive": [{"risk": "市场份额下降"}],
                "market": [{"risk": "熊市"}],
                "tokenomics": [{"risk": "解锁抛压"}]
            },
            "risk_reward_analysis": {
                "upside_potential": "+50%",
                "downside_risk": "-30%",
                "risk_reward_ratio": 1.67,
                "asymmetry": "正向不对称",
                "rationale": "催化剂多于风险"
            },
            "tail_risks": [
                {
                    "event": "黑客攻击",
                    "probability": "极低",
                    "impact": "极高"
                }
            ],
            "scenario_analysis": {
                "bull_case": {
                    "triggers": ["V4成功", "费用开关"],
                    "price_target": "+100%",
                    "probability": "25%"
                },
                "base_case": {
                    "triggers": ["部分催化剂"],
                    "price_target": "+30%",
                    "probability": "50%"
                },
                "bear_case": {
                    "triggers": ["监管风险"],
                    "price_target": "-40%",
                    "probability": "25%"
                }
            },
            "overall_risk_rating": {
                "rating": "中等风险",
                "score": 5,
                "risk_factors_summary": "监管不确定",
                "catalyst_summary": "多个近期催化剂",
                "recommendation": "可以配置"
            },
            "summary": "Uniswap 风险回报比良好"
        }

        with patch.object(analyzer, '_call_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_response

            result = await analyzer.analyze(sample_aggregated_data)

            assert result["error"] is False
            assert "catalysts" in result
            assert result["overall_risk_rating"]["rating"] == "中等风险"

    @pytest.mark.asyncio
    async def test_analyze_llm_failure(self, analyzer, sample_aggregated_data):
        """测试 LLM 调用失败"""
        with patch.object(analyzer, '_call_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = None

            result = await analyzer.analyze(sample_aggregated_data)

            assert result["error"] is True
            assert "LLM 调用失败" in result["message"]

    @pytest.mark.asyncio
    async def test_analyze_invalid_output_fixed(self, analyzer, sample_aggregated_data):
        """测试无效输出被修复"""
        invalid_response = {
            "catalysts": {}
            # Missing other required fields
        }

        with patch.object(analyzer, '_call_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = invalid_response

            result = await analyzer.analyze(sample_aggregated_data)

            assert result["error"] is False
            assert "risks" in result
            assert "risk_reward_analysis" in result
            assert "overall_risk_rating" in result
