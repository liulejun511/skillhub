"""memoket.lock：已安装技能的锁定记录。"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from memoket import paths

LOCK_VERSION = 1


def load_lock(root: Optional[Path] = None) -> Dict:
    p = paths.lockfile_path(root)
    if not p.exists():
        return {"version": LOCK_VERSION, "skills": []}
    return json.loads(p.read_text(encoding="utf-8"))


def save_lock(lock: Dict, root: Optional[Path] = None) -> None:
    paths.lockfile_path(root).write_text(
        json.dumps(lock, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def get_entry(name: str, root: Optional[Path] = None) -> Optional[Dict]:
    for entry in load_lock(root).get("skills", []):
        if entry.get("name") == name:
            return entry
    return None


def upsert_entry(entry: Dict, root: Optional[Path] = None) -> None:
    lock = load_lock(root)
    skills: List[Dict] = lock.setdefault("skills", [])
    for i, existing in enumerate(skills):
        if existing.get("name") == entry["name"]:
            skills[i] = entry
            break
    else:
        skills.append(entry)
    save_lock(lock, root)


def remove_entry(name: str, root: Optional[Path] = None) -> None:
    lock = load_lock(root)
    lock["skills"] = [s for s in lock.get("skills", []) if s.get("name") != name]
    save_lock(lock, root)
