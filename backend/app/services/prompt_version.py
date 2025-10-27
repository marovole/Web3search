"""
Prompt版本控制系统（任务 12.1）

功能：
1. Prompt版本管理
2. 变更历史追踪
3. 版本对比
4. 回滚机制（任务12.7完成）
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path


@dataclass
class PromptVersion:
    """Prompt版本"""
    version: str  # 版本号（如：v1.0.0）
    content: str  # Prompt内容
    author: str  # 作者
    created_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    changelog: str = ""  # 变更说明

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "content": self.content,
            "author": self.author,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
            "changelog": self.changelog,
        }


class PromptVersionControl:
    """Prompt版本控制管理器"""

    def __init__(self, prompt_name: str, versions_dir: Optional[Path] = None):
        self.prompt_name = prompt_name
        self.versions_dir = versions_dir or Path(__file__).parent.parent / "data" / "prompt_versions"
        self.versions_dir.mkdir(parents=True, exist_ok=True)

        self.versions: List[PromptVersion] = []
        self._load_versions()

    def _get_version_file(self) -> Path:
        return self.versions_dir / f"{self.prompt_name}.json"

    def _load_versions(self):
        """加载版本历史"""
        file_path = self._get_version_file()
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data.get("versions", []):
                    item["created_at"] = datetime.fromisoformat(item["created_at"])
                    self.versions.append(PromptVersion(**item))

    def _save_versions(self):
        """保存版本历史"""
        file_path = self._get_version_file()
        data = {
            "prompt_name": self.prompt_name,
            "versions": [v.to_dict() for v in self.versions]
        }
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def create_version(
        self,
        content: str,
        author: str,
        version: Optional[str] = None,
        changelog: str = ""
    ) -> PromptVersion:
        """创建新版本"""
        if not version:
            # 自动版本号
            if self.versions:
                last_v = self.versions[-1].version
                major, minor, patch = map(int, last_v.lstrip('v').split('.'))
                version = f"v{major}.{minor}.{patch + 1}"
            else:
                version = "v1.0.0"

        new_version = PromptVersion(
            version=version,
            content=content,
            author=author,
            created_at=datetime.utcnow(),
            changelog=changelog
        )

        self.versions.append(new_version)
        self._save_versions()
        return new_version

    def get_version(self, version: str) -> Optional[PromptVersion]:
        """获取指定版本"""
        for v in self.versions:
            if v.version == version:
                return v
        return None

    def get_latest_version(self) -> Optional[PromptVersion]:
        """获取最新版本"""
        return self.versions[-1] if self.versions else None

    def list_versions(self) -> List[PromptVersion]:
        """列出所有版本"""
        return self.versions


# 便捷函数
def create_prompt_version(prompt_name: str, content: str, author: str, changelog: str = ""):
    """便捷函数：创建Prompt版本"""
    vc = PromptVersionControl(prompt_name)
    return vc.create_version(content, author, changelog=changelog)
