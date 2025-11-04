## MODIFIED Requirements

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
