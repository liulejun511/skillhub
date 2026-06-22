"""marketplace.json 结构校验（Claude Code 原生 catalog 的子集契约）。

确认 catalog 骨架合法（name/owner/plugins、每个 plugin 有 name+source、curated 的
github 源 sha 为 40 位）。Claude Code 可能新增字段，故只校验必要部分。
"""
from __future__ import annotations

import functools
import json
from pathlib import Path
from typing import Any, Dict, List

from jsonschema import Draft202012Validator

_SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schemas" / "marketplace.schema.json"


@functools.lru_cache(maxsize=None)
def _validator() -> Draft202012Validator:
    return Draft202012Validator(json.loads(_SCHEMA_PATH.read_text(encoding="utf-8")))


def iter_marketplace_errors(catalog: Dict[str, Any]) -> List[str]:
    """按 schema 校验已解析的 catalog，返回可读错误列表（空 = 通过）。"""
    errors = sorted(_validator().iter_errors(catalog), key=lambda e: list(e.path))
    return [f"{'.'.join(str(p) for p in e.path) or '<root>'}: {e.message}" for e in errors]


def validate_marketplace_file(path) -> List[str]:
    """读取并校验一个 marketplace.json 文件；解析失败也作为错误返回（fail-closed）。"""
    p = Path(path)
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return [f"<load>: 无法解析 {p}: {exc}"]
    return iter_marketplace_errors(data)
