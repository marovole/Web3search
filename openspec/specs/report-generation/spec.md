# report-generation Specification

## Purpose
TBD - created by archiving change add-crypto-ai-search-platform. Update Purpose after archive.
## Requirements
### Requirement: 机构级Markdown报告生成
系统 SHALL 生成符合机构研报标准的Markdown格式报告，**完整实现六维分析内容整合和质量验证**。

#### Scenario: 生成完整研究报告结构
- **WHEN** Deep Research完成所有分析维度
- **THEN** 报告包含以下章节（按顺序）：
  1. **标题**：`# [项目名称] 深度研究报告`
  2. **TL;DR**：核心判断（Bull/Neutral/Bear）+置信度+一句话总结
  3. **核心分析**：
     - **时间窗分析（24h/7d/30d）**：价格变化、交易量趋势、市场表现
     - **基本面分析**：项目背景、团队、代币经济学、TVL、协议收入
     - **技术面分析**：价格走势、支撑阻力、技术指标、交易信号
     - **链上数据分析**：活跃地址、交易笔数、大户持仓、链上交易量
     - **社媒情绪分析**：Twitter/Reddit/Telegram情绪聚合、热度趋势
     - **竞品对比分析**：多维度对比表格（交易量、TVL、市值、估值倍数）
  4. **代币经济学**：流通供应、释放计划、持仓分布
  5. **风险评估**：市场风险、技术风险、监管风险、竞争风险
  6. **结论**：投资建议+关键跟踪指标+预期催化剂
- **AND** 总字数3000-5000字
- **AND** 包含至少3个Markdown表格
- **AND** 每个分析维度150-500字
- **AND** 使用清晰的结构和格式（标题层级、列表、粗体）

#### Scenario: 从Analyzer输出整合报告
- **WHEN** 报告生成器接收到所有analyzer输出
- **THEN** 解析每个analyzer返回的结构化数据：
  ```python
  {
      "dimension": "tldr",
      "content": "...",
      "metadata": {
          "model": "qwen3-235b",
          "confidence": 85,
          "timestamp": "..."
      },
      "tables": [...],  # 表格数据
      "metrics": {...}  # 关键指标
  }
  ```
- **AND** 按预定义顺序排列各个分析维度
- **AND** 提取tables字段生成Markdown表格
- **AND** 格式化metrics字段为关键指标列表
- **AND** 在每个章节末尾添加数据来源标注
- **AND** 生成metadata记录使用的模型版本和Prompt版本

#### Scenario: Markdown格式规范和质量
- **WHEN** 生成Markdown内容
- **THEN** 遵循以下格式规范：
  - 一级标题：`# 标题`（仅报告标题）
  - 二级标题：`## 标题`（主要章节）
  - 三级标题：`### 标题`（子章节）
  - 粗体：`**文字**`（强调关键信息）
  - 列表：`- 项目`（要点）或`1. 项目`（有序列表）
  - 表格：使用GitHub Flavored Markdown表格语法
  - 代码块：使用三个反引号包裹（用于显示原始数据）
- **AND** 换行使用空行分隔段落
- **AND** 特殊字符正确转义（如`$`转义为`\$`）
- **AND** 数字格式化（价格保留2位小数、大数字使用亿/万单位）

#### Scenario: 报告质量验证流程
- **WHEN** 报告生成完成
- **THEN** 调用quality_validator执行以下验证：
  1. **结构完整性**：检查所有必需章节存在
  2. **内容长度**：每个章节内容长度符合要求（TL;DR 50-200字，其他150-500字）
  3. **Markdown语法**：验证标题层级正确、表格格式有效
  4. **数据一致性**：报告中的数字与原始数据差异< 10%
  5. **可读性评分**：计算整体质量评分（0-100）
- **AND** 验证通过后返回报告
- **AND** 验证失败时记录详细错误并标记报告为"质量不合格"
- **AND** 严重质量问题时拒绝返回报告，要求重新生成

#### Scenario: 部分维度失败的报告生成
- **WHEN** 某些分析维度失败但至少50%维度成功
- **THEN** 生成部分报告，包含成功的维度
- **AND** 在报告顶部添加警告：
  ```markdown
  > ⚠️ **注意**：部分分析维度生成失败，报告可能不完整。
  > 失败的维度：技术面分析、竞品对比分析
  ```
- **AND** 失败的维度章节显示占位符：
  ```markdown
  ## 技术面分析
  该分析维度暂时不可用，请稍后重试或联系支持团队。
  ```
- **AND** 报告metadata标记为"partial_success"
- **AND** 提供"重新生成失败维度"的选项

### Requirement: 动态表格生成
系统**SHALL**使用table_generator模块根据analyzer输出动态生成Markdown表格，支持复杂的多列对比。

#### Scenario: 集成table_generator生成表格
- **WHEN** analyzer的visualization_hints.type为"table"
- **THEN** 提取table_columns和table_data
- **AND** 调用`utils/table_generator.py`的`generate_table()`方法
- **AND** 传入列定义和数据行
- **AND** 接收生成的Markdown表格字符串
- **AND** 将表格嵌入到报告对应章节

#### Scenario: 生成竞品对比表格
- **WHEN** 生成竞品对比章节
- **THEN** 创建Markdown表格，包含以下列：
  ```markdown
  | 协议 | 日交易量 | 月交易量 | 活跃用户(30d) | TVL | 协议收入(30d) | 代币市值 |
  |------|---------|---------|--------------|-----|-------------|---------|
  | Hyperliquid | $85亿 | $3164亿 | ~25万 | $47.3亿 | $1.014亿 | $107.7亿 |
  | dYdX | ~$20亿 | ~$600亿 | ~5万 | $1.85亿 | $170万 | $2.98亿 |
  ```
- **AND** 数字格式化（如亿/万/K/M/B）
- **AND** 支持排序和对比计算（如计算市场份额占比）
- **AND** 表格宽度适配（移动端横向滚动）

#### Scenario: 生成估值倍数表格
- **WHEN** 生成竞品对比章节
- **THEN** 创建估值倍数表格：
  ```markdown
  | 协议 | P/S比率 | FDV/收入 | FDV/TVL |
  |------|--------|---------|---------|
  | Hyperliquid | 8.8x | 32.6x | 8.4x |
  | dYdX | 14.6x | 29.2x | 3.2x |
  ```
- **AND** 倍数保留1位小数并添加"x"后缀
- **AND** 高亮最优/最劣值（使用粗体）

#### Scenario: 生成支撑阻力表格
- **WHEN** 生成技术面分析章节
- **THEN** 创建支撑阻力表格：
  ```markdown
  | 类型 | 水平 | 强度 | 依据 |
  |------|------|------|------|
  | 支撑 | $38.65 | 中等 | 1h 50 SMA + OBV 枢轴 |
  | 支撑 | $37.99-$38.50 | 强 | 清算集群（累计 1800 万美元多头） |
  | 阻力 | $40.81 | 中等 | 1h 上布林带 |
  | 阻力 | $42.59 | 强 | 日/周 VWAP + 200 SMA 延伸 |
  ```
- **AND** 价格格式化为美元符号+小数
- **AND** 强度标注为"强/中等/弱"

#### Scenario: 表格生成错误处理
- **WHEN** table_generator调用失败（如数据格式不正确）
- **THEN** 捕获异常并记录错误日志
- **AND** 在报告中显示占位符："[表格生成失败]"
- **AND** 继续生成报告其他部分（不中断整体流程）

### Requirement: 图表嵌入与生成
系统**SHALL**使用chart_generator模块生成数据可视化图表并嵌入到报告中。

#### Scenario: 集成chart_generator生成图表
- **WHEN** analyzer的visualization_hints.type为"chart"
- **THEN** 提取chart_type和chart_data
- **AND** 调用`utils/chart_generator.py`的`generate_chart()`方法
- **AND** 传入图表类型（line/bar/pie）和数据
- **AND** 接收生成的图表（PNG格式）
- **AND** 将图表Base64编码并嵌入Markdown：`![chart](data:image/png;base64,...)`

#### Scenario: 生成价格走势图
- **WHEN** 生成时间窗分析章节
- **THEN** 使用chart_generator生成价格K线图（30天数据）
- **AND** X轴为日期，Y轴为价格
- **AND** 包含成交量柱状图（副图）
- **AND** 转换为PNG格式并Base64编码
- **AND** 嵌入Markdown：`![价格走势图](data:image/png;base64,iVBORw0...)`
- **AND** 图表尺寸：800x400px

#### Scenario: 生成情绪分布饼图
- **WHEN** 生成社媒情绪章节
- **THEN** 使用chart_generator生成饼图（正面/中性/负面占比）
- **AND** 使用颜色：绿色（正面）、灰色（中性）、红色（负面）
- **AND** 显示百分比标签
- **AND** 转换为Base64编码嵌入

#### Scenario: 生成TVL趋势图
- **WHEN** 生成基本面分析章节
- **THEN** 使用chart_generator生成折线图（30天TVL趋势）
- **AND** X轴为日期，Y轴为TVL（单位：亿美元）
- **AND** 标注关键事件点（如TVL峰值）
- **AND** 转换为Base64编码嵌入

#### Scenario: 图表生成错误处理
- **WHEN** chart_generator调用失败（如数据缺失、matplotlib错误）
- **THEN** 捕获异常并记录错误日志
- **AND** 跳过该图表（不在报告中显示）
- **AND** 继续生成报告其他部分（不中断整体流程）

### Requirement: PDF导出功能
系统**SHALL**支持将Markdown报告导出为专业PDF文档，包含中文字体支持和图表嵌入。

#### Scenario: PDF导出成功
- **WHEN** 用户点击"导出PDF"按钮
- **THEN** 后端接收导出请求（POST /api/v1/reports/{id}/export）
- **AND** 使用WeasyPrint将Markdown转换为PDF
- **AND** 应用CSS样式表（fonts, margins, page-break）
- **AND** 生成目录（TOC）基于标题层级
- **AND** 添加页码（格式："第X页 / 共Y页"）
- **AND** 添加页眉（项目名称）和页脚（生成时间）
- **AND** PDF文件大小< 2MB
- **AND** 返回PDF文件流（Content-Type: application/pdf）

#### Scenario: PDF样式优化
- **WHEN** 生成PDF
- **THEN** 应用以下样式：
  - 字体：中文使用思源黑体或Noto Sans CJK，英文使用Roboto
  - 页边距：上下2cm，左右2.5cm
  - 标题1：24pt加粗，颜色#1a1a1a
  - 标题2：18pt加粗，颜色#333333
  - 正文：12pt，行高1.6，颜色#333333
  - 表格：边框1px solid #ddd，斑马纹背景
  - 图表：居中显示，最大宽度100%
- **AND** 长表格自动分页（不截断）
- **AND** 代码块保留等宽字体

#### Scenario: PDF包含中文字体
- **WHEN** 导出包含中文的报告
- **THEN** 在CSS中配置中文字体回退链：
  ```css
  font-family: "Noto Sans CJK SC", "Source Han Sans CN", "Microsoft YaHei", sans-serif;
  ```
- **AND** 确认生产环境（Render.com）已安装中文字体
- **AND** PDF正确渲染所有中文字符（无方框或乱码）
- **AND** 字体回退顺序优先使用高质量开源字体

#### Scenario: PDF包含图表
- **WHEN** 导出包含图表的报告
- **THEN** 图表作为Base64编码的PNG图像嵌入PDF
- **AND** 图表保持原始尺寸和清晰度
- **AND** 图表居中显示并保持纵横比
- **AND** 图表不被页面边界截断（必要时自动缩放）

#### Scenario: PDF导出超时控制
- **WHEN** PDF生成过程耗时较长（如包含大量图表）
- **THEN** 设置最大生成时间为30秒
- **AND** 超时后中断生成并返回错误
- **AND** 错误消息："PDF生成超时，请稍后重试"
- **AND** 释放WeasyPrint占用的资源

#### Scenario: PDF导出失败处理
- **WHEN** PDF生成过程中出现错误（如内存不足、字体缺失）
- **THEN** 捕获异常并返回500错误
- **AND** 错误消息："PDF生成失败，请稍后重试"
- **AND** 记录详细错误日志（堆栈跟踪）
- **AND** 通知运维团队（通过Sentry）

### Requirement: 分享链接生成
系统 SHALL 为每份报告生成唯一的分享链接，**支持完整的报告访问和过期管理**。

#### Scenario: 分享链接生成和存储
- **WHEN** 报告生成完成
- **THEN** 创建唯一share_token（使用UUID v4，32位hex）
- **AND** 将报告完整内容存储到`reports`表：
  ```sql
  INSERT INTO reports (
    id, share_token, project_name, report_type,
    content, metadata, expires_at, created_at
  ) VALUES (
    uuid_generate_v4(), 'abc123...', 'Hyperliquid', 'deep_research',
    '...', '{"quality_score": 85, ...}', now() + interval '7 days', now()
  )
  ```
- **AND** 设置过期时间为7天
- **AND** 返回分享URL：`https://web3search.ai/reports/{share_token}`
- **AND** 前端显示"复制链接"按钮（一键复制到剪贴板）
- **AND** 显示过期时间提示："此链接将在7天后过期"

#### Scenario: 通过分享链接访问报告
- **WHEN** 用户访问分享链接（如`/reports/abc123...`）
- **THEN** 后端查询`reports`表（WHERE share_token = 'abc123...'）
- **AND** 检查是否过期（expires_at > now()）
- **AND** 如未过期，返回报告内容（JSON格式）
- **AND** 前端渲染完整报告（包含所有章节、表格）
- **AND** 显示生成时间和数据新鲜度提示
- **AND** 提供"导出PDF"选项
- **AND** 增加访问计数（views字段+1）

#### Scenario: 分享链接过期和清理
- **WHEN** 用户访问已过期的分享链接
- **THEN** 返回404错误
- **AND** 显示友好提示："此报告已过期（保留期7天），请重新生成"
- **AND** 提供"重新生成"按钮（跳转到首页并预填项目名）
- **AND** Celery定时任务每日凌晨3点清理过期记录
- **AND** 清理时记录删除数量到日志

### Requirement: 报告质量验证
系统 SHALL 验证生成报告的质量，**实施严格的质量门禁和评分机制**。

#### Scenario: 结构完整性检查
- **WHEN** 报告生成完成
- **THEN** 验证以下章节存在：
  - TL;DR ✅
  - 基本面分析 ✅
  - 技术面分析 ✅
  - 链上数据分析 ✅
  - 社媒情绪分析 ✅
  - 竞品对比分析 ✅
  - 代币经济学 ✅
  - 风险评估 ✅
  - 结论 ✅
- **AND** 如缺少超过2个章节，拒绝生成报告
- **AND** 如缺少1-2个章节，标记为"部分完成"并添加警告
- **AND** 记录缺失章节到metadata

#### Scenario: 数据准确性验证
- **WHEN** 报告包含数字数据（如价格、市值、TVL）
- **THEN** 与原始输入数据交叉验证：
  ```python
  diff = abs(report_value - source_value) / source_value
  if diff > 0.10:  # 差异>10%
      warnings.append("数据可能不准确")
  ```
- **AND** 如发现数据偏差> 10%，在对应章节添加警告："⚠️ 数据可能存在偏差"
- **AND** 严重偏差（> 30%）时拒绝该章节内容，要求重新生成
- **AND** 记录所有数据验证结果到日志

#### Scenario: 质量评分计算
- **WHEN** 报告生成完成
- **THEN** 计算综合质量评分（0-100）：
  - **结构完整性**（30分）：所有章节存在+20，缺1-2章节+10，缺3+章节+0
  - **内容长度**（20分）：总字数在3000-5000范围+20，否则按比例扣分
  - **表格数量**（15分）：>= 3个表格+15，2个+10，1个+5
  - **数据准确性**（20分）：无偏差+20，轻微偏差+10，严重偏差+0
  - **Markdown格式**（15分）：格式正确+15，轻微问题+10，严重问题+5
- **AND** 评分>= 80分：标记为"优质"
- **AND** 评分60-79分：标记为"合格"
- **AND** 评分< 60分：标记为"不合格"，拒绝返回
- **AND** 在报告metadata中记录质量评分
- **AND** 在管理后台显示质量评分趋势图

#### Scenario: 质量门禁和拒绝机制
- **WHEN** 质量评分< 60分或存在严重问题
- **THEN** 拒绝返回报告给用户
- **AND** 返回错误："报告质量不符合标准，请稍后重试"
- **AND** 自动触发重新生成（最多2次）
- **AND** 2次重试仍失败时通知运维团队
- **AND** 记录详细的质量问题到日志（用于Prompt优化）

### Requirement: Frontend Report Display
The system SHALL provide comprehensive frontend display capabilities for generated reports.

#### Scenario: Interactive Report Viewing
- **WHEN** reports are generated by the system
- **THEN** they shall be displayed in an interactive, scrollable format
- **AND** users shall be able to navigate between different report sections
- **AND** charts and tables shall be rendered properly in the browser
- **AND** report formatting shall be consistent with design specifications

#### Scenario: Report Sharing Interface
- **WHEN** users want to share generated reports
- **THEN** they shall be able to generate shareable links
- **AND** configure sharing permissions and expiration settings
- **AND** preview how reports will appear to shared recipients
- **AND** track access to shared reports

### Requirement: Frontend Report Generation Controls
The system SHALL provide frontend controls for initiating and customizing report generation.

#### Scenario: Report Template Selection
- **WHEN** users generate new reports
- **THEN** they shall be able to select from available report templates
- **AND** customize report sections and formatting options
- **AND** preview report layout before generation
- **AND** save report preferences for future use

#### Scenario: Real-time Generation Progress
- **WHEN** reports are being generated
- **THEN** users shall see real-time progress indicators
- **AND** be notified of which sections are currently being processed
- **AND** receive notifications when generation is complete
- **AND** be able to cancel generation if needed

### Requirement: Frontend Export and Download
The system SHALL provide comprehensive export and download capabilities through the frontend interface.

#### Scenario: Multiple Format Export
- **WHEN** users want to export reports
- **THEN** they shall be able to choose from multiple export formats
- **AND** download PDF versions with proper formatting
- **AND** export raw data in CSV or JSON formats
- **AND** receive notifications when exports are ready for download

#### Scenario: Batch Export Operations
- **WHEN** users need to export multiple reports
- **THEN** they shall be able to select multiple reports for batch export
- **AND** choose consistent formatting across all selected reports
- **AND** receive packaged downloads for batch operations
- **AND** track the progress of batch export operations

### Requirement: Report Performance Optimization
The system SHALL provide optimal performance for report display and interaction.

#### Scenario: Large Report Handling
- **WHEN** reports contain large amounts of data
- **THEN** the system shall implement virtual scrolling for long content
- **AND** lazy load report sections to improve initial load time
- **AND** provide search functionality within large reports
- **AND** maintain smooth scrolling and interaction performance

#### Scenario: Chart and Visualization Performance
- **WHEN** reports contain multiple charts and visualizations
- **THEN** charts shall render efficiently without blocking the UI
- **AND** interactive elements shall respond smoothly to user input
- **AND** data shall be cached to avoid redundant processing
- **AND** visualization performance shall be optimized for different device capabilities

### Requirement: Mocking Infrastructure for Report Tests
The test suite **SHALL** provide reusable mock implementations for OpenRouter and Supabase to enable deterministic testing of report generation flows.

#### Scenario: OpenRouter mock responses
- **WHEN** tests need to simulate OpenRouter API calls
- **THEN** provide mock functions that return configurable responses with:
  - Success: valid message content with usage data
  - Failure: network errors, HTTP 500 responses
  - Timeout: delayed responses for timeout testing
- **AND** mock responses must match OpenRouter API response structure

#### Scenario: Supabase mock database
- **WHEN** tests need to simulate Supabase operations
- **THEN** provide mock client with verifiable `insert`, `select`, `update` methods
- **AND** allow inspection of arguments passed to mocked methods
- **AND** simulate both success and failure scenarios

#### Scenario: Test helper reusability
- **WHEN** writing multiple report tests
- **THEN** extract common setup logic (mock creation, request builders) into shared helpers
- **AND** ensure helpers are maintainable and well-documented

