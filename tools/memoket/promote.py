"""晋级 helper：把一个 sandbox 技能移入 curated 插件树，置 active，并把该插件在
curated marketplace.json 的 source 钉到给定 commit SHA（设计 R1.3 / R2.4）。

人执行、人合入——绝不自动晋级。移动 + frontmatter 改 + json 改 = 一个 git-traced
commit；回滚 = revert 该 merge commit。
"""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Dict, Optional

from memoket import paths
from memoket.errors import ConflictError, MemoketError, SkillNotFoundError
from memoket.skill import SKILL_ENTRY, parse_skill, write_skill

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def promote_skill(name: str, sha: str, repo: str,
                  plugin: str = "memoket-core", root: Optional[Path] = None) -> Dict:
    """把 sandbox/skills/<name> 晋级进 plugins/<plugin>/skills/<name>。

    返回 {skill, moved_to, plugin, sha}；任何前置条件不满足则抛异常（不留半成品）。
    """
    base = root or paths.workspace()
    if not _SHA_RE.match(sha):
        raise MemoketError(f"SHA 必须是 40 位十六进制 commit：{sha}")

    src = paths.sandbox_skills(base) / name
    if not (src / SKILL_ENTRY).exists():
        raise SkillNotFoundError(f"sandbox 中找不到技能：{name}")

    dst = paths.curated_dir(base) / plugin / "skills" / name
    if dst.exists():
        raise ConflictError(f"curated 已有同名技能：{dst}")

    catalog_path = base / ".claude-plugin" / "marketplace.json"
    if not catalog_path.exists():
        raise MemoketError(f"找不到 curated marketplace.json：{catalog_path}")
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    entry = next((p for p in catalog.get("plugins", []) if p.get("name") == plugin), None)
    if entry is None:
        raise MemoketError(f"marketplace.json 中无插件 {plugin}")

    # 1) 移树
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))

    # 2) 置 active
    skill = parse_skill(dst)
    frontmatter = dict(skill.frontmatter)
    frontmatter["status"] = "active"
    write_skill(dst, frontmatter, skill.body)

    # 3) curated 源钉 commit SHA（防篡改、可复现）
    entry["source"] = {"source": "github", "repo": repo, "sha": sha}
    catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return {"skill": name, "moved_to": str(dst), "plugin": plugin, "sha": sha}
