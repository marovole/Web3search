"""
辅助脚本：批量为analyzers添加新接口导入
临时使用，完成后可删除
"""
import re

# 需要添加的导入语句
IMPORTS_TO_ADD = """import time
from app.services.research_engine.analyzers.analyzer_output import (
    AnalyzerOutput,
    create_analyzer_output,
    create_error_output,
    create_price_chart_hint,
    create_sentiment_pie_hint,
    create_competitor_table_hint,
)
"""

ANALYZERS = [
    "timeframe_analyzer.py",
    "sentiment_analyzer.py",
    "technical_analyzer.py",
    "onchain_analyzer.py",
]

def update_imports(filepath: str):
    """更新文件的导入语句"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 检查是否已经有analyzer_output导入
    if 'analyzer_output' in content:
        print(f"✓ {filepath} 已包含analyzer_output导入，跳过")
        return False

    # 在from app.services.llm之后添加新导入
    pattern = r'(from app\.services\.llm import .*?\n)'
    replacement = r'\1' + IMPORTS_TO_ADD + '\n'

    new_content = re.sub(pattern, replacement, content, count=1)

    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"✓ {filepath} 导入更新成功")
        return True
    else:
        print(f"✗ {filepath} 未找到匹配的导入位置")
        return False

if __name__ == "__main__":
    import os
    base_path = "app/services/research_engine/analyzers/"

    for analyzer in ANALYZERS:
        filepath = os.path.join(base_path, analyzer)
        if os.path.exists(filepath):
            update_imports(filepath)
        else:
            print(f"✗ {filepath} 文件不存在")
