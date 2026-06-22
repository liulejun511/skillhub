"""加载 JSON Schema 并对 frontmatter 做结构校验。

这里只提供「按 schema 列出错误」的通用能力；面向用户的两层校验逻辑
（通用层 + 适配器层）在 memoket.validate（任务 3）基于此构建。
"""
from __future__ import annotations

import functools
import json
from pathlib import Path
from typing import Any, Dict, List

from jsonschema import Draft202012Validator

# 仓库根：本文件位于 memoket/，schemas/ 与之同级于仓库根。
_REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_SCHEMA_PATH = _REPO_ROOT / "schemas" / "skill.schema.json"


@functools.lru_cache(maxsize=None)
def load_skill_schema() -> Dict[str, Any]:
    """加载技能 frontmatter 的 JSON Schema（带缓存）。"""
    return json.loads(SKILL_SCHEMA_PATH.read_text(encoding="utf-8"))


@functools.lru_cache(maxsize=None)
def _skill_validator() -> Draft202012Validator:
    return Draft202012Validator(load_skill_schema())


def iter_schema_errors(frontmatter: Dict[str, Any]) -> List[str]:
    """按 schema 校验 frontmatter，返回人类可读的错误列表（按路径排序）。

    返回空列表表示通过。
    """
    errors = sorted(_skill_validator().iter_errors(frontmatter), key=lambda e: list(e.path))
    messages: List[str] = []
    for err in errors:
        location = ".".join(str(p) for p in err.path) or "<root>"
        messages.append(f"{location}: {err.message}")
    return messages
