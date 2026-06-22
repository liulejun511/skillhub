"""多语言 locale 同步：主 locale 演化后，其余标 stale（设计 H7 / R14.3）。"""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from memoket.skill import parse_skill, write_skill


def mark_others_stale(skill_dir, primary_lang: str, root: Optional[Path] = None) -> List[str]:
    """把除 primary_lang 外的 locale 标记为 sync=stale，返回被标记的语言码。"""
    skill = parse_skill(skill_dir)
    fm = dict(skill.frontmatter)
    locales = fm.get("locales") or {}
    marked = []
    for lang, content in locales.items():
        if lang == primary_lang:
            if isinstance(content, dict):
                content["sync"] = "fresh"
            continue
        if isinstance(content, dict):
            content["sync"] = "stale"
            marked.append(lang)
    if marked or primary_lang in locales:
        fm["locales"] = locales
        write_skill(Path(skill_dir), fm, skill.body)
    return marked
