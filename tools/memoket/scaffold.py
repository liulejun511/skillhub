"""new：生成合规的空技能脚手架。"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from memoket import paths
from memoket.errors import ConflictError
from memoket.skill import CURRENT_FORMAT_VERSION

_SKELETON = """\
---
name: {name}
description: Use when ...（填写触发场景：何时该用这个技能）
version: 0.1.0
format_version: {fmt}
status: draft
origin: authored
---

# {title}

## 为何优秀 / 有益
（这个能力好在哪、为何值得复用或学习）

## 任务 (Task)
（这个技能要完成什么）

## 判断重点 (Judgment focus)
- （关注什么、如何判断）

## 规则 (Rules)
- （硬约束，例如：以证据为准、不编造）

## 输出 / 行动结构 (Output / Action)
（产物的结构或要采取的行动）
"""


def _title_from_name(name: str) -> str:
    return " ".join(w.capitalize() for w in name.split("-"))


def new_skill(name: str, root: Optional[Path] = None) -> Path:
    """在 vault/mine/<name>/ 生成空技能；已存在则抛 ConflictError。"""
    target_dir = paths.vault_mine(root) / name
    skill_md = target_dir / "SKILL.md"
    if skill_md.exists():
        raise ConflictError(f"技能已存在，未覆盖: {skill_md}")
    target_dir.mkdir(parents=True, exist_ok=True)
    skill_md.write_text(
        _SKELETON.format(name=name, title=_title_from_name(name), fmt=CURRENT_FORMAT_VERSION),
        encoding="utf-8",
    )
    return skill_md
