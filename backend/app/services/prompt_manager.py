"""
提示词管理器
加载和管理YAML格式的提示词模板
"""
import os
from typing import Dict, Any, Optional
import yaml
from pathlib import Path
import jinja2

class PromptManager:
    """
    提示词管理器
    负责加载、缓存和格式化提示词模板
    """
    DEEP_RESEARCH_DIR = "deep_research"

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
            filename: YAML文件名 (e.g., "deep_research/tldr.yaml")

        Returns:
            Dict: YAML内容
        """
        full_filename = filename
        # 检查缓存
        if full_filename in self._cache:
            return self._cache[full_filename]

        # 加载文件
        file_path = self.prompts_dir / full_filename

        if not file_path.exists():
            raise FileNotFoundError(f"提示词文件不存在: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # 缓存结果
        self._cache[full_filename] = data
        return data

    def _render_prompt(self, data: Dict[str, Any], **kwargs) -> str:
        """
        Render the prompt using Jinja2
        """
        env = jinja2.Environment(loader=jinja2.BaseLoader)
        user_template = env.from_string(data["user_prompt_template"])
        rendered_user = user_template.render(**kwargs)

        full_prompt = data["system_prompt"] + "\n\n" + rendered_user

        # Append examples if present
        if "examples" in data and data["examples"]:
            full_prompt += "\n\n## Examples:\n"
            for ex in data["examples"][:3]:  # Limit to 3 examples
                full_prompt += f"Input: {ex.get('input', 'N/A')}\nOutput: {ex.get('output', 'N/A')}\n\n"

        return full_prompt

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
    # Deep Research 提示词 - Updated to individual files
    # ================================

    def get_tldr_prompt(self, **kwargs) -> str:
        """
        获取TL;DR生成提示词
        """
        filename = f"{self.DEEP_RESEARCH_DIR}/tldr.yaml"
        data = self._load_yaml(filename)
        return self._render_prompt(data, **kwargs)

    def get_timeframe_prompt(self, **kwargs) -> str:
        """
        获取时间窗分析提示词
        """
        filename = f"{self.DEEP_RESEARCH_DIR}/timeframe.yaml"
        data = self._load_yaml(filename)
        return self._render_prompt(data, **kwargs)

    def get_technical_prompt(self, **kwargs) -> str:
        """
        获取技术面分析提示词
        """
        filename = f"{self.DEEP_RESEARCH_DIR}/technical.yaml"
        data = self._load_yaml(filename)
        return self._render_prompt(data, **kwargs)

    def get_tokenomics_prompt(self, **kwargs) -> str:
        """
        获取代币经济学分析提示词
        """
        filename = f"{self.DEEP_RESEARCH_DIR}/tokenomics.yaml"
        data = self._load_yaml(filename)
        return self._render_prompt(data, **kwargs)

    def get_onchain_prompt(self, **kwargs) -> str:
        """
        获取链上数据分析提示词
        """
        filename = f"{self.DEEP_RESEARCH_DIR}/onchain.yaml"
        data = self._load_yaml(filename)
        return self._render_prompt(data, **kwargs)

    def get_sentiment_prompt(self, **kwargs) -> str:
        """
        获取社媒情绪分析提示词
        """
        filename = f"{self.DEEP_RESEARCH_DIR}/sentiment.yaml"
        data = self._load_yaml(filename)
        return self._render_prompt(data, **kwargs)

    def get_competitor_prompt(self, **kwargs) -> str:
        """
        获取竞品分析提示词
        """
        filename = f"{self.DEEP_RESEARCH_DIR}/competitor.yaml"
        data = self._load_yaml(filename)
        return self._render_prompt(data, **kwargs)

    def get_risk_prompt(self, **kwargs) -> str:
        """
        获取风险评估提示词
        """
        filename = f"{self.DEEP_RESEARCH_DIR}/risk.yaml"
        data = self._load_yaml(filename)
        return self._render_prompt(data, **kwargs)

    def get_conclusion_prompt(self, **kwargs) -> str:
        """
        获取结论合成提示词
        """
        filename = f"{self.DEEP_RESEARCH_DIR}/conclusion.yaml"
        data = self._load_yaml(filename)
        return self._render_prompt(data, **kwargs)

    # Legacy methods - map to new
    def get_overview_prompt(self, **kwargs) -> str:
        """Legacy: Map to conclusion for overview"""
        return self.get_conclusion_prompt(**kwargs)

    def get_market_analysis_prompt(self, **kwargs) -> str:
        """Legacy: Map to tokenomics or onchain"""
        return self.get_tokenomics_prompt(**kwargs)

    def get_community_analysis_prompt(self, **kwargs) -> str:
        """Legacy: Map to sentiment"""
        return self.get_sentiment_prompt(**kwargs)

    def get_risk_assessment_prompt(self, **kwargs) -> str:
        """Legacy: Already matches"""
        return self.get_risk_prompt(**kwargs)

    def get_competitor_analysis_prompt(self, **kwargs) -> str:
        """Legacy: Already matches"""
        return self.get_competitor_prompt(**kwargs)

    def get_full_report_structure(self, **kwargs) -> str:
        """
        获取完整报告结构 - keep loading from deep_research.yaml if exists
        """
        try:
            data = self._load_yaml("deep_research.yaml")
            template = data["full_report_structure"]
            return template.format(**kwargs)
        except FileNotFoundError:
            # Fallback to basic structure
            return "Basic report structure: TL;DR, Overview, Analysis, Conclusion"

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
        deep_dir = self.prompts_dir / self.DEEP_RESEARCH_DIR

        if deep_dir.exists():
            for yaml_file in deep_dir.glob("*.yaml"):
                try:
                    data = self._load_yaml(f"{self.DEEP_RESEARCH_DIR}/{yaml_file.name}")
                    available[yaml_file.stem] = {
                        "version": data.get("version", "unknown"),
                        "description": data.get("description", "No description"),
                        "variables": len(data.get("variables", []))
                    }
                except Exception as e:
                    print(f"⚠️ 加载 {yaml_file.name} 失败: {e}")

        # System prompts
        try:
            sys_data = self._load_yaml("system_prompts.yaml")
            available["system"] = list(sys_data.keys())
        except Exception as e:
            print(f"⚠️ 加载 system_prompts.yaml 失败: {e}")

        return available


# ================================
# 全局实例
# ================================

prompt_manager = PromptManager()
