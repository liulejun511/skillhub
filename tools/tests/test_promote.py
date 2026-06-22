"""晋级 helper：把 sandbox 技能移入 curated、置 active、curated 源钉 SHA、仍 schema 合法。"""
import json
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path

from memoket import paths
from memoket.marketplace import iter_marketplace_errors
from memoket.promote import promote_skill
from memoket.skill import parse_skill

_SHA = "0123456789abcdef0123456789abcdef01234567"

_SKILL = """\
---
name: foo
description: Use when testing promotion (fixture)
version: 0.1.0
status: draft
origin: authored
---

# Foo

Body.
"""

_CATALOG = {
    "name": "skillhub",
    "owner": {"name": "x", "email": "x@example.com"},
    "plugins": [{"name": "memoket-core", "source": "./plugins/memoket-core", "version": "0.1.0"}],
}


@contextmanager
def _workspace():
    root = Path(tempfile.mkdtemp())
    try:
        (root / "sandbox" / "skills" / "foo").mkdir(parents=True)
        (root / "sandbox" / "skills" / "foo" / "SKILL.md").write_text(_SKILL, encoding="utf-8")
        (root / "plugins" / "memoket-core").mkdir(parents=True)
        (root / ".claude-plugin").mkdir(parents=True)
        (root / ".claude-plugin" / "marketplace.json").write_text(
            json.dumps(_CATALOG, ensure_ascii=False, indent=2), encoding="utf-8")
        yield root
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_promote_moves_sets_active_and_pins_sha():
    with _workspace() as root:
        result = promote_skill("foo", _SHA, repo="liulejun511/skillhub", root=root)

        moved = root / "plugins" / "memoket-core" / "skills" / "foo"
        assert moved.exists() and (moved / "SKILL.md").exists()
        assert not (root / "sandbox" / "skills" / "foo").exists()  # 已移走
        assert result["sha"] == _SHA

        # 置 active
        assert parse_skill(moved).frontmatter["status"] == "active"

        # curated 源钉 github + SHA，且 catalog 仍 schema 合法
        catalog = json.loads((root / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
        entry = next(p for p in catalog["plugins"] if p["name"] == "memoket-core")
        assert entry["source"] == {"source": "github", "repo": "liulejun511/skillhub", "sha": _SHA}
        assert iter_marketplace_errors(catalog) == []


def test_promote_rejects_bad_sha():
    with _workspace() as root:
        try:
            promote_skill("foo", "not-a-sha", repo="o/r", root=root)
            assert False, "应因 SHA 非法而抛错"
        except Exception as exc:
            assert "SHA" in str(exc)


def test_promote_missing_skill_raises():
    with _workspace() as root:
        try:
            promote_skill("nope", _SHA, repo="o/r", root=root)
            assert False, "应因找不到技能而抛错"
        except Exception:
            pass
