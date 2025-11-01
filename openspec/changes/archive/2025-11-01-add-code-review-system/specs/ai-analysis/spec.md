## ADDED Requirements
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
