"""catalog：把所有技能的 name/description/标签汇成一页可浏览的 CATALOG.md。

让人不进 Claude 也能一眼看清每个技能干啥（描述可视化）。每个技能 = 一个可独立
安装的插件，故目录即「能装哪些、各自干啥」的清单。自动生成，勿手改。
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from memoket import paths
from memoket.skill import SKILL_ENTRY, parse_skill


def collect(root: Optional[Path] = None) -> List[Dict]:
    """扫 curated + sandbox 技能，抽取目录所需字段。"""
    rows: List[Dict] = []
    for base, tier in ((paths.curated_dir(root), "curated"), (paths.sandbox_skills(root), "sandbox")):
        if not base.exists():
            continue
        for md in sorted(base.rglob(SKILL_ENTRY)):
            try:
                skill = parse_skill(md.parent)
            except Exception:
                continue  # 结构坏的跳过，不让目录生成失败
            rows.append({
                "name": skill.name or md.parent.name,
                "description": " ".join((skill.description or "").split()),
                "tags": list(skill.frontmatter.get("tags", [])),
                "tier": tier,
            })
    return rows


def render(root: Optional[Path] = None) -> str:
    rows = collect(root)
    curated = [r for r in rows if r["tier"] == "curated"]
    sandbox = [r for r in rows if r["tier"] == "sandbox"]

    out: List[str] = [
        "# skillhub 技能目录 / Skill Catalog",
        "",
        "> 自动生成（`python -m memoket catalog`），勿手改。每个技能 = 一个可独立安装的插件。",
        "",
    ]

    def section(title: str, items: List[Dict]) -> None:
        out.append(f"## {title}（{len(items)}）")
        out.append("")
        if not items:
            out.append("_（暂无）_")
            out.append("")
            return
        for r in sorted(items, key=lambda x: x["name"]):
            tags = "  ".join(f"`{t}`" for t in r["tags"])
            out.append(f"### {r['name']}")
            out.append("")
            out.append(r["description"] or "_（无描述）_")
            if tags:
                out.append("")
                out.append(tags)
            out.append("")

    section("Curated（已策展，可一键安装）", curated)
    section("Pending submissions（暂存待审，未发布、不可装）", sandbox)
    return "\n".join(out) + "\n"


def write_catalog(root: Optional[Path] = None) -> Path:
    base = root or paths.workspace()
    out_path = base / "CATALOG.md"
    out_path.write_text(render(base), encoding="utf-8")
    return out_path
