"""晋级 helper：把暂存技能收成 curated 独立插件——建插件树 + plugin.json + 置 active +
marketplace 追加条目(默认相对源;给 repo+sha 则 github 钉死),且 catalog 仍 schema 合法。"""
import json
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path

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
tags: [test, fixture]
---

# Foo

Body.
"""

_CATALOG = {"name": "skillhub", "owner": {"name": "x", "email": "x@example.com"}, "plugins": []}


@contextmanager
def _workspace():
    root = Path(tempfile.mkdtemp())
    try:
        skill_dir = root / "sandbox" / "skills" / "foo"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(_SKILL, encoding="utf-8")
        (root / ".claude-plugin").mkdir(parents=True)
        (root / ".claude-plugin" / "marketplace.json").write_text(
            json.dumps(_CATALOG, ensure_ascii=False, indent=2), encoding="utf-8")
        yield root
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _entry(root, name="foo"):
    catalog = json.loads((root / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
    return next(p for p in catalog["plugins"] if p["name"] == name), catalog


def test_promote_relative_source_by_default():
    with _workspace() as root:
        r = promote_skill("foo", root=root)
        skill_md = root / "plugins" / "foo" / "skills" / "foo" / "SKILL.md"
        assert skill_md.exists()
        assert not (root / "sandbox" / "skills" / "foo").exists()
        assert (root / "plugins" / "foo" / ".claude-plugin" / "plugin.json").exists()
        assert parse_skill(skill_md.parent).frontmatter["status"] == "active"
        entry, catalog = _entry(root)
        assert entry["source"] == "./plugins/foo"   # 默认相对源
        assert iter_marketplace_errors(catalog) == []


def test_promote_github_sha_when_given():
    with _workspace() as root:
        promote_skill("foo", root=root, repo="liulejun511/skillhub", sha=_SHA)
        entry, catalog = _entry(root)
        assert entry["source"] == {"source": "github", "repo": "liulejun511/skillhub", "sha": _SHA}
        assert iter_marketplace_errors(catalog) == []


def test_promote_bad_sha_raises():
    with _workspace() as root:
        try:
            promote_skill("foo", root=root, repo="o/r", sha="not-a-sha")
            assert False, "应因 SHA 非法而抛错"
        except Exception as exc:
            assert "SHA" in str(exc)


def test_promote_missing_skill_raises():
    with _workspace() as root:
        try:
            promote_skill("nope", root=root)
            assert False
        except Exception:
            pass


def test_promote_duplicate_plugin_raises():
    with _workspace() as root:
        (root / "plugins" / "foo").mkdir(parents=True)
        try:
            promote_skill("foo", root=root)
            assert False
        except Exception:
            pass
