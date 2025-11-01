## Why
Web3项目成功高度依赖社区情绪和社交热度，目前缺少系统化的多平台社交情绪分析工具。通过集成Twitter、Reddit、Telegram等平台数据，结合AI情感分析，可为投资者提供社区热度和情绪趋势洞察，增强投资决策质量。

## What Changes
- 扩展现有Twitter和Reddit数据采集器，增加Telegram/Discord采集能力
- 新增社交情绪分析引擎，集成多种NLP模型进行情感识别
- 实现多平台情绪数据聚合和趋势分析
- 添加社区热度和影响力评估算法
- 集成情绪指标到Deep Research报告生成流程
- 新增情绪数据可视化组件和仪表板

## Impact
- **新增capability**: `social-sentiment` - 社交情绪分析引擎
- **修改capabilities**: 
  - `data-collection` - 扩展社交平台数据源
  - `ai-analysis` - 集成情感分析模型
  - `report-generation` - 增加情绪洞察报告
- **新增API端点**: 5个情绪分析相关接口
- **前端组件**: 新增情绪数据可视化和趋势图表
- **数据模型**: 新增情绪指标和社区影响力评分表
