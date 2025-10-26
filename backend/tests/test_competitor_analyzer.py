"""
CompetitorAnalyzer 单元测试
测试竞品对比分析器的所有功能
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.research_engine.analyzers.competitor_analyzer import CompetitorAnalyzer, competitor_analyzer


@pytest.fixture
def analyzer():
    """创建 CompetitorAnalyzer 实例"""
    return CompetitorAnalyzer()


@pytest.fixture
def sample_aggregated_data():
    """示例聚合数据"""
    return {
        "symbol": "UNI",
        "market_data": {
            "name": "Uniswap",
            "category": "DEX",
            "market_cap": 4500000000,
            "volume_24h": 1200000000
        },
        "onchain_data": {
            "tvl": 3200000000,
            "active_addresses_24h": 150000,
            "protocol_revenue_30d": 45000000
        },
        "competitors": [
            {
                "name": "PancakeSwap",
                "symbol": "CAKE",
                "market_cap": 800000000,
                "tvl": 1500000000,
                "active_users_24h": 80000,
                "volume_24h": 400000000,
                "protocol_revenue_30d": 15000000,
                "market_share": "12%",
                "differentiation": "BSC生态最大DEX"
            },
            {
                "name": "SushiSwap",
                "symbol": "SUSHI",
                "market_cap": 300000000,
                "tvl": 600000000,
                "active_users_24h": 30000,
                "volume_24h": 200000000,
                "protocol_revenue_30d": 8000000,
                "market_share": "5%",
                "differentiation": "多链部署"
            },
            {
                "name": "Curve",
                "symbol": "CRV",
                "market_cap": 500000000,
                "tvl": 2500000000,
                "active_users_24h": 20000,
                "volume_24h": 300000000,
                "protocol_revenue_30d": 12000000,
                "market_share": "8%",
                "differentiation": "稳定币交易专家"
            }
        ]
    }


class TestCompetitorAnalyzerInit:
    """测试初始化"""

    def test_init_success(self, analyzer):
        """测试正常初始化"""
        assert analyzer.system_prompt is not None
        assert analyzer.user_prompt_template is not None
        assert analyzer.model_config is not None
        assert analyzer.validation_rules is not None
        assert "competitive_landscape" in analyzer.validation_rules["required_fields"]
        assert "competitors" in analyzer.validation_rules["required_fields"]

    def test_singleton_instance(self):
        """测试单例实例"""
        assert competitor_analyzer is not None
        assert isinstance(competitor_analyzer, CompetitorAnalyzer)

    def test_sector_competitors_mapping(self, analyzer):
        """测试赛道竞品映射表"""
        assert "DEX" in analyzer.SECTOR_COMPETITORS
        assert "UNI" in analyzer.SECTOR_COMPETITORS["DEX"]
        assert "借贷协议" in analyzer.SECTOR_COMPETITORS
        assert "AAVE" in analyzer.SECTOR_COMPETITORS["借贷协议"]


class TestIdentifyCompetitors:
    """测试识别竞品"""

    def test_identify_competitors_dex(self, analyzer):
        """测试 DEX 赛道竞品识别"""
        competitors = analyzer._identify_competitors("DEX", "UNI")
        assert isinstance(competitors, list)
        assert len(competitors) <= 5
        assert "UNI" not in competitors  # 不包含自身
        assert any(c in ["CAKE", "SUSHI", "CRV"] for c in competitors)

    def test_identify_competitors_lending(self, analyzer):
        """测试借贷协议赛道竞品识别"""
        competitors = analyzer._identify_competitors("借贷协议", "AAVE")
        assert isinstance(competitors, list)
        assert "AAVE" not in competitors
        assert any(c in ["COMP", "MKR"] for c in competitors)

    def test_identify_competitors_case_insensitive(self, analyzer):
        """测试类别名称大小写不敏感"""
        competitors1 = analyzer._identify_competitors("dex", "UNI")
        competitors2 = analyzer._identify_competitors("DEX", "UNI")
        assert competitors1 == competitors2

    def test_identify_competitors_category_mapping(self, analyzer):
        """测试类别名称映射"""
        competitors = analyzer._identify_competitors("decentralized exchange", "UNI")
        assert len(competitors) > 0  # 应该能识别为 DEX

    def test_identify_competitors_unknown_category(self, analyzer):
        """测试未知类别"""
        competitors = analyzer._identify_competitors("Unknown Category", "TEST")
        assert isinstance(competitors, list)
        assert len(competitors) == 0

    def test_identify_competitors_max_five(self, analyzer):
        """测试最多返回5个竞品"""
        competitors = analyzer._identify_competitors("DEX", "UNI")
        assert len(competitors) <= 5


class TestExtractCompetitorData:
    """测试提取竞品数据"""

    def test_extract_competitor_data_complete(self, analyzer, sample_aggregated_data):
        """测试提取完整竞品数据"""
        competitors = analyzer._extract_competitor_data(sample_aggregated_data)

        assert len(competitors) == 3
        assert competitors[0]["name"] == "PancakeSwap"
        assert competitors[0]["symbol"] == "CAKE"
        assert competitors[0]["market_cap"] == 800000000
        assert competitors[0]["tvl"] == 1500000000

    def test_extract_competitor_data_missing_competitors(self, analyzer):
        """测试缺少竞品数据"""
        data = {"symbol": "TEST"}
        competitors = analyzer._extract_competitor_data(data)
        assert isinstance(competitors, list)
        assert len(competitors) == 0

    def test_extract_competitor_data_missing_fields(self, analyzer):
        """测试竞品缺少部分字段"""
        data = {
            "competitors": [
                {"name": "Test1", "market_cap": 1000000}
                # 缺少其他字段
            ]
        }
        competitors = analyzer._extract_competitor_data(data)
        assert len(competitors) == 1
        assert competitors[0]["symbol"] == ""  # 默认值
        assert competitors[0]["tvl"] == 0


class TestFormatCompetitorsData:
    """测试格式化竞品数据"""

    def test_format_competitors_data_complete(self, analyzer):
        """测试格式化完整竞品数据"""
        competitors = [
            {
                "name": "PancakeSwap",
                "symbol": "CAKE",
                "market_cap": 800000000,
                "tvl": 1500000000,
                "active_users_24h": 80000,
                "volume_24h": 400000000,
                "protocol_revenue_30d": 15000000
            }
        ]
        formatted = analyzer._format_competitors_data(competitors)

        assert "PancakeSwap" in formatted
        assert "CAKE" in formatted
        assert "800M" in formatted  # 市值
        assert "1.5B" in formatted  # TVL

    def test_format_competitors_data_empty(self, analyzer):
        """测试格式化空竞品列表"""
        formatted = analyzer._format_competitors_data([])
        assert formatted == "暂无竞品数据"

    def test_format_competitors_data_multiple(self, analyzer):
        """测试格式化多个竞品"""
        competitors = [
            {"name": "Comp1", "symbol": "C1", "market_cap": 1000000000},
            {"name": "Comp2", "symbol": "C2", "market_cap": 2000000000}
        ]
        formatted = analyzer._format_competitors_data(competitors)

        assert "竞品1" in formatted
        assert "竞品2" in formatted
        assert "Comp1" in formatted
        assert "Comp2" in formatted


class TestBuildComparisonTable:
    """测试构建对比表格"""

    def test_build_comparison_table_complete(self, analyzer):
        """测试构建完整对比表格"""
        target_data = {
            "symbol": "UNI",
            "market_cap": 4500000000,
            "tvl": 3200000000,
            "active_users_24h": 150000,
            "volume_24h": 1200000000,
            "protocol_revenue_30d": 45000000
        }
        competitors = [
            {
                "name": "CAKE",
                "market_cap": 800000000,
                "tvl": 1500000000,
                "active_users_24h": 80000,
                "volume_24h": 400000000,
                "protocol_revenue_30d": 15000000
            }
        ]

        table = analyzer._build_comparison_table(target_data, competitors)

        assert "metrics" in table
        assert "target_project" in table
        assert "competitors" in table
        assert len(table["metrics"]) == 5
        assert table["target_project"]["name"] == "UNI"
        assert len(table["target_project"]["values"]) == 5
        assert len(table["competitors"]) == 1

    def test_build_comparison_table_missing_data(self, analyzer):
        """测试缺失数据的对比表格"""
        target_data = {"symbol": "TEST"}
        competitors = []

        table = analyzer._build_comparison_table(target_data, competitors)

        assert table["target_project"]["values"][0] == 0  # market_cap
        assert len(table["competitors"]) == 0


class TestCalculateValuationMultiples:
    """测试计算估值倍数"""

    def test_calculate_valuation_multiples_complete(self, analyzer):
        """测试计算完整估值倍数"""
        target_data = {
            "market_cap": 4500000000,
            "tvl": 3200000000,
            "protocol_revenue_30d": 45000000
        }
        competitors = [
            {
                "market_cap": 800000000,
                "tvl": 1500000000,
                "protocol_revenue_30d": 15000000
            },
            {
                "market_cap": 300000000,
                "tvl": 600000000,
                "protocol_revenue_30d": 8000000
            }
        ]

        result = analyzer._calculate_valuation_multiples(target_data, competitors)

        assert "target_project" in result
        assert "sector_median" in result
        assert "valuation_assessment" in result
        assert "rationale" in result

        # 检查目标项目倍数
        target = result["target_project"]
        assert target["ps_ratio"] > 0
        assert target["fdv_to_revenue"] > 0
        assert target["fdv_to_tvl"] > 0

        # 检查赛道中位数
        sector = result["sector_median"]
        assert sector["ps_ratio"] > 0

    def test_calculate_valuation_multiples_zero_revenue(self, analyzer):
        """测试收入为0的估值倍数"""
        target_data = {
            "market_cap": 1000000000,
            "tvl": 500000000,
            "protocol_revenue_30d": 0
        }
        competitors = []

        result = analyzer._calculate_valuation_multiples(target_data, competitors)

        assert result["target_project"]["ps_ratio"] == 0
        assert result["target_project"]["fdv_to_revenue"] == 0

    def test_calculate_valuation_multiples_zero_tvl(self, analyzer):
        """测试 TVL 为0的估值倍数"""
        target_data = {
            "market_cap": 1000000000,
            "tvl": 0,
            "protocol_revenue_30d": 10000000
        }
        competitors = []

        result = analyzer._calculate_valuation_multiples(target_data, competitors)

        assert result["target_project"]["fdv_to_tvl"] == 0

    def test_calculate_valuation_multiples_assessment(self, analyzer):
        """测试估值评估"""
        # 被低估场景
        target_data = {
            "market_cap": 1000000000,
            "tvl": 500000000,
            "protocol_revenue_30d": 50000000  # 高收入
        }
        competitors = [
            {
                "market_cap": 1000000000,
                "tvl": 500000000,
                "protocol_revenue_30d": 10000000  # 低收入
            }
        ]

        result = analyzer._calculate_valuation_multiples(target_data, competitors)

        # 目标项目的倍数应该低于赛道中位数
        assert result["valuation_assessment"] in ["被低估", "合理估值", "被高估", "数据不足"]


class TestMedian:
    """测试中位数计算"""

    def test_median_odd_count(self, analyzer):
        """测试奇数个元素的中位数"""
        values = [1, 3, 5, 7, 9]
        median = analyzer._median(values)
        assert median == 5

    def test_median_even_count(self, analyzer):
        """测试偶数个元素的中位数"""
        values = [1, 2, 3, 4]
        median = analyzer._median(values)
        assert median == 2.5

    def test_median_empty(self, analyzer):
        """测试空列表的中位数"""
        median = analyzer._median([])
        assert median == 0

    def test_median_single(self, analyzer):
        """测试单个元素的中位数"""
        median = analyzer._median([42])
        assert median == 42

    def test_median_unsorted(self, analyzer):
        """测试未排序列表的中位数"""
        values = [9, 1, 5, 3, 7]
        median = analyzer._median(values)
        assert median == 5


class TestFormatPrompt:
    """测试格式化 prompt"""

    def test_format_prompt_complete_data(self, analyzer, sample_aggregated_data):
        """测试完整数据的 prompt 格式化"""
        prompt = analyzer._format_prompt(sample_aggregated_data)

        assert "UNI" in prompt
        assert "Uniswap" in prompt
        assert "DEX" in prompt
        assert "4500000000" in prompt  # market_cap
        assert "PancakeSwap" in prompt  # 竞品

    def test_format_prompt_missing_data(self, analyzer):
        """测试缺失数据的 prompt 格式化"""
        data = {"symbol": "TEST"}
        prompt = analyzer._format_prompt(data)

        assert "TEST" in prompt
        assert "Unknown" in prompt


class TestOutputValidation:
    """测试输出验证"""

    def test_validate_output_valid(self, analyzer):
        """测试有效输出验证"""
        output = {
            "competitive_landscape": {
                "sector": "DEX",
                "market_size": "$15B",
                "growth_trend": "稳定增长",
                "key_trends": ["趋势1", "趋势2"],
                "competition_intensity": "激烈"
            },
            "competitors": [
                {"name": "Comp1", "symbol": "C1"},
                {"name": "Comp2", "symbol": "C2"}
            ],
            "comparison_table": {},
            "valuation_multiples": {
                "valuation_assessment": "被低估",
                "rationale": "估值低"
            },
            "competitive_advantages": {
                "moat_score": 8
            },
            "competitive_risks": {},
            "market_position": {
                "position_type": "领导者"
            },
            "summary": "总结"
        }

        is_valid, errors = analyzer._validate_output(output)
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_output_missing_required_fields(self, analyzer):
        """测试缺少必需字段"""
        output = {
            "competitive_landscape": {}
        }

        is_valid, errors = analyzer._validate_output(output)
        assert is_valid is False
        assert len(errors) > 0

    def test_validate_output_invalid_sector(self, analyzer):
        """测试无效 sector"""
        output = {
            "competitive_landscape": {
                "sector": "InvalidSector"
            },
            "competitors": [{"name": "C1"}, {"name": "C2"}],
            "comparison_table": {},
            "valuation_multiples": {"valuation_assessment": "被低估"},
            "competitive_advantages": {"moat_score": 5},
            "competitive_risks": {},
            "market_position": {"position_type": "领导者"},
            "summary": "test"
        }

        is_valid, errors = analyzer._validate_output(output)
        assert is_valid is False
        assert any("sector" in error for error in errors)

    def test_validate_output_invalid_competitors_count(self, analyzer):
        """测试竞品数量不在2-5范围"""
        output = {
            "competitive_landscape": {"sector": "DEX"},
            "competitors": [{"name": "Only1"}],  # 只有1个
            "comparison_table": {},
            "valuation_multiples": {"valuation_assessment": "被低估"},
            "competitive_advantages": {"moat_score": 5},
            "competitive_risks": {},
            "market_position": {"position_type": "领导者"},
            "summary": "test"
        }

        is_valid, errors = analyzer._validate_output(output)
        assert is_valid is False
        assert any("competitors" in error for error in errors)

    def test_validate_output_invalid_moat_score(self, analyzer):
        """测试无效 moat_score"""
        output = {
            "competitive_landscape": {"sector": "DEX"},
            "competitors": [{"name": "C1"}, {"name": "C2"}],
            "comparison_table": {},
            "valuation_multiples": {"valuation_assessment": "被低估"},
            "competitive_advantages": {"moat_score": 15},  # 超过10
            "competitive_risks": {},
            "market_position": {"position_type": "领导者"},
            "summary": "test"
        }

        is_valid, errors = analyzer._validate_output(output)
        assert is_valid is False
        assert any("moat_score" in error for error in errors)


class TestFixInvalidOutput:
    """测试修复无效输出"""

    def test_fix_invalid_output_missing_fields(self, analyzer):
        """测试修复缺少字段的输出"""
        invalid_output = {
            "competitive_landscape": {"sector": "DEX"}
        }

        fixed = analyzer._fix_invalid_output(invalid_output, ["Missing fields"])

        assert "competitors" in fixed
        assert "comparison_table" in fixed
        assert "valuation_multiples" in fixed
        assert "competitive_advantages" in fixed
        assert "competitive_risks" in fixed
        assert "market_position" in fixed
        assert "summary" in fixed

    def test_fix_invalid_output_invalid_moat_score(self, analyzer):
        """测试修复无效 moat_score"""
        invalid_output = {
            "competitive_advantages": {"moat_score": 15}
        }

        fixed = analyzer._fix_invalid_output(invalid_output, ["Invalid moat_score"])

        assert fixed["competitive_advantages"]["moat_score"] == 10  # 修正为10

    def test_fix_invalid_output_negative_moat_score(self, analyzer):
        """测试修复负数 moat_score"""
        invalid_output = {
            "competitive_advantages": {"moat_score": -5}
        }

        fixed = analyzer._fix_invalid_output(invalid_output, ["Invalid moat_score"])

        assert fixed["competitive_advantages"]["moat_score"] == 0


class TestErrorResponse:
    """测试错误响应"""

    def test_create_error_response(self, analyzer):
        """测试创建错误响应"""
        error_msg = "LLM 调用失败"
        response = analyzer._create_error_response(error_msg)

        assert response["error"] is True
        assert error_msg in response["message"]
        assert "competitive_landscape" in response
        assert "competitors" in response
        assert response["competitors"] == []
        assert response["valuation_multiples"]["valuation_assessment"] == "数据不足"


class TestAnalyze:
    """测试 analyze 主函数"""

    @pytest.mark.asyncio
    async def test_analyze_success(self, analyzer, sample_aggregated_data):
        """测试成功分析"""
        mock_response = {
            "competitive_landscape": {
                "sector": "DEX",
                "market_size": "$15B",
                "growth_trend": "稳定增长",
                "key_trends": ["Layer2扩展", "聚合器兴起"],
                "competition_intensity": "激烈"
            },
            "competitors": [
                {"name": "PancakeSwap", "symbol": "CAKE"},
                {"name": "SushiSwap", "symbol": "SUSHI"}
            ],
            "comparison_table": {
                "metrics": ["市值", "TVL"],
                "target_project": {"name": "UNI", "values": [4500000000, 3200000000]},
                "competitors": []
            },
            "valuation_multiples": {
                "target_project": {"ps_ratio": 8.3},
                "sector_median": {"ps_ratio": 12.0},
                "valuation_assessment": "被低估",
                "rationale": "估值倍数低于赛道中位数"
            },
            "competitive_advantages": {
                "strengths": ["最强品牌", "最深流动性"],
                "moat_score": 9,
                "moat_types": ["网络效应", "品牌优势"]
            },
            "competitive_risks": {
                "threats": ["Layer2竞争"],
                "risk_level": "中"
            },
            "market_position": {
                "ranking": "第1名",
                "position_type": "领导者",
                "market_share_trend": "稳定增长",
                "strategic_recommendation": "积极持有"
            },
            "summary": "Uniswap是DEX赛道的领导者"
        }

        with patch.object(analyzer, '_call_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_response

            result = await analyzer.analyze(sample_aggregated_data)

            assert result["error"] is False
            assert result["competitive_landscape"]["sector"] == "DEX"
            assert result["market_position"]["position_type"] == "领导者"

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
            "competitive_landscape": {"sector": "DEX"}
            # Missing other required fields
        }

        with patch.object(analyzer, '_call_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = invalid_response

            result = await analyzer.analyze(sample_aggregated_data)

            assert result["error"] is False
            assert "competitors" in result
            assert "valuation_multiples" in result
            assert "market_position" in result
