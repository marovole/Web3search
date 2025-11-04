#!/usr/bin/env python3
"""
手动验证脚本：测试Prompt模板管理器
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from app.services.prompt_manager import PromptManager


def test_template_loading():
    """测试模板加载"""
    print("=" * 60)
    print("测试1: 加载模板元数据")
    print("=" * 60)

    pm = PromptManager()

    templates = ["tldr", "fundamental_analysis", "technical_analysis",
                 "competitor_analysis", "risk_assessment"]

    for template in templates:
        try:
            metadata = pm.get_template_metadata(template)
            print(f"\n✅ {template}:")
            print(f"   Name: {metadata['name']}")
            print(f"   Version: {metadata['version']}")
            print(f"   Model: {metadata['model']}")
            print(f"   Temperature: {metadata['temperature']}")
            print(f"   Max Tokens: {metadata['max_tokens']}")
        except Exception as e:
            print(f"\n❌ {template}: {e}")


def test_template_rendering():
    """测试模板渲染"""
    print("\n" + "=" * 60)
    print("测试2: 渲染TL;DR模板")
    print("=" * 60)

    pm = PromptManager()

    try:
        rendered = pm.get_tldr_prompt(
            project_name="Ethereum",
            price=3500,
            market_cap="420B",
            volume_24h="15B",
            price_change_24h=2.5,
            price_change_7d=8.3,
            price_change_30d=15.0,
            active_addresses="500K",
            daily_transactions="1.2M",
            twitter_sentiment="积极 (75%)",
            reddit_sentiment="积极 (70%)"
        )

        print("\n✅ TL;DR模板渲染成功")
        print(f"长度: {len(rendered)} 字符")
        print(f"\n前200字符预览:\n{rendered[:200]}...\n")

        # 检查关键内容
        checks = ["Ethereum", "3500", "专业的加密货币分析师", "Examples"]
        for check in checks:
            if check in rendered:
                print(f"✅ 包含关键词: {check}")
            else:
                print(f"❌ 缺少关键词: {check}")

    except Exception as e:
        print(f"❌ TL;DR模板渲染失败: {e}")


def test_template_with_config():
    """测试获取模板和配置"""
    print("\n" + "=" * 60)
    print("测试3: 获取模板和模型配置")
    print("=" * 60)

    pm = PromptManager()

    try:
        result = pm.get_template_with_config(
            "fundamental_analysis",
            project_name="Uniswap",
            project_type="DEX",
            launch_date="2020-09",
            website="https://uniswap.org",
            symbol="UNI",
            total_supply="1B",
            circulating_supply="620M",
            price=6.5,
            fdv="6.5B",
            tvl="4.5B",
            revenue_30d="42M",
            active_users_30d="250K",
            team_info="Hayden Adams等",
            investors="a16z, Paradigm"
        )

        print("\n✅ 获取配置成功")
        print(f"Model: {result['model']}")
        print(f"Temperature: {result['temperature']}")
        print(f"Max Tokens: {result['max_tokens']}")
        print(f"Prompt长度: {len(result['prompt'])} 字符")

    except Exception as e:
        print(f"❌ 获取配置失败: {e}")


def test_list_prompts():
    """测试列出所有可用prompt"""
    print("\n" + "=" * 60)
    print("测试4: 列出所有可用Prompt模板")
    print("=" * 60)

    pm = PromptManager()

    try:
        available = pm.list_available_prompts()

        print(f"\n✅ 找到 {len(available)} 个模板")
        for name, info in available.items():
            if isinstance(info, dict):
                print(f"  • {name}: {info.get('name', 'N/A')} (v{info.get('version', 'N/A')})")
            else:
                print(f"  • {name}: {info}")

    except Exception as e:
        print(f"❌ 列出模板失败: {e}")


def test_caching():
    """测试缓存机制"""
    print("\n" + "=" * 60)
    print("测试5: 测试缓存机制")
    print("=" * 60)

    pm = PromptManager()

    # 首次加载
    pm.get_template_metadata("tldr")
    cache_size_1 = len(pm._cache)
    print(f"首次加载后缓存大小: {cache_size_1}")

    # 再次加载（应该从缓存读取）
    pm.get_template_metadata("tldr")
    cache_size_2 = len(pm._cache)
    print(f"二次加载后缓存大小: {cache_size_2}")

    if cache_size_1 == cache_size_2:
        print("✅ 缓存机制正常工作")
    else:
        print("❌ 缓存机制异常")

    # 清空缓存
    pm.reload_cache()
    cache_size_3 = len(pm._cache)
    print(f"清空后缓存大小: {cache_size_3}")

    if cache_size_3 == 0:
        print("✅ 缓存清空成功")
    else:
        print("❌ 缓存清空失败")


def test_validation():
    """测试模板验证"""
    print("\n" + "=" * 60)
    print("测试6: 测试模板验证")
    print("=" * 60)

    pm = PromptManager()

    # 有效模板
    valid_template = {
        "name": "Test",
        "model": "test-model",
        "system": "Test system",
        "user_template": "Test template"
    }

    try:
        pm._validate_template(valid_template)
        print("✅ 有效模板验证通过")
    except Exception as e:
        print(f"❌ 有效模板验证失败: {e}")

    # 无效模板 - 缺少必需字段
    invalid_template_1 = {
        "name": "Test"
        # 缺少其他字段
    }

    try:
        pm._validate_template(invalid_template_1)
        print("❌ 无效模板未被检测到")
    except ValueError as e:
        print(f"✅ 无效模板被正确检测: {e}")

    # 无效模板 - 缺少用户模板
    invalid_template_2 = {
        "name": "Test",
        "model": "test-model",
        "system": "Test system"
        # 缺少 user_template
    }

    try:
        pm._validate_template(invalid_template_2)
        print("❌ 无效模板未被检测到")
    except ValueError as e:
        print(f"✅ 无效模板被正确检测: {e}")


def main():
    """运行所有测试"""
    print("\n🚀 开始测试Prompt模板管理器\n")

    try:
        test_template_loading()
        test_template_rendering()
        test_template_with_config()
        test_list_prompts()
        test_caching()
        test_validation()

        print("\n" + "=" * 60)
        print("✅ 所有测试完成!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
