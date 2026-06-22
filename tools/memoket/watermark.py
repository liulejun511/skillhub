"""演化水位：记录「处理到哪了」，支撑增量与幂等。

成功收尾才推进水位；失败不推进 → 下轮重试同批（设计 H6 幂等）。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from memoket import paths

WM_VERSION = 1


def load(root: Optional[Path] = None) -> dict:
    p = paths.watermark_path(root)
    if not p.exists():
        return {"version": WM_VERSION, "user_id": None, "last_processed_at": None, "last_cycle": None}
    return json.loads(p.read_text(encoding="utf-8"))


def save(wm: dict, root: Optional[Path] = None) -> None:
    paths.watermark_path(root).write_text(
        json.dumps(wm, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def get_last_processed(root: Optional[Path] = None) -> Optional[str]:
    return load(root).get("last_processed_at")


def advance(processed_at: str, user_id: Optional[str] = None, cursor: Optional[str] = None,
            root: Optional[Path] = None) -> dict:
    """成功收尾：推进水位。"""
    wm = load(root)
    wm["last_processed_at"] = processed_at
    if user_id is not None:
        wm["user_id"] = user_id
    wm["last_cycle"] = {"status": "success", "cursor": cursor}
    save(wm, root)
    return wm


def record_failure(root: Optional[Path] = None) -> dict:
    """失败收尾：不推进水位，仅记录状态。"""
    wm = load(root)
    last = wm.get("last_cycle") or {}
    last["status"] = "failed"
    wm["last_cycle"] = last
    save(wm, root)
    return wm
