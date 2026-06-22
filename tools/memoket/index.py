"""技能检索索引：规模化去重与「找对的技能」（设计 H5）。

v1 用离线、零依赖的**词法相似度**（token 集合 Jaccard）；不依赖 embedding API。
随技能增删增量更新。后续可替换为向量索引而不改调用方。
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from memoket import paths
from memoket.skill import SKILL_ENTRY, parse_skill

# 英文/数字按词切；中文连续段单独取出，再切成重叠 bigram（提升区分度，
# 避免单字 token 噪声把不同主题搅成一团）。
_EN_RE = re.compile(r"[a-z0-9]+")
_CJK_RUN_RE = re.compile(r"[一-鿿]+")


def tokens(text: str) -> set:
    text = (text or "").lower()
    out = set(_EN_RE.findall(text))
    for run in _CJK_RUN_RE.findall(text):
        if len(run) == 1:
            out.add(run)
        else:
            out.update(run[i:i + 2] for i in range(len(run) - 1))  # 重叠 bigram
    return out


def _skill_tokens(skill_dir: Path) -> set:
    skill = parse_skill(skill_dir)
    return tokens(" ".join([skill.name or "", skill.description or "", skill.body]))


def _all_skill_dirs(root: Optional[Path]) -> List[Path]:
    dirs = []
    for base in (paths.vault_mine(root), paths.vault_installed(root)):
        if base.exists():
            for md in sorted(base.rglob(SKILL_ENTRY)):
                dirs.append(md.parent)
    return dirs


def build_index(root: Optional[Path] = None) -> Dict[str, List[str]]:
    idx = {d.name: sorted(_skill_tokens(d)) for d in _all_skill_dirs(root)}
    _save(idx, root)
    return idx


def _save(idx: Dict[str, List[str]], root: Optional[Path]) -> None:
    p = paths.index_path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(idx, ensure_ascii=False) + "\n", encoding="utf-8")


def _load(root: Optional[Path]) -> Dict[str, List[str]]:
    p = paths.index_path(root)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def update_skill(name: str, skill_dir: Path, root: Optional[Path] = None) -> None:
    idx = _load(root)
    idx[name] = sorted(_skill_tokens(skill_dir))
    _save(idx, root)


def remove_skill(name: str, root: Optional[Path] = None) -> None:
    idx = _load(root)
    idx.pop(name, None)
    _save(idx, root)


def _jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b)


def nearest(query: str, k: int = 5, root: Optional[Path] = None,
            is_name: bool = False) -> List[Tuple[str, float]]:
    """返回与 query 最相似的 top-k 技能 [(name, score)]。

    is_name=True 时 query 是已有技能名（用其 token 集合，并排除自身）。
    """
    idx = _load(root)
    if is_name:
        q = set(idx.get(query, []))
    else:
        q = tokens(query)
    scored = [
        (name, _jaccard(q, set(toks)))
        for name, toks in idx.items()
        if not (is_name and name == query)
    ]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:k]
