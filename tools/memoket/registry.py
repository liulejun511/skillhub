"""registry：技能商店目录的加载与检索。"""
from __future__ import annotations

import functools
import json
from pathlib import Path
from typing import Dict, List, Optional

from jsonschema import Draft202012Validator

from memoket import paths


@functools.lru_cache(maxsize=None)
def _registry_validator() -> Draft202012Validator:
    schema_path = paths.PACKAGE_ROOT / "schemas" / "registry.schema.json"
    return Draft202012Validator(json.loads(schema_path.read_text(encoding="utf-8")))


def load_registry(root: Optional[Path] = None) -> List[Dict]:
    p = paths.registry_path(root)
    if not p.exists():
        return []
    return json.loads(p.read_text(encoding="utf-8"))


def validate_registry(root: Optional[Path] = None) -> List[str]:
    data = load_registry(root)
    errors = sorted(_registry_validator().iter_errors(data), key=lambda e: list(e.path))
    return [f"{'.'.join(str(x) for x in e.path) or '<root>'}: {e.message}" for e in errors]


def find_entry(name: str, root: Optional[Path] = None) -> Optional[Dict]:
    for entry in load_registry(root):
        if entry.get("name") == name:
            return entry
    return None


def search_registry(keyword: str, root: Optional[Path] = None) -> List[Dict]:
    """按名称/描述/标签（大小写不敏感）检索，返回匹配条目摘要。"""
    kw = (keyword or "").lower().strip()
    results = []
    for entry in load_registry(root):
        haystack = " ".join(
            [
                entry.get("name", ""),
                entry.get("description", ""),
                " ".join(entry.get("tags", [])),
            ]
        ).lower()
        if not kw or kw in haystack:
            results.append(entry)
    return results
