# AI Analysis Capability Specification

## ADDED Requirements

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
系统**SHALL**对加密货币项目进行六个维度的深度分析：TL;DR、时间窗分析、情绪分析、技术面分析、基本面分析、竞品对比。

#### Scenario: 生成完整研究报告
- **WHEN** 用户请求项目X（如Hyperliquid）的深度研究
- **THEN** 系统并行执行以下6个分析维度：
  1. TL;DR生成（核心判断+置信度）
  2. 时间窗分析（24h/7d/30d）
  3. 社媒情绪分析
  4. 技术面分析
  5. 基本面分析
  6. 竞品对比分析
- **AND** 每个维度调用对应的LLM模型
- **AND** 返回结构化的JSON结果（符合预定义Schema）
- **AND** 每个维度包含置信度评分（0-100）
- **AND** 总处理时间< 30秒（通过并行化）

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

#### Scenario: 技术面分析包含关键指标
- **WHEN** 生成技术面分析
- **THEN** 输出包含：
  - 当前价位和趋势描述
  - 关键支撑位和阻力位（至少各2个）
  - 技术指标：
    - RSI（1h/4h/日线，标注超买超卖）
    - MACD（柱状图、信号线描述）
    - 成交量OBV（趋势方向）
  - 衍生品市场：
    - 未平仓合约（OI）变化
    - 资金费率（正/负，多空偏向）
    - 清算风险区域（价格+金额）
- **AND** 使用deepseek-r1模型进行推理分析
- **AND** 输出结构化数据（用于前端图表渲染）

#### Scenario: 竞品对比生成标准表格
- **WHEN** 生成竞品对比分析
- **THEN** 自动识别3-5个竞品（基于类别/赛道）
- **AND** 生成对比表格，列包含：
  - 协议名称
  - 日交易量
  - 月交易量
  - 活跃用户（30d）
  - TVL
  - 协议收入（30d）
  - 代币市值
- **AND** 计算估值倍数表格：
  - P/S比率（市值/收入）
  - FDV/收入
  - FDV/TVL
- **AND** 生成竞争优势和劣势文字描述（各100字）

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
