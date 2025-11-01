# ai-analysis Specification

## Purpose
TBD - created by archiving change add-crypto-ai-search-platform. Update Purpose after archive.
## Requirements
### Requirement: OpenRouter多模型路由
系统**SHALL**根据任务类型智能路由到最合适的OpenRouter免费模型，实现成本优化和质量保证。

#### Scenario: Quick Chat使用快速模型
- **WHEN** 用户发起快速问答请求（如"BTC current price?"）
- **THEN** 系统路由到`qwen/qwen3-30b-a3b:free`模型
- **AND** 响应时间< 3秒
- **AND** 输出简洁文字回答（50-200字）
- **AND** 在响应metadata中标注使用的模型名称

#### Scenario: Deep Research使用高质量模型
- **WHEN** 用户发起深度研究请求（如"Generate Hyperliquid deep research"）
- **THEN** TL;DR和基本面分析路由到`qwen/qwen3-235b-a22b:free`
- **AND** 技术分析路由到`deepseek/deepseek-r1-0528:free`
- **AND** 情绪分析路由到`qwen/qwen3-30b-a3b:free`
- **AND** 总生成时间< 30秒
- **AND** 每个分析维度的响应质量通过验证（结构化输出检查）

#### Scenario: 模型降级处理
- **WHEN** 首选模型`qwen/qwen3-235b-a22b:free`不可用（返回503或超时）
- **THEN** 自动降级到`qwen/qwen3-30b-a3b:free`
- **AND** 重试间隔为2秒
- **AND** 在响应metadata中标注"fallback_model_used": true
- **AND** 记录降级事件到监控系统
- **AND** 如所有备用模型均失败，返回错误并建议用户稍后重试

#### Scenario: Token使用监控
- **WHEN** 调用OpenRouter API
- **THEN** 记录每次调用的Token使用量（input_tokens + output_tokens）
- **AND** 累计每日总Token使用量
- **AND** 当日使用量接近免费额度80%时发送告警
- **AND** 在管理后台展示Token使用趋势图

### Requirement: 六维深度分析
系统**SHALL**对加密货币项目进行六个维度的深度分析，完整集成9个专用analyzers（TldrGenerator、TimeframeAnalyzer、SentimentAnalyzer、TechnicalAnalyzer、OnchainAnalyzer、CompetitorAnalyzer、TokenomicsAnalyzer、RiskAssessor、ConclusionSynthesizer）的结构化输出。

#### Scenario: 生成完整研究报告
- **WHEN** 用户请求项目X（如Hyperliquid）的深度研究
- **THEN** 系统并行执行以下9个专用analyzers：
  1. TldrGenerator（核心判断+置信度）
  2. TimeframeAnalyzer（24h/7d/30d）
  3. SentimentAnalyzer（社媒情绪）
  4. TechnicalAnalyzer（技术面）
  5. OnchainAnalyzer（链上数据）
  6. CompetitorAnalyzer（竞品对比）
  7. TokenomicsAnalyzer（代币经济学）
  8. RiskAssessor（风险评估）
  9. ConclusionSynthesizer（结论）
- **AND** 每个analyzer返回结构化的Dict输出（包含data、metadata、visualization_hints字段）
- **AND** 每个analyzer的输出通过Pydantic验证（符合预定义Schema）
- **AND** 总处理时间< 30秒（通过并行化）

#### Scenario: Analyzer输出完整集成
- **WHEN** Deep Research引擎调用analyzers
- **THEN** 收集所有9个analyzers的结构化输出
- **AND** 验证每个analyzer输出包含必需字段：
  - data: 分析结果数据（Dict类型）
  - metadata: 元数据（模型名称、生成时间、置信度等）
  - visualization_hints: 可视化建议（表格结构、图表类型等）
- **AND** 输出数据传递给报告生成器用于生成Markdown和图表
- **AND** 在报告metadata中记录每个analyzer的执行状态

#### Scenario: Analyzer失败降级策略
- **WHEN** 某个analyzer执行失败（如LLM超时、输出验证失败）
- **THEN** 记录错误日志（包含analyzer名称、错误原因、输入参数）
- **AND** 继续执行其他analyzers（不中断整体流程）
- **AND** 在报告中标注该部分缺失："[该章节生成失败，请稍后重试]"
- **AND** 在响应metadata中添加警告标识：`"partial_failure": ["TechnicalAnalyzer"]`
- **AND** 如超过3个analyzers失败，返回整体错误并建议用户稍后重试

#### Scenario: Analyzer输出包含可视化数据
- **WHEN** analyzer返回可表格化或可图表化的数据
- **THEN** 在visualization_hints字段中包含以下信息：
  - type: "table" 或 "chart"
  - table_columns: 表格列定义（如["协议", "日交易量", "TVL"]）
  - chart_type: 图表类型（如"line", "bar", "pie"）
  - chart_data: 图表数据（x轴、y轴值）
- **AND** 报告生成器根据visualization_hints自动调用table_generator或chart_generator
- **AND** 生成的表格和图表嵌入到对应章节

#### Scenario: TL;DR生成符合标准格式
- **WHEN** 生成TL;DR部分
- **THEN** 输出包含以下元素：
  - 核心判断：`Bull`/`Neutral`/`Bear`（看涨/中性/看跌）
  - 置信度：百分比（如75%）
  - 一句话总结：100字以内，包含具体数字和关键催化剂
- **AND** 格式严格匹配模板：
  ```
  核心判断: Bull (看涨，置信度 75%)
  一句话总结: [项目] 凭借 [核心优势]，展现了 [领域] 的 [地位]。尽管面临 [短期压力]，但其 [核心机制] 和 [增长点] 提供了 [支撑类型]。
  ```
- **AND** 使用Pydantic模型验证输出格式
- **AND** 验证失败时重新生成（最多3次）

#### Scenario: 时间窗分析多维度输出
- **WHEN** 分析时间窗口数据
- **THEN** 输出包含3个时间窗口：
  - **24h**: 价格变化、成交量变化、短期驱动因素
  - **7d**: 周度表现、板块对比、主要事件
  - **30d**: 月度趋势、里程碑事件、协议指标变化
- **AND** 每个时间窗口包含：
  - 价格涨跌幅（带正负号和百分比）
  - 关键事件列表（最多3个）
  - 叙事性描述（50-100字）
- **AND** 数据来源标注（如"数据来源：CoinGecko, 更新时间：2025-01-15 10:30"）

#### Scenario: 情绪分析量化
- **WHEN** 分析社交媒体情绪
- **THEN** 输出包含：
  - 正面/中性/负面占比（总和100%）
  - Twitter提及量趋势（7天趋势图数据）
  - Top 5讨论话题（关键词+频次）
  - 关键KOL发声（用户名+粉丝数+核心观点）
- **AND** 情绪得分计算公式：`(正面% * 1 + 中性% * 0 + 负面% * -1) / 100`
- **AND** 情绪得分范围：-1（极度负面）到+1（极度正面）

### Requirement: 社媒情绪分析
系统 SHALL分析社交媒体数据（Twitter、Reddit、Telegram、Discord），识别市场情绪和热门话题。**多平台情绪分析已完成集成。**

#### Scenario: 多平台情绪整合
- **WHEN** Deep Research进行社媒情绪分析时
- **THEN** 系统整合Twitter、Reddit、Telegram、Discord四平台数据 ✅
- **AND** 实时获取24小时内的综合情绪指标 ✅
- **AND** 提供平台权重和可信度评估 ✅
- **AND** 生成统一的情绪评分和趋势分析 ✅

#### Scenario: 情绪数据实时更新
- **WHEN** 用户查询项目情绪状态时
- **THEN** 获取最新的多平台情绪数据 ✅
- **AND** 提供情绪分布百分比（积极/中性/消极） ✅
- **AND** 包含社区参与度和热度指标 ✅
- **AND** 展示KOL情绪影响分析 ✅

#### Scenario: Deep Research情绪增强
- **WHEN** 生成Deep Research报告时
- **THEN** 自动集成实时情绪分析数据 ✅
- **AND** 增强投资建议的情绪依据 ✅
- **AND** 提供情绪趋势预测和风险预警 ✅
- **AND** 生成基于情绪的市场洞察 ✅

### Requirement: Prompt模板管理
系统**SHALL**使用YAML格式管理AI Prompt模板，支持版本控制和动态加载。

#### Scenario: 从YAML加载Prompt模板
- **WHEN** 系统启动时
- **THEN** 从`prompts/deep_research/`目录加载所有YAML文件
- **AND** 解析每个YAML文件的结构：
  - name: 模板名称
  - model: 首选模型
  - temperature: 温度参数
  - max_tokens: 最大输出tokens
  - system: 系统prompt
  - user_template: 用户prompt模板（支持变量占位符）
  - few_shot_examples: Few-shot示例列表
- **AND** 验证YAML格式正确性
- **AND** 缓存到内存中（避免重复读取文件）

#### Scenario: 动态渲染Prompt模板
- **WHEN** 生成某个分析维度（如TL;DR）
- **THEN** 从内存中获取对应的Prompt模板
- **AND** 使用Jinja2渲染user_template，替换变量占位符
  ```
  项目：{project_name} → 项目：Hyperliquid
  价格：${price} → 价格：$39.58
  ```
- **AND** 拼接system prompt + few-shot examples + 渲染后的user prompt
- **AND** 调用LLM API生成响应

#### Scenario: Prompt版本更新
- **WHEN** 需要优化某个Prompt模板（如提高TL;DR质量）
- **THEN** 修改对应的YAML文件（如`tldr.yaml`）
- **AND** 提交到Git版本控制（记录变更历史）
- **AND** 重启服务或热重载配置
- **AND** 新请求使用更新后的Prompt
- **AND** 记录Prompt版本号到生成的报告metadata中

### Requirement: 输出质量验证
系统**SHALL**验证AI生成内容的质量，确保符合预定义格式和标准。

#### Scenario: 结构化输出验证
- **WHEN** LLM返回分析结果
- **THEN** 使用Pydantic Schema验证输出结构
- **AND** 检查必填字段是否存在（如TL;DR的核心判断、置信度）
- **AND** 检查数据类型是否正确（如置信度为0-100的整数）
- **AND** 检查值域是否合法（如核心判断只能是Bull/Neutral/Bear）
- **AND** 如验证失败，记录错误日志并重新生成（最多3次）
- **AND** 3次验证仍失败则返回错误"AI生成失败，请稍后重试"

#### Scenario: 内容长度验证
- **WHEN** 验证生成内容
- **THEN** 检查以下长度要求：
  - TL;DR一句话总结：50-150字
  - 时间窗分析叙述：50-100字/窗口
  - 技术面分析：200-500字
  - 基本面分析：200-500字
  - 竞品分析：150-300字
  - 风险评估：100-200字
- **AND** 如内容过短（< 最小长度），标记为"内容不足"并重新生成
- **AND** 如内容过长（> 最大长度），进行智能截断（保留完整句子）

#### Scenario: 幻觉检测
- **WHEN** LLM生成包含具体数据的内容（如"日交易量85亿美元"）
- **THEN** 与原始输入数据进行交叉验证
- **AND** 如数据差异> 10%，标记为"可能存在幻觉"
- **AND** 记录警告日志（包含原始数据和生成数据）
- **AND** 在响应metadata中添加警告标识
- **AND** 考虑降低该部分内容的置信度评分

### Requirement: 代码分析AI模型集成
系统**SHALL**扩展现有AI分析引擎，支持智能合约代码的深度分析和理解。

#### Scenario: 专用代码分析模型路由
- **WHEN** 用户提交代码分析请求
- **THEN** 系统路由到专门的代码分析模型：
  - `deepseek/deepseek-r1-0528:free` 用于漏洞检测推理
  - `qwen/qwen3-235b-a22b:free` 用于代码质量评估
  - `qwen/qwen3-30b-a3b:free` 用于快速代码检查
- **AND** 根据代码复杂度动态选择模型
- **AND** 分析响应时间< 30秒

#### Scenario: 代码上下文理解
- **WHEN** AI模型分析合约代码
- **THEN** 模型理解以下代码上下文：
  - 合约继承关系和接口实现
  - 函数调用图和数据流
  - 状态变量依赖关系
  - 外部合约交互模式
- **AND** 识别业务逻辑意图
- **AND** 检测潜在的逻辑缺陷

#### Scenario: 多维度代码分析
- **WHEN** 执行代码分析任务
- **THEN** 并行运行以下专用analyzers：
  1. SecurityVulnerabilityAnalyzer（安全漏洞检测）
  2. CodeQualityAnalyzer（代码质量评估）
  3. ArchitectureAnalyzer（架构模式分析）
  4. GasEfficiencyAnalyzer（Gas效率分析）
  5. ComplianceAnalyzer（合规性检查）
- **AND** 每个analyzer返回结构化结果
- **AND** 总分析时间< 45秒

### Requirement: 代码分析Prompt模板
系统**SHALL**提供专门的代码分析Prompt模板，确保AI输出的准确性和一致性。

#### Scenario: 安全漏洞检测Prompt
- **WHEN** 分析安全漏洞
- **THEN** 使用专门的漏洞检测Prompt模板：
  - 包含常见漏洞类型定义
  - 提供历史攻击案例参考
  - 设置输出格式要求
  - 包含严重程度评估标准
- **AND** 支持Few-shot学习示例
- **AND** 动态调整Prompt复杂度

#### Scenario: 代码质量评估Prompt
- **WHEN** 评估代码质量
- **THEN** 使用质量评估专用模板：
  - 定义代码质量维度
  - 提供行业最佳实践参考
  - 设置评分标准和方法
  - 包含改进建议格式
- **AND** 支持不同项目类型的定制化模板

#### Scenario: Prompt模板版本管理
- **WHEN** 优化代码分析Prompt
- **THEN** 维护Prompt模板版本历史
- **AND** 支持A/B测试不同Prompt版本
- **AND** 记录每个版本的分析效果指标
- **AND** 支持热更新Prompt配置

### Requirement: Real-time Analysis Display
The system SHALL provide real-time display of AI analysis progress and results.

#### Scenario: Streaming Analysis Updates
- **WHEN** Deep Research analysis is processing
- **THEN** users shall see real-time progress updates via streaming interface
- **AND** partial results shall be displayed as they become available
- **AND** streaming connection failures shall be handled gracefully
- **AND** users shall be able to interrupt long-running analyses

#### Scenario: Analysis Progress Visualization
- **WHEN** multi-step analysis is being performed
- **THEN** progress indicators shall show current analysis stage
- **AND** estimated completion time shall be displayed
- **AND** users shall see which analyzers are currently active
- **AND** completed analysis steps shall be clearly marked

### Requirement: Frontend Analysis Interface
The system SHALL provide a comprehensive frontend interface for AI-powered analysis features.

#### Scenario: Interactive Analysis Configuration
- **WHEN** users initiate Deep Research analysis
- **THEN** they shall be able to configure analysis parameters
- **AND** select specific analysis dimensions (market, technical, sentiment, etc.)
- **AND** adjust analysis depth and time horizon preferences
- **AND** save analysis configurations for future use

#### Scenario: Analysis Results Visualization
- **WHEN** AI analysis is completed
- **THEN** results shall be displayed in an intuitive, interactive format
- **AND** charts and graphs shall visualize key metrics and trends
- **AND** users shall be able to drill down into specific analysis sections
- **AND** results shall be exportable in multiple formats

#### Scenario: Analysis History Management
- **WHEN** users complete multiple analyses
- **THEN** they shall be able to access previous analysis results
- **AND** search and filter analysis history by symbol or date
- **AND** compare current analysis with previous results
- **AND** share analysis results with other users

### Requirement: Frontend Error Handling for AI Services
The system SHALL provide robust error handling specifically for AI analysis operations.

#### Scenario: AI Service Unavailability
- **WHEN** backend AI services are temporarily unavailable
- **THEN** frontend shall display clear service status messages
- **AND** provide estimated recovery time when available
- **AND** offer alternative analysis options or retry mechanisms
- **AND** gracefully degrade functionality when appropriate

#### Scenario: Analysis Timeout Handling
- **WHEN** AI analysis exceeds expected time limits
- **THEN** users shall be notified of the delay
- **AND** offered options to continue waiting or cancel the analysis
- **AND** partial results shall be preserved if available
- **AND** users shall be able to restart the analysis from the last completed step

