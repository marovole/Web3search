# ai-analysis Spec Delta

## MODIFIED Requirements

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
