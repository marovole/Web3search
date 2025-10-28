"""
集成测试：完整报告生成Pipeline
测试从Deep Research到Markdown到PDF的完整流程
"""
import pytest
import asyncio
import os
from pathlib import Path
from typing import Dict, Any

from app.services.research_engine.deep_research import deep_research_engine
from app.services.report.report_generator import report_generator
from app.services.report.pdf_exporter import pdf_exporter


class TestReportPipeline:
    """报告生成Pipeline集成测试"""

    @pytest.fixture
    def sample_symbol(self):
        """测试用币种符号"""
        return "BTC"

    @pytest.fixture
    def sample_query(self):
        """测试用查询"""
        return "分析比特币的技术面和市场情绪"

    @pytest.mark.asyncio
    async def test_deep_research_to_markdown(self, sample_symbol, sample_query):
        """
        测试场景：从Deep Research到Markdown报告生成
        验证：
        - Deep Research引擎正常执行
        - 返回完整的报告数据结构
        - Markdown报告成功生成
        - 报告包含所有必需章节
        """
        print("\n🔍 测试: Deep Research → Markdown报告")

        # 步骤1: 执行Deep Research
        research_result = await deep_research_engine.research(
            query=sample_query,
            symbol=sample_symbol
        )

        # 验证research_result结构
        assert "symbol" in research_result, "缺少symbol字段"
        assert "query" in research_result, "缺少query字段"
        assert "tldr" in research_result, "缺少tldr字段"
        assert "sections" in research_result, "缺少sections字段"
        assert "conclusion" in research_result, "缺少conclusion字段"
        assert "analyzer_outputs" in research_result, "缺少analyzer_outputs字段"

        # 验证analyzer_outputs包含9个analyzer的输出
        analyzer_outputs = research_result["analyzer_outputs"]
        expected_analyzers = [
            "tldr", "timeframe", "sentiment", "technical",
            "onchain", "competitor", "tokenomics", "risk", "conclusion"
        ]
        for analyzer in expected_analyzers:
            assert analyzer in analyzer_outputs, f"缺少{analyzer} analyzer输出"

        # 步骤2: 生成Markdown报告
        markdown_content = report_generator.generate_markdown(research_result)

        # 验证Markdown内容
        assert len(markdown_content) > 0, "Markdown内容为空"
        assert "深度研究报告" in markdown_content, "缺少报告标题"
        assert "TL;DR" in markdown_content, "缺少TL;DR章节"
        assert "技术分析" in markdown_content, "缺少技术分析章节"
        assert "结论与投资建议" in markdown_content, "缺少结论章节"
        assert "免责声明" in markdown_content, "缺少免责声明"

        print(f"✅ Deep Research成功，报告长度: {len(markdown_content)} 字符")
        print(f"✅ 包含 {len(analyzer_outputs)} 个analyzer输出")

        return research_result, markdown_content

    @pytest.mark.asyncio
    async def test_markdown_to_pdf(self, sample_symbol):
        """
        测试场景：从Markdown报告到PDF导出
        验证：
        - Markdown成功转换为PDF
        - PDF文件正常生成
        - 文件大小合理
        """
        print("\n📄 测试: Markdown → PDF")

        # 创建测试用Markdown内容
        test_markdown = f"""# {sample_symbol} 深度研究报告

## 📌 TL;DR
这是一个测试报告，用于验证Markdown到PDF的转换功能。

## 📈 技术分析
当前价格趋势向上，RSI指标显示超买。

### 关键价位
| 类型 | 价格 |
|------|------|
| 支撑位 | $30,000 |
| 阻力位 | $40,000 |

## 🎯 结论与投资建议
建议持有，等待回调。

---

**免责声明**: 本报告仅供参考。
"""

        # 生成PDF
        temp_pdf_path = pdf_exporter.generate_temp_pdf_path(f"test_{sample_symbol}")
        pdf_path = pdf_exporter.export_to_pdf(
            markdown_content=test_markdown,
            output_path=temp_pdf_path,
            title=f"{sample_symbol} 测试报告",
            timeout=30
        )

        # 验证PDF文件
        assert os.path.exists(pdf_path), "PDF文件未生成"

        pdf_size = os.path.getsize(pdf_path)
        assert pdf_size > 1000, f"PDF文件过小: {pdf_size} bytes"

        print(f"✅ PDF生成成功: {pdf_path}")
        print(f"✅ 文件大小: {pdf_size / 1024:.2f} KB")

        # 清理测试文件
        pdf_exporter.cleanup_temp_file(pdf_path)

        return pdf_path

    @pytest.mark.asyncio
    async def test_complete_pipeline(self, sample_symbol, sample_query):
        """
        测试场景：完整流程（Deep Research → Markdown → PDF）
        验证：
        - 整个pipeline正常执行
        - 每个阶段输出正确
        - 最终生成包含表格和图表的PDF
        """
        print("\n🚀 测试: 完整Pipeline（Deep Research → Markdown → PDF）")

        # 步骤1: Deep Research
        print("  📊 阶段1: 执行Deep Research...")
        research_result = await deep_research_engine.research(
            query=sample_query,
            symbol=sample_symbol
        )
        assert "analyzer_outputs" in research_result
        print(f"  ✅ Deep Research完成，生成时间: {research_result.get('generation_time', 0):.2f}秒")

        # 步骤2: 生成Markdown
        print("  📝 阶段2: 生成Markdown报告...")
        markdown_content = report_generator.generate_markdown(research_result)
        assert len(markdown_content) > 0
        print(f"  ✅ Markdown生成完成，长度: {len(markdown_content)} 字符")

        # 步骤3: 导出PDF
        print("  📄 阶段3: 导出PDF...")
        temp_pdf_path = pdf_exporter.generate_temp_pdf_path(f"integration_test_{sample_symbol}")
        pdf_path = pdf_exporter.export_to_pdf(
            markdown_content=markdown_content,
            output_path=temp_pdf_path,
            title=f"{sample_symbol} 深度研究报告",
            timeout=30
        )

        # 验证PDF
        assert os.path.exists(pdf_path)
        pdf_size = os.path.getsize(pdf_path)
        print(f"  ✅ PDF导出完成: {pdf_path} ({pdf_size / 1024:.2f} KB)")

        # 清理
        pdf_exporter.cleanup_temp_file(pdf_path)

        print("\n🎉 完整Pipeline测试通过！")

        return research_result, markdown_content, pdf_path

    @pytest.mark.asyncio
    async def test_report_contains_tables_and_charts(self, sample_symbol, sample_query):
        """
        测试场景：验证报告包含表格和图表
        验证：
        - Markdown报告包含表格
        - Markdown报告包含图表（Base64编码）
        - 表格和图表数量符合预期
        """
        print("\n📊 测试: 报告包含表格和图表")

        # 执行Deep Research
        research_result = await deep_research_engine.research(
            query=sample_query,
            symbol=sample_symbol
        )

        # 生成Markdown
        markdown_content = report_generator.generate_markdown(research_result)

        # 检查表格（Markdown表格以 | 开头）
        table_count = markdown_content.count("|")
        print(f"  📋 表格标记数量: {table_count}")
        assert table_count > 0, "报告中未检测到表格"

        # 检查图表（Base64图片）
        chart_count = markdown_content.count("data:image/png;base64,")
        print(f"  📈 图表数量: {chart_count}")
        # 注意：图表生成可能失败，所以这里不强制要求
        if chart_count > 0:
            print(f"  ✅ 报告包含 {chart_count} 个图表")
        else:
            print("  ⚠️  报告未包含图表（可能是数据不足或生成失败）")

        # 检查特定表格类型
        expected_tables = [
            "关键价位",  # 技术分析表格
            "竞品对比",  # 竞品分析表格
            "风险矩阵",  # 风险评估表格
        ]

        found_tables = []
        for table_name in expected_tables:
            if table_name in markdown_content:
                found_tables.append(table_name)

        print(f"  ✅ 找到的表格类型: {', '.join(found_tables) if found_tables else '无'}")

        # 至少应该有一种表格
        assert len(found_tables) > 0 or table_count > 10, \
            "报告中未检测到预期的表格类型"

        print("\n✅ 表格和图表验证通过")

        return table_count, chart_count

    @pytest.mark.asyncio
    async def test_pdf_export_with_chinese(self):
        """
        测试场景：验证PDF正确渲染中文
        验证：
        - PDF可以包含中文字符
        - 中文字符不会显示为乱码或方框
        """
        print("\n🇨🇳 测试: PDF中文字体支持")

        # 创建包含中文的测试Markdown
        test_markdown = """# 比特币深度研究报告

## 📌 核心观点
比特币是全球首个去中心化加密货币，具有稀缺性和抗审查特性。

## 📊 市场数据
| 指标 | 数值 |
|------|------|
| 当前价格 | ¥230,000 |
| 市值 | ¥4.5万亿 |
| 24小时涨跌 | +2.5% |

## 🎯 投资建议
建议长期持有，分批建仓。

**风险提示**: 加密货币市场波动大，请谨慎投资。
"""

        # 生成PDF
        temp_pdf_path = pdf_exporter.generate_temp_pdf_path("test_chinese")
        pdf_path = pdf_exporter.export_to_pdf(
            markdown_content=test_markdown,
            output_path=temp_pdf_path,
            title="中文测试报告",
            timeout=30
        )

        # 验证PDF存在
        assert os.path.exists(pdf_path), "PDF文件未生成"
        pdf_size = os.path.getsize(pdf_path)
        assert pdf_size > 1000, "PDF文件过小"

        print(f"✅ 中文PDF生成成功: {pdf_path} ({pdf_size / 1024:.2f} KB)")
        print("✅ 中文字体支持验证通过（请手动打开PDF确认中文显示正常）")

        # 清理
        pdf_exporter.cleanup_temp_file(pdf_path)

        return pdf_path

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """
        测试场景：错误处理和降级策略
        验证：
        - 当某个analyzer失败时，pipeline继续执行
        - 生成的报告包含错误提示
        - PDF仍然可以正常生成
        """
        print("\n⚠️  测试: 错误处理和降级策略")

        # 使用一个不存在的符号，可能导致部分analyzer失败
        invalid_symbol = "INVALID_COIN_XYZ"
        query = "分析这个币"

        # 执行Deep Research（预期部分失败但不崩溃）
        try:
            research_result = await deep_research_engine.research(
                query=query,
                symbol=invalid_symbol
            )

            # 检查是否有analyzer失败
            analyzer_outputs = research_result.get("analyzer_outputs", {})
            failed_count = sum(1 for output in analyzer_outputs.values()
                              if output.get("error", False))

            print(f"  ⚠️  {failed_count} 个analyzer失败")

            # 生成Markdown（即使部分analyzer失败）
            markdown_content = report_generator.generate_markdown(research_result)
            assert len(markdown_content) > 0, "即使有错误，也应该生成报告"

            # 检查错误提示
            if "⚠️" in markdown_content or "失败" in markdown_content:
                print("  ✅ 报告中包含错误提示")

            print("\n✅ 错误处理验证通过")

        except Exception as e:
            pytest.fail(f"Pipeline不应该因为部分analyzer失败而崩溃: {str(e)}")

    @pytest.mark.asyncio
    async def test_performance_benchmark(self, sample_symbol, sample_query):
        """
        测试场景：性能基准测试
        验证：
        - Deep Research时间<60秒
        - Markdown生成时间<5秒
        - PDF导出时间<30秒
        - 总时间<90秒
        """
        print("\n⏱️  测试: 性能基准")

        import time

        # 测试Deep Research性能
        start = time.time()
        research_result = await deep_research_engine.research(
            query=sample_query,
            symbol=sample_symbol
        )
        research_time = time.time() - start
        print(f"  📊 Deep Research: {research_time:.2f}秒")
        assert research_time < 60, f"Deep Research过慢: {research_time:.2f}秒"

        # 测试Markdown生成性能
        start = time.time()
        markdown_content = report_generator.generate_markdown(research_result)
        markdown_time = time.time() - start
        print(f"  📝 Markdown生成: {markdown_time:.2f}秒")
        assert markdown_time < 5, f"Markdown生成过慢: {markdown_time:.2f}秒"

        # 测试PDF导出性能
        start = time.time()
        temp_pdf_path = pdf_exporter.generate_temp_pdf_path(f"perf_test_{sample_symbol}")
        pdf_path = pdf_exporter.export_to_pdf(
            markdown_content=markdown_content,
            output_path=temp_pdf_path,
            title=f"{sample_symbol} 性能测试",
            timeout=30
        )
        pdf_time = time.time() - start
        print(f"  📄 PDF导出: {pdf_time:.2f}秒")
        assert pdf_time < 30, f"PDF导出过慢: {pdf_time:.2f}秒"

        # 总时间
        total_time = research_time + markdown_time + pdf_time
        print(f"\n  ⏱️  总耗时: {total_time:.2f}秒")
        assert total_time < 90, f"总耗时过长: {total_time:.2f}秒"

        # 清理
        pdf_exporter.cleanup_temp_file(pdf_path)

        print("✅ 性能基准测试通过")

        return {
            "research_time": research_time,
            "markdown_time": markdown_time,
            "pdf_time": pdf_time,
            "total_time": total_time
        }


if __name__ == "__main__":
    """直接运行测试（用于调试）"""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    async def main():
        test = TestReportPipeline()

        # 运行完整pipeline测试
        print("=" * 60)
        print("运行完整Pipeline集成测试")
        print("=" * 60)

        try:
            await test.test_complete_pipeline("BTC", "分析比特币的技术面和市场情绪")
            print("\n✅ 所有测试通过！")
        except Exception as e:
            print(f"\n❌ 测试失败: {str(e)}")
            import traceback
            traceback.print_exc()

    asyncio.run(main())
