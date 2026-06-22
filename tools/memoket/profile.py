"""用户价值档案：distill 价值判断的对齐输入（设计 H4 / R11.3-4）。"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from memoket import paths

_TEMPLATE = """\
# 我的价值档案（distill 对齐输入）

## 我在意什么
- （待填）

## 什么算「好」的技能
- （待填）

## 领域偏好
- （待填）

## 不要提炼成技能的东西
- （待填）
"""


def ensure_profile(root: Optional[Path] = None) -> Path:
    p = paths.profile_path(root)
    if not p.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(_TEMPLATE, encoding="utf-8")
    return p


def read_profile(root: Optional[Path] = None) -> Optional[str]:
    p = paths.profile_path(root)
    return p.read_text(encoding="utf-8") if p.exists() else None
