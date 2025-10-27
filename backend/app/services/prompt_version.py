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

    def rollback_to_version(
        self,
        target_version: str,
        author: str,
        reason: str = ""
    ) -> PromptVersion:
        """
        回滚到指定版本（任务12.7）

        Args:
            target_version: 目标版本号
            author: 操作者
            reason: 回滚原因

        Returns:
            PromptVersion: 新创建的版本（内容是target_version的内容）
        """
        # 查找目标版本
        target = self.get_version(target_version)
        if not target:
            raise ValueError(f"版本不存在: {target_version}")

        # 获取当前版本号
        current = self.get_latest_version()
        if not current:
            raise ValueError("没有当前版本")

        # 创建新版本（内容回滚，但版本号递增）
        new_version = self.create_version(
            content=target.content,
            author=author,
            changelog=f"回滚到 {target_version}。原因: {reason}"
        )

        return new_version

    def get_version_at_index(self, index: int) -> Optional[PromptVersion]:
        """
        获取指定索引的版本

        Args:
            index: 版本索引（-1表示最新，-2表示上一个）

        Returns:
            Optional[PromptVersion]: 版本对象
        """
        if not self.versions:
            return None

        try:
            return self.versions[index]
        except IndexError:
            return None

    def rollback_to_previous(self, author: str, reason: str = "") -> PromptVersion:
        """
        回滚到上一个版本（任务12.7）

        Args:
            author: 操作者
            reason: 回滚原因

        Returns:
            PromptVersion: 新版本
        """
        if len(self.versions) < 2:
            raise ValueError("没有足够的版本历史进行回滚")

        # 获取上一个版本（倒数第二个）
        previous = self.versions[-2]

        return self.rollback_to_version(
            target_version=previous.version,
            author=author,
            reason=reason or "回滚到上一个版本"
        )


# ================================
# 自动回滚系统（任务 12.7）
# ================================

@dataclass
class RollbackPolicy:
    """回滚策略"""
    min_quality_threshold: float = 0.6  # 最低质量阈值
    error_rate_threshold: float = 0.1  # 错误率阈值（10%）
    response_time_threshold_ms: float = 5000  # 响应时间阈值（5秒）
    min_sample_size: int = 10  # 最小样本量
    check_window_minutes: int = 30  # 检查窗口（30分钟）


class AutoRollbackManager:
    """自动回滚管理器（任务12.7）"""

    def __init__(self, policy: Optional[RollbackPolicy] = None):
        """
        初始化自动回滚管理器

        Args:
            policy: 回滚策略
        """
        self.policy = policy or RollbackPolicy()
        self.rollback_history: List[Dict[str, Any]] = []

    def should_rollback(
        self,
        avg_quality_score: float,
        error_rate: float,
        avg_response_time_ms: float,
        sample_size: int
    ) -> Tuple[bool, str]:
        """
        判断是否应该回滚（任务12.7）

        Args:
            avg_quality_score: 平均质量得分
            error_rate: 错误率
            avg_response_time_ms: 平均响应时间
            sample_size: 样本量

        Returns:
            Tuple[bool, str]: (是否回滚, 原因)
        """
        # 样本量不足，不回滚
        if sample_size < self.policy.min_sample_size:
            return False, "样本量不足"

        # 检查质量得分
        if avg_quality_score < self.policy.min_quality_threshold:
            reason = f"质量得分过低：{avg_quality_score:.3f} < {self.policy.min_quality_threshold}"
            return True, reason

        # 检查错误率
        if error_rate > self.policy.error_rate_threshold:
            reason = f"错误率过高：{error_rate:.1%} > {self.policy.error_rate_threshold:.1%}"
            return True, reason

        # 检查响应时间
        if avg_response_time_ms > self.policy.response_time_threshold_ms:
            reason = f"响应时间过长：{avg_response_time_ms:.0f}ms > {self.policy.response_time_threshold_ms:.0f}ms"
            return True, reason

        return False, "正常"

    def execute_rollback(
        self,
        prompt_name: str,
        reason: str,
        author: str = "system"
    ) -> Dict[str, Any]:
        """
        执行回滚（任务12.7）

        Args:
            prompt_name: Prompt名称
            reason: 回滚原因
            author: 操作者

        Returns:
            Dict[str, Any]: 回滚结果
        """
        try:
            vc = PromptVersionControl(prompt_name)
            current_version = vc.get_latest_version()

            if not current_version:
                return {
                    "success": False,
                    "error": "没有当前版本"
                }

            # 执行回滚到上一个版本
            new_version = vc.rollback_to_previous(
                author=author,
                reason=reason
            )

            # 记录回滚历史
            rollback_record = {
                "timestamp": datetime.utcnow().isoformat(),
                "prompt_name": prompt_name,
                "from_version": current_version.version,
                "to_version": new_version.version,
                "reason": reason,
                "author": author
            }
            self.rollback_history.append(rollback_record)

            return {
                "success": True,
                "from_version": current_version.version,
                "to_version": new_version.version,
                "reason": reason
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def check_and_rollback(
        self,
        prompt_name: str,
        metrics: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        检查指标并自动回滚（任务12.7）

        Args:
            prompt_name: Prompt名称
            metrics: 监控指标

        Returns:
            Optional[Dict[str, Any]]: 回滚结果（如果执行了回滚）
        """
        # 提取指标
        avg_quality = metrics.get("avg_quality_score", 1.0)
        error_rate = metrics.get("error_rate", 0.0)
        avg_response_time = metrics.get("avg_response_time_ms", 0.0)
        sample_size = metrics.get("total_requests", 0)

        # 判断是否需要回滚
        should_rollback, reason = self.should_rollback(
            avg_quality,
            error_rate,
            avg_response_time,
            sample_size
        )

        if should_rollback:
            # 执行回滚
            result = self.execute_rollback(
                prompt_name=prompt_name,
                reason=reason,
                author="auto_rollback_system"
            )
            return result

        return None

    def get_rollback_history(self) -> List[Dict[str, Any]]:
        """获取回滚历史"""
        return self.rollback_history


# 全局实例
auto_rollback_manager = AutoRollbackManager()


# 便捷函数
def create_prompt_version(prompt_name: str, content: str, author: str, changelog: str = ""):
    """便捷函数：创建Prompt版本"""
    vc = PromptVersionControl(prompt_name)
    return vc.create_version(content, author, changelog=changelog)


def rollback_prompt(prompt_name: str, target_version: str, author: str, reason: str = ""):
    """
    便捷函数：回滚Prompt（任务12.7）

    Args:
        prompt_name: Prompt名称
        target_version: 目标版本
        author: 操作者
        reason: 回滚原因

    Returns:
        PromptVersion: 新版本
    """
    vc = PromptVersionControl(prompt_name)
    return vc.rollback_to_version(target_version, author, reason)
