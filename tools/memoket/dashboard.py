"""技能触发板：一眼看清哪些技能被触发用了、哪些没被触发，方便优化。

数据来源（evolution.json，由 MCP 自动写）：
- surfaced_count：被检索呈现过几次（search 命中）
- used_count：被真正取用几次（get_skill 自动记 + 手动 record_use）
- reinforced_count / quality.avg：演化与质量
据此把技能分三档：活跃 / 只被搜到没用 / 从未被触发。
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from memoket import paths
from memoket.lifecycle import get_evolution
from memoket.skill import SKILL_ENTRY


def _mine_dirs(root: Optional[Path]) -> List[Path]:
    base = paths.vault_mine(root)
    return sorted(md.parent for md in base.rglob(SKILL_ENTRY)) if base.exists() else []


def collect(root: Optional[Path] = None) -> List[Dict]:
    rows = []
    for d in _mine_dirs(root):
        rec = get_evolution(d)
        used = rec.get("used_count") or 0
        surfaced = rec.get("surfaced_count") or 0
        q = (rec.get("quality") or {}).get("avg")
        if used > 0:
            bucket = "active"        # 被真正取用
        elif surfaced > 0:
            bucket = "surfaced_only"  # 搜到但没用
        else:
            bucket = "untriggered"    # 从未被触发
        rows.append({
            "name": d.name,
            "used": used,
            "surfaced": surfaced,
            "last_used": rec.get("last_used_at"),
            "quality": q,
            "bucket": bucket,
        })
    # 排序：活跃(按用量)→只搜到→从未；同档内用量/呈现降序
    order = {"active": 0, "surfaced_only": 1, "untriggered": 2}
    rows.sort(key=lambda r: (order[r["bucket"]], -r["used"], -r["surfaced"]))
    return rows


def _snapshot_path(root: Optional[Path]) -> Path:
    return (root or paths.workspace()) / "trigger-snapshot.json"


def daily_delta(root: Optional[Path] = None, save: bool = True) -> Dict:
    """对比上次快照，算出「自上次以来」每个技能的触发增量。

    每天定时跑：得到当日新增的 used/surfaced，并把当前累计存为新快照。
    返回 {date_basis, rows:[{name, used_today, surfaced_today, used_total, quality}], any}。
    """
    import json

    rows = collect(root)
    snap_p = _snapshot_path(root)
    prev = {}
    if snap_p.exists():
        prev = json.loads(snap_p.read_text(encoding="utf-8")).get("counts", {})

    out = []
    for r in rows:
        p = prev.get(r["name"], {})
        used_today = max(0, r["used"] - (p.get("used") or 0))
        surf_today = max(0, r["surfaced"] - (p.get("surfaced") or 0))
        out.append({
            "name": r["name"],
            "used_today": used_today,
            "surfaced_today": surf_today,
            "used_total": r["used"],
            "quality": r["quality"],
        })
    out.sort(key=lambda x: (-x["used_today"], -x["surfaced_today"]))

    if save:
        snap_p.write_text(json.dumps(
            {"counts": {r["name"]: {"used": r["used"], "surfaced": r["surfaced"]} for r in rows}},
            ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return {
        "rows": out,
        "any": any(r["used_today"] or r["surfaced_today"] for r in out),
        "total_used_today": sum(r["used_today"] for r in out),
    }


def render_daily_report(when_label: str, delta: Dict) -> str:
    """把今日增量格式化成发给飞书的纯文本报告。"""
    lines = [f"📊 memoket 技能触发日报 · {when_label}", ""]
    if not delta["any"]:
        lines.append("今天没有技能被触发（这一天没用到库里的技能）。")
    else:
        lines.append(f"今日共触发 {delta['total_used_today']} 次。明细：")
        for r in delta["rows"]:
            if r["used_today"] or r["surfaced_today"]:
                lines.append(f"· {r['name']}：用 {r['used_today']} 次 / 搜到 {r['surfaced_today']} 次")
        idle = [r["name"] for r in delta["rows"] if not (r["used_today"] or r["surfaced_today"])]
        if idle:
            lines.append("")
            lines.append(f"未触发（{len(idle)}）：" + "、".join(idle))
    return "\n".join(lines)


def summary(root: Optional[Path] = None) -> Dict:
    rows = collect(root)
    return {
        "total": len(rows),
        "active": [r for r in rows if r["bucket"] == "active"],
        "surfaced_only": [r for r in rows if r["bucket"] == "surfaced_only"],
        "untriggered": [r for r in rows if r["bucket"] == "untriggered"],
        "rows": rows,
    }


def render_text(root: Optional[Path] = None) -> str:
    s = summary(root)
    lines = [
        f"技能触发板  共 {s['total']} 个  |  活跃 {len(s['active'])} · 只搜到 {len(s['surfaced_only'])} · 从未触发 {len(s['untriggered'])}",
        "",
    ]

    def block(title: str, rows: List[Dict], hint: str):
        lines.append(f"━━ {title}（{len(rows)}）{hint}")
        if not rows:
            lines.append("   （无）")
        for r in rows:
            qs = f"q{r['quality']}" if r["quality"] is not None else "q?"
            lu = (r["last_used"] or "")[:10]
            lines.append(f"   {r['name']:42s} 用{r['used']:>2}  搜{r['surfaced']:>2}  {qs:>5}  {lu}")
        lines.append("")

    block("🟢 活跃（被真正取用）", s["active"], "")
    block("🟡 只被搜到、没被取用", s["surfaced_only"], "← 描述可能不够准/与更优技能撞车")
    block("⚪ 从未被触发", s["untriggered"], "← 要么没场景、要么触发词不对，考虑精炼或归档")
    return "\n".join(lines)
