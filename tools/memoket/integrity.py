"""技能包完整性哈希：可复现、可校验篡改。"""
from __future__ import annotations

import hashlib
from pathlib import Path


def hash_package(pkg_dir: Path) -> str:
    """对技能包目录内所有文件求稳定哈希（与文件遍历顺序无关）。"""
    pkg_dir = Path(pkg_dir)
    h = hashlib.sha256()
    for f in sorted(p for p in pkg_dir.rglob("*") if p.is_file()):
        rel = f.relative_to(pkg_dir).as_posix()
        h.update(rel.encode("utf-8"))
        h.update(b"\0")
        h.update(f.read_bytes())
        h.update(b"\0")
    return "sha256-" + h.hexdigest()
