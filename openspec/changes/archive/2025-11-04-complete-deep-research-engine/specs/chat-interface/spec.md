## MODIFIED Requirements

### Requirement: SSE流式响应
系统 SHALL 支持Server-Sent Events（SSE）实现流式输出和实时进度推送，**完整实现Deep Research流式进度更新**。

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

#### Scenario: Deep Research完整进度推送
- **WHEN** Deep Research任务执行中
- **THEN** 通过SSE推送详细的进度事件：
  ```json
  {
    "type": "progress",
    "stage": "data_collection",
    "message": "正在采集市场数据...",
    "progress": 10,
    "completed_tasks": ["获取价格数据"],
    "pending_tasks": ["获取链上数据", "分析社媒情绪"]
  }

  {
    "type": "progress",
    "stage": "analysis",
    "message": "正在生成TL;DR...",
    "progress": 30,
    "dimension": "tldr"
  }

  {
    "type": "dimension_complete",
    "dimension": "tldr",
    "content": "{TL;DR完整内容}",
    "progress": 40
  }

  {
    "type": "complete",
    "message": "报告生成完成",
    "progress": 100,
    "report": "{完整报告JSON}"
  }
  ```
- **AND** 进度百分比从0更新到100，细粒度追踪每个分析维度
- **AND** 前端显示进度条和当前阶段文字
- **AND** 每个维度完成时立即显示部分结果
- **AND** 最后推送完整报告内容（type: "complete"）

#### Scenario: 进度推送错误处理
- **WHEN** 某个分析维度失败
- **THEN** 推送错误事件：
  ```json
  {
    "type": "error",
    "dimension": "technical_analysis",
    "message": "技术分析暂时不可用",
    "progress": 60,
    "recoverable": true
  }
  ```
- **AND** 继续推送其他维度的进度
- **AND** 前端标记失败的维度，但显示成功的部分
- **AND** 最终报告标注哪些维度成功、哪些失败

### Requirement: 对话界面响应式设计
聊天界面 SHALL 提供现代化的响应式设计，**完整支持Deep Research进度可视化**。

#### Scenario: 桌面端布局
- **WHEN** 用户在桌面端访问应用
- **THEN** 界面显示为三栏布局（侧边栏、聊天区域、信息面板）
- **AND** 所有功能按钮和控件正常显示和交互
- **AND** 支持键盘快捷键操作
- **AND** **Deep Research进度显示在独立面板中（新增）**

#### Scenario: Deep Research进度可视化
- **WHEN** Deep Research任务执行中
- **THEN** 显示六维分析进度面板：
  - TL;DR生成：⏳ 进行中（40%）
  - 基本面分析：✅ 已完成
  - 技术分析：⏸️ 等待中
  - 链上数据：✅ 已完成
  - 社媒情绪：⏳ 进行中（75%）
  - 竞品对比：⏸️ 等待中
- **AND** 使用图标和颜色区分状态（进行中/已完成/失败）
- **AND** 显示总体进度条（0-100%）
- **AND** 显示预计剩余时间
- **AND** 已完成的维度内容实时显示在聊天区域

#### Scenario: Deep Research结果展示
- **WHEN** Deep Research完成
- **THEN** 在聊天区域展示完整的结构化报告
- **AND** 使用折叠面板组织各个分析维度
- **AND** 表格和图表正确渲染
- **AND** 提供"导出PDF"和"分享链接"按钮
- **AND** 支持复制单个章节内容
- **AND** 提供"重新生成"选项（针对失败的维度）
