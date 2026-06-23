"""真实 Claude 技能格式应被闸接纳:无 version、长 description、含原生字段、'Use this whenever' 触发。"""
import shutil
import tempfile
from pathlib import Path

from memoket import ci

# 模拟一个真实 Claude 技能:没有 version,description 很长(触发面),带 Claude 原生字段 allowed-tools。
_NATIVE = """\
---
name: native-style-skill
description: >-
  Use this whenever you are writing or rewriting a git commit message or a pull
  request description — even when the user only says things like "commit this",
  "push it", or "open a PR" without explicitly mentioning conventions. Apply it
  for squashing or rebasing commits before opening or updating a PR as well.
allowed-tools: Read, Edit
---

# Native Style Skill

Body that explains what Claude should do.
"""


def _make(body: str) -> Path:
    d = Path(tempfile.mkdtemp()) / "native-style-skill"
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(body, encoding="utf-8")
    return d


def test_native_claude_skill_passes_gate():
    d = _make(_NATIVE)
    try:
        r = ci.gate_skill(d)
        assert r["ok"], r["blocks"]  # 无 version / 长描述 / 额外字段 / 'Use this' 都应被接纳
    finally:
        shutil.rmtree(d.parent, ignore_errors=True)
