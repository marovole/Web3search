# Enhance Deep Research Report Pipeline

## Why

当前Deep Research功能虽然已实现核心架构和9个专用analyzers（TldrGenerator、TimeframeAnalyzer、SentimentAnalyzer等，共计~5000行业务逻辑），但存在以下关键问题：

1. **Analyzers集成不完整**: `deep_research.py`的`_generate_sections()`方法使用简化的6维度硬编码逻辑，未充分利用9个专用analyzers的结构化输出（Dict格式），导致分析深度和数据质量未达预期。

2. **报告可视化缺失**: `report_generator.py`仅生成基础Markdown文本，已实现的`table_generator.py`和`chart_generator.py`模块未被调用，导致报告缺少表格和图表，可读性和专业性不足。

3. **PDF导出不完整**: `pdf_exporter.py`框架存在但核心逻辑缺失，包括WeasyPrint CSS样式未定义、中文字体支持未配置、图表嵌入未测试，无法生成生产级PDF报告。

这些问题直接影响MVP核心价值交付（对标asksurf.ai的机构级研究报告），需要立即完善。

## What Changes

### 1. Deep Research引擎集成优化
- 重构`deep_research.py`的`_generate_sections()`方法，完整集成9个analyzers的输出
- 添加analyzers输出验证和降级策略（当某个analyzer失败时保证整体流程不中断）
- 标准化analyzers输出格式（Dict结构），确保下游报告生成器可解析

### 2. 报告生成器增强
- 在`report_generator.py`中集成`table_generator.py`和`chart_generator.py`
- 实现从analyzers输出自动提取结构化数据并生成表格
- 实现趋势数据可视化（价格走势、情绪变化等）并嵌入Markdown
- 集成`quality_validator.py`进行报告质量检查
- 充分利用`markdown_builder.py`的高级功能（目录生成、锚点链接等）

### 3. PDF导出功能完善
- 完善`pdf_exporter.py`的WeasyPrint CSS样式定义
- 配置中文字体支持（Noto Sans CJK或思源黑体）
- 实现图表Base64嵌入到PDF
- 完善API端点`/reports/{id}/export`
- 添加PDF导出错误处理和降级逻辑

## Impact

### 受影响的Specs
- **ai-analysis**: MODIFIED Requirement 2（六维度深度分析）- 补充analyzers集成细节和输出验证场景
- **report-generation**: MODIFIED Requirement 1-4（Markdown格式、表格生成、图表生成、PDF导出）- 补充表格/图表场景和PDF中文支持场景

### 受影响的代码
**核心文件**（约1500-2000行代码改动）:
- `backend/services/deep_research.py` (~200行修改)
- `backend/services/report_generator.py` (~300行修改)
- `backend/services/pdf_exporter.py` (~150行修改)
- `backend/api/reports.py` (~50行修改，完善export端点)

**依赖文件**（已存在，需集成调用）:
- `backend/utils/table_generator.py` (已实现，新增调用)
- `backend/utils/chart_generator.py` (已实现，新增调用)
- `backend/utils/quality_validator.py` (已实现，新增调用)
- `backend/utils/markdown_builder.py` (已实现，扩展使用)

### 测试影响
需新增或更新以下测试：
- `tests/services/test_deep_research.py` (新增analyzers集成测试)
- `tests/services/test_report_generator.py` (新增表格/图表生成测试)
- `tests/services/test_pdf_exporter.py` (新增PDF导出端到端测试)
- `tests/integration/test_report_pipeline.py` (新增完整pipeline测试)

### 非功能性影响
- **性能**: 图表生成可能增加5-10秒处理时间（已有缓存系统可优化）
- **依赖**: 需确认WeasyPrint和中文字体在Render.com生产环境可用
- **向后兼容**: 完全向后兼容，仅增强现有功能，不改变API接口

### 风险评估
- **低风险**: 所有依赖模块（9个analyzers、table/chart generators）已实现，仅需集成工作
- **技术栈熟悉**: Python + FastAPI + WeasyPrint，团队已有经验
- **可回滚**: 改动集中在service层，数据库schema无变化，可快速回滚
