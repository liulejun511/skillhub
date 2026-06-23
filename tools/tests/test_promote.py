"""晋级 helper：把 sandbox 技能晋级成 curated 独立插件——建插件树 + plugin.json + 置 active +
marketplace 追加 github/SHA 条目，且 catalog 仍 schema 合法。"""
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

_CATALOG = {
    "name": "skillhub",
    "owner": {"name": "x", "email": "x@example.com"},
    "plugins": [],
}


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


def test_promote_creates_standalone_plugin():
    with _workspace() as root:
        result = promote_skill("foo", _SHA, repo="liulejun511/skillhub", root=root)

        # 移进独立插件树
        plugin = root / "plugins" / "foo"
        skill_md = plugin / "skills" / "foo" / "SKILL.md"
        assert skill_md.exists(), "技能未移入 plugins/foo/skills/foo/"
        assert not (root / "sandbox" / "skills" / "foo").exists(), "sandbox 源未移走"
        assert result["plugin_dir"].endswith("foo")

        # 插件 manifest 带描述(浏览器装前可视化)
        manifest = json.loads((plugin / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        assert manifest["name"] == "foo"
        assert manifest["description"]

        # status 置 active
        assert parse_skill(skill_md.parent).frontmatter["status"] == "active"

        # marketplace 追加 github+SHA 条目，且仍 schema 合法
        catalog = json.loads((root / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
        entry = next(p for p in catalog["plugins"] if p["name"] == "foo")
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


def test_promote_duplicate_plugin_raises():
    with _workspace() as root:
        (root / "plugins" / "foo").mkdir(parents=True)  # 已存在同名插件
        try:
            promote_skill("foo", _SHA, repo="o/r", root=root)
            assert False, "应因 curated 已有同名插件而抛错"
        except Exception:
            pass
