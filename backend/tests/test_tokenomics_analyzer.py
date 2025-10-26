"""
TokenomicsAnalyzer 单元测试
测试代币经济学分析器的所有功能
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from app.services.research_engine.analyzers.tokenomics_analyzer import TokenomicsAnalyzer, tokenomics_analyzer


@pytest.fixture
def analyzer():
    """创建 TokenomicsAnalyzer 实例"""
    return TokenomicsAnalyzer()


@pytest.fixture
def sample_aggregated_data():
    """示例聚合数据"""
    today = datetime.now()
    future_3m = (today + timedelta(days=90)).strftime("%Y-%m-%d")
    future_6m = (today + timedelta(days=180)).strftime("%Y-%m-%d")

    return {
        "symbol": "UNI",
        "market_data": {
            "market_cap": 4500000000,
            "fdv": 6000000000
        },
        "onchain_data": {
            "protocol_revenue_30d": 45000000,
            "buyback_burn_30d": 5000000
        },
        "tokenomics": {
            "total_supply": 1000000000,
            "circulating_supply": 750000000,
            "max_supply": 1000000000,
            "allocation": {
                "team": {"percent": 21.5, "vesting_period": "4年线性解锁"},
                "investors": {"percent": 17.8, "vesting_period": "4年线性解锁"},
                "community": {"percent": 43, "vesting_period": "社区金库管理"},
                "liquidity_mining": {"percent": 17.7, "vesting_period": "4年分发"}
            },
            "unlock_schedule": [
                {
                    "date": future_3m,
                    "amount": 10000000,
                    "beneficiary": "投资人"
                },
                {
                    "date": future_6m,
                    "amount": 15000000,
                    "beneficiary": "团队"
                }
            ],
            "value_capture": {
                "mechanisms": [
                    {
                        "type": "治理权",
                        "description": "投票决定协议参数"
                    },
                    {
                        "type": "质押奖励",
                        "description": "质押获得收入分成",
                        "apy": "15%"
                    }
                ],
                "revenue_share_to_holders": "70%",
                "deflationary": True,
                "flywheel_effect": "强"
            }
        }
    }


class TestTokenomicsAnalyzerInit:
    """测试初始化"""

    def test_init_success(self, analyzer):
        """测试正常初始化"""
        assert analyzer.system_prompt is not None
        assert analyzer.user_prompt_template is not None
        assert analyzer.model_config is not None
        assert analyzer.validation_rules is not None
        assert "supply_structure" in analyzer.validation_rules["required_fields"]
        assert "unlock_schedule" in analyzer.validation_rules["required_fields"]
        assert "value_capture" in analyzer.validation_rules["required_fields"]

    def test_singleton_instance(self):
        """测试单例实例"""
        assert tokenomics_analyzer is not None
        assert isinstance(tokenomics_analyzer, TokenomicsAnalyzer)


class TestAnalyzeSupplyStructure:
    """测试供应结构分析"""

    def test_analyze_supply_structure_complete_data(self, analyzer):
        """测试完整数据的供应结构分析"""
        tokenomics_data = {
            "total_supply": 1000000000,
            "circulating_supply": 750000000,
            "max_supply": 1000000000,
            "allocation": {
                "team": {"percent": 20, "vesting_period": "4年"},
                "community": {"percent": 40, "vesting_period": "即时"}
            }
        }

        result = analyzer._analyze_supply_structure(tokenomics_data)

        assert result["total_supply"] == 1000000000
        assert result["circulating_supply"] == 750000000
        assert result["circulation_rate"] == 75.0
        assert result["max_supply"] == 1000000000
        assert "team" in result["allocation"]

    def test_analyze_supply_structure_no_max_supply(self, analyzer):
        """测试无最大供应量的情况"""
        tokenomics_data = {
            "total_supply": 1000000000,
            "circulating_supply": 500000000,
            "max_supply": None
        }

        result = analyzer._analyze_supply_structure(tokenomics_data)

        assert result["max_supply"] == "无上限"

    def test_analyze_supply_structure_zero_total_supply(self, analyzer):
        """测试总供应量为0的情况"""
        tokenomics_data = {
            "total_supply": 0,
            "circulating_supply": 0
        }

        result = analyzer._analyze_supply_structure(tokenomics_data)

        assert result["circulation_rate"] == 0


class TestAnalyzeUnlockSchedule:
    """测试解锁时间表分析"""

    def test_analyze_unlock_schedule_complete_data(self, analyzer):
        """测试完整数据的解锁时间表分析"""
        today = datetime.now()
        future_3m = (today + timedelta(days=90)).strftime("%Y-%m-%d")
        future_9m = (today + timedelta(days=270)).strftime("%Y-%m-%d")

        tokenomics_data = {
            "unlock_schedule": [
                {
                    "date": future_3m,
                    "amount": 10000000,
                    "beneficiary": "投资人"
                },
                {
                    "date": future_9m,
                    "amount": 20000000,
                    "beneficiary": "团队"
                }
            ]
        }
        circulating_supply = 100000000

        result = analyzer._analyze_unlock_schedule(tokenomics_data, circulating_supply)

        assert "upcoming_unlocks" in result
        assert len(result["upcoming_unlocks"]) == 2
        assert result["next_6months_unlock"] == 10000000
        assert result["next_12months_unlock"] == 30000000

    def test_analyze_unlock_schedule_high_pressure(self, analyzer):
        """测试高解锁压力场景"""
        today = datetime.now()
        future_1m = (today + timedelta(days=30)).strftime("%Y-%m-%d")

        tokenomics_data = {
            "unlock_schedule": [
                {
                    "date": future_1m,
                    "amount": 25000000,  # 25%流通量
                    "beneficiary": "投资人"
                }
            ]
        }
        circulating_supply = 100000000

        result = analyzer._analyze_unlock_schedule(tokenomics_data, circulating_supply)

        assert result["unlock_pressure"] == "高"
        assert "25.0%" in result["pressure_rationale"]

    def test_analyze_unlock_schedule_medium_pressure(self, analyzer):
        """测试中等解锁压力场景"""
        today = datetime.now()
        future_2m = (today + timedelta(days=60)).strftime("%Y-%m-%d")

        tokenomics_data = {
            "unlock_schedule": [
                {
                    "date": future_2m,
                    "amount": 15000000,  # 15%流通量
                    "beneficiary": "团队"
                }
            ]
        }
        circulating_supply = 100000000

        result = analyzer._analyze_unlock_schedule(tokenomics_data, circulating_supply)

        assert result["unlock_pressure"] == "中"

    def test_analyze_unlock_schedule_low_pressure(self, analyzer):
        """测试低解锁压力场景"""
        today = datetime.now()
        future_3m = (today + timedelta(days=90)).strftime("%Y-%m-%d")

        tokenomics_data = {
            "unlock_schedule": [
                {
                    "date": future_3m,
                    "amount": 5000000,  # 5%流通量
                    "beneficiary": "投资人"
                }
            ]
        }
        circulating_supply = 100000000

        result = analyzer._analyze_unlock_schedule(tokenomics_data, circulating_supply)

        assert result["unlock_pressure"] == "低"

    def test_analyze_unlock_schedule_invalid_date(self, analyzer):
        """测试无效日期格式"""
        tokenomics_data = {
            "unlock_schedule": [
                {
                    "date": "invalid-date",
                    "amount": 10000000,
                    "beneficiary": "投资人"
                }
            ]
        }
        circulating_supply = 100000000

        result = analyzer._analyze_unlock_schedule(tokenomics_data, circulating_supply)

        # 无效日期应该被跳过
        assert result["next_6months_unlock"] == 0

    def test_analyze_unlock_schedule_empty(self, analyzer):
        """测试空解锁时间表"""
        result = analyzer._analyze_unlock_schedule({}, 100000000)

        assert result["upcoming_unlocks"] == []
        assert result["next_6months_unlock"] == 0
        assert result["unlock_pressure"] == "低"


class TestAnalyzeValueCapture:
    """测试价值捕获分析"""

    def test_analyze_value_capture_complete_data(self, analyzer):
        """测试完整数据的价值捕获分析"""
        tokenomics_data = {
            "value_capture": {
                "mechanisms": [
                    {"type": "质押奖励", "description": "质押获得收入"},
                    {"type": "回购销毁", "description": "协议回购代币"}
                ],
                "revenue_share_to_holders": "70%",
                "deflationary": True,
                "flywheel_effect": "强"
            }
        }

        result = analyzer._analyze_value_capture(tokenomics_data)

        assert len(result["mechanisms"]) == 2
        assert result["revenue_share_to_holders"] == "70%"
        assert result["deflationary"] is True
        assert result["flywheel_effect"] == "强"

    def test_analyze_value_capture_missing_data(self, analyzer):
        """测试缺失数据的价值捕获分析"""
        result = analyzer._analyze_value_capture({})

        assert result["mechanisms"] == []
        assert result["revenue_share_to_holders"] == "0%"
        assert result["deflationary"] is False
        assert result["flywheel_effect"] == "弱"


class TestFormatAllocationData:
    """测试格式化分配数据"""

    def test_format_allocation_data_complete(self, analyzer):
        """测试格式化完整分配数据"""
        allocation = {
            "team": {"percent": 20, "vesting_period": "4年"},
            "community": {"percent": 40, "vesting_period": "即时"}
        }

        formatted = analyzer._format_allocation_data(allocation)

        assert "team: 20%" in formatted
        assert "4年" in formatted
        assert "community: 40%" in formatted

    def test_format_allocation_data_empty(self, analyzer):
        """测试格式化空分配数据"""
        formatted = analyzer._format_allocation_data({})

        assert formatted == "暂无分配数据"

    def test_format_allocation_data_simple_values(self, analyzer):
        """测试格式化简单值"""
        allocation = {
            "team": "20%",
            "community": "40%"
        }

        formatted = analyzer._format_allocation_data(allocation)

        assert "team: 20%" in formatted
        assert "community: 40%" in formatted


class TestFormatUnlockSchedule:
    """测试格式化解锁时间表"""

    def test_format_unlock_schedule_complete(self, analyzer):
        """测试格式化完整解锁时间表"""
        unlock_schedule = [
            {
                "date": "2025-03-01",
                "amount": 10000000,
                "beneficiary": "投资人",
                "percent_of_circulating": 5.5
            },
            {
                "date": "2025-06-01",
                "amount": 15000000,
                "beneficiary": "团队",
                "percent_of_circulating": 8.0
            }
        ]

        formatted = analyzer._format_unlock_schedule(unlock_schedule)

        assert "2025-03-01" in formatted
        assert "10,000,000" in formatted
        assert "投资人" in formatted
        assert "5.50%" in formatted

    def test_format_unlock_schedule_empty(self, analyzer):
        """测试格式化空解锁时间表"""
        formatted = analyzer._format_unlock_schedule([])

        assert formatted == "暂无解锁时间表数据"

    def test_format_unlock_schedule_max_five(self, analyzer):
        """测试最多格式化5个解锁"""
        unlock_schedule = [
            {"date": f"2025-0{i}-01", "amount": 1000000, "beneficiary": "Test", "percent_of_circulating": 1.0}
            for i in range(1, 10)  # 9个解锁
        ]

        formatted = analyzer._format_unlock_schedule(unlock_schedule)

        # 只应该包含前5个
        assert "2025-01-01" in formatted
        assert "2025-05-01" in formatted
        assert "2025-09-01" not in formatted


class TestFormatValueCapture:
    """测试格式化价值捕获机制"""

    def test_format_value_capture_complete(self, analyzer):
        """测试格式化完整价值捕获机制"""
        mechanisms = [
            {"type": "质押奖励", "description": "质押获得收入"},
            {"type": "回购销毁", "description": "协议回购代币"}
        ]

        formatted = analyzer._format_value_capture(mechanisms)

        assert "质押奖励" in formatted
        assert "质押获得收入" in formatted
        assert "回购销毁" in formatted

    def test_format_value_capture_empty(self, analyzer):
        """测试格式化空价值捕获机制"""
        formatted = analyzer._format_value_capture([])

        assert formatted == "暂无价值捕获机制数据"


class TestFormatPrompt:
    """测试格式化 prompt"""

    def test_format_prompt_complete_data(self, analyzer, sample_aggregated_data):
        """测试完整数据的 prompt 格式化"""
        prompt = analyzer._format_prompt(sample_aggregated_data)

        assert "UNI" in prompt
        assert "1000000000" in prompt  # total_supply
        assert "750000000" in prompt  # circulating_supply
        assert "75.0%" in prompt or "75.4%" in prompt  # circulation_rate
        assert "团队" in prompt or "team" in prompt

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
            "supply_structure": {
                "circulation_rate": 75.0
            },
            "unlock_schedule": {
                "unlock_pressure": "低"
            },
            "value_capture": {
                "deflationary": True,
                "flywheel_effect": "强"
            },
            "token_utility": {
                "utility_score": 8
            },
            "inflation_deflation": {},
            "risk_assessment": {},
            "incentive_alignment": {
                "alignment_score": 7
            },
            "tokenomics_health_score": {
                "score": 75
            },
            "summary": "总结"
        }

        is_valid, errors = analyzer._validate_output(output)
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_output_missing_required_fields(self, analyzer):
        """测试缺少必需字段"""
        output = {
            "supply_structure": {}
        }

        is_valid, errors = analyzer._validate_output(output)
        assert is_valid is False
        assert len(errors) > 0

    def test_validate_output_invalid_circulation_rate(self, analyzer):
        """测试无效流通率"""
        output = {
            "supply_structure": {"circulation_rate": 150},  # 超过100
            "unlock_schedule": {"unlock_pressure": "低"},
            "value_capture": {"deflationary": True, "flywheel_effect": "强"},
            "token_utility": {"utility_score": 5},
            "inflation_deflation": {},
            "risk_assessment": {},
            "incentive_alignment": {"alignment_score": 5},
            "tokenomics_health_score": {"score": 50},
            "summary": "test"
        }

        is_valid, errors = analyzer._validate_output(output)
        assert is_valid is False
        assert any("circulation_rate" in error for error in errors)

    def test_validate_output_invalid_utility_score(self, analyzer):
        """测试无效实用性分数"""
        output = {
            "supply_structure": {"circulation_rate": 75},
            "unlock_schedule": {"unlock_pressure": "低"},
            "value_capture": {"deflationary": True, "flywheel_effect": "强"},
            "token_utility": {"utility_score": 15},  # 超过10
            "inflation_deflation": {},
            "risk_assessment": {},
            "incentive_alignment": {"alignment_score": 5},
            "tokenomics_health_score": {"score": 50},
            "summary": "test"
        }

        is_valid, errors = analyzer._validate_output(output)
        assert is_valid is False
        assert any("utility_score" in error for error in errors)


class TestFixInvalidOutput:
    """测试修复无效输出"""

    def test_fix_invalid_output_missing_fields(self, analyzer):
        """测试修复缺少字段的输出"""
        invalid_output = {
            "supply_structure": {"circulation_rate": 75}
        }

        fixed = analyzer._fix_invalid_output(invalid_output, ["Missing fields"])

        assert "unlock_schedule" in fixed
        assert "value_capture" in fixed
        assert "token_utility" in fixed
        assert "tokenomics_health_score" in fixed

    def test_fix_invalid_output_invalid_circulation_rate(self, analyzer):
        """测试修复无效流通率"""
        invalid_output = {
            "supply_structure": {"circulation_rate": 150}
        }

        fixed = analyzer._fix_invalid_output(invalid_output, ["Invalid rate"])

        assert fixed["supply_structure"]["circulation_rate"] == 100

    def test_fix_invalid_output_negative_scores(self, analyzer):
        """测试修复负数分数"""
        invalid_output = {
            "token_utility": {"utility_score": -5},
            "incentive_alignment": {"alignment_score": -3},
            "tokenomics_health_score": {"score": -10}
        }

        fixed = analyzer._fix_invalid_output(invalid_output, ["Negative scores"])

        assert fixed["token_utility"]["utility_score"] == 0
        assert fixed["incentive_alignment"]["alignment_score"] == 0
        assert fixed["tokenomics_health_score"]["score"] == 0


class TestErrorResponse:
    """测试错误响应"""

    def test_create_error_response(self, analyzer):
        """测试创建错误响应"""
        error_msg = "LLM 调用失败"
        response = analyzer._create_error_response(error_msg)

        assert response["error"] is True
        assert error_msg in response["message"]
        assert "supply_structure" in response
        assert "unlock_schedule" in response
        assert response["tokenomics_health_score"]["score"] == 0


class TestAnalyze:
    """测试 analyze 主函数"""

    @pytest.mark.asyncio
    async def test_analyze_success(self, analyzer, sample_aggregated_data):
        """测试成功分析"""
        mock_response = {
            "supply_structure": {
                "total_supply": 1000000000,
                "circulating_supply": 750000000,
                "circulation_rate": 75.0,
                "max_supply": "1000000000",
                "emission_rate": "无新增",
                "allocation_breakdown": {},
                "distribution_fairness": "公平",
                "fairness_rationale": "社区占比高"
            },
            "unlock_schedule": {
                "upcoming_unlocks": [],
                "next_6months_unlock": 25000000,
                "next_12months_unlock": 40000000,
                "unlock_pressure": "低",
                "pressure_rationale": "解锁压力小"
            },
            "value_capture": {
                "mechanisms": [],
                "revenue_share_to_holders": "70%",
                "deflationary": True,
                "flywheel_effect": "强",
                "flywheel_description": "协议增长驱动代币需求"
            },
            "token_utility": {
                "use_cases": ["治理", "质押"],
                "demand_drivers": ["质押需求"],
                "utility_score": 8,
                "utility_rating": "强"
            },
            "inflation_deflation": {
                "current_inflation_rate": "0%",
                "future_inflation_rate": "0%",
                "deflation_mechanisms": ["回购销毁"],
                "net_inflation": "0%",
                "inflation_vs_revenue_growth": "可持续",
                "sustainability": "可持续"
            },
            "risk_assessment": {
                "tokenomics_risks": ["解锁压力"],
                "death_spiral_risk": "低",
                "risk_rationale": "风险可控",
                "mitigation_factors": ["协议收入增长"]
            },
            "incentive_alignment": {
                "aligned_with_protocol_success": True,
                "alignment_score": 8,
                "alignment_factors": ["收入分配"],
                "misalignment_concerns": []
            },
            "tokenomics_health_score": {
                "score": 80,
                "rating": "优秀 (80+)",
                "strengths": ["强价值捕获", "低通胀"],
                "weaknesses": ["解锁压力"]
            },
            "summary": "代币经济学设计优秀"
        }

        with patch.object(analyzer, '_call_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_response

            result = await analyzer.analyze(sample_aggregated_data)

            assert result["error"] is False
            assert result["supply_structure"]["circulation_rate"] == 75.0
            assert result["tokenomics_health_score"]["score"] == 80

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
            "supply_structure": {"circulation_rate": 75}
            # Missing other required fields
        }

        with patch.object(analyzer, '_call_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = invalid_response

            result = await analyzer.analyze(sample_aggregated_data)

            assert result["error"] is False
            assert "unlock_schedule" in result
            assert "value_capture" in result
            assert "tokenomics_health_score" in result
