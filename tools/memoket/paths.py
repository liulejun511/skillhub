"""工作区路径布局（skillhub git 树）。

工具运行在仓库根（可用 SKILLHUB_HOME / MEMOKET_HOME 覆盖）。技能活在两棵树：
- sandbox/skills/<name>/          人人 PR 的未策展技能（也是 new/scaffold 的落点）
- plugins/<plugin>/skills/<name>/ 已策展、随原生 marketplace 分发的技能
归档移入 .archive/（绝不删除，可 restore）。schemas/ 随包发布，按包相对路径定位。
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional

# 包位于 <repo>/tools/memoket/；仓库根（含 plugins/ sandbox/）在其上两级。
_REPO_ROOT = Path(__file__).resolve().parents[2]


def workspace() -> Path:
    """当前工作区根（仓库根，含 plugins/ 与 sandbox/）：SKILLHUB_HOME / MEMOKET_HOME，否则推断。"""
    env = os.environ.get("SKILLHUB_HOME") or os.environ.get("MEMOKET_HOME")
    return Path(env).resolve() if env else _REPO_ROOT


def sandbox_dir(root: Optional[Path] = None) -> Path:
    """未策展沙盒区根。"""
    return (root or workspace()) / "sandbox"


def sandbox_skills(root: Optional[Path] = None) -> Path:
    """沙盒技能目录；new/scaffold 落点。"""
    return sandbox_dir(root) / "skills"


def curated_dir(root: Optional[Path] = None) -> Path:
    """已策展插件根；技能在 plugins/<plugin>/skills/<name>/。"""
    return (root or workspace()) / "plugins"


def archive_dir(root: Optional[Path] = None) -> Path:
    """归档区（绝不删除，可 restore）。"""
    return (root or workspace()) / ".archive"


def skill_roots(root: Optional[Path] = None) -> List[Path]:
    """扫描 SKILL.md 的活跃技能根：sandbox + curated（不含 archive）。"""
    return [sandbox_skills(root), curated_dir(root)]


def find_skill(name: str, root: Optional[Path] = None) -> Optional[Path]:
    """按名在活跃技能根里定位技能目录（首个命中）。沙盒平铺、curated 嵌套。"""
    from memoket.skill import SKILL_ENTRY

    direct = sandbox_skills(root) / name
    if (direct / SKILL_ENTRY).exists():
        return direct
    curated = curated_dir(root)
    if curated.exists():
        for md in sorted(curated.rglob(SKILL_ENTRY)):
            if md.parent.name == name:
                return md.parent
    return None


def build_dir(root: Optional[Path] = None) -> Path:
    return (root or workspace()) / "build"
