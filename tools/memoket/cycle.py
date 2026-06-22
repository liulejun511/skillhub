"""evolve-cycle 的确定性脊柱（编排轨道）。

智能步骤（triage/distill/质量闸的语义判断）由 agent 执行（headless 或 inline）；
本模块负责把它前后的**确定性轨道**焊上：ingest → (agent distill) → validate → 脱敏扫描
→ evolution.json → 推进水位 → report。失败不推进水位（幂等，设计 H6）。
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from memoket import paths, watermark
from memoket.ingest import ingest
from memoket.locking import file_lock
from memoket.skill import SKILL_ENTRY

# 并发保护：第二个并发 cycle 等待至多 _LOCK_TIMEOUT 秒，仍拿不到则快速失败。
_LOCK_TIMEOUT = 2.0


def stage(user: str, since: Optional[str] = None, root: Optional[Path] = None,
          source=None, from_path=None) -> List[Path]:
    """阶段一：经素材源连接器（或一次性 --from 文本输入）拉素材到 .work/。不推进水位。"""
    with file_lock(root, timeout=_LOCK_TIMEOUT):
        return ingest(user, since=since, root=root, source=source, from_path=from_path)


def _mine_skill_dirs(root: Optional[Path]) -> List[Path]:
    base = paths.vault_mine(root)
    if not base.exists():
        return []
    return sorted(md.parent for md in base.rglob(SKILL_ENTRY))


def finalize(user: str, processed_at: str, root: Optional[Path] = None) -> Dict:
    """阶段二：对 distill 产出的草稿跑确定性轨道。

    - 校验闸：任一技能不过 → 不推进水位（事务化）。
    - 脱敏扫描：报告疑似 PII/机密（draft 阶段仅告警，publish 时才阻断）。
    - evolution.json：新草稿落 lifecycle 与首次 reinforce。
    - 成功 → 推进水位 + 生成 report。
    """
    from memoket.validate import validate_skill, has_issues
    from memoket.redaction import scan
    from memoket.lifecycle import get_evolution, save_evolution, reinforce
    from memoket.report import report as build_report

    with file_lock(root, timeout=_LOCK_TIMEOUT):
        return _finalize_locked(user, processed_at, root, validate_skill, has_issues,
                                scan, get_evolution, save_evolution, reinforce, build_report)


def _finalize_locked(user, processed_at, root, validate_skill, has_issues,
                     scan, get_evolution, save_evolution, reinforce, build_report) -> Dict:
    skills = _mine_skill_dirs(root)
    validation_fail: Dict[str, List[str]] = {}
    redaction_flags: Dict[str, int] = {}

    for d in skills:
        result = validate_skill(d)
        if has_issues(result):
            validation_fail[str(d)] = [f"{layer}: {i}" for layer, issues in result.items() for i in issues]
        findings = scan((d / SKILL_ENTRY).read_text(encoding="utf-8"))
        if findings:
            redaction_flags[d.name] = len(findings)

    summary: Dict = {
        "skills": [d.name for d in skills],
        "validation_fail": validation_fail,
        "redaction_flags": redaction_flags,
        "watermark_advanced": False,
        "report": "",
    }

    if validation_fail:
        watermark.record_failure(root)
        summary["report"] = "校验未过，未推进水位（幂等，可修复后重跑）。"
        return summary

    # 校验通过：落 evolution，首次入库视为一次 reinforce。
    for d in skills:
        rec = get_evolution(d)
        try:
            from memoket.skill import parse_skill
            rec["lifecycle"] = parse_skill(d).status or "draft"
        except Exception:
            pass
        save_evolution(d, rec)
        if not rec.get("reinforced_count"):
            reinforce(d, processed_at)

    watermark.advance(processed_at, user_id=user)
    summary["watermark_advanced"] = True
    summary["report"] = build_report(root)
    return summary
