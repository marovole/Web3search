"""
提示词管理器
加载和管理YAML格式的提示词模板
"""
import os
from typing import Dict, Any, Optional
import yaml
from pathlib import Path


class PromptManager:
    """
    提示词管理器
    负责加载、缓存和格式化提示词模板
    """

    def __init__(self, prompts_dir: Optional[str] = None):
        """
        初始化提示词管理器

        Args:
            prompts_dir: 提示词目录路径，默认为项目根目录的prompts/
        """
        if prompts_dir is None:
            # 默认使用项目根目录的prompts文件夹
            current_dir = Path(__file__).parent
            project_root = current_dir.parent.parent.parent
            prompts_dir = project_root / "prompts"

        self.prompts_dir = Path(prompts_dir)
        self._cache: Dict[str, Dict[str, Any]] = {}

    def _load_yaml(self, filename: str) -> Dict[str, Any]:
        """
        加载YAML文件

        Args:
            filename: YAML文件名

        Returns:
            Dict: YAML内容
        """
        # 检查缓存
        if filename in self._cache:
            return self._cache[filename]

        # 加载文件
        file_path = self.prompts_dir / filename

        if not file_path.exists():
            raise FileNotFoundError(f"提示词文件不存在: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # 缓存结果
        self._cache[filename] = data
        return data

    # ================================
    # 系统提示词
    # ================================

    def get_base_system_prompt(self) -> str:
        """获取基础系统提示词"""
        data = self._load_yaml("system_prompts.yaml")
        return data["base_system_prompt"]

    def get_quick_chat_system_prompt(self) -> str:
        """获取Quick Chat系统提示词"""
        data = self._load_yaml("system_prompts.yaml")
        return data["quick_chat_system_prompt"]

    def get_deep_research_system_prompt(self) -> str:
        """获取Deep Research系统提示词"""
        data = self._load_yaml("system_prompts.yaml")
        return data["deep_research_system_prompt"]

    def get_disclaimer(self) -> str:
        """获取免责声明"""
        data = self._load_yaml("system_prompts.yaml")
        return data["disclaimer"]

    # ================================
    # Deep Research 提示词
    # ================================

    def get_tldr_prompt(self, **kwargs) -> str:
        """
        获取TL;DR生成提示词

        Args:
            **kwargs: 格式化参数（query, market_data, project_info, social_data）

        Returns:
            str: 格式化后的提示词
        """
        data = self._load_yaml("deep_research.yaml")
        template = data["tldr_prompt"]
        return template.format(**kwargs)

    def get_overview_prompt(self, **kwargs) -> str:
        """
        获取项目概览提示词

        Args:
            **kwargs: 格式化参数（query, project_info, market_data）

        Returns:
            str: 格式化后的提示词
        """
        data = self._load_yaml("deep_research.yaml")
        template = data["overview_prompt"]
        return template.format(**kwargs)

    def get_technical_analysis_prompt(self, **kwargs) -> str:
        """
        获取技术分析提示词

        Args:
            **kwargs: 格式化参数

        Returns:
            str: 格式化后的提示词
        """
        data = self._load_yaml("deep_research.yaml")
        template = data["technical_analysis_prompt"]
        return template.format(**kwargs)

    def get_market_analysis_prompt(self, **kwargs) -> str:
        """
        获取市场分析提示词

        Args:
            **kwargs: 格式化参数

        Returns:
            str: 格式化后的提示词
        """
        data = self._load_yaml("deep_research.yaml")
        template = data["market_analysis_prompt"]
        return template.format(**kwargs)

    def get_community_analysis_prompt(self, **kwargs) -> str:
        """
        获取社区分析提示词

        Args:
            **kwargs: 格式化参数

        Returns:
            str: 格式化后的提示词
        """
        data = self._load_yaml("deep_research.yaml")
        template = data["community_analysis_prompt"]
        return template.format(**kwargs)

    def get_risk_assessment_prompt(self, **kwargs) -> str:
        """
        获取风险评估提示词

        Args:
            **kwargs: 格式化参数

        Returns:
            str: 格式化后的提示词
        """
        data = self._load_yaml("deep_research.yaml")
        template = data["risk_assessment_prompt"]
        return template.format(**kwargs)

    def get_competitor_analysis_prompt(self, **kwargs) -> str:
        """
        获取竞品分析提示词

        Args:
            **kwargs: 格式化参数

        Returns:
            str: 格式化后的提示词
        """
        data = self._load_yaml("deep_research.yaml")
        template = data["competitor_analysis_prompt"]
        return template.format(**kwargs)

    def get_full_report_structure(self, **kwargs) -> str:
        """
        获取完整报告结构

        Args:
            **kwargs: 格式化参数

        Returns:
            str: 格式化后的报告结构
        """
        data = self._load_yaml("deep_research.yaml")
        template = data["full_report_structure"]
        return template.format(**kwargs)

    # ================================
    # 辅助方法
    # ================================

    def reload_cache(self):
        """清空缓存并重新加载"""
        self._cache.clear()

    def list_available_prompts(self) -> Dict[str, list]:
        """
        列出所有可用的提示词

        Returns:
            Dict: 按文件分类的提示词列表
        """
        available = {}

        for yaml_file in self.prompts_dir.glob("*.yaml"):
            try:
                data = self._load_yaml(yaml_file.name)
                available[yaml_file.stem] = list(data.keys())
            except Exception as e:
                print(f"⚠️ 加载 {yaml_file.name} 失败: {e}")

        return available


# ================================
# 全局实例
# ================================

prompt_manager = PromptManager()
