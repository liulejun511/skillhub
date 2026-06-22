"""园艺机械件：健康指标与膨胀约束（防止技能库无限膨胀）。

智能动作（判语义重叠、提合并/拆分）在 skills/garden；这里只做确定性的
健康统计与「该不该进入园艺」的触发判断。
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional

from memoket import paths
from memoket.lifecycle import get_evolution
from memoket.skill import SKILL_ENTRY, parse_skill

# 用 tag 粗分能力象限，用于覆盖均衡诊断（防止库扎堆单一领域）。
_DOMAIN_OF_TAG = {
    "debugging": "排障/诊断", "postgresql": "排障/诊断", "shell": "排障/诊断",
    "rag": "排障/诊断", "llm": "排障/诊断", "pipeline": "排障/诊断", "git": "排障/诊断",
    "review": "代码/改动卫生", "code-review": "代码/改动卫生", "ai-coding": "代码/改动卫生",
    "change-hygiene": "代码/改动卫生", "standards": "代码/改动卫生",
    "verification": "验证/复盘", "performance": "验证/复盘", "metrics": "验证/复盘",
    "testing": "验证/复盘", "eval": "验证/复盘", "data": "验证/复盘",
    "management": "协作/管理", "delegation": "协作/管理", "communication": "沟通/写作",
    "methodology": "方法论",
}


def coverage(root: Optional[Path] = None) -> Dict[str, List[str]]:
    """按能力象限聚合技能，诊断覆盖是否扎堆。"""
    buckets: Dict[str, List[str]] = {}
    for d in _active_skill_dirs(root):
        try:
            skill = parse_skill(d)
        except Exception:
            continue
        domains = {_DOMAIN_OF_TAG.get(t) for t in skill.tags} - {None}
        for dom in (domains or {"未分类"}):
            buckets.setdefault(dom, []).append(d.name)
    return buckets


def coverage_diagnosis(root: Optional[Path] = None) -> Dict:
    cov = coverage(root)
    sizes = {k: len(v) for k, v in cov.items()}
    total = sum(sizes.values()) or 1
    top = max(sizes.values()) if sizes else 0
    return {
        "buckets": cov,
        "skew": round(top / total, 3),         # 最大象限占比，越高越扎堆
        "skewed": top / total >= 0.5,
        "domains": len(cov),
    }


def overlap_pairs(threshold: float = 0.25, root: Optional[Path] = None):
    """用检索索引找语义重叠的技能对（合并候选），避免两两比对全库。"""
    from memoket import index

    names = [d.name for d in _active_skill_dirs(root)]
    seen = set()
    pairs = []
    for n in names:
        for other, score in index.nearest(n, k=3, root=root, is_name=True):
            key = tuple(sorted((n, other)))
            if score >= threshold and key not in seen:
                seen.add(key)
                pairs.append({"a": key[0], "b": key[1], "score": round(score, 3)})
    return sorted(pairs, key=lambda p: -p["score"])


def proposals_path(root: Optional[Path] = None) -> Path:
    return (root or paths.workspace()) / "garden-proposals.json"


def assemble_garden_request(root: Optional[Path] = None) -> Path:
    """组装园艺请求：健康+覆盖+质量分+重叠对，交给 agent 产出提案 JSON。"""
    from memoket.lifecycle import get_evolution

    out = proposals_path(root)
    cov = coverage_diagnosis(root)
    health = health_report(root)
    pairs = overlap_pairs(root=root)
    lines = [
        "# Garden Request\n",
        "请加载并执行 `skills/garden/SKILL.md`，据下列信息产出园艺提案，",
        f"用 Write 工具写到 `{out.as_posix()}`，格式：",
        '```json\n[{"action":"merge|deprecate|split|archive","targets":["..."],"into":"<可选>","reason":"..."}]\n```\n',
        f"## 健康\n总数 {health['total']}，陈旧 {health['stale']}，象限扎堆={cov['skewed']}（最大象限占比 {cov['skew']}）\n",
        "## 覆盖象限",
    ]
    for dom, names in sorted(cov["buckets"].items(), key=lambda x: -len(x[1])):
        lines.append(f"- {dom}: {', '.join(names)}")
    lines.append("\n## 质量分（avg，低分优先考虑打回/补强）")
    for d in _active_skill_dirs(root):
        q = get_evolution(d).get("quality")
        if q:
            lines.append(f"- {d.name}: {q['avg']}  {q.get('note','')[:30]}")
    lines.append("\n## 语义重叠对（合并候选）")
    for p in pairs:
        lines.append(f"- {p['a']} <-> {p['b']}  相似度 {p['score']}")
    lines.append("\n## 要求\n- merge/split 需改写内容,作为提案不自动执行;archive/deprecate 工具会自动执行(可逆)。"
                 "\n- 绝不建议删除;低质又无救的建议 archive。")
    req = (root or paths.workspace()) / "garden-request.md"
    req.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return req


def apply_proposals(path=None, root: Optional[Path] = None) -> Dict:
    """执行园艺提案：自动应用安全可逆动作（archive/deprecate→归档），
    merge/split 仅作提案返回（需改内容+用户确认）。"""
    import json

    from memoket.lifecycle import archive_skill

    p = Path(path) if path else proposals_path(root)
    if not p.exists():
        return {"applied": [], "proposals": [], "note": "无提案文件"}
    data = json.loads(p.read_text(encoding="utf-8"))
    applied, deferred = [], []
    for prop in data:
        action = prop.get("action")
        targets = prop.get("targets", [])
        if action in ("archive", "deprecate"):
            for name in targets:
                if (paths.vault_mine(root) / name / SKILL_ENTRY).exists():
                    try:
                        archive_skill(name, root)
                        applied.append({"action": "archive", "skill": name, "reason": prop.get("reason", "")})
                    except Exception as exc:
                        deferred.append({**prop, "error": str(exc)})
        else:
            deferred.append(prop)  # merge/split 留作提案
    return {"applied": applied, "proposals": deferred}


def _active_skill_dirs(root: Optional[Path]) -> List[Path]:
    dirs = []
    for base in (paths.vault_mine(root), paths.vault_installed(root)):
        if base.exists():
            for md in sorted(base.rglob(SKILL_ENTRY)):
                dirs.append(md.parent)
    return dirs


def stale_candidates(root: Optional[Path] = None) -> List[str]:
    """陈旧候选：从未被强化、且用量为**已知的 0**（用量未知者不算，尊重 R11.2）。"""
    out = []
    for d in _active_skill_dirs(root):
        rec = get_evolution(d)
        used = rec.get("used_count")
        if (rec.get("reinforced_count") or 0) == 0 and used == 0:
            out.append(d.name)
    return out


def health_report(root: Optional[Path] = None, soft_cap: Optional[int] = None) -> Dict:
    """库健康概览 + 是否触发（强制）园艺。"""
    dirs = _active_skill_dirs(root)
    stale = stale_candidates(root)
    total = len(dirs)
    over_budget = soft_cap is not None and total > soft_cap
    # 触发园艺：超软上限，或陈旧占比偏高
    stale_ratio = (len(stale) / total) if total else 0.0
    trigger = over_budget or stale_ratio >= 0.3
    return {
        "total": total,
        "stale": stale,
        "stale_ratio": round(stale_ratio, 3),
        "over_budget": over_budget,
        "soft_cap": soft_cap,
        "should_garden": trigger,
    }
