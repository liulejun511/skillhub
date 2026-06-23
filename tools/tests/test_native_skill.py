"""真实 Claude 技能格式应被接纳;但 description 仍有 1536 硬上限,过长(>1024)给非阻断提醒。"""
import shutil
import tempfile
from pathlib import Path

from memoket import ci

# 模拟真实 Claude 技能:没有 version,长 description(触发面),带原生字段 allowed-tools。
_NATIVE = """\
---
name: native-style-skill
description: >-
  Use this whenever you are writing or rewriting a git commit message or a pull
  request description — even when the user only says things like "commit this",
  "push it", or "open a PR" without explicitly mentioning conventions.
allowed-tools: Read, Edit
---

# Native Style Skill

Body that explains what Claude should do.
"""


def _make(body: str, name: str = "native-style-skill") -> Path:
    d = Path(tempfile.mkdtemp()) / name
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(body, encoding="utf-8")
    return d


def _skill(name: str, description: str) -> str:
    return f"---\nname: {name}\ndescription: {description}\n---\n\n# {name}\n\nBody.\n"


def test_native_claude_skill_passes_gate():
    d = _make(_NATIVE)
    try:
        r = ci.gate_skill(d)
        assert r["ok"], r["blocks"]  # 无 version / 长描述 / 额外字段 / 'Use this' 都应被接纳
    finally:
        shutil.rmtree(d.parent, ignore_errors=True)


def test_overlong_description_blocked():
    desc = "Use when " + ("word " * 350)  # > 1536 chars
    d = _make(_skill("too-long", desc), "too-long")
    try:
        assert len(desc) > 1536
        r = ci.gate_skill(d)
        assert not r["ok"]
        assert any("1536" in b or "too long" in b.lower() or "maxLength" in b for b in r["blocks"]), r["blocks"]
    finally:
        shutil.rmtree(d.parent, ignore_errors=True)


def test_long_description_warns_but_passes():
    desc = "Use when " + ("word " * 230)  # ~1024-1536 range
    assert 1024 < len(desc) <= 1536
    d = _make(_skill("longish", desc), "longish")
    try:
        r = ci.gate_skill(d)
        assert r["ok"], r["blocks"]
        assert any("description" in w and "偏长" in w for w in r["warns"]), r["warns"]
    finally:
        shutil.rmtree(d.parent, ignore_errors=True)
