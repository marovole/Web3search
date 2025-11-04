# Deep Research Prompt模板库

## 概述

这个目录包含用于Deep Research功能的Prompt模板。所有模板都采用YAML格式，支持Jinja2变量替换和Few-shot学习。

## 模板列表

### 1. TL;DR生成 (`tldr.yaml`)

- **功能**: 生成项目的核心投资判断和置信度
- **模型**: qwen/qwen-2.5-72b-instruct:free
- **输出格式**: JSON (包含core_thesis, confidence, one_liner)
- **核心判断**: Bull/Neutral/Bear
- **置信度范围**: 0-100

### 2. 基本面分析 (`fundamental_analysis.yaml`)

- **功能**: 分析项目基本面（项目背景、团队、代币经济学、TVL）
- **模型**: qwen/qwen-2.5-72b-instruct:free
- **分析维度**:
  - 项目概述
  - 代币经济学
  - 市场表现
  - 竞争优势

### 3. 技术分析 (`technical_analysis.yaml`)

- **功能**: 分析价格走势、技术指标和支撑阻力位
- **模型**: deepseek/deepseek-chat
- **分析维度**:
  - 价格走势
  - 技术指标（RSI、MACD）
  - 支撑与阻力
  - 短期展望

### 4. 竞品对比分析 (`competitor_analysis.yaml`)

- **功能**: 对比项目与主要竞品的优劣势
- **模型**: qwen/qwen-2.5-72b-instruct:free
- **对比维度**:
  - 关键指标对比（Markdown表格）
  - 相对优势
  - 差距分析
  - 市场地位

### 5. 风险评估 (`risk_assessment.yaml`)

- **功能**: 评估项目的潜在风险和挑战
- **模型**: qwen/qwen-2.5-72b-instruct:free
- **风险类别**:
  - 市场风险
  - 技术风险
  - 监管风险
  - 竞争风险
  - 运营风险

## 模板结构

每个YAML模板包含以下字段：

```yaml
name: "模板名称"
version: "1.0.0"
description: "模板描述"

# 模型配置
model: "模型名称"
temperature: 0.7
max_tokens: 500

# 系统Prompt
system: |
  系统提示词内容...

# 用户Prompt模板（支持Jinja2变量）
user_template: |
  用户提示词模板...
  变量格式: {variable_name}

# Few-shot示例
few_shot_examples:
  - input: |
      示例输入...
    output: |
      示例输出...
```

## 使用方法

### 通过PromptManager使用

```python
from app.services.prompt_manager import prompt_manager

# 获取渲染后的prompt
prompt = prompt_manager.get_tldr_prompt(
    project_name="Ethereum",
    price=3500,
    market_cap="420B",
    # ... 其他变量
)

# 获取prompt和模型配置
config = prompt_manager.get_template_with_config(
    "tldr",
    project_name="Ethereum",
    price=3500,
    # ... 其他变量
)

# 访问配置
model = config["model"]          # "qwen/qwen-2.5-72b-instruct:free"
temperature = config["temperature"]  # 0.7
max_tokens = config["max_tokens"]   # 500
prompt = config["prompt"]         # 渲染后的完整prompt
```

### 获取模板元数据

```python
metadata = prompt_manager.get_template_metadata("tldr")

print(metadata["name"])        # "TL;DR Generator"
print(metadata["version"])     # "1.0.0"
print(metadata["model"])       # "qwen/qwen-2.5-72b-instruct:free"
print(metadata["temperature"]) # 0.7
print(metadata["max_tokens"])  # 500
```

### 列出所有可用模板

```python
available = prompt_manager.list_available_prompts()

for name, info in available.items():
    print(f"{name}: {info['description']}")
```

## 模板变量

### TL;DR模板变量
- `project_name`: 项目名称
- `price`: 当前价格
- `market_cap`: 市值
- `volume_24h`: 24小时交易量
- `price_change_24h`: 24小时价格变化
- `price_change_7d`: 7天价格变化
- `price_change_30d`: 30天价格变化
- `active_addresses`: 活跃地址数
- `daily_transactions`: 日交易笔数
- `twitter_sentiment`: Twitter情绪
- `reddit_sentiment`: Reddit情绪

### 基本面分析模板变量
- `project_name`: 项目名称
- `project_type`: 项目类型
- `launch_date`: 上线时间
- `website`: 官网
- `symbol`: 代币符号
- `total_supply`: 总供应量
- `circulating_supply`: 流通供应量
- `price`: 当前价格
- `fdv`: 完全稀释估值
- `tvl`: TVL
- `revenue_30d`: 30天协议收入
- `active_users_30d`: 30天活跃用户
- `team_info`: 核心团队
- `investors`: 主要投资机构

### 技术分析模板变量
- `current_price`: 当前价格
- `high_24h`, `low_24h`: 24小时高/低
- `high_7d`, `low_7d`: 7天高/低
- `high_30d`, `low_30d`: 30天高/低
- `rsi_14`: RSI指标
- `macd_value`: MACD值
- `macd_signal`: MACD信号
- `ma_50`: 50日移动平均
- `ma_200`: 200日移动平均
- `volume_24h`: 24小时交易量
- `volume_7d_avg`: 7天平均交易量

### 竞品分析模板变量
- `project_name`: 目标项目名称
- `project_tvl`: 目标项目TVL
- `project_volume`: 目标项目日交易量
- `project_users`: 目标项目活跃用户
- `project_market_cap`: 目标项目市值
- `competitor1_name`, `competitor1_tvl`, ... : 竞品1数据
- `competitor2_name`, `competitor2_tvl`, ... : 竞品2数据

### 风险评估模板变量
- `project_name`: 项目名称
- `project_type`: 项目类型
- `running_time`: 运行时长
- `audit_status`: 智能合约审计状态
- `regulatory_status`: 监管合规状态
- `competition_level`: 市场竞争情况
- `token_concentration`: 代币集中度
- `liquidity_level`: 流动性水平

## 模型配置

不同模板使用不同的模型和参数：

| 模板 | 模型 | Temperature | Max Tokens |
|------|------|-------------|------------|
| TL;DR | qwen/qwen-2.5-72b-instruct:free | 0.7 | 500 |
| 基本面分析 | qwen/qwen-2.5-72b-instruct:free | 0.6 | 800 |
| 技术分析 | deepseek/deepseek-chat | 0.5 | 600 |
| 竞品分析 | qwen/qwen-2.5-72b-instruct:free | 0.6 | 700 |
| 风险评估 | qwen/qwen-2.5-72b-instruct:free | 0.5 | 500 |

## Few-shot学习

每个模板都包含1-2个真实的示例，帮助模型理解期望的输出格式和质量标准。示例会自动追加到渲染后的prompt中。

## 版本管理

所有模板都包含版本号，当前版本为 `1.0.0`。

更新模板时，请遵循语义化版本规范：
- **主版本号（Major）**: 不兼容的API更改
- **次版本号（Minor）**: 向后兼容的功能新增
- **修订号（Patch）**: 向后兼容的问题修正

## 模板验证

PromptManager会自动验证模板的完整性，确保包含以下必需字段：
- `name`: 模板名称
- `model`: 模型标识
- `system`: 系统提示词
- `user_template` 或 `user_prompt_template`: 用户提示词模板

## 缓存机制

PromptManager使用内存缓存来提高性能：
- 首次加载模板时会缓存YAML数据
- 后续调用直接从缓存读取
- 可通过 `prompt_manager.reload_cache()` 清空缓存

## 测试

运行单元测试：

```bash
pytest tests/test_prompt_manager.py -v
```

## 统计信息

- **模板文件数**: 5个
- **总代码行数**: 443行
- **平均每个模板**: 88.6行
- **PromptManager代码**: 351行
- **测试代码**: 261行

## 更新日志

### 2025-11-04 - v1.0.0
- ✅ 创建5个核心Prompt模板
- ✅ 实现YAML加载和Jinja2渲染
- ✅ 添加模板验证和缓存机制
- ✅ 编写完整的单元测试
- ✅ 支持Few-shot学习
- ✅ 添加模板元数据和版本管理

## 下一步计划

### 阶段2: 质量验证 + TLDRGenerator修复
- 整合新的Prompt模板到Deep Research服务
- 修复TLDRGenerator的输出格式
- 添加质量验证机制

### 阶段3: 报告生成 + 错误处理
- 实现Markdown报告生成
- 完善错误处理和重试机制
- 优化用户体验
