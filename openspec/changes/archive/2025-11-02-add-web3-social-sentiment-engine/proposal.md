## Why
Web3项目成功高度依赖社区情绪和社交热度，现有系统缺少系统化的多平台社交情绪分析工具。通过集成Twitter、Reddit、Telegram、Discord等平台数据，结合AI情感分析，可为投资者提供社区热度和情绪趋势洞察，显著增强Deep Research报告的分析深度和投资决策质量。

## What Changes
- 实现Discord数据采集器（唯一缺失的数据源）
- 完善社交情绪分析引擎的实时处理能力
- 将情绪分析深度集成到Deep Research AI分析流程
- 开发前端情绪可视化组件和实时仪表板
- 实现WebSocket实时情绪监控推送
- 增强多平台情绪数据聚合和趋势分析算法
- 集成情绪洞察到报告生成系统

## Impact
- **新增capability**: `social-sentiment` - 社交情绪分析引擎（已有85%代码）
- **修改capabilities**:
  - `data-collection` - 新增Discord采集器
  - `ai-analysis` - 集成情绪分析到Deep Research流程
  - `chat-interface` - 新增情绪可视化组件
  - `report-generation` - 增强情绪洞察报告
- **API增强**: 扩展现有8个sentiment API端点
- **前端组件**: 新增情绪仪表板、实时图表、情绪趋势组件
- **实时功能**: WebSocket情绪监控和推送系统

## 技术优势
- 充分利用现有85%完成度的代码基础
- 基于已实现的Web3特定情感词典和权重算法
- 异步处理和实时分析架构已完善
- 快速交付，预计12-17天完成剩余15%功能