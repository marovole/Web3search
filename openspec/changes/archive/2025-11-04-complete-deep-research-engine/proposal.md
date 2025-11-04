# Deep Research核心功能完整实现提案

## Why
当前Deep Research功能实现不完整，虽然API端点和基础框架已搭建，但核心分析引擎、Prompt模板库和报告生成器尚未完全实现。需要完成Deep Research的六维度深度分析、Prompt模板管理、输出质量验证等关键功能，使其达到生产就绪状态。

## What Changes
- **完成**六维深度分析引擎（TL;DR、基本面、技术面、链上数据、社媒情绪、竞品对比）
- **新增**Prompt模板库（YAML格式，支持版本控制）
- **完成**TLDRGenerator函数签名兼容性修复
- **新增**输出质量验证器（Pydantic Schema验证）
- **完成**报告生成器（Markdown格式，支持导出）
- **完善**流式响应和进度推送（SSE）
- **新增**缓存策略优化（多层缓存）
- **完善**错误处理和降级机制

## Impact
### 影响的规范
- `specs/ai-analysis/spec.md` - 修改AI分析实现（MODIFIED）
- `specs/chat-interface/spec.md` - 修改Deep Research交互流程（MODIFIED）
- `specs/report-generation/spec.md` - 完善报告生成功能（MODIFIED）

### 影响的代码
#### 新增文件
- `backend/prompts/deep_research/tldr.yaml` - TL;DR Prompt模板
- `backend/prompts/deep_research/fundamental_analysis.yaml` - 基本面分析模板
- `backend/prompts/deep_research/technical_analysis.yaml` - 技术分析模板
- `backend/prompts/deep_research/competitor_analysis.yaml` - 竞品分析模板
- `backend/prompts/deep_research/risk_assessment.yaml` - 风险评估模板
- `backend/app/services/research_engine/quality_validator.py` - 质量验证器
- `backend/app/services/research_engine/output_formatter.py` - 输出格式化器
- `backend/app/services/report/markdown_generator.py` - Markdown报告生成器

#### 修改文件
- `backend/app/services/research_engine/deep_research_engine.py` - 完善分析流程
- `backend/app/services/research_engine/analyzers/tldr_generator.py` - 修复函数签名
- `backend/app/services/prompt_manager.py` - 添加YAML模板加载
- `backend/app/api/v1/chat.py` - 完善Deep Research端点
- `backend/app/services/llm.py` - 优化模型路由逻辑

### 预期收益
- Deep Research功能完全可用，达到生产质量标准
- 生成的报告质量对标 Hyperliquid PDF 示例
- 响应时间< 30秒，满足性能要求
- 支持完整的错误处理和降级策略
- Prompt模板可维护、可版本控制

## Non-Goals
- 不包含PDF导出功能（留待后续迭代）
- 不包含图表生成功能（使用文字描述替代）
- 不包含历史数据对比（仅分析当前状态）
