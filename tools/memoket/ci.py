"""CI 自动闸（fail-closed）：对每个技能跑 L0 + L1 + 能力分级，任一 block 即拒。

任何检查抛异常都按失败处理（fail-closed）——无绿不合。承重的安全控制是人工策展
合入；本闸只是抬高攻击成本的自动过滤器（设计 R4.5）。
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Sequence

from memoket import paths
from memoket.skill import SKILL_ENTRY


def gate_skill(skill_dir) -> Dict:
    """对单个技能跑全部 v1 闸，返回 {skill, ok, blocks[], warns[]}。"""
    d = Path(skill_dir)
    blocks: List[str] = []
    warns: List[str] = []

    # L0：结构 + schema + 通用层（含触发场景）
    try:
        from memoket.validate import has_issues, validate_skill

        result = validate_skill(d)
        if has_issues(result):
            blocks.extend(f"L0 {layer}: {m}" for layer, msgs in result.items() for m in msgs)
    except Exception as exc:
        blocks.append(f"L0 scanner_error: {exc!r}")

    # L1 脱敏：命中即 block（同旧 publish 的 RedactionBlocked 规则）
    try:
        from memoket.redaction import scan as redaction_scan

        text = (d / SKILL_ENTRY).read_text(encoding="utf-8")
        for f in redaction_scan(text):
            blocks.append(f"L1 redaction[{f['type']}] line {f['line']}: {f['match']}")
    except Exception as exc:
        blocks.append(f"L1 redaction scanner_error: {exc!r}")

    # L1 注入：block 档拒，warn 档下放人审
    try:
        from memoket.injection_scan import scan_skill

        for f in scan_skill(d):
            line = f"L1 injection[{f['type']}] {f['file']}:{f['line']}: {f['match']}"
            (blocks if f["severity"] == "block" else warns).append(line)
    except Exception as exc:
        blocks.append(f"L1 injection scanner_error: {exc!r}")

    # 能力分级：v1 仅收 Inert，Active 入口拒
    try:
        from memoket.classify import classify_skill

        c = classify_skill(d)
        if c["capability"] == "active":
            blocks.append(f"capability: Active 暂不收（v1 仅 Inert）；标记 {c['markers']}")
    except Exception as exc:
        blocks.append(f"capability scanner_error: {exc!r}")

    return {"skill": str(d), "ok": not blocks, "blocks": blocks, "warns": warns}


def discover_skills(roots: Optional[Sequence[Path]] = None) -> List[Path]:
    """枚举待闸技能目录（默认 sandbox + curated 全部）。"""
    roots = roots if roots is not None else paths.skill_roots()
    dirs: List[Path] = []
    for base in roots:
        base = Path(base)
        if base.exists():
            dirs.extend(md.parent for md in base.rglob(SKILL_ENTRY))
    return sorted(dirs)


def gate_skills(skill_dirs: Sequence[Path]) -> Dict:
    """对一批技能跑闸，汇总。ok 仅当全部通过。"""
    results = [gate_skill(d) for d in skill_dirs]
    return {
        "results": results,
        "ok": all(r["ok"] for r in results),
        "blocked": [r for r in results if not r["ok"]],
    }


def format_report(report: Dict) -> str:
    """人/机可读的闸报告（供 CI 打印 / 贴 PR）。"""
    lines: List[str] = []
    for r in report["results"]:
        status = "OK" if r["ok"] else "BLOCK"
        lines.append(f"[{status}] {r['skill']}")
        for b in r["blocks"]:
            lines.append(f"    ✗ {b}")
        for w in r["warns"]:
            lines.append(f"    ⚠ {w}（warn，下放人审）")
    n = len(report["results"])
    bad = len(report["blocked"])
    lines.append(f"\n{n - bad}/{n} 通过；{bad} 个被拒。")
    return "\n".join(lines)
