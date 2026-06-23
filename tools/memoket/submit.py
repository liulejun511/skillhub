"""submit：把一个现成技能放进 sandbox/skills/ 并过一遍 CI 闸，一步备好投稿。

接受 `~/.claude/skills/<name>/`(用户级技能)或任意路径的技能,拷进 sandbox,
立刻跑 gate,告诉你过没过、下一步做什么。把「放哪 + 格式 + 自查」压成一条命令。
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Dict, Optional

from memoket import paths
from memoket.errors import ConflictError, SkillNotFoundError
from memoket.skill import SKILL_ENTRY


def _resolve_source(name_or_path: str) -> Path:
    """按「路径」或「~/.claude/skills/<name>」解析出技能源目录。"""
    p = Path(name_or_path)
    if (p / SKILL_ENTRY).exists():
        return p
    user_skill = Path(os.path.expanduser("~")) / ".claude" / "skills" / name_or_path
    if (user_skill / SKILL_ENTRY).exists():
        return user_skill
    raise SkillNotFoundError(
        f"找不到技能：{name_or_path}（既不是带 SKILL.md 的路径，也不在 ~/.claude/skills/ 下）")


def submit_skill(name_or_path: str, root: Optional[Path] = None) -> Dict:
    """把技能拷进 sandbox/skills/<name>/ 并过闸。返回 {name, dst, report}。"""
    base = root or paths.workspace()
    src = _resolve_source(name_or_path)
    name = src.name

    dst = paths.sandbox_skills(base) / name
    if dst.exists():
        raise ConflictError(f"sandbox 已有同名技能：{name}（先改名或删掉旧的）")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dst)

    from memoket import ci

    report = ci.gate_skill(dst)
    return {"name": name, "dst": str(dst), "report": report}
