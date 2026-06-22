"""运行时适配器：把通用技能编译为某运行时可消费的形态。

架构红线：新增适配器不得要求改动通用 SKILL.md 核心契约；
运行时专属字段一律取自 skill.adapters.<name>.*。
"""
from __future__ import annotations

from typing import Dict, List, Protocol, runtime_checkable
from pathlib import Path

from memoket.skill import SkillPackage


@runtime_checkable
class Adapter(Protocol):
    name: str

    def required_fields(self) -> List[str]:
        """该运行时需要的 adapters.<name>.* 字段名列表。"""
        ...

    def build(self, skill: SkillPackage, out_dir: Path) -> Path:
        """把技能编译到 out_dir，返回产物目录。"""
        ...


_REGISTRY: Dict[str, "Adapter"] = {}


def register(adapter: "Adapter") -> None:
    _REGISTRY[adapter.name] = adapter


def get_adapter(name: str) -> "Adapter":
    if name not in _REGISTRY:
        raise KeyError(f"未知适配器: {name}（可用: {', '.join(sorted(_REGISTRY)) or '无'}）")
    return _REGISTRY[name]


def available() -> List[str]:
    return sorted(_REGISTRY)


# 注册内置适配器
from memoket.adapters.claude_code import ClaudeCodeAdapter  # noqa: E402

register(ClaudeCodeAdapter())
