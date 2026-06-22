"""build：把技能编译成目标适配器形态。"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from memoket import paths
from memoket.adapters import get_adapter
from memoket.errors import MissingFieldError
from memoket.skill import parse_skill
from memoket.validate import validate_adapter


def build_skill(skill_path, adapter_name: str, out_root: Optional[Path] = None) -> Path:
    """构建单个技能；缺适配器字段则抛 MissingFieldError（指明补齐位置）。"""
    skill = parse_skill(skill_path)
    issues = validate_adapter(skill, adapter_name)
    if issues:
        raise MissingFieldError(
            f"无法为适配器 '{adapter_name}' 构建技能 '{skill.name}'：\n  - "
            + "\n  - ".join(issues)
        )
    adapter = get_adapter(adapter_name)
    out_dir = (out_root or paths.build_dir()) / adapter_name
    out_dir.mkdir(parents=True, exist_ok=True)
    return adapter.build(skill, out_dir)
