#!/usr/bin/env python3
"""
简化版测试脚本：直接测试YAML模板文件
"""
import yaml
from pathlib import Path


def test_yaml_templates():
    """测试所有YAML模板文件的完整性"""
    print("=" * 60)
    print("测试YAML模板文件完整性")
    print("=" * 60)

    prompts_dir = Path(__file__).parent / "prompts" / "deep_research"

    if not prompts_dir.exists():
        print(f"❌ 目录不存在: {prompts_dir}")
        return

    templates = [
        "tldr.yaml",
        "fundamental_analysis.yaml",
        "technical_analysis.yaml",
        "competitor_analysis.yaml",
        "risk_assessment.yaml"
    ]

    required_fields = ["name", "version", "description", "model", "temperature",
                       "max_tokens", "system", "user_template", "few_shot_examples"]

    for template_file in templates:
        template_path = prompts_dir / template_file
        print(f"\n{'=' * 60}")
        print(f"检查: {template_file}")
        print(f"{'=' * 60}")

        if not template_path.exists():
            print(f"❌ 文件不存在: {template_path}")
            continue

        try:
            with open(template_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            # 检查必需字段
            missing_fields = []
            for field in required_fields:
                if field not in data:
                    missing_fields.append(field)
                else:
                    print(f"✅ {field}: {str(data[field])[:50]}...")

            if missing_fields:
                print(f"❌ 缺少字段: {', '.join(missing_fields)}")
            else:
                print(f"\n✅ 所有必需字段完整!")

            # 检查few-shot示例
            if "few_shot_examples" in data and data["few_shot_examples"]:
                print(f"✅ Few-shot示例数量: {len(data['few_shot_examples'])}")
                for i, example in enumerate(data["few_shot_examples"], 1):
                    if "input" in example and "output" in example:
                        print(f"   • 示例{i}: ✅")
                    else:
                        print(f"   • 示例{i}: ❌ (缺少input或output)")

        except yaml.YAMLError as e:
            print(f"❌ YAML解析错误: {e}")
        except Exception as e:
            print(f"❌ 其他错误: {e}")


def test_jinja2_variables():
    """测试Jinja2变量"""
    print("\n" + "=" * 60)
    print("测试Jinja2模板变量")
    print("=" * 60)

    from jinja2 import Environment, BaseLoader

    prompts_dir = Path(__file__).parent / "prompts" / "deep_research"

    # 测试 TL;DR 模板
    tldr_path = prompts_dir / "tldr.yaml"
    if tldr_path.exists():
        print(f"\n测试: tldr.yaml")
        with open(tldr_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        env = Environment(loader=BaseLoader())
        template = env.from_string(data["user_template"])

        test_vars = {
            "project_name": "Test Project",
            "price": 100,
            "market_cap": "1B",
            "volume_24h": "10M",
            "price_change_24h": 5.0,
            "price_change_7d": 10.0,
            "price_change_30d": 20.0,
            "active_addresses": "10K",
            "daily_transactions": "1K",
            "twitter_sentiment": "积极",
            "reddit_sentiment": "积极"
        }

        try:
            rendered = template.render(**test_vars)
            print("✅ Jinja2渲染成功")
            print(f"渲染长度: {len(rendered)} 字符")
            print(f"\n前100字符预览:\n{rendered[:100]}...\n")
        except Exception as e:
            print(f"❌ Jinja2渲染失败: {e}")


def test_model_configs():
    """测试模型配置"""
    print("\n" + "=" * 60)
    print("测试模型配置")
    print("=" * 60)

    prompts_dir = Path(__file__).parent / "prompts" / "deep_research"

    templates = [
        "tldr.yaml",
        "fundamental_analysis.yaml",
        "technical_analysis.yaml",
        "competitor_analysis.yaml",
        "risk_assessment.yaml"
    ]

    print("\n模型配置汇总:")
    print(f"{'模板':<30} {'模型':<35} {'温度':<6} {'Max Tokens'}")
    print("-" * 80)

    for template_file in templates:
        template_path = prompts_dir / template_file
        if template_path.exists():
            with open(template_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            name = data.get("name", "N/A")
            model = data.get("model", "N/A")
            temp = data.get("temperature", "N/A")
            max_tokens = data.get("max_tokens", "N/A")

            print(f"{name:<30} {model:<35} {temp:<6} {max_tokens}")


def main():
    """运行所有测试"""
    print("\n🚀 开始测试Prompt模板文件\n")

    try:
        test_yaml_templates()
        test_jinja2_variables()
        test_model_configs()

        print("\n" + "=" * 60)
        print("✅ 所有测试完成!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
