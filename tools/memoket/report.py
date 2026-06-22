"""report：把本轮变更汇总成人类可读 digest。"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Dict, List, Optional

from memoket import paths

_ACTION_LABEL = {"A": "新增", "M": "精炼", "D": "归档/移除", "R": "重命名"}


def build_digest(changes: List[Dict]) -> str:
    """把变更列表格式化为 digest。change: {action, path, note?}。"""
    if not changes:
        return "# 演化 Digest\n\n本轮无变更。\n"
    lines = ["# 演化 Digest\n"]
    by_action: Dict[str, List[Dict]] = {}
    for c in changes:
        by_action.setdefault(c.get("action", "?"), []).append(c)
    for action in sorted(by_action):
        lines.append(f"## {_ACTION_LABEL.get(action, action)}")
        for c in by_action[action]:
            note = f" — {c['note']}" if c.get("note") else ""
            lines.append(f"- {c['path']}{note}")
        lines.append("")
    return "\n".join(lines)


def collect_git_changes(root: Optional[Path] = None) -> List[Dict]:
    """从 git 工作树/暂存区收集 vault/ 下的变更（无 git 时返回空）。"""
    ws = root or paths.workspace()
    try:
        out = subprocess.run(
            ["git", "status", "--porcelain", "vault"],
            cwd=ws, capture_output=True, text=True,
        )
    except (FileNotFoundError, OSError):
        return []
    if out.returncode != 0:
        return []
    changes: List[Dict] = []
    for line in out.stdout.splitlines():
        if not line.strip():
            continue
        code = line[:2].strip()[:1] or "?"
        path = line[3:].strip()
        changes.append({"action": code, "path": path})
    return changes


def report(root: Optional[Path] = None) -> str:
    return build_digest(collect_git_changes(root))
