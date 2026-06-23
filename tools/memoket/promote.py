"""晋级 helper：把一个暂存技能(sandbox/skills/<name>)收成 curated 的**独立插件**。

每个技能 = 一个可独立选装/卸载的插件。晋级做三件事：
- 建 plugins/<name>/skills/<name>/（移树）+ plugins/<name>/.claude-plugin/plugin.json；
- 把 SKILL.md 的 status 置 active；
- 在 curated marketplace.json 追加一条 entry。

源类型：默认 **相对路径** `./plugins/<name>`（与种子一致，靠整仓克隆解析）；若给了
repo+sha 则用 **github + commit SHA 钉死**（公开发布时的防篡改硬化，可选）。

人执行、人合入——绝不自动晋级。移动 + 改 = 一个 git-traced commit；回滚 = revert 该 merge。
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


def promote_skill(name: str, root: Optional[Path] = None,
                  repo: Optional[str] = None, sha: Optional[str] = None) -> Dict:
    """把 sandbox/skills/<name> 收成独立插件 plugins/<name>/。

    repo+sha 都给 → 用 github+SHA 源；否则 → 相对路径源。
    返回 {skill, plugin_dir, source}；前置条件不满足则抛异常(不留半成品)。
    """
    base = root or paths.workspace()
    pin_sha = bool(repo and sha)
    if sha and not _SHA_RE.match(sha):
        raise MemoketError(f"SHA 必须是 40 位十六进制 commit：{sha}")

    src = paths.sandbox_skills(base) / name
    if not (src / SKILL_ENTRY).exists():
        raise SkillNotFoundError(f"暂存区(sandbox/skills)中找不到技能：{name}")

    plugin_dir = paths.curated_dir(base) / name
    if plugin_dir.exists():
        raise ConflictError(f"curated 已有同名插件：{plugin_dir}")

    catalog_path = base / ".claude-plugin" / "marketplace.json"
    if not catalog_path.exists():
        raise MemoketError(f"找不到 curated marketplace.json：{catalog_path}")
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    if any(p.get("name") == name for p in catalog.get("plugins", [])):
        raise ConflictError(f"marketplace.json 中已有插件 {name}")

    skill = parse_skill(src)
    description = (skill.description or "").strip()
    version = str(skill.frontmatter.get("version", "0.1.0"))
    keywords = list(skill.frontmatter.get("tags", []))
    body = skill.body

    # 1) 移树进独立插件
    dst_skill = plugin_dir / "skills" / name
    dst_skill.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst_skill))

    # 2) 置 active
    frontmatter = dict(parse_skill(dst_skill).frontmatter)
    frontmatter["status"] = "active"
    write_skill(dst_skill, frontmatter, body)

    # 3) 写插件 manifest（description 即浏览器装前可见的说明）
    plugin_json = plugin_dir / ".claude-plugin" / "plugin.json"
    plugin_json.parent.mkdir(parents=True, exist_ok=True)
    plugin_json.write_text(
        json.dumps({"name": name, "version": version, "description": description, "keywords": keywords},
                   ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")

    # 4) curated marketplace 追加 entry：默认相对源，给了 repo+sha 则 github 钉死
    source = {"source": "github", "repo": repo, "sha": sha} if pin_sha else f"./plugins/{name}"
    catalog.setdefault("plugins", []).append({
        "name": name,
        "source": source,
        "description": description,
        "version": version,
        "category": "engineering",
        "keywords": keywords,
    })
    catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return {"skill": name, "plugin_dir": str(plugin_dir), "source": source}
