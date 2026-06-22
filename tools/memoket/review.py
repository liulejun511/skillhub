"""review 分支生命周期：超期提醒 + 冲突提示（设计 H7 / R14.5）。

自动循环把变更提交到 review 分支（约定前缀 `review/`）。本模块帮用户发现
长期未审阅的分支，并对将合入主干的分支做最佳努力的冲突预判。
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import List, Optional

from memoket import paths

REVIEW_PREFIX = "review/"


def _git(args: List[str], root: Optional[Path]) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=(root or paths.workspace()), capture_output=True, text=True
    )


def list_review_branches(root: Optional[Path] = None) -> List[str]:
    out = _git(["for-each-ref", "--format=%(refname:short)", "refs/heads"], root)
    if out.returncode != 0:
        return []
    return [b for b in out.stdout.split() if b.startswith(REVIEW_PREFIX)]


def branch_age_seconds(branch: str, root: Optional[Path] = None) -> Optional[int]:
    out = _git(["log", "-1", "--format=%ct", branch], root)
    if out.returncode != 0 or not out.stdout.strip():
        return None
    last = int(out.stdout.strip())
    now = _git(["log", "-1", "--format=%ct", "HEAD"], root)
    head_ts = int(now.stdout.strip()) if now.returncode == 0 and now.stdout.strip() else last
    return max(0, head_ts - last)


def stale_review_branches(max_age_seconds: int, root: Optional[Path] = None) -> List[str]:
    """返回相对 HEAD 的最后提交早于阈值的 review 分支（超期未审阅提醒）。"""
    stale = []
    for b in list_review_branches(root):
        age = branch_age_seconds(b, root)
        if age is not None and age >= max_age_seconds:
            stale.append(b)
    return stale


def would_conflict(branch: str, base: str = "HEAD", root: Optional[Path] = None) -> Optional[bool]:
    """最佳努力的冲突预判：返回 True/False，无法判断时返回 None。"""
    out = _git(["merge-tree", "--write-tree", base, branch], root)
    if out.returncode not in (0, 1):
        return None
    # git merge-tree 在有冲突时输出含 'CONFLICT' 标记
    return "CONFLICT" in (out.stdout + out.stderr)
