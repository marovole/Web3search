# Chat Interface Capability Specification

## ADDED Requirements

### Requirement: 双模式对话交互
系统**SHALL**提供Quick Chat和Deep Research两种交互模式，满足不同用户需求。

#### Scenario: Quick Chat即时响应
- **WHEN** 用户选择Quick Chat模式并提问"What is the current price of Bitcoin?"
- **THEN** 系统3秒内返回简洁文字回答（如"Bitcoin当前价格$65,432，24h涨幅+2.5%"）
- **AND** 支持SSE流式输出（逐字显示，提升体验）
- **AND** 自动识别意图类型（价格查询/项目对比/概念解释）
- **AND** 响应格式为纯文本（不包含Markdown格式）

#### Scenario: Deep Research生成报告
- **WHEN** 用户选择Deep Research模式并输入项目名"Hyperliquid"
- **THEN** 显示分析进度提示：
  - "正在采集市场数据..." (0-8秒)
  - "正在分析链上活动..." (8-15秒)
  - "正在评估社交情绪..." (15-20秒)
  - "正在生成技术面分析..." (20-25秒)
  - "正在组装报告..." (25-30秒)
- **AND** 15-30秒内生成完整研究报告（3000-5000字）
- **AND** 报告格式符合Markdown标准（包含标题/列表/表格/粗体）
- **AND** 报告结构符合PDF示例标准（TL;DR → 核心分析 → 结论）

#### Scenario: 模式切换保留上下文
- **WHEN** 用户在对话中从Quick Chat切换到Deep Research模式
- **THEN** 保留之前的对话历史（最近10条消息）
- **AND** 新模式可以引用之前的内容（如"刚才提到的Hyperliquid"）
- **AND** 上下文存储在Redis中（session_id为key）
- **AND** 切换动画流畅（< 300ms过渡效果）

#### Scenario: 模式选择指引
- **WHEN** 用户首次访问或输入框为空时
- **THEN** 显示模式选择提示：
  - **Quick Chat**: 适合快速问答、价格查询、简单对比
  - **Deep Research**: 适合生成完整研究报告、多维度分析
- **AND** 显示示例查询（每个模式3个示例）
- **AND** 点击示例自动填充到输入框

### Requirement: 对话历史管理
系统**SHALL**保存用户的对话历史，支持多轮对话和上下文理解。

#### Scenario: 多轮对话上下文
- **WHEN** 用户连续提问：
  1. "Hyperliquid怎么样？"
  2. "它的竞争对手是谁？"
  3. "对比一下它们的TVL"
- **THEN** 第2个问题理解"它"指代Hyperliquid
- **AND** 第3个问题理解"它们"指代Hyperliquid和其竞争对手
- **AND** 给出准确的对比答案（带数据表格）
- **AND** 上下文窗口最多保留最近10轮对话

#### Scenario: 历史记录存储
- **WHEN** 对话结束或用户关闭页面
- **THEN** 对话内容存储到PostgreSQL `conversations`表
- **AND** 每条消息包含：role (user/assistant)、content、timestamp
- **AND** 使用JSONB格式存储消息数组（便于查询和扩展）
- **AND** 对话记录保留30天（之后自动清理）

#### Scenario: 重新加载历史对话
- **WHEN** 用户返回网站并检测到有效的session_id（从localStorage读取）
- **THEN** 从Redis或PostgreSQL加载历史对话
- **AND** 在Chat界面恢复之前的消息列表
- **AND** 用户可以继续之前的对话（无需重新开始）
- **AND** 加载时间< 1秒

#### Scenario: 清空对话历史
- **WHEN** 用户点击"开始新对话"按钮
- **THEN** 清除当前session的所有历史消息
- **AND** 生成新的session_id
- **AND** 更新localStorage和Redis
- **AND** 界面显示欢迎信息和模式选择提示

### Requirement: SSE流式响应
系统**SHALL**支持Server-Sent Events（SSE）实现流式输出，提升用户体验。

#### Scenario: 流式输出逐字显示
- **WHEN** 用户发送Quick Chat请求
- **THEN** 后端通过SSE逐token推送响应
- **AND** 前端实时接收并逐字显示（打字机效果）
- **AND** 每次推送间隔50-100ms（模拟人类打字速度）
- **AND** 连接保持打开直到响应完成或超时（30秒）

#### Scenario: SSE连接异常处理
- **WHEN** SSE连接中断（如网络抖动）
- **THEN** 前端自动重连（最多3次）
- **AND** 重连间隔递增（1秒、3秒、5秒）
- **AND** 3次重连失败后显示错误提示"连接已断开，请刷新页面重试"
- **AND** 已接收的部分内容保留显示

#### Scenario: Deep Research进度推送
- **WHEN** Deep Research任务执行中
- **THEN** 通过SSE推送进度事件：
  ```json
  {
    "type": "progress",
    "stage": "data_collection",
    "message": "正在采集市场数据...",
    "progress": 20
  }
  ```
- **AND** 进度百分比从0更新到100
- **AND** 前端显示进度条和状态文字
- **AND** 最后推送完整报告内容（type: "complete"）

### Requirement: 意图识别与路由
系统**SHALL**自动识别用户查询意图，路由到对应的处理逻辑。

#### Scenario: 价格查询意图
- **WHEN** 用户输入"BTC price" 或 "以太坊多少钱"
- **THEN** 识别为`price_query`意图
- **AND** 直接调用价格查询API（无需LLM）
- **AND** 响应时间< 1秒
- **AND** 返回格式化价格信息（价格+涨跌幅+市值）

#### Scenario: 项目对比意图
- **WHEN** 用户输入"Compare Hyperliquid and dYdX" 或 "对比Uniswap和Sushiswap"
- **THEN** 识别为`project_comparison`意图
- **AND** 提取两个项目名称
- **AND** 调用竞品对比分析器
- **AND** 返回对比表格和文字分析

#### Scenario: 概念解释意图
- **WHEN** 用户输入"What is DeFi?" 或 "解释一下Layer 2"
- **THEN** 识别为`concept_explanation`意图
- **AND** 调用通用QA模型（qwen3-30b）
- **AND** 返回简洁的概念解释（100-300字）
- **AND** 包含关键术语加粗显示

#### Scenario: 意图不明确处理
- **WHEN** 用户输入模糊查询（如"告诉我一些东西"）
- **THEN** 识别为`general_qa`意图
- **AND** 返回澄清问题："请问您想了解哪个加密货币项目？或者您可以尝试以下查询：..."
- **AND** 提供3个建议查询示例

### Requirement: 用户交互体验
系统**SHALL**提供流畅、友好的用户交互体验。

#### Scenario: 输入验证与提示
- **WHEN** 用户在输入框输入文字
- **THEN** 实时显示字符计数（最多1000字）
- **AND** 超过1000字时显示警告"输入过长，请精简问题"
- **AND** 支持Enter键发送、Shift+Enter换行
- **AND** 空输入时发送按钮禁用（灰色）

#### Scenario: 加载状态动画
- **WHEN** 系统处理请求时
- **THEN** 显示加载动画（跳动的点点或波纹效果）
- **AND** Quick Chat显示"思考中..."
- **AND** Deep Research显示详细进度文案
- **AND** 用户可以点击"停止生成"按钮取消请求

#### Scenario: 错误提示友好
- **WHEN** 请求失败（如API错误、超时）
- **THEN** 显示用户友好的错误提示：
  - 网络错误 → "网络连接不稳定，请检查网络后重试"
  - API限流 → "请求过于频繁，请稍后再试（剩余时间XX秒）"
  - 服务器错误 → "服务暂时不可用，我们正在修复中"
- **AND** 提供"重试"按钮
- **AND** 不显示技术性错误信息（如堆栈跟踪）

#### Scenario: 响应消息格式化
- **WHEN** AI返回Markdown格式的响应
- **THEN** 前端正确渲染：
  - 标题（#/##/###）显示不同字号
  - 粗体（**text**）加粗显示
  - 列表（- item）显示为项目符号
  - 表格（| col |）渲染为HTML表格
  - 代码块（```code```）语法高亮
- **AND** 长表格支持横向滚动（移动端）
- **AND** 链接可点击跳转

### Requirement: 速率限制与防滥用
系统**SHALL**实施速率限制，防止恶意滥用和保护资源。

#### Scenario: IP级限流
- **WHEN** 同一IP地址发起请求
- **THEN** Quick Chat限制：每分钟最多10次请求
- **AND** Deep Research限制：每小时最多3次请求
- **AND** 超过限制时返回429状态码
- **AND** 响应头包含`Retry-After`（秒数）
- **AND** 前端显示倒计时"请等待XX秒后重试"

#### Scenario: Session级限流
- **WHEN** 同一session_id连续请求
- **THEN** 防止重复提交（2秒内相同问题视为重复）
- **AND** 重复请求直接返回缓存结果
- **AND** 记录重复请求次数到日志
- **AND** 异常频繁的session标记为可疑并额外限流

#### Scenario: 限流白名单
- **WHEN** 管理员或测试账户请求
- **THEN** 绕过速率限制
- **AND** 在配置文件中维护白名单IP列表
- **AND** 白名单变更无需重启服务（热更新）
