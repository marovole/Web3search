"""
模板系统测试套件（任务 11.8）

测试覆盖：
1. 变量替换（任务11.1）
2. 条件渲染（任务11.1, 11.5）
3. 循环渲染（任务11.1）
4. 变量注入系统（任务11.4）
5. 输出格式控制（任务11.6）
6. 模板继承（任务11.7）
"""
import pytest
from app.services.prompt_template import (
    PromptTemplate,
    ContextBuilder,
    QUICK_CHAT_TEMPLATE,
    DEEP_RESEARCH_TEMPLATE,
    BASE_CRYPTO_TEMPLATE,
    PRICE_ANALYSIS_TEMPLATE,
    TemplateManager,
    template_manager,
)
from app.services.output_schema import (
    OutputFormat,
    ValidationResult,
)


# ================================
# 测试1-5：基本变量替换（任务11.1）
# ================================

def test_basic_variable_substitution():
    """测试1：基本变量替换"""
    template = PromptTemplate(
        name="test",
        template_str="Hello {name}! You have {count} messages."
    )

    result = template.render({"name": "Alice", "count": 5})
    assert result == "Hello Alice! You have 5 messages."


def test_missing_variable():
    """测试2：缺失变量保持原样"""
    template = PromptTemplate(
        name="test",
        template_str="Hello {name}! Missing: {missing}"
    )

    result = template.render({"name": "Bob"})
    assert "Hello Bob!" in result
    assert "{missing}" in result


def test_multiple_variables():
    """测试3：多个变量"""
    template = PromptTemplate(
        name="test",
        template_str="Symbol: {symbol}, Price: ${price}, Change: {change}%"
    )

    result = template.render({
        "symbol": "BTC",
        "price": 45000,
        "change": 5.2
    })
    assert "Symbol: BTC" in result
    assert "Price: $45000" in result
    assert "Change: 5.2%" in result


def test_nested_variable_context():
    """测试4：上下文嵌套（字典值）"""
    template = PromptTemplate(
        name="test",
        template_str="Market cap: {market_cap}"
    )

    result = template.render({"market_cap": 1000000000})
    assert "1000000000" in result


def test_special_characters_in_values():
    """测试5：值中包含特殊字符"""
    template = PromptTemplate(
        name="test",
        template_str="Message: {msg}"
    )

    result = template.render({"msg": "Price $100 up 10%!"})
    assert "Price $100 up 10%!" in result


# ================================
# 测试6-10：条件渲染（任务11.1, 11.5）
# ================================

def test_conditional_rendering_true():
    """测试6：条件为真时渲染"""
    template = PromptTemplate(
        name="test",
        template_str="""Base content
{% if show_extra %}
Extra content
{% endif %}"""
    )

    result = template.render({"show_extra": True})
    assert "Base content" in result
    assert "Extra content" in result


def test_conditional_rendering_false():
    """测试7：条件为假时不渲染"""
    template = PromptTemplate(
        name="test",
        template_str="""Base content
{% if show_extra %}
Extra content
{% endif %}"""
    )

    result = template.render({"show_extra": False})
    assert "Base content" in result
    assert "Extra content" not in result


def test_nested_conditionals():
    """测试8：嵌套条件"""
    template = PromptTemplate(
        name="test",
        template_str="""{% if outer %}
Outer
{% if inner %}
Inner
{% endif %}
{% endif %}"""
    )

    # 两层都为真
    result1 = template.render({"outer": True, "inner": True})
    assert "Outer" in result1
    assert "Inner" in result1

    # 外层真，内层假
    result2 = template.render({"outer": True, "inner": False})
    assert "Outer" in result2
    assert "Inner" not in result2


def test_conditional_with_variables():
    """测试9：条件内包含变量"""
    template = PromptTemplate(
        name="test",
        template_str="""{% if has_price %}
Price: ${price}
{% endif %}"""
    )

    result = template.render({"has_price": True, "price": 100})
    assert "Price: $100" in result


def test_conditional_missing_variable():
    """测试10：条件变量缺失视为false"""
    template = PromptTemplate(
        name="test",
        template_str="""Base
{% if missing %}
Should not appear
{% endif %}"""
    )

    result = template.render({})
    assert "Base" in result
    assert "Should not appear" not in result


# ================================
# 测试11-13：循环渲染（任务11.1）
# ================================

def test_basic_loop():
    """测试11：基本循环"""
    template = PromptTemplate(
        name="test",
        template_str="""{% for item in items %}
- {item}
{% endfor %}"""
    )

    result = template.render({"items": ["A", "B", "C"]})
    assert "- A" in result
    assert "- B" in result
    assert "- C" in result


def test_loop_with_dict_items():
    """测试12：循环字典列表"""
    template = PromptTemplate(
        name="test",
        template_str="""{% for ex in examples %}
Input: {ex}
{% endfor %}"""
    )

    result = template.render({
        "examples": ["Example 1", "Example 2"]
    })
    assert "Input: Example 1" in result
    assert "Input: Example 2" in result


def test_empty_loop():
    """测试13：空列表循环"""
    template = PromptTemplate(
        name="test",
        template_str="""Before
{% for item in items %}
- {item}
{% endfor %}
After"""
    )

    result = template.render({"items": []})
    assert "Before" in result
    assert "After" in result
    # 空循环不应产生任何输出
    assert result.count("-") == 0


# ================================
# 测试14-16：ContextBuilder（任务11.4）
# ================================

def test_context_builder_basic():
    """测试14：ContextBuilder基本功能"""
    builder = ContextBuilder()
    context = (
        builder
        .add_query("What is BTC price?")
        .add_symbol("BTC")
        .build()
    )

    assert context["query"] == "What is BTC price?"
    assert context["symbol"] == "BTC"


def test_context_builder_market_data():
    """测试15：ContextBuilder市场数据"""
    builder = ContextBuilder()
    context = (
        builder
        .add_market_data({
            "price_usd": 45000,
            "price_change_24h": 5.2
        })
        .build()
    )

    assert context["market_data"] is True
    assert context["price_usd"] == 45000
    assert context["price_change_24h"] == 5.2


def test_context_builder_chaining():
    """测试16：ContextBuilder链式调用"""
    builder = ContextBuilder()
    context = (
        builder
        .add_query("Analyze ETH")
        .add_symbol("ETH")
        .add_timeframe("1d")
        .add_few_shot_examples(["Example 1", "Example 2"])
        .add_custom("custom_field", "custom_value")
        .build()
    )

    assert context["query"] == "Analyze ETH"
    assert context["symbol"] == "ETH"
    assert context["timeframe"] == "1d"
    assert context["has_examples"] is True
    assert len(context["examples"]) == 2
    assert context["custom_field"] == "custom_value"


# ================================
# 测试17-18：输出格式控制（任务11.6）
# ================================

def test_output_format_validation_success():
    """测试17：输出格式验证通过"""
    template = PromptTemplate(
        name="test",
        template_str="Test",
        output_format=OutputFormat.QUICK_CHAT
    )

    valid_output = {
        "summary": "This is a test summary that is long enough",
        "analysis": {
            "key_points": ["Point 1", "Point 2"],
            "data_sources": ["Source 1"]
        },
        "risk_warning": "This is a risk warning"
    }

    result = template.validate_output(valid_output)
    assert result.is_valid is True
    assert len(result.errors) == 0


def test_output_format_validation_failure():
    """测试18：输出格式验证失败"""
    template = PromptTemplate(
        name="test",
        template_str="Test",
        output_format=OutputFormat.QUICK_CHAT
    )

    invalid_output = {
        "summary": "Too short"  # 不满足minLength: 20
        # 缺少required字段：analysis, risk_warning
    }

    result = template.validate_output(invalid_output)
    assert result.is_valid is False
    assert len(result.errors) > 0


# ================================
# 测试19-20：模板继承（任务11.7）
# ================================

def test_template_inheritance():
    """测试19：模板继承"""
    parent = PromptTemplate(
        name="parent",
        template_str="Parent content",
        output_format=OutputFormat.QUICK_CHAT
    )

    child = parent.extend(
        name="child",
        template_str="Child content"
    )

    # 检查继承关系
    assert child.parent_template == parent
    assert child.output_format == OutputFormat.QUICK_CHAT

    # 渲染应包含父子内容
    result = child.render({})
    assert "Parent content" in result
    assert "Child content" in result


def test_multilevel_inheritance():
    """测试20：多层继承"""
    grandparent = PromptTemplate(
        name="grandparent",
        template_str="Grandparent",
        metadata={"version": "1.0"}
    )

    parent = grandparent.extend(
        name="parent",
        template_str="Parent",
        metadata={"author": "Alice"}
    )

    child = parent.extend(
        name="child",
        template_str="Child"
    )

    # 检查三层继承
    assert child.parent_template == parent
    assert parent.parent_template == grandparent

    # metadata应该合并
    assert child.metadata["version"] == "1.0"
    assert child.metadata["author"] == "Alice"

    # 渲染应包含所有层级
    result = child.render({})
    assert "Grandparent" in result
    assert "Parent" in result
    assert "Child" in result


# ================================
# 集成测试
# ================================

def test_quick_chat_template_integration():
    """集成测试：Quick Chat模板"""
    context = (
        ContextBuilder()
        .add_query("What is BTC price?")
        .add_symbol("BTC")
        .add_market_data({
            "price_usd": 45000,
            "price_change_24h": 5.2,
            "market_cap": 900000000000,
            "volume_24h": 30000000000
        })
        .build()
    )

    result = QUICK_CHAT_TEMPLATE.render(context)

    # 验证关键内容
    assert "What is BTC price?" in result
    assert "BTC" in result
    assert "45000" in result
    assert "5.2" in result

    # 验证有输出格式
    assert QUICK_CHAT_TEMPLATE.output_format == OutputFormat.QUICK_CHAT


def test_deep_research_template_integration():
    """集成测试：Deep Research模板"""
    context = (
        ContextBuilder()
        .add_query("Analyze Ethereum ecosystem")
        .add_symbol("ETH")
        .add_market_data({
            "price_usd": 2500,
            "market_cap": 300000000000,
            "volume_24h": 15000000000,
            "circulating_supply": 120000000
        })
        .build()
    )

    result = DEEP_RESEARCH_TEMPLATE.render(context)

    # 验证关键内容
    assert "Analyze Ethereum ecosystem" in result
    assert "ETH" in result
    assert "2500" in result

    # 验证有5阶段方法论
    assert "阶段1" in result or "阶段" in result

    assert DEEP_RESEARCH_TEMPLATE.output_format == OutputFormat.DEEP_RESEARCH


def test_price_analysis_template_inheritance():
    """集成测试：价格分析模板继承"""
    context = (
        ContextBuilder()
        .add_query("BTC price analysis")
        .add_symbol("BTC")
        .add_market_data({
            "price_usd": 45000,
            "price_change_24h": 5.2,
            "market_cap": 900000000000,
            "volume_24h": 30000000000
        })
        .build()
    )

    result = PRICE_ANALYSIS_TEMPLATE.render(context)

    # 应包含基础模板内容
    assert "专业" in result or "Web3" in result

    # 应包含价格分析特定内容
    assert "价格分析" in result
    assert "45000" in result

    # 验证继承关系
    assert PRICE_ANALYSIS_TEMPLATE.parent_template == BASE_CRYPTO_TEMPLATE
    assert PRICE_ANALYSIS_TEMPLATE.output_format == OutputFormat.PRICE_ANALYSIS


def test_template_manager():
    """集成测试：模板管理器"""
    # 获取已注册的模板
    quick_chat = template_manager.get_template("quick_chat")
    assert quick_chat is not None
    assert quick_chat.name == "quick_chat"

    # 渲染模板
    context = {"query": "Test query"}
    result = template_manager.render_template("quick_chat", context)
    assert "Test query" in result

    # 注册新模板
    new_template = PromptTemplate(
        name="test_new",
        template_str="New template: {value}"
    )
    template_manager.register_template(new_template)

    retrieved = template_manager.get_template("test_new")
    assert retrieved is not None
    assert retrieved.name == "test_new"


def test_format_instruction_inclusion():
    """集成测试：格式说明注入"""
    template = PromptTemplate(
        name="test",
        template_str="Test prompt",
        output_format=OutputFormat.QUICK_CHAT
    )

    # 不包含格式说明
    result1 = template.render({}, include_format_spec=False)
    assert "Test prompt" in result1
    assert "输出格式要求" not in result1

    # 包含格式说明
    result2 = template.render({}, include_format_spec=True)
    assert "Test prompt" in result2
    assert "输出格式要求" in result2 or "JSON" in result2


# ================================
# Edge Cases
# ================================

def test_empty_template():
    """边缘测试：空模板"""
    template = PromptTemplate(name="empty", template_str="")
    result = template.render({})
    assert result == ""


def test_template_with_only_whitespace():
    """边缘测试：仅空白字符"""
    template = PromptTemplate(name="whitespace", template_str="   \n\n   ")
    result = template.render({})
    assert result == ""


def test_large_context():
    """边缘测试：大量上下文变量"""
    template = PromptTemplate(
        name="test",
        template_str="Value: {key1}, {key2}, {key3}"
    )

    context = {f"key{i}": f"value{i}" for i in range(1, 101)}
    result = template.render(context)
    assert "value1" in result
    assert "value2" in result


def test_unicode_in_template():
    """边缘测试：Unicode字符"""
    template = PromptTemplate(
        name="test",
        template_str="你好 {name}! 价格：¥{price}"
    )

    result = template.render({"name": "用户", "price": 100})
    assert "你好 用户" in result
    assert "¥100" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
