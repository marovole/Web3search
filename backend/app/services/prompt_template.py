"""
Prompt模板系统（任务 11.1-11.5）

功能：
1. 模板变量替换（任务11.1）
2. 条件渲染（任务11.1, 11.5扩展）
3. 列表循环渲染（任务11.1）
4. 变量注入系统（任务11.4）
5. Quick Chat模板（任务11.2）
6. Deep Research模板（任务11.3）

批次3将完成：任务11.6-11.8（输出验证、继承、测试）
"""
from typing import Dict, Any, List, Optional
import re
from dataclasses import dataclass, field


@dataclass
class PromptTemplate:
    """
    Prompt模板基础类

    支持：
    - 变量替换：{variable_name}
    - 条件渲染：{% if condition %}...{% endif %}
    - 列表循环：{% for item in list %}...{% endfor %}
    """
    name: str
    template_str: str
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def render(self, context: Dict[str, Any]) -> str:
        """
        渲染模板

        Args:
            context: 上下文变量字典

        Returns:
            str: 渲染后的文本
        """
        result = self.template_str

        # 1. 处理条件渲染
        result = self._render_conditionals(result, context)

        # 2. 处理循环
        result = self._render_loops(result, context)

        # 3. 替换变量
        result = self._substitute_variables(result, context)

        return result.strip()

    def _substitute_variables(self, text: str, context: Dict[str, Any]) -> str:
        """替换{variable}格式的变量"""
        def replace(match):
            var_name = match.group(1).strip()
            return str(context.get(var_name, f"{{{var_name}}}"))

        return re.sub(r'\{([^}]+)\}', replace, text)

    def _render_conditionals(self, text: str, context: Dict[str, Any]) -> str:
        """
        处理条件渲染
        格式：{% if variable %}...{% endif %}
        """
        pattern = r'{%\s*if\s+(\w+)\s*%}(.*?){%\s*endif\s*%}'

        def replace(match):
            var_name = match.group(1).strip()
            content = match.group(2)

            # 检查变量是否为真
            if context.get(var_name):
                return content
            return ""

        return re.sub(pattern, replace, text, flags=re.DOTALL)

    def _render_loops(self, text: str, context: Dict[str, Any]) -> str:
        """
        处理循环
        格式：{% for item in items %}...{% endfor %}
        """
        pattern = r'{%\s*for\s+(\w+)\s+in\s+(\w+)\s*%}(.*?){%\s*endfor\s*%}'

        def replace(match):
            item_name = match.group(1).strip()
            list_name = match.group(2).strip()
            content = match.group(3)

            items = context.get(list_name, [])
            if not isinstance(items, list):
                return ""

            # 渲染每个项
            results = []
            for item in items:
                item_context = context.copy()
                item_context[item_name] = item
                # 递归替换变量
                rendered = self._substitute_variables(content, item_context)
                results.append(rendered)

            return "\n".join(results)

        return re.sub(pattern, replace, text, flags=re.DOTALL)


# ================================
# 变量注入系统（任务 11.4）
# ================================

class ContextBuilder:
    """
    上下文构建器

    提供类型安全的变量注入
    """

    def __init__(self):
        self.context: Dict[str, Any] = {}

    def add_query(self, query: str) -> "ContextBuilder":
        """添加查询"""
        self.context["query"] = query
        return self

    def add_symbol(self, symbol: str) -> "ContextBuilder":
        """添加代币符号"""
        self.context["symbol"] = symbol.upper()
        return self

    def add_timeframe(self, timeframe: str) -> "ContextBuilder":
        """添加时间范围"""
        self.context["timeframe"] = timeframe
        return self

    def add_market_data(self, market_data: Dict[str, Any]) -> "ContextBuilder":
        """添加市场数据"""
        self.context["market_data"] = True  # 条件标记
        self.context.update(market_data)  # 展开数据
        return self

    def add_social_data(self, social_data: Dict[str, Any]) -> "ContextBuilder":
        """添加社交数据"""
        self.context["social_data"] = True
        self.context.update(social_data)
        return self

    def add_few_shot_examples(self, examples: List[str]) -> "ContextBuilder":
        """添加few-shot示例"""
        self.context["examples"] = examples
        self.context["has_examples"] = len(examples) > 0
        return self

    def add_custom(self, key: str, value: Any) -> "ContextBuilder":
        """添加自定义变量"""
        self.context[key] = value
        return self

    def build(self) -> Dict[str, Any]:
        """构建最终上下文"""
        return self.context


# ================================
# Quick Chat模板（任务 11.2）
# ================================

QUICK_CHAT_TEMPLATE = PromptTemplate(
    name="quick_chat",
    description="Quick Chat完整模板（任务11.2）",
    template_str="""你是专业的Web3加密货币投资分析助手。你的职责是为用户提供准确、及时、专业的加密货币分析。

## 角色定位
- 专业的加密货币分析师
- 精通技术分析、基本面分析、市场情绪分析
- 客观中立，不做绝对预测
- 强调风险提示

## 输出要求
- 简洁明了（200-400字）
- 结构化呈现（使用Markdown）
- 数据支撑（引用具体指标）
- 包含数据来源

---

{% if has_examples %}
## 参考示例

{% for example in examples %}
{example}
{% endfor %}

---
{% endif %}

## 用户查询
{query}

{% if symbol %}
**代币**: {symbol}
{% endif %}

{% if timeframe %}
**时间范围**: {timeframe}
{% endif %}

{% if market_data %}
## 当前市场数据

- **价格**: ${price_usd}
- **24h变化**: {price_change_24h}%
{% if market_cap %}
- **市值**: ${market_cap}
{% endif %}
{% if volume_24h %}
- **24h交易量**: ${volume_24h}
{% endif %}
{% endif %}

{% if social_data %}
## 社交媒体情绪

- **情绪得分**: {sentiment_score}/1.0
- **讨论热度**: {mention_count}
{% endif %}

---

## 分析要求

请按照以下步骤进行分析：

1. **理解查询意图**：识别用户关注的核心问题
2. **数据分析**：基于提供的市场数据进行分析
3. **专业解读**：给出专业、客观的判断
4. **风险提示**：明确指出潜在风险
5. **操作建议**：给出可执行的建议（如适用）

**重要**：
- 避免绝对预测（"一定会涨"等）
- 强调市场不确定性
- 不构成投资建议免责声明

现在请开始分析。"""
)


# ================================
# Deep Research模板（任务 11.3）
# ================================

DEEP_RESEARCH_TEMPLATE = PromptTemplate(
    name="deep_research",
    description="Deep Research分阶段模板（任务11.3）",
    template_str="""你是加密货币深度研究专家，将进行全面系统的研究分析。

## 研究主题
{query}

{% if symbol %}
**研究对象**: {symbol}
{% endif %}

---

## 研究方法论

本研究将分5个阶段进行：

### 阶段1：数据收集与整理
收集多维度数据：
- 链上数据（交易量、持币地址、活跃度）
- 市场数据（价格、市值、交易量）
- 社交数据（Twitter、Reddit情绪）
- 技术数据（开发活跃度、代码提交）
- 基本面数据（代币经济学、团队、路线图）

### 阶段2：定量分析
进行数据分析：
- **技术分析**：趋势、指标、支撑阻力
- **链上分析**：鲸鱼行为、资金流向
- **市值分析**：估值合理性
- **流动性分析**：交易深度、滑点

### 阶段3：定性分析
评估非量化因素：
- **项目愿景**：解决什么问题？
- **技术实力**：创新性、可行性
- **团队背景**：经验、信誉
- **社区质量**：活跃度、忠诚度
- **竞争格局**：优势、劣势

### 阶段4：风险评估
识别并量化风险：
- **市场风险**：波动率、相关性
- **技术风险**：智能合约安全、可扩展性
- **监管风险**：合规性、政策不确定性
- **竞争风险**：替代方案、护城河
- **流动性风险**：退出难度

### 阶段5：综合结论
形成研究报告：
- **核心观点**：投资价值判断
- **支撑论据**：3-5个关键论据
- **风险因素**：主要风险列表
- **估值区间**：合理价格范围（如适用）
- **投资建议**：适合人群、仓位建议

---

## 输出格式要求

请按照以下Markdown结构输出：

```markdown
# {symbol} 深度研究报告

## 执行摘要
[200-300字核心观点]

## 1. 项目概述
### 1.1 基本信息
### 1.2 核心价值主张
### 1.3 发展历程

## 2. 技术分析
### 2.1 价格走势
### 2.2 技术指标
### 2.3 支撑阻力

## 3. 基本面分析
### 3.1 代币经济学
### 3.2 技术架构
### 3.3 生态发展

## 4. 市场情绪分析
### 4.1 社交媒体
### 4.2 社区质量
### 4.3 市场共识

## 5. 风险评估
### 5.1 风险等级
### 5.2 主要风险
### 5.3 风险缓解

## 6. 投资建议
### 6.1 核心观点
### 6.2 目标价位
### 6.3 配置建议

## 7. 参考文献与数据来源
```

---

{% if market_data %}
## 当前数据快照

- 价格：${price_usd}
- 市值：${market_cap}
- 24h交易量：${volume_24h}
- 流通量：{circulating_supply}
{% endif %}

---

**重要提示**：
- 本报告仅供研究参考
- 不构成投资建议
- 市场有风险，投资需谨慎
- 请做好风险管理

现在请开始深度研究分析。"""
)


# ================================
# 模板管理器
# ================================

class TemplateManager:
    """模板管理器"""

    def __init__(self):
        self.templates: Dict[str, PromptTemplate] = {
            "quick_chat": QUICK_CHAT_TEMPLATE,
            "deep_research": DEEP_RESEARCH_TEMPLATE,
        }

    def get_template(self, name: str) -> Optional[PromptTemplate]:
        """获取模板"""
        return self.templates.get(name)

    def register_template(self, template: PromptTemplate):
        """注册新模板"""
        self.templates[template.name] = template

    def render_template(self, name: str, context: Dict[str, Any]) -> str:
        """渲染指定模板"""
        template = self.get_template(name)
        if not template:
            raise ValueError(f"Template not found: {name}")
        return template.render(context)


# 全局实例
template_manager = TemplateManager()
