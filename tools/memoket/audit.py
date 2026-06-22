"""聚合校验：通用层 + 适配器层 + 个人库一致性 + 隐私回归（设计 R5.4 / 任务 12）。"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Sequence

from memoket import lockfile, paths
from memoket.skill import SKILL_ENTRY
from memoket.validate import has_issues, validate_skill

# 不应出现在 vault 内的素材类文件名/后缀（隐私回归）。
_MATERIAL_NAMES = {"distill-request.md", "evolve-request.md"}
_MATERIAL_SUFFIXES = {".transcript"}
# 技能包内允许的文件/目录。
_ALLOWED_TOP = {"SKILL.md", "evolution.json", "scripts", "reference"}


def _skill_dirs(root: Optional[Path]) -> List[Path]:
    dirs = []
    for base in (paths.vault_mine(root), paths.vault_installed(root),
                 paths.vault_archive(root), paths.skills_dir(root)):
        if base.exists():
            for md in sorted(base.rglob(SKILL_ENTRY)):
                dirs.append(md.parent)
    return dirs


def _privacy_regression(root: Optional[Path]) -> List[str]:
    issues = []
    vault = paths.vault(root)
    if vault.exists():
        for f in vault.rglob("*"):
            if f.is_file() and (f.name in _MATERIAL_NAMES or f.suffix in _MATERIAL_SUFFIXES):
                issues.append(f"vault 内混入疑似素材文件: {f.relative_to(root or paths.workspace())}")
    return issues


def _lock_consistency(root: Optional[Path]) -> List[str]:
    issues = []
    installed = paths.vault_installed(root)
    locked = {e["name"] for e in lockfile.load_lock(root).get("skills", [])}
    on_disk = {d.name for d in (installed.iterdir() if installed.exists() else []) if (d / "SKILL.md").exists()}
    for name in on_disk - locked:
        issues.append(f"installed/{name} 无 lock 记录")
    for name in locked - on_disk:
        issues.append(f"lock 记录 {name} 在 installed/ 下缺失")
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
    consistency = _lock_consistency(root)
    if consistency:
        report["<consistency>"] = consistency
    return report
