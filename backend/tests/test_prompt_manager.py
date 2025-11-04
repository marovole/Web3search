"""
单元测试: Prompt Manager
测试YAML模板加载、渲染、缓存和验证功能
"""
import pytest
from pathlib import Path
from app.services.prompt_manager import PromptManager


class TestPromptManager:
    """测试PromptManager类"""

    @pytest.fixture
    def prompt_manager(self):
        """创建PromptManager实例"""
        return PromptManager()

    def test_load_tldr_template(self, prompt_manager):
        """测试加载TL;DR模板"""
        metadata = prompt_manager.get_template_metadata("tldr")

        assert metadata["name"] == "TL;DR Generator"
        assert metadata["version"] == "1.0.0"
        assert metadata["model"] == "qwen/qwen-2.5-72b-instruct:free"
        assert metadata["temperature"] == 0.7
        assert metadata["max_tokens"] == 500

    def test_load_fundamental_analysis_template(self, prompt_manager):
        """测试加载基本面分析模板"""
        metadata = prompt_manager.get_template_metadata("fundamental_analysis")

        assert metadata["name"] == "Fundamental Analysis"
        assert metadata["version"] == "1.0.0"
        assert metadata["model"] == "qwen/qwen-2.5-72b-instruct:free"

    def test_load_technical_analysis_template(self, prompt_manager):
        """测试加载技术分析模板"""
        metadata = prompt_manager.get_template_metadata("technical_analysis")

        assert metadata["name"] == "Technical Analysis"
        assert metadata["version"] == "1.0.0"
        assert metadata["model"] == "deepseek/deepseek-chat"

    def test_load_competitor_analysis_template(self, prompt_manager):
        """测试加载竞品分析模板"""
        metadata = prompt_manager.get_template_metadata("competitor_analysis")

        assert metadata["name"] == "Competitor Analysis"
        assert metadata["version"] == "1.0.0"

    def test_load_risk_assessment_template(self, prompt_manager):
        """测试加载风险评估模板"""
        metadata = prompt_manager.get_template_metadata("risk_assessment")

        assert metadata["name"] == "Risk Assessment"
        assert metadata["version"] == "1.0.0"

    def test_render_tldr_prompt(self, prompt_manager):
        """测试渲染TL;DR prompt"""
        rendered = prompt_manager.get_tldr_prompt(
            project_name="Ethereum",
            price=3500,
            market_cap="420B",
            volume_24h="15B",
            price_change_24h=2.5,
            price_change_7d=8.3,
            price_change_30d=15.0,
            active_addresses="500K",
            daily_transactions="1.2M",
            twitter_sentiment="积极 (75%)",
            reddit_sentiment="积极 (70%)"
        )

        assert "Ethereum" in rendered
        assert "3500" in rendered
        assert "专业的加密货币分析师" in rendered
        assert "Examples" in rendered

    def test_render_fundamental_analysis_prompt(self, prompt_manager):
        """测试渲染基本面分析prompt"""
        rendered = prompt_manager.get_fundamental_analysis_prompt(
            project_name="Uniswap",
            project_type="DEX",
            launch_date="2020-09",
            website="https://uniswap.org",
            symbol="UNI",
            total_supply="1B",
            circulating_supply="620M",
            price=6.5,
            fdv="6.5B",
            tvl="4.5B",
            revenue_30d="42M",
            active_users_30d="250K",
            team_info="Hayden Adams等",
            investors="a16z, Paradigm"
        )

        assert "Uniswap" in rendered
        assert "DEX" in rendered
        assert "基本面分析专家" in rendered

    def test_render_technical_analysis_prompt(self, prompt_manager):
        """测试渲染技术分析prompt"""
        rendered = prompt_manager.get_technical_analysis_prompt(
            current_price=45000,
            high_24h=46000,
            low_24h=44000,
            high_7d=48000,
            low_7d=43000,
            high_30d=52000,
            low_30d=40000,
            rsi_14=68,
            macd_value="正值",
            macd_signal="金叉",
            ma_50=43500,
            ma_200=42000,
            volume_24h="25B",
            volume_7d_avg="22B"
        )

        assert "45000" in rendered
        assert "技术分析师" in rendered

    def test_get_template_with_config(self, prompt_manager):
        """测试获取模板和配置"""
        result = prompt_manager.get_template_with_config(
            "tldr",
            project_name="Bitcoin",
            price=50000,
            market_cap="1T",
            volume_24h="30B",
            price_change_24h=3.2,
            price_change_7d=10.5,
            price_change_30d=20.0,
            active_addresses="800K",
            daily_transactions="300K",
            twitter_sentiment="积极",
            reddit_sentiment="中性"
        )

        assert "prompt" in result
        assert "model" in result
        assert "temperature" in result
        assert "max_tokens" in result
        assert "Bitcoin" in result["prompt"]
        assert result["model"] == "qwen/qwen-2.5-72b-instruct:free"

    def test_template_caching(self, prompt_manager):
        """测试模板缓存机制"""
        # 首次加载
        metadata1 = prompt_manager.get_template_metadata("tldr")

        # 二次加载（应该从缓存读取）
        metadata2 = prompt_manager.get_template_metadata("tldr")

        assert metadata1 == metadata2
        assert len(prompt_manager._cache) > 0

    def test_cache_reload(self, prompt_manager):
        """测试缓存清空"""
        # 加载一些模板
        prompt_manager.get_template_metadata("tldr")
        prompt_manager.get_template_metadata("fundamental_analysis")

        assert len(prompt_manager._cache) > 0

        # 清空缓存
        prompt_manager.reload_cache()

        assert len(prompt_manager._cache) == 0

    def test_list_available_prompts(self, prompt_manager):
        """测试列出可用的prompt模板"""
        available = prompt_manager.list_available_prompts()

        assert "tldr" in available
        assert "fundamental_analysis" in available
        assert "technical_analysis" in available
        assert "competitor_analysis" in available
        assert "risk_assessment" in available

        # 检查元数据
        assert available["tldr"]["version"] == "1.0.0"
        assert available["tldr"]["name"] == "TL;DR Generator"

    def test_template_validation_missing_fields(self, prompt_manager):
        """测试模板验证 - 缺少必需字段"""
        invalid_data = {
            "name": "Test Template",
            # 缺少 "model" 和 "system" 字段
        }

        with pytest.raises(ValueError, match="模板缺少必需字段"):
            prompt_manager._validate_template(invalid_data)

    def test_template_validation_missing_user_template(self, prompt_manager):
        """测试模板验证 - 缺少用户模板字段"""
        invalid_data = {
            "name": "Test Template",
            "model": "test-model",
            "system": "Test system prompt",
            # 缺少 "user_template" 或 "user_prompt_template"
        }

        with pytest.raises(ValueError, match="必须包含 'user_template' 或 'user_prompt_template'"):
            prompt_manager._validate_template(invalid_data)

    def test_legacy_methods(self, prompt_manager):
        """测试向后兼容的legacy方法"""
        # 测试 get_technical_prompt 映射到 get_technical_analysis_prompt
        prompt1 = prompt_manager.get_technical_prompt(
            current_price=50000,
            high_24h=51000,
            low_24h=49000,
            high_7d=52000,
            low_7d=48000,
            high_30d=55000,
            low_30d=45000,
            rsi_14=65,
            macd_value="正",
            macd_signal="金叉",
            ma_50=48000,
            ma_200=46000,
            volume_24h="20B",
            volume_7d_avg="18B"
        )

        prompt2 = prompt_manager.get_technical_analysis_prompt(
            current_price=50000,
            high_24h=51000,
            low_24h=49000,
            high_7d=52000,
            low_7d=48000,
            high_30d=55000,
            low_30d=45000,
            rsi_14=65,
            macd_value="正",
            macd_signal="金叉",
            ma_50=48000,
            ma_200=46000,
            volume_24h="20B",
            volume_7d_avg="18B"
        )

        assert prompt1 == prompt2

    def test_nonexistent_template(self, prompt_manager):
        """测试加载不存在的模板"""
        with pytest.raises(FileNotFoundError):
            prompt_manager.get_template_metadata("nonexistent_template")

    def test_render_with_missing_variables(self, prompt_manager):
        """测试使用缺少变量渲染模板（Jinja2应该保留原样或报错）"""
        # Jinja2默认行为：缺少变量会显示为空字符串
        rendered = prompt_manager.get_tldr_prompt(
            project_name="Test Project"
            # 缺少其他必需变量
        )

        # 至少应该包含项目名称
        assert "Test Project" in rendered
