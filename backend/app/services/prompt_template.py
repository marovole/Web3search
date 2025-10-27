"""
Prompt模板系统（任务 11.1，基础版）

功能：
1. 模板变量替换
2. 条件渲染（简单if/else）
3. 列表循环渲染
4. 模板继承（基础版）

完整实现将在批次2完成（任务11.2-11.7）
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
# 预定义模板（任务11.2-11.3将扩展）
# ================================

QUICK_CHAT_TEMPLATE = PromptTemplate(
    name="quick_chat",
    description="Quick Chat基础模板",
    template_str="""你是专业的加密货币投资分析助手。

用户查询：{query}

{% if market_data %}
当前市场数据：
- 价格：${price_usd}
- 24h变化：{price_change_24h}%
{% endif %}

请提供简洁专业的分析。"""
)

DEEP_RESEARCH_TEMPLATE = PromptTemplate(
    name="deep_research",
    description="Deep Research基础模板",
    template_str="""你是加密货币深度研究专家。

研究主题：{query}

请进行全面深入的分析，包括：
1. 技术分析
2. 基本面分析
3. 市场情绪
4. 风险评估

生成详细的研究报告。"""
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
