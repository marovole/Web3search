# chat-interface Specification

## Purpose
TBD - created by archiving change add-crypto-ai-search-platform. Update Purpose after archive.
## Requirements
### Requirement: 双模式对话交互
系统**SHALL**提供Quick Chat和Deep Research两种交互模式，满足不同用户需求。**集成L1内存缓存加速响应。**

#### Scenario: Quick Chat with L1 Cache
- **WHEN** 用户提问热门币种（如"BTC price"）
- **THEN** 首先检查L1内存缓存
- **AND** L1命中时响应延迟< 500ms（含AI生成）
- **AND** L1未命中但L2命中时响应延迟< 1秒
- **AND** 缓存完全未命中时响应延迟< 3秒
- **AND** 响应头包含缓存信息（X-Cache: HIT-L1/HIT-L2/MISS）

#### Scenario: Cache-aware Response Headers
- **WHEN** 系统返回Quick Chat或Deep Research响应
- **THEN** 响应头包含缓存状态信息：
  - `X-Cache`: HIT-L1 | HIT-L2 | MISS
  - `X-Cache-Age`: 缓存数据年龄（秒）
  - `X-Data-Source`: cached | live | fallback
- **AND** 用户可以在开发工具中查看缓存状态
- **AND** 监控系统记录缓存命中率统计

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

### Requirement: 对话界面响应式设计
聊天界面 SHALL 提供现代化的响应式设计，适配桌面、平板和移动设备。

#### Scenario: 桌面端布局
- **WHEN** 用户在桌面端访问应用
- **THEN** 界面显示为三栏布局（侧边栏、聊天区域、信息面板）
- **AND** 所有功能按钮和控件正常显示和交互
- **AND** 支持键盘快捷键操作

#### Scenario: 平板端布局
- **WHEN** 用户在平板设备上访问
- **THEN** 界面自适应为两栏布局
- **AND** 可通过手势切换侧边栏显示/隐藏
- **AND** 聊天输入框适配触摸操作

#### Scenario: 移动端布局
- **WHEN** 用户在手机设备上访问
- **THEN** 界面简化为单栏全屏布局
- **AND** 侧边栏通过汉堡菜单控制
- **AND** 聊天输入框支持语音输入和表情选择
- **AND** 消息气泡适配移动端显示

### Requirement: 现代化UI组件
聊天界面 SHALL 使用现代化的UI组件库，提供专业的视觉效果和交互体验。

#### Scenario: 消息气泡设计
- **WHEN** 显示用户或AI消息
- **THEN** 消息气泡具有现代化设计（圆角、阴影、渐变）
- **AND** 支持Markdown格式渲染（代码高亮、表格、链接）
- **AND** 提供消息操作菜单（复制、分享、重新生成）
- **AND** 显示消息发送状态和时间戳

#### Scenario: 输入框增强
- **WHEN** 用户在输入框中输入内容
- **THEN** 输入框支持自动调整高度
- **AND** 提供输入建议和自动完成功能
- **AND** 支持快捷键操作（Ctrl+Enter发送、Shift+Enter换行）
- **AND** 显示字符计数和输入限制提示

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

### Requirement: 流畅动画和过渡效果
聊天界面 SHALL 提供流畅的动画效果，增强用户体验和界面反馈。

#### Scenario: 消息发送动画
- **WHEN** 用户发送消息
- **THEN** 消息气泡以淡入动画出现在聊天区域
- **AND** 输入框显示发送中状态
- **AND** AI响应以打字机效果逐步显示
- **AND** 动画时长控制在200-500ms内

#### Scenario: 页面切换动画
- **WHEN** 用户在不同页面或功能间切换
- **THEN** 页面以滑动或淡入淡出效果切换
- **AND** 加载状态以骨架屏或进度条形式展示
- **AND** 切换动画流畅，无明显卡顿
- **AND** 支持减少动画选项（accessibility）

#### Scenario: 交互反馈动画
- **WHEN** 用户与界面元素交互
- **THEN** 按钮和链接具有悬停和点击反馈
- **AND** 表单验证错误以震动效果提示
- **AND** 成功操作以绿色勾选动画确认
- **AND** 加载状态以旋转器或进度条显示

### Requirement: 智能错误处理和重试机制
聊天界面 SHALL 提供智能的错误处理和重试机制，确保用户体验的连续性。

#### Scenario: 网络连接错误
- **WHEN** 检测到网络连接中断
- **THEN** 显示友好的离线状态提示
- **AND** 自动保存用户输入的内容
- **AND** 网络恢复后自动重试发送
- **AND** 提供手动重试按钮

#### Scenario: API请求失败
- **WHEN** API请求失败或超时
- **THEN** 显示具体的错误信息和建议解决方案
- **AND** 提供重试发送选项
- **AND** 记录失败的消息，允许稍后重新发送
- **AND** 区分临时错误和永久错误

#### Scenario: 输入验证错误
- **WHEN** 用户输入不符合验证规则
- **THEN** 在输入框旁显示具体错误提示
- **AND** 错误输入高亮显示
- **AND** 提供修改建议或示例
- **AND** 阻止提交直到错误修复

### Requirement: 用户体验优化功能
聊天界面 SHALL 提供多种用户体验优化功能，提升使用便利性和效率。

#### Scenario: 消息搜索和历史
- **WHEN** 用户需要查找历史对话
- **THEN** 提供全文搜索功能
- **AND** 支持按日期、关键词或对话类型筛选
- **AND** 搜索结果高亮显示匹配内容
- **AND** 支持导出或分享搜索结果

#### Scenario: 快捷操作和模板
- **WHEN** 用户频繁使用相似查询
- **THEN** 提供常用查询模板和快捷短语
- **AND** 支持自定义查询模板
- **AND** 提供查询历史快速访问
- **AND** 支持一键重新运行历史查询

#### Scenario: 个性化设置
- **WHEN** 用户希望自定义界面体验
- **THEN** 提供主题切换（浅色/深色模式）
- **AND** 支持字体大小调节
- **AND** 可自定义快捷键设置
- **AND** 提供消息通知偏好设置

### Requirement: 代码审查对话模式
系统**SHALL**扩展现有对话界面，支持代码审查相关的交互和功能。

#### Scenario: 代码输入对话
- **WHEN** 用户在对话界面输入合约地址或代码
- **THEN** 系统识别为代码审查请求
- **AND** 自动切换到代码审查模式
- **AND** 显示代码预览和分析选项
- **AND** 提供快速分析和深度分析选择

#### Scenario: 分析结果对话展示
- **WHEN** 代码分析完成
- **THEN** 在对话界面展示结构化结果：
  - 安全漏洞列表（按严重程度排序）
  - 代码质量评分和建议
  - 可视化图表和统计数据
  - 修复建议和代码示例
- **AND** 支持交互式追问和深入分析
- **AND** 提供导出报告功能

#### Scenario: 代码审查对话历史
- **WHEN** 用户进行多次代码审查
- **THEN** 保存审查历史到对话记录
- **AND** 支持回顾之前的分析结果
- **AND** 可以对比不同版本的审查结果
- **AND** 提供代码改进追踪功能

### Requirement: 代码审查界面组件
系统**SHALL**提供专门的代码审查界面组件，集成到现有的对话系统中。

#### Scenario: 代码编辑器集成
- **WHEN** 用户查看分析结果
- **THEN** 显示内嵌代码编辑器：
  - 语法高亮和行号显示
  - 漏洞位置标记和高亮
  - 代码折叠和搜索功能
  - 实时协作编辑支持
- **AND** 支持多种区块链语言
- **AND** 提供代码格式化和验证

#### Scenario: 漏洞可视化组件
- **WHEN** 展示安全分析结果
- **THEN** 使用可视化组件：
  - 漏洞严重程度分布图
  - 代码质量雷达图
  - 函数复杂度热力图
  - 攻击向量流程图
- **AND** 支持交互式数据探索
- **AND** 提供图表导出功能

#### Scenario: 修复建议交互
- **WHEN** 用户查看修复建议
- **THEN** 提供交互式修复界面：
  - 一键应用修复代码
  - 修复前后对比视图
  - 多种修复方案选择
  - 修复效果预览
- **AND** 支持批量修复操作
- **AND** 提供修复历史记录

