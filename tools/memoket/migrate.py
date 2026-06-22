"""格式迁移 runner：格式契约升级时批量迁移存量技能（设计 H7 / R14.4）。

v1 的迁移规则：未声明 format_version 的技能补上当前版本。后续格式演进时在
_MIGRATIONS 里追加从 N→N+1 的转换函数。
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict, List, Optional

from memoket import paths
from memoket.skill import CURRENT_FORMAT_VERSION, SKILL_ENTRY, parse_skill, write_skill

# 版本 N -> N+1 的 frontmatter 转换函数。当前无结构性迁移。
_MIGRATIONS: Dict[int, Callable[[dict], dict]] = {}


def needs_migration(format_version: int) -> bool:
    return format_version < CURRENT_FORMAT_VERSION


def _migrate_frontmatter(fm: dict, from_version: int) -> dict:
    v = from_version
    while v < CURRENT_FORMAT_VERSION:
        transform = _MIGRATIONS.get(v)
        if transform:
            fm = transform(fm)
        v += 1
    fm["format_version"] = CURRENT_FORMAT_VERSION
    return fm


def migrate_all(root: Optional[Path] = None) -> List[str]:
    """迁移 vault 下所有技能，返回被迁移的技能名列表。"""
    migrated: List[str] = []
    for base in (paths.vault_mine(root), paths.vault_installed(root), paths.vault_archive(root)):
        if not base.exists():
            continue
        for md in sorted(base.rglob(SKILL_ENTRY)):
            skill = parse_skill(md.parent)
            fv = skill.format_version
            if needs_migration(fv) or "format_version" not in skill.frontmatter:
                fm = _migrate_frontmatter(dict(skill.frontmatter), fv)
                write_skill(md.parent, fm, skill.body)
                migrated.append(skill.name or md.parent.name)
    return migrated
