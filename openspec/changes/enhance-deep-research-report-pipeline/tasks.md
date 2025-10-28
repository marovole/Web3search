# Implementation Tasks: Enhance Deep Research Report Pipeline

## 1. Deep Research引擎集成优化

### 1.1 Analyzers输出标准化
- [ ] 1.1.1 审查9个analyzers的当前输出格式（TldrGenerator, TimeframeAnalyzer, SentimentAnalyzer, TechnicalAnalyzer, OnchainAnalyzer, CompetitorAnalyzer, TokenomicsAnalyzer, RiskAssessor, ConclusionSynthesizer）
- [ ] 1.1.2 定义统一的Analyzer输出接口（Dict结构，包含data, metadata, visualization_hints字段）
- [ ] 1.1.3 更新所有analyzers以符合新接口（如需要）
- [ ] 1.1.4 为每个analyzer添加输出验证单元测试

### 1.2 Deep Research引擎重构
- [ ] 1.2.1 重构`services/deep_research.py`的`_generate_sections()`方法，移除硬编码的6维度逻辑
- [ ] ] 1.2.2 实现analyzers完整调用流程，收集所有9个analyzers的结构化输出
- [ ] 1.2.3 添加analyzer失败时的降级策略（记录错误但继续处理其他analyzers）
- [ ] 1.2.4 添加analyzer输出验证逻辑（检查必需字段是否存在）
- [ ] 1.2.5 更新`test_deep_research.py`，添加analyzers集成测试

## 2. 报告生成器增强

### 2.1 表格生成集成
- [x] 2.1.1 分析analyzers输出中可表格化的数据（如tokenomics分配、竞品对比、风险评分等）
- [x] 2.1.2 在`services/report_generator.py`中集成`utils/table_generator.py`
- [x] 2.1.3 实现从analyzer输出自动提取数据并调用table_generator生成Markdown表格
- [x] 2.1.4 添加表格生成错误处理（数据缺失时显示占位符）
- [x] 2.1.5 编写表格生成单元测试

### 2.2 图表生成集成
- [x] 2.2.1 分析analyzers输出中可可视化的时序数据（如价格走势、情绪变化、链上指标等）
- [x] 2.2.2 在`services/report_generator.py`中集成`utils/chart_generator.py`
- [x] 2.2.3 实现从analyzer输出自动提取时序数据并调用chart_generator生成图表
- [x] 2.2.4 实现图表Base64编码嵌入到Markdown（`![chart](data:image/png;base64,...)`格式）
- [x] 2.2.5 添加图表生成错误处理（生成失败时跳过图表）
- [x] 2.2.6 编写图表生成单元测试

### 2.3 Markdown Builder高级功能
- [ ] 2.3.1 审查`utils/markdown_builder.py`可用的高级功能
- [ ] 2.3.2 在报告中添加自动生成的目录（Table of Contents）
- [ ] 2.3.3 为报告章节添加锚点链接，支持内部跳转
- [ ] 2.3.4 优化报告格式（标题层级、段落间距、列表缩进等）

### 2.4 质量验证集成
- [x] 2.4.1 在报告生成完成后调用`utils/quality_validator.py`
- [x] 2.4.2 检查报告完整性（所有必需章节是否存在）
- [x] 2.4.3 检查报告格式正确性（Markdown语法、链接有效性等）
- [x] 2.4.4 记录质量验证结果到日志
- [x] 2.4.5 更新`test_report_generator.py`，添加质量验证测试

## 3. PDF导出功能完善

### 3.1 WeasyPrint CSS样式
- [x] 3.1.1 创建PDF专用CSS样式文件（`backend/utils/pdf_styles.css`）
- [x] 3.1.2 定义页面布局（A4尺寸、页边距、页眉页脚）
- [x] 3.1.3 定义字体样式（标题、正文、代码块）
- [x] 3.1.4 定义表格样式（边框、间距、斑马纹）
- [x] 3.1.5 定义图表样式（居中、最大宽度、标题）
- [x] 3.1.6 添加分页控制（避免章节标题在页尾、保持表格完整性）

### 3.2 中文字体支持
- [x] 3.2.1 确认Render.com生产环境可用的中文字体（或打包字体文件）
- [x] 3.2.2 在CSS中配置中文字体回退链（Noto Sans CJK, Arial Unicode MS, sans-serif）
- [x] 3.2.3 测试包含中文的PDF导出，确保字符正确渲染
- [x] 3.2.4 更新`settings.py`，添加PDF字体配置项

### 3.3 PDF导出核心逻辑
- [x] 3.3.1 完善`services/pdf_exporter.py`的`export_to_pdf()`方法
- [x] 3.3.2 实现Markdown到HTML的转换（使用markdown库）
- [x] 3.3.3 将CSS样式注入到HTML
- [x] 3.3.4 使用WeasyPrint生成PDF（处理图表Base64嵌入）
- [x] 3.3.5 添加PDF生成错误处理和超时控制（30秒）
- [x] 3.3.6 实现PDF文件临时存储和清理机制

### 3.4 API端点完善
- [x] 3.4.1 更新`api/reports.py`的`export_report()`端点
- [x] 3.4.2 调用`pdf_exporter.export_to_pdf()`生成PDF
- [x] 3.4.3 设置正确的响应头（Content-Type: application/pdf, Content-Disposition: attachment）
- [x] 3.4.4 添加PDF导出速率限制（防止滥用）
- [x] 3.4.5 更新API文档（OpenAPI schema）

### 3.5 PDF导出测试
- [x] 3.5.1 编写`test_pdf_exporter.py`单元测试
- [x] 3.5.2 测试场景：基础Markdown转PDF
- [x] 3.5.3 测试场景：包含表格的PDF
- [x] 3.5.4 测试场景：包含图表的PDF
- [x] 3.5.5 测试场景：包含中文的PDF
- [x] 3.5.6 测试场景：大型报告的PDF导出（性能测试）
- [x] 3.5.7 编写端到端集成测试（从API调用到PDF下载）

## 4. 集成测试和文档

### 4.1 完整Pipeline测试
- [x] 4.1.1 创建`tests/integration/test_report_pipeline.py`
- [x] 4.1.2 测试场景：从Deep Research到Markdown报告生成
- [x] 4.1.3 测试场景：从Markdown报告到PDF导出
- [x] 4.1.4 测试场景：完整流程（Deep Research → Markdown → PDF）
- [x] 4.1.5 验证报告包含表格和图表

### 4.2 文档更新
- [x] 4.2.1 更新README.md，说明报告生成增强功能
- [x] 4.2.2 更新API文档，添加表格/图表示例
- [x] 4.2.3 更新部署文档，说明中文字体配置要求
- [x] 4.2.4 添加报告模板示例（包含表格和图表的Markdown）

### 4.3 部署验证
- [x] 4.3.1 在本地环境完整测试所有功能
- [x] 4.3.2 确认WeasyPrint和中文字体在生产环境可用
- [x] 4.3.3 部署到Render.com staging环境
- [x] 4.3.4 在staging环境测试PDF导出（包含中文）
- [x] 4.3.5 监控性能指标（报告生成时间、PDF导出时间）
- [x] 4.3.6 部署到生产环境并验证

## 5. 清理和优化

### 5.1 代码清理
- [ ] 5.1.1 移除deep_research.py中的旧硬编码逻辑
- [ ] 5.1.2 移除不再使用的临时代码和注释
- [ ] 5.1.3 统一代码风格（运行black和isort）
- [ ] 5.1.4 更新类型注解（Type hints）

### 5.2 性能优化
- [ ] 5.2.1 分析报告生成性能瓶颈（使用cProfile）
- [ ] 5.2.2 优化图表生成性能（考虑异步生成）
- [ ] 5.2.3 优化PDF导出性能（考虑缓存CSS和HTML模板）
- [ ] 5.2.4 确认缓存系统对新功能的覆盖

### 5.3 监控和日志
- [ ] 5.3.1 添加报告生成各阶段的性能日志
- [ ] 5.3.2 添加PDF导出成功/失败的监控指标
- [ ] 5.3.3 配置告警阈值（报告生成时间>60秒、PDF导出失败率>5%）

---

## 预估时间

- **阶段1（Deep Research引擎）**: 2-3天
- **阶段2（报告生成器）**: 3-4天
- **阶段3（PDF导出）**: 2天
- **阶段4（测试和文档）**: 1-2天
- **阶段5（清理和优化）**: 1天

**总计**: 9-12天（考虑测试和调试时间）

## 依赖关系

- 阶段2依赖阶段1（需要标准化的analyzer输出）
- 阶段3依赖阶段2（需要完整的Markdown报告）
- 阶段4依赖阶段1-3全部完成
- 阶段5可并行进行（持续优化）

## 完成标准

- [ ] 所有单元测试通过（覆盖率>80%）
- [ ] 所有集成测试通过
- [ ] Deep Research报告包含9个analyzers的完整输出
- [ ] 报告包含至少2个表格和1个图表
- [ ] PDF导出成功，包含中文字符
- [ ] PDF导出时间<30秒（对于标准报告）
- [ ] 生产环境验证通过
- [ ] 文档更新完成
