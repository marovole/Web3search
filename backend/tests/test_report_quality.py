"""
报告质量验证测试
测试报告生成和质量评分功能
"""
import pytest
from app.services.report.quality_validator import (
    quality_validator,
    validate_markdown_syntax,
    estimate_reading_time
)


# ================================
# 测试数据
# ================================

SAMPLE_DEEP_RESEARCH_REPORT = """
# BTC 深度研究报告

生成时间：2025-01-25 10:30

---

## TL;DR

**一句话总结**：比特币是第一大加密货币，当前处于上升趋势，机构采用持续增加。

**看涨理由**：
- 机构持续买入，ETF 流入强劲
- 链上活跃地址增长 20%
- 减半效应预期

**看跌理由**：
- 短期超买，RSI 接近 70
- 宏观经济不确定性
- 监管风险

**风险等级**：中

---

## 多时间周期分析

### 7天表现
- 价格变化：+5.2%
- 成交量变化：+12.3%
- 市值：$1.2T

### 30天表现
- 价格变化：+18.5%
- 成交量变化：+8.7%
- 创新高次数：3次

---

## 社交情绪分析

### Twitter
- 提及次数：1,234,567
- 情绪分数：75/100（积极）
- KOL观点：看涨为主

### Reddit
- 活跃讨论：5,678 个帖子
- 情绪：中性偏积极
- 热门话题：ETF、减半

---

## 技术分析

**当前价格**：$52,345

**支撑位**：
- $50,000（强支撑）
- $48,500（中等）

**阻力位**：
- $55,000（强阻力）
- $58,000（历史高点）

**技术指标**：
- RSI: 68（接近超买）
- MACD: 看涨
- MA50 > MA200：金叉信号

---

## 链上数据分析

**活跃地址**：1,234,567（+20% MoM）

**交易量**：$28.5B（24h）

**持币分布**：
- 巨鲸（>1000 BTC）：2.3%
- 大户（100-1000 BTC）：15.2%
- 散户（<100 BTC）：82.5%

**资金流向**：净流入 $156M

---

## 竞品对比

| 项目 | 市值 | TVL | 24h成交量 |
|------|------|-----|----------|
| BTC | $1.2T | - | $28.5B |
| ETH | $450B | $55B | $15.2B |

---

## 代币经济学

**总供应量**：21,000,000 BTC

**流通供应**：19,500,000 BTC（92.8%）

**通胀率**：1.7%/年（递减）

**下次减半**：2024年4月

---

## 风险评估

### 监管风险（中）
- 多国监管政策不确定
- SEC 对 ETF 态度谨慎

### 技术风险（低）
- 网络算力持续增长
- 安全性经过验证

### 市场风险（中）
- 短期价格波动大
- 宏观经济影响

---

## 投资结论

**综合评分**：85/100

**投资建议**：中性偏看涨

**适合投资者**：中长期持有者

**催化剂**：
- ETF 持续流入
- 2024年减半
- 机构采用增加

**注意事项**：
- 控制仓位，分批建仓
- 设置止损位
- 关注宏观环境变化

---

**免责声明**：本报告由 AI 自动生成，仅供参考，不构成投资建议。

**数据来源**：CoinGecko, Twitter, Reddit, Etherscan

**生成时间**：2025-01-25 10:30:00
"""

SAMPLE_SHORT_REPORT = """
# BTC 快速分析

## TL;DR
比特币当前价格 $52,345，短期看涨。

## 技术分析
RSI: 68, MACD: 看涨

## 结论
建议持有。
"""


# ================================
# 测试用例
# ================================

class TestReportQualityValidator:
    """测试报告质量验证器"""

    def test_validate_deep_research_report(self):
        """测试深度研究报告验证"""
        score, details = quality_validator.validate_report(
            markdown_content=SAMPLE_DEEP_RESEARCH_REPORT,
            data_sources=["CoinGecko", "Twitter", "Reddit", "Etherscan"],
            report_type="deep_research",
            metadata={"generation_time_seconds": 28.5}
        )

        # 应该得到较高分数
        assert score >= 70, f"Expected score >= 70, got {score}"
        assert details["grade"] in ["A", "B", "C"], f"Expected grade A/B/C, got {details['grade']}"

        # 检查评分细节
        assert "completeness" in details["breakdown"]
        assert "data_quality" in details["breakdown"]
        assert "structure" in details["breakdown"]
        assert "depth" in details["breakdown"]

        print(f"\n✅ Deep Research Report Score: {score}/100")
        print(f"   Grade: {details['grade']}")
        print(f"   Breakdown: {details['breakdown']}")
        if details["issues"]:
            print(f"   Issues: {details['issues']}")
        if details["recommendations"]:
            print(f"   Recommendations: {details['recommendations']}")

    def test_validate_short_report(self):
        """测试短报告验证"""
        score, details = quality_validator.validate_report(
            markdown_content=SAMPLE_SHORT_REPORT,
            data_sources=["CoinGecko"],
            report_type="quick_chat",
            metadata={"generation_time_seconds": 5.2}
        )

        # Quick Chat 报告标准较低
        assert score >= 40, f"Expected score >= 40, got {score}"

        print(f"\n✅ Quick Chat Report Score: {score}/100")
        print(f"   Grade: {details['grade']}")

    def test_validate_incomplete_report(self):
        """测试不完整报告"""
        incomplete_report = "# Test\n\nSome content."

        score, details = quality_validator.validate_report(
            markdown_content=incomplete_report,
            data_sources=[],
            report_type="deep_research",
            metadata=None
        )

        # 应该得到较低分数
        assert score < 50, f"Expected score < 50 for incomplete report, got {score}"
        assert len(details["issues"]) > 0, "Expected issues for incomplete report"

        print(f"\n⚠️  Incomplete Report Score: {score}/100")
        print(f"   Issues: {details['issues']}")

    def test_completeness_validation(self):
        """测试内容完整性验证"""
        score = quality_validator._validate_completeness(
            markdown_content=SAMPLE_DEEP_RESEARCH_REPORT,
            sections=None,
            report_type="deep_research"
        )

        # 完整报告应该得到高分
        assert score >= 30, f"Expected completeness score >= 30, got {score}"

        print(f"\n✅ Completeness Score: {score}/40")

    def test_data_quality_validation(self):
        """测试数据质量验证"""
        score = quality_validator._validate_data_quality(
            data_sources=["CoinGecko", "Twitter", "Reddit", "Etherscan", "CryptoPanic"],
            metadata={"generation_time_seconds": 28.5}
        )

        # 5个数据源 + 合理生成时间应该得到高分
        assert score >= 25, f"Expected data quality score >= 25, got {score}"

        print(f"\n✅ Data Quality Score: {score}/30")

    def test_structure_validation(self):
        """测试结构规范验证"""
        score = quality_validator._validate_structure(
            markdown_content=SAMPLE_DEEP_RESEARCH_REPORT
        )

        # 规范的 Markdown 应该得到高分
        assert score >= 15, f"Expected structure score >= 15, got {score}"

        print(f"\n✅ Structure Score: {score}/20")

    def test_depth_validation(self):
        """测试内容深度验证"""
        score = quality_validator._validate_depth(
            markdown_content=SAMPLE_DEEP_RESEARCH_REPORT,
            sections=None
        )

        # 详细报告应该得到较高深度分
        assert score >= 7, f"Expected depth score >= 7, got {score}"

        print(f"\n✅ Depth Score: {score}/10")


class TestMarkdownValidation:
    """测试 Markdown 语法验证"""

    def test_valid_markdown(self):
        """测试有效的 Markdown"""
        result = validate_markdown_syntax(SAMPLE_DEEP_RESEARCH_REPORT)

        assert result["valid"] == True
        assert len(result["errors"]) == 0

        print(f"\n✅ Markdown Syntax: Valid")

    def test_invalid_markdown_unclosed_bold(self):
        """测试未闭合的粗体"""
        invalid_md = "# Title\n\n**Unclosed bold\n\nSome text."

        result = validate_markdown_syntax(invalid_md)

        assert result["valid"] == False
        assert len(result["errors"]) > 0
        assert any("粗体" in err for err in result["errors"])

        print(f"\n⚠️  Invalid Markdown (unclosed bold)")
        print(f"   Errors: {result['errors']}")

    def test_invalid_markdown_unclosed_code_block(self):
        """测试未闭合的代码块"""
        invalid_md = "# Title\n\n```python\ncode\n\nSome text."

        result = validate_markdown_syntax(invalid_md)

        assert result["valid"] == False
        assert len(result["errors"]) > 0
        assert any("代码块" in err for err in result["errors"])

        print(f"\n⚠️  Invalid Markdown (unclosed code block)")
        print(f"   Errors: {result['errors']}")


class TestReadingTime:
    """测试阅读时间估算"""

    def test_estimate_reading_time(self):
        """测试阅读时间估算"""
        reading_time = estimate_reading_time(SAMPLE_DEEP_RESEARCH_REPORT)

        # 应该在合理范围内
        assert reading_time >= 2, f"Expected reading time >= 2 min, got {reading_time}"
        assert reading_time <= 10, f"Expected reading time <= 10 min, got {reading_time}"

        print(f"\n✅ Estimated Reading Time: {reading_time} minutes")


# ================================
# 运行测试
# ================================

if __name__ == "__main__":
    # 运行所有测试
    pytest.main([__file__, "-v", "-s"])
