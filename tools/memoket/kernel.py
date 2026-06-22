"""受保护内核：标记一组不可被工具自动修改的不变量。

自修改系统必须有不可自修改的核（设计 H1）。tool-retro 的任何自动改动若触及
KERNEL.lock 覆盖的文件/规则，必须被拒绝、要求人工介入。
"""
from __future__ import annotations

import fnmatch
import json
from pathlib import Path
from typing import List, Optional

from memoket import paths
from memoket.errors import MemoketError


class KernelViolation(MemoketError):
    """自动改动试图触及受保护内核。"""


def load_kernel(root: Optional[Path] = None) -> dict:
    p = paths.kernel_path(root)
    if not p.exists():
        return {"version": 1, "protected_paths": [], "protected_rules": []}
    return json.loads(p.read_text(encoding="utf-8"))


def protected_paths(root: Optional[Path] = None) -> List[str]:
    return list(load_kernel(root).get("protected_paths", []))


def is_protected(rel_path: str, root: Optional[Path] = None) -> bool:
    """判断某工作区相对路径是否落在受保护范围。"""
    rel = rel_path.replace("\\", "/")
    for pattern in protected_paths(root):
        if fnmatch.fnmatch(rel, pattern) or rel == pattern or rel.startswith(pattern.rstrip("/*") + "/"):
            return True
    return False


def assert_changes_allowed(changed_rel_paths: List[str], root: Optional[Path] = None) -> None:
    """若任一改动路径触及受保护内核则抛 KernelViolation（供自动改动闸调用）。"""
    violations = [p for p in changed_rel_paths if is_protected(p, root)]
    if violations:
        raise KernelViolation(
            "自动改动触及受保护内核，已拒绝（需人工修改）：\n  - " + "\n  - ".join(violations)
        )
