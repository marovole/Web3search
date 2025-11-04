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

    def _validate_template(self, data: Dict[str, Any]) -> bool:
        """
        验证模板包含必需字段

        Args:
            data: YAML模板数据

        Returns:
            bool: 验证是否通过

        Raises:
            ValueError: 缺少必需字段时抛出
        """
        required_fields = ["name", "model", "system"]
        missing = [f for f in required_fields if f not in data]

        if missing:
            raise ValueError(f"模板缺少必需字段: {', '.join(missing)}")

        # 检查至少有一个用户模板字段
        if "user_template" not in data and "user_prompt_template" not in data:
            raise ValueError("模板必须包含 'user_template' 或 'user_prompt_template' 字段")

        return True

    def _render_prompt(self, data: Dict[str, Any], **kwargs) -> str:
        """
        使用Jinja2渲染prompt
        支持新旧两种模板格式
        """
        # 验证模板
        self._validate_template(data)

        env = jinja2.Environment(loader=jinja2.BaseLoader)

        # 兼容新旧字段名
        user_template_str = data.get("user_template") or data.get("user_prompt_template")
        system_prompt_str = data.get("system") or data.get("system_prompt")

        user_template = env.from_string(user_template_str)
        rendered_user = user_template.render(**kwargs)

        full_prompt = system_prompt_str + "\n\n" + rendered_user

        # 兼容新旧示例字段名
        examples = data.get("few_shot_examples") or data.get("examples")
        if examples:
            full_prompt += "\n\n## Examples:\n"
            for ex in examples[:3]:  # Limit to 3 examples
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
        """获取TL;DR生成提示词"""
        filename = f"{self.DEEP_RESEARCH_DIR}/tldr.yaml"
        data = self._load_yaml(filename)
        return self._render_prompt(data, **kwargs)

    def get_fundamental_analysis_prompt(self, **kwargs) -> str:
        """获取基本面分析提示词"""
        filename = f"{self.DEEP_RESEARCH_DIR}/fundamental_analysis.yaml"
        data = self._load_yaml(filename)
        return self._render_prompt(data, **kwargs)

    def get_technical_analysis_prompt(self, **kwargs) -> str:
        """获取技术分析提示词"""
        filename = f"{self.DEEP_RESEARCH_DIR}/technical_analysis.yaml"
        data = self._load_yaml(filename)
        return self._render_prompt(data, **kwargs)

    def get_competitor_analysis_prompt(self, **kwargs) -> str:
        """获取竞品对比分析提示词"""
        filename = f"{self.DEEP_RESEARCH_DIR}/competitor_analysis.yaml"
        data = self._load_yaml(filename)
        return self._render_prompt(data, **kwargs)

    def get_risk_assessment_prompt(self, **kwargs) -> str:
        """获取风险评估提示词"""
        filename = f"{self.DEEP_RESEARCH_DIR}/risk_assessment.yaml"
        data = self._load_yaml(filename)
        return self._render_prompt(data, **kwargs)

    # Legacy methods for backward compatibility
    def get_timeframe_prompt(self, **kwargs) -> str:
        """获取时间窗分析提示词（如果存在）"""
        try:
            filename = f"{self.DEEP_RESEARCH_DIR}/timeframe.yaml"
            data = self._load_yaml(filename)
            return self._render_prompt(data, **kwargs)
        except FileNotFoundError:
            # Fallback to technical analysis
            return self.get_technical_analysis_prompt(**kwargs)

    def get_technical_prompt(self, **kwargs) -> str:
        """Legacy: 映射到技术分析"""
        return self.get_technical_analysis_prompt(**kwargs)

    def get_tokenomics_prompt(self, **kwargs) -> str:
        """获取代币经济学分析提示词（如果存在）"""
        try:
            filename = f"{self.DEEP_RESEARCH_DIR}/tokenomics.yaml"
            data = self._load_yaml(filename)
            return self._render_prompt(data, **kwargs)
        except FileNotFoundError:
            # Fallback to fundamental analysis
            return self.get_fundamental_analysis_prompt(**kwargs)

    def get_onchain_prompt(self, **kwargs) -> str:
        """获取链上数据分析提示词（如果存在）"""
        try:
            filename = f"{self.DEEP_RESEARCH_DIR}/onchain.yaml"
            data = self._load_yaml(filename)
            return self._render_prompt(data, **kwargs)
        except FileNotFoundError:
            # Fallback to fundamental analysis
            return self.get_fundamental_analysis_prompt(**kwargs)

    def get_sentiment_prompt(self, **kwargs) -> str:
        """获取社媒情绪分析提示词（如果存在）"""
        try:
            filename = f"{self.DEEP_RESEARCH_DIR}/sentiment.yaml"
            data = self._load_yaml(filename)
            return self._render_prompt(data, **kwargs)
        except FileNotFoundError:
            # Placeholder for future implementation
            return "社媒情绪分析暂未实现"

    def get_competitor_prompt(self, **kwargs) -> str:
        """Legacy: 映射到竞品分析"""
        return self.get_competitor_analysis_prompt(**kwargs)

    def get_risk_prompt(self, **kwargs) -> str:
        """Legacy: 映射到风险评估"""
        return self.get_risk_assessment_prompt(**kwargs)

    def get_conclusion_prompt(self, **kwargs) -> str:
        """获取结论合成提示词（如果存在）"""
        try:
            filename = f"{self.DEEP_RESEARCH_DIR}/conclusion.yaml"
            data = self._load_yaml(filename)
            return self._render_prompt(data, **kwargs)
        except FileNotFoundError:
            # Placeholder for future implementation
            return "结论合成分析暂未实现"

    # Additional legacy mappings
    def get_overview_prompt(self, **kwargs) -> str:
        """Legacy: 映射到结论合成"""
        return self.get_conclusion_prompt(**kwargs)

    def get_market_analysis_prompt(self, **kwargs) -> str:
        """Legacy: 映射到基本面分析"""
        return self.get_fundamental_analysis_prompt(**kwargs)

    def get_community_analysis_prompt(self, **kwargs) -> str:
        """Legacy: 映射到社媒情绪分析"""
        return self.get_sentiment_prompt(**kwargs)

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

    def get_template_metadata(self, template_name: str) -> Dict[str, Any]:
        """
        获取模板元数据（版本、模型配置等）

        Args:
            template_name: 模板名称（不含.yaml后缀）

        Returns:
            Dict: 包含版本、模型、温度等元数据
        """
        filename = f"{self.DEEP_RESEARCH_DIR}/{template_name}.yaml"
        data = self._load_yaml(filename)

        return {
            "name": data.get("name"),
            "version": data.get("version", "1.0.0"),
            "description": data.get("description", ""),
            "model": data.get("model"),
            "temperature": data.get("temperature", 0.7),
            "max_tokens": data.get("max_tokens", 500),
        }

    def get_template_with_config(self, template_name: str, **kwargs) -> Dict[str, Any]:
        """
        获取渲染后的prompt和模型配置

        Args:
            template_name: 模板名称（不含.yaml后缀）
            **kwargs: 模板变量

        Returns:
            Dict: 包含prompt、model、temperature、max_tokens
        """
        filename = f"{self.DEEP_RESEARCH_DIR}/{template_name}.yaml"
        data = self._load_yaml(filename)

        rendered_prompt = self._render_prompt(data, **kwargs)

        return {
            "prompt": rendered_prompt,
            "model": data.get("model", "qwen/qwen-2.5-72b-instruct:free"),
            "temperature": data.get("temperature", 0.7),
            "max_tokens": data.get("max_tokens", 500),
        }

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
                        "name": data.get("name", yaml_file.stem),
                        "version": data.get("version", "unknown"),
                        "description": data.get("description", "No description"),
                        "model": data.get("model", "N/A"),
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
