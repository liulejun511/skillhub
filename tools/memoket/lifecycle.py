"""技能生命周期与健康指标。

状态：draft → active → deprecated → archived（可逆）。
核心红线：**绝不删除**——归档只是移入 vault/archive/，可 restore（设计 R7.6）。
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Dict, Optional

from memoket import paths
from memoket.errors import ConflictError, MemoketError

LIFECYCLE_STATES = ("draft", "active", "deprecated", "archived")

# 允许的状态流转（含可逆）。
_ALLOWED = {
    "draft": {"active"},
    "active": {"deprecated"},
    "deprecated": {"active", "archived"},
    "archived": {"active"},
}

_DEFAULT_EVOLUTION = {
    "lifecycle": "active",
    "reinforced_count": 0,
    "used_count": None,   # None = 用量未知（园艺不得据此弃用）
    "last_reinforced_at": None,
    "last_used_at": None,
    "last_evolved_at": None,
    "rejected_count": 0,
    "last_reject_reason": None,
}


def _evolution_path(skill_dir: Path) -> Path:
    return Path(skill_dir) / "evolution.json"


def get_evolution(skill_dir: Path) -> Dict:
    p = _evolution_path(skill_dir)
    rec = dict(_DEFAULT_EVOLUTION)
    if p.exists():
        rec.update(json.loads(p.read_text(encoding="utf-8")))
    return rec


def save_evolution(skill_dir: Path, rec: Dict) -> None:
    _evolution_path(skill_dir).write_text(
        json.dumps(rec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def set_lifecycle(skill_dir: Path, new_state: str) -> Dict:
    if new_state not in LIFECYCLE_STATES:
        raise MemoketError(f"非法生命周期状态: {new_state}")
    rec = get_evolution(skill_dir)
    current = rec.get("lifecycle", "active")
    if new_state != current and new_state not in _ALLOWED.get(current, set()):
        raise MemoketError(f"不允许的状态流转: {current} → {new_state}")
    rec["lifecycle"] = new_state
    save_evolution(skill_dir, rec)
    return rec


def reinforce(skill_dir: Path, when: str) -> Dict:
    rec = get_evolution(skill_dir)
    rec["reinforced_count"] = (rec.get("reinforced_count") or 0) + 1
    rec["last_reinforced_at"] = when
    save_evolution(skill_dir, rec)
    return rec


def record_use(skill_dir: Path, when: str) -> Dict:
    rec = get_evolution(skill_dir)
    rec["used_count"] = (rec.get("used_count") or 0) + 1
    rec["last_used_at"] = when
    save_evolution(skill_dir, rec)
    return rec


def record_reject(skill_dir: Path, reason: str) -> Dict:
    rec = get_evolution(skill_dir)
    rec["rejected_count"] = (rec.get("rejected_count") or 0) + 1
    rec["last_reject_reason"] = reason
    save_evolution(skill_dir, rec)
    return rec


def record_surface(skill_dir: Path, when: str) -> Dict:
    """技能在检索中被「呈现」一次（出现在 search 结果里），但不一定被取用。
    用来区分「检索到但没用」vs「真用了」（used_count）。"""
    rec = get_evolution(skill_dir)
    rec["surfaced_count"] = (rec.get("surfaced_count") or 0) + 1
    rec["last_surfaced_at"] = when
    save_evolution(skill_dir, rec)
    return rec


def archive_skill(name: str, root: Optional[Path] = None) -> Path:
    """把技能移入 vault/archive/（无删除）。从 mine 或 installed 查找。"""
    for base in (paths.vault_mine(root), paths.vault_installed(root)):
        src = base / name
        if (src / "SKILL.md").exists():
            dst = paths.vault_archive(root) / name
            if dst.exists():
                raise ConflictError(f"archive 中已有同名: {name}")
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            rec = get_evolution(dst)
            rec["lifecycle"] = "archived"
            save_evolution(dst, rec)
            return dst
    raise MemoketError(f"找不到技能可归档: {name}")


def restore_skill(name: str, root: Optional[Path] = None) -> Path:
    """从 archive 恢复到 vault/mine/。"""
    src = paths.vault_archive(root) / name
    if not (src / "SKILL.md").exists():
        raise MemoketError(f"archive 中无此技能: {name}")
    dst = paths.vault_mine(root) / name
    if dst.exists():
        raise ConflictError(f"vault/mine 已有同名: {name}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))
    rec = get_evolution(dst)
    rec["lifecycle"] = "active"
    save_evolution(dst, rec)
    return dst
