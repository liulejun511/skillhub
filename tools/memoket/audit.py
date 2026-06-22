"""聚合校验：通用层 + 适配器层 + 隐私回归（设计 R5.4）。"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Sequence

from memoket import paths
from memoket.skill import SKILL_ENTRY
from memoket.validate import has_issues, validate_skill

# 不应混入技能树的素材类文件名/后缀（隐私回归红线）。
_MATERIAL_NAMES = {"distill-request.md", "evolve-request.md", "quality-review-request.md"}
_MATERIAL_SUFFIXES = {".transcript"}
# 技能包内允许的顶层文件/目录。
_ALLOWED_TOP = {"SKILL.md", "evolution.json", "scripts", "reference"}


def _skill_dirs(root: Optional[Path]) -> List[Path]:
    dirs = []
    for base in paths.skill_roots(root):
        if base.exists():
            for md in sorted(base.rglob(SKILL_ENTRY)):
                dirs.append(md.parent)
    return dirs


def _privacy_regression(root: Optional[Path]) -> List[str]:
    issues = []
    for tree in (paths.sandbox_dir(root), paths.curated_dir(root)):
        if not tree.exists():
            continue
        for f in tree.rglob("*"):
            if f.is_file() and (f.name in _MATERIAL_NAMES or f.suffix in _MATERIAL_SUFFIXES):
                issues.append(f"技能树内混入疑似素材文件: {f.relative_to(root or paths.workspace())}")
    return issues


def aggregate_validate(root: Optional[Path] = None, adapters: Sequence[str] = ()) -> Dict[str, List[str]]:
    """返回 {target -> 问题列表}；空 dict = 全过。"""
    report: Dict[str, List[str]] = {}
    for d in _skill_dirs(root):
        result = validate_skill(d, adapters)
        if has_issues(result):
            flat = [f"{layer}: {msg}" for layer, msgs in result.items() for msg in msgs]
            report[str(d)] = flat
    privacy = _privacy_regression(root)
    if privacy:
        report["<privacy>"] = privacy
    return report
