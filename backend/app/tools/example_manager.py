#!/usr/bin/env python3
"""
Few-shot示例库管理工具（任务 10.8）

命令行工具，用于管理few-shot示例库：
1. 列出示例
2. 搜索示例
3. 添加示例
4. 编辑示例
5. 删除示例
6. 导出/导入
7. 统计信息

用法：
    python -m app.tools.example_manager list --type technical_analysis
    python -m app.tools.example_manager search "BTC RSI"
    python -m app.tools.example_manager add
    python -m app.tools.example_manager stats
"""
import argparse
import json
import sys
from pathlib import Path
from typing import Optional, List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich import print as rprint

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.few_shot_library import (
    FewShotExample,
    ExampleLibrary,
    ExampleType,
    example_library,
    add_example
)
from app.services.semantic_search import search_examples

console = Console()


# ================================
# 命令实现
# ================================

def cmd_list(args):
    """列出示例"""
    console.print("[bold cyan]Few-shot示例库[/bold cyan]")
    console.print()

    if args.type:
        # 按类型筛选
        try:
            example_type = ExampleType(args.type)
            examples = example_library.get_examples_by_type(example_type)
            console.print(f"类型：{example_type.value}")
        except ValueError:
            console.print(f"[red]错误：无效的类型 '{args.type}'[/red]")
            console.print(f"有效类型：{', '.join([t.value for t in ExampleType])}")
            return
    else:
        # 所有示例
        examples = example_library.list_all_examples()
        console.print("所有类型")

    if not examples:
        console.print("[yellow]没有找到示例[/yellow]")
        return

    # 创建表格
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("ID", style="dim", width=8)
    table.add_column("类型", width=20)
    table.add_column("输入查询", width=40)
    table.add_column("标签", width=15)

    for i, ex in enumerate(examples, 1):
        table.add_row(
            str(i),
            ex.example_type.value,
            ex.input_query[:37] + "..." if len(ex.input_query) > 40 else ex.input_query,
            ", ".join(ex.tags) if ex.tags else ""
        )

    console.print(table)
    console.print(f"\n总计：{len(examples)} 个示例")


def cmd_search(args):
    """搜索示例"""
    query = args.query
    example_type = None

    if args.type:
        try:
            example_type = ExampleType(args.type)
        except ValueError:
            console.print(f"[red]错误：无效的类型 '{args.type}'[/red]")
            return

    console.print(f"[bold cyan]搜索：[/bold cyan]{query}")
    if example_type:
        console.print(f"类型：{example_type.value}")
    console.print()

    # 执行搜索
    results = search_examples(query, example_type, top_k=args.top_k)

    if not results:
        console.print("[yellow]没有找到匹配的示例[/yellow]")
        return

    # 显示结果
    for i, ex in enumerate(results, 1):
        panel = Panel(
            f"[bold]输入：[/bold]{ex.input_query}\n\n"
            f"[bold]输出：[/bold]{ex.expected_output[:200]}...\n\n"
            f"[dim]类型：{ex.example_type.value} | 标签：{', '.join(ex.tags)}[/dim]",
            title=f"结果 {i}",
            border_style="cyan"
        )
        console.print(panel)

    console.print(f"\n找到 {len(results)} 个相关示例")


def cmd_add(args):
    """添加示例"""
    console.print("[bold cyan]添加新示例[/bold cyan]")
    console.print()

    # 选择类型
    console.print("可用类型：")
    for t in ExampleType:
        console.print(f"  - {t.value}")

    type_str = Prompt.ask("示例类型")
    try:
        example_type = ExampleType(type_str)
    except ValueError:
        console.print(f"[red]错误：无效的类型 '{type_str}'[/red]")
        return

    # 输入信息
    input_query = Prompt.ask("输入查询")
    expected_output = Prompt.ask("期望输出（可多行，输入END结束）")

    if expected_output == "END":
        # 多行模式
        console.print("输入多行输出（输入单独的'END'结束）：")
        lines = []
        while True:
            line = input()
            if line.strip() == "END":
                break
            lines.append(line)
        expected_output = "\n".join(lines)

    tags_str = Prompt.ask("标签（逗号分隔）", default="")
    tags = [t.strip() for t in tags_str.split(",") if t.strip()]

    # 创建示例
    example = FewShotExample(
        example_type=example_type,
        input_query=input_query,
        expected_output=expected_output,
        tags=tags
    )

    # 确认
    console.print("\n预览：")
    console.print(Panel(
        f"[bold]类型：[/bold]{example_type.value}\n"
        f"[bold]输入：[/bold]{input_query}\n"
        f"[bold]输出：[/bold]{expected_output[:100]}...\n"
        f"[bold]标签：[/bold]{', '.join(tags)}",
        border_style="green"
    ))

    if Confirm.ask("确认添加？"):
        add_example(example)
        console.print("[green]✓ 示例已添加[/green]")
    else:
        console.print("[yellow]已取消[/yellow]")


def cmd_export(args):
    """导出示例"""
    output_file = args.output or "examples_export.json"

    if args.type:
        try:
            example_type = ExampleType(args.type)
            examples = example_library.get_examples_by_type(example_type)
        except ValueError:
            console.print(f"[red]错误：无效的类型 '{args.type}'[/red]")
            return
    else:
        examples = example_library.list_all_examples()

    # 转换为字典
    data = {
        "total": len(examples),
        "examples": [
            {
                "type": ex.example_type.value,
                "input": ex.input_query,
                "output": ex.expected_output,
                "tags": ex.tags
            }
            for ex in examples
        ]
    }

    # 写入文件
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    console.print(f"[green]✓ 已导出 {len(examples)} 个示例到 {output_file}[/green]")


def cmd_import(args):
    """导入示例"""
    input_file = args.input

    if not Path(input_file).exists():
        console.print(f"[red]错误：文件不存在 '{input_file}'[/red]")
        return

    # 读取文件
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    examples = data.get("examples", [])
    console.print(f"找到 {len(examples)} 个示例")

    if not Confirm.ask("确认导入？"):
        console.print("[yellow]已取消[/yellow]")
        return

    # 导入
    imported = 0
    for item in examples:
        try:
            example_type = ExampleType(item["type"])
            example = FewShotExample(
                example_type=example_type,
                input_query=item["input"],
                expected_output=item["output"],
                tags=item.get("tags", [])
            )
            add_example(example)
            imported += 1
        except Exception as e:
            console.print(f"[red]跳过无效示例：{e}[/red]")

    console.print(f"[green]✓ 已导入 {imported} 个示例[/green]")


def cmd_stats(args):
    """统计信息"""
    console.print("[bold cyan]示例库统计[/bold cyan]")
    console.print()

    # 按类型统计
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("类型", width=25)
    table.add_column("数量", justify="right", width=10)
    table.add_column("占比", justify="right", width=10)

    all_examples = example_library.list_all_examples()
    total = len(all_examples)

    for example_type in ExampleType:
        examples = example_library.get_examples_by_type(example_type)
        count = len(examples)
        percentage = (count / total * 100) if total > 0 else 0
        table.add_row(
            example_type.value,
            str(count),
            f"{percentage:.1f}%"
        )

    console.print(table)
    console.print(f"\n总计：{total} 个示例")

    # 标签统计
    console.print("\n[bold cyan]热门标签：[/bold cyan]")
    tag_counts = {}
    for ex in all_examples:
        for tag in ex.tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
    for tag, count in sorted_tags[:10]:
        console.print(f"  {tag}: {count}")


def cmd_delete(args):
    """删除示例（基于搜索）"""
    query = args.query

    console.print(f"[bold yellow]搜索要删除的示例：[/bold yellow]{query}")
    results = search_examples(query, top_k=5)

    if not results:
        console.print("[yellow]没有找到匹配的示例[/yellow]")
        return

    # 显示结果供选择
    for i, ex in enumerate(results, 1):
        console.print(f"\n[{i}] {ex.input_query[:60]}...")

    choice = Prompt.ask("选择要删除的示例（1-5，0取消）", default="0")

    if choice == "0" or not choice.isdigit():
        console.print("[yellow]已取消[/yellow]")
        return

    idx = int(choice) - 1
    if 0 <= idx < len(results):
        if Confirm.ask(f"确认删除示例 '{results[idx].input_query[:40]}'？"):
            # 注意：实际实现需要在ExampleLibrary中添加delete方法
            console.print("[yellow]注意：删除功能需要扩展ExampleLibrary[/yellow]")
            console.print("[dim]建议：手动编辑 few_shot_library.py[/dim]")
    else:
        console.print("[red]无效的选择[/red]")


# ================================
# CLI入口
# ================================

def main():
    parser = argparse.ArgumentParser(
        description="Few-shot示例库管理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # list命令
    parser_list = subparsers.add_parser("list", help="列出示例")
    parser_list.add_argument("--type", "-t", help="按类型筛选")

    # search命令
    parser_search = subparsers.add_parser("search", help="搜索示例")
    parser_search.add_argument("query", help="搜索查询")
    parser_search.add_argument("--type", "-t", help="限制类型")
    parser_search.add_argument("--top-k", "-k", type=int, default=3, help="返回结果数")

    # add命令
    parser_add = subparsers.add_parser("add", help="添加示例")

    # delete命令
    parser_delete = subparsers.add_parser("delete", help="删除示例")
    parser_delete.add_argument("query", help="搜索要删除的示例")

    # export命令
    parser_export = subparsers.add_parser("export", help="导出示例")
    parser_export.add_argument("--output", "-o", help="输出文件")
    parser_export.add_argument("--type", "-t", help="只导出指定类型")

    # import命令
    parser_import = subparsers.add_parser("import", help="导入示例")
    parser_import.add_argument("input", help="输入文件")

    # stats命令
    parser_stats = subparsers.add_parser("stats", help="统计信息")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # 执行命令
    commands = {
        "list": cmd_list,
        "search": cmd_search,
        "add": cmd_add,
        "delete": cmd_delete,
        "export": cmd_export,
        "import": cmd_import,
        "stats": cmd_stats,
    }

    if args.command in commands:
        try:
            commands[args.command](args)
        except KeyboardInterrupt:
            console.print("\n[yellow]已中断[/yellow]")
        except Exception as e:
            console.print(f"[red]错误：{e}[/red]")
            import traceback
            traceback.print_exc()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
