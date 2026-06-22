"""极简语义化版本：解析、比较、按级别递增。

升版规则（设计 R14.2）：行为/契约破坏 → major，能力增强 → minor，措辞/修正 → patch。
"""
from __future__ import annotations

import re
from typing import Tuple

_SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)")

LEVELS = ("major", "minor", "patch")


def parse(version: str) -> Tuple[int, int, int]:
    m = _SEMVER_RE.match(str(version))
    if not m:
        raise ValueError(f"非法语义化版本: {version!r}")
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def compare(a: str, b: str) -> int:
    """返回 -1 / 0 / 1。"""
    pa, pb = parse(a), parse(b)
    return (pa > pb) - (pa < pb)


def bump(version: str, level: str) -> str:
    if level not in LEVELS:
        raise ValueError(f"未知升版级别: {level}（应为 {LEVELS}）")
    major, minor, patch = parse(version)
    if level == "major":
        return f"{major + 1}.0.0"
    if level == "minor":
        return f"{major}.{minor + 1}.0"
    return f"{major}.{minor}.{patch + 1}"
