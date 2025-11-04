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
系统 SHALL 提供完整的六维深度分析功能，生成机构级加密货币研究报告。

#### Scenario: 完整分析流程
- **WHEN** 用户发起Deep Research请求（如"Generate Hyperliquid deep research"）
- **THEN** 系统并行执行以下六个分析维度：
  1. TL;DR生成（核心判断+置信度+一句话总结）
  2. 基本面分析（项目背景、团队、代币经济学、TVL）
  3. 技术分析（价格走势、支撑阻力、技术指标）
  4. 链上数据分析（交易量、活跃地址、大户持仓）
  5. 社媒情绪分析（Twitter/Reddit/Telegram情绪聚合）
  6. 竞品对比分析（多维度对比表格）
- **AND** 每个维度独立完成，部分失败不影响其他维度
- **AND** 总生成时间< 30秒
- **AND** 通过SSE推送实时进度（0% → 100%）
- **AND** 最终返回完整的结构化报告

#### Scenario: TLDRGenerator函数签名正确性
- **WHEN** 调用TLDRGenerator.generate_tldr()方法
- **THEN** 函数签名与实现完全匹配
- **AND** 接受正确的参数：`project_name`, `market_data`, `onchain_data`, `sentiment_data`
- **AND** 不包含不存在的`symbol`参数
- **AND** 返回格式正确的TLDR对象：
  ```python
  {
      "core_thesis": "Bull/Neutral/Bear",
      "confidence": 85,  # 0-100
      "one_liner": "一句话总结（50-150字）",
      "key_metrics": {...},
      "timestamp": "2025-01-15T10:00:00Z"
  }
  ```
- **AND** 处理边界情况（空输入、数据缺失）

#### Scenario: 分析质量验证
- **WHEN** 每个分析维度完成生成
- **THEN** 使用Pydantic Schema验证输出结构
- **AND** 检查必填字段存在性（如TL;DR的核心判断、置信度）
- **AND** 检查数据类型正确性（如置信度为整数）
- **AND** 检查值域合法性（如核心判断只能是Bull/Neutral/Bear）
- **AND** 检查内容长度合规（TL;DR一句话总结50-150字）
- **AND** 验证失败时自动重试（最多3次）
- **AND** 3次验证仍失败则返回降级内容或错误提示

#### Scenario: 错误处理和降级
- **WHEN** 某个分析维度生成失败（如API超时、数据缺失）
- **THEN** 该维度返回友好的错误提示："该分析维度暂时不可用，请稍后重试"
- **AND** 其他维度继续正常执行
- **AND** 最终报告标注哪些维度成功、哪些失败
- **AND** 记录详细错误日志（包含失败原因、重试次数）
- **AND** 发送告警到监控系统

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
系统 SHALL 使用YAML格式管理所有AI Prompt模板，支持版本控制和动态加载。

#### Scenario: YAML模板加载和缓存
- **WHEN** 系统启动时
- **THEN** 从`prompts/deep_research/`目录加载所有YAML文件
- **AND** 解析每个YAML的结构：
  ```yaml
  name: "TL;DR Generator"
  version: "1.2.0"
  model: "qwen/qwen3-235b-a22b:free"
  temperature: 0.7
  max_tokens: 500
  system: "You are a crypto research analyst..."
  user_template: |
    Project: {project_name}
    Price: ${price}
    ...
  few_shot_examples:
    - input: "..."
      output: "..."
  ```
- **AND** 验证YAML格式正确性（必填字段检查）
- **AND** 缓存到内存中（LRU缓存，容量100）
- **AND** 加载失败时记录错误并使用默认模板

#### Scenario: 模板渲染和变量替换
- **WHEN** 生成某个分析维度（如TL;DR）
- **THEN** 从缓存中获取对应的Prompt模板
- **AND** 使用Jinja2渲染`user_template`，替换变量：
  ```
  {project_name} → "Hyperliquid"
  {price} → "39.58"
  {market_cap} → "5.2B"
  ```
- **AND** 拼接`system` + `few_shot_examples` + 渲染后的`user_template`
- **AND** 使用模板指定的`model`和`temperature`调用LLM
- **AND** 在响应metadata中记录使用的模板版本号

#### Scenario: 模板热更新
- **WHEN** 需要优化某个Prompt模板（如提高TL;DR质量）
- **THEN** 修改对应的YAML文件（如`tldr.yaml`）
- **AND** 更新`version`字段（如1.2.0 → 1.3.0）
- **AND** 提交到Git版本控制（记录变更历史）
- **AND** 重启服务或调用热重载API
- **AND** 新请求使用更新后的模板
- **AND** 生成的报告metadata记录模板版本号（用于A/B测试）

### Requirement: 输出质量验证
系统 SHALL 对所有AI生成内容执行严格的质量验证，确保输出符合预定义标准。

#### Scenario: 结构化输出验证
- **WHEN** LLM返回分析结果
- **THEN** 使用Pydantic Schema验证输出结构
- **AND** 检查必填字段是否存在（如TL;DR的核心判断、置信度）
- **AND** 检查数据类型是否正确（如置信度为0-100的整数）
- **AND** 检查值域是否合法（如核心判断只能是Bull/Neutral/Bear）
- **AND** 如验证失败，记录详细错误信息并重新生成（最多3次）
- **AND** 3次验证仍失败则返回错误"AI生成失败，请稍后重试"

#### Scenario: 内容长度验证
- **WHEN** 验证生成内容
- **THEN** 检查以下长度要求：
  - TL;DR一句话总结：50-150字
  - 基本面分析：200-500字
  - 技术面分析：200-500字
  - 链上数据分析：150-300字
  - 社媒情绪分析：150-300字
  - 竞品分析：200-400字
- **AND** 如内容过短（< 最小长度），标记为"内容不足"并重新生成
- **AND** 如内容过长（> 最大长度），进行智能截断（保留完整句子）
- **AND** 记录长度验证结果到日志

#### Scenario: 幻觉检测和数据验证
- **WHEN** LLM生成包含具体数据的内容（如"日交易量85亿美元"）
- **THEN** 与原始输入数据进行交叉验证
- **AND** 如数据差异> 10%，标记为"可能存在幻觉"
- **AND** 记录警告日志（包含原始数据vs生成数据）
- **AND** 在响应metadata中添加警告标识：`"hallucination_risk": true`
- **AND** 降低该部分内容的置信度评分（如从90降至75）
- **AND** 严重幻觉时拒绝该内容并重新生成

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

