"""
独立测试运行脚本 - 绕过conftest.py的复杂依赖

直接运行缓存预热测试，无需加载整个应用
"""
import sys
import os

# 设置 PYTHONPATH
sys.path.insert(0, os.path.dirname(__file__))

# 导入必要模块（按需Mock）
import pytest

if __name__ == "__main__":
    # 运行测试
    exit_code = pytest.main([
        "tests/test_cache_prewarming.py",
        "-v",
        "--tb=short",
        "-p", "no:cacheprovider",  # 禁用缓存
        "--ignore=tests/conftest.py"  # 忽略conftest.py
    ])

    sys.exit(exit_code)
