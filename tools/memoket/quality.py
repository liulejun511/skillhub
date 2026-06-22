"""技能内容质量评估（quality）：validate 管合规、eval 管大脑不退化，
本模块补「技能写得好不好」这一层。

分工同 distill：
- 确定性部分（本模块）：客观体检（有无命令块 / 有无 Not-for / 可执行信号密度 /
  脱敏复查），把「该改」信号挑出来；并存取 agent 的三维打分到 evolution.json。
- 智能部分（agent，按 skills/quality-review）：1-5 的 reusable/actionable/boundary
  三维打分由 agent 产出后回写，本模块负责存取与门限判定、低分进 digest。
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional

from memoket import paths
from memoket.lifecycle import get_evolution, save_evolution
from memoket.redaction import scan
from memoket.skill import SKILL_ENTRY, parse_skill

# 三维平均低于此线 → 进 digest 等用户处置。
QUALITY_FLOOR = 3.0

# 可执行信号：命令块、SQL/git/shell 关键字、模板/清单/阈值等。密度过低 = 偏空泛。
_ACTIONABLE = re.compile(
    r"```|EXPLAIN|SELECT|`git |`docker |psql|步骤|命令|模板|清单|检查项|阈值|前后对比"
)
_TECH = re.compile(r"sql|git|shell|psql|docker|代码|命令|部署|脚本|接口", re.I)


def deterministic_checks(skill_dir: Path) -> Dict:
    skill = parse_skill(skill_dir)
    body = skill.body
    text = (skill_dir / SKILL_ENTRY).read_text(encoding="utf-8")
    return {
        "has_command_block": "```" in body,
        "has_not_for": ("不适用" in body) or ("not for" in body.lower()),
        "actionable_hits": len(_ACTIONABLE.findall(body)),
        "redaction_findings": len(scan(text)),
        "is_technical": bool(_TECH.search((skill.description or "") + body)),
    }


def floor_flags(skill_dir: Path) -> List[str]:
    """无需 agent 的「该改」信号。"""
    c = deterministic_checks(skill_dir)
    flags: List[str] = []
    if not c["has_not_for"]:
        flags.append("缺 Not-for 边界")
    if c["is_technical"] and not c["has_command_block"]:
        flags.append("技术类但无可复制命令块")
    if c["actionable_hits"] < 2:
        flags.append("可执行信号过少（疑似表扬信）")
    if c["redaction_findings"] > 0:
        flags.append(f"疑似脱敏遗漏 {c['redaction_findings']} 处")
    return flags


def save_quality(skill_dir: Path, reusable: int, actionable: int, boundary: int,
                 note: str = "") -> Dict:
    rec = get_evolution(skill_dir)
    rec["quality"] = {
        "reusable": reusable, "actionable": actionable, "boundary": boundary,
        "avg": round((reusable + actionable + boundary) / 3, 2), "note": note,
    }
    save_evolution(skill_dir, rec)
    return rec["quality"]


def _mine_dirs(root: Optional[Path]) -> List[Path]:
    base = paths.vault_mine(root)
    return sorted(md.parent for md in base.rglob(SKILL_ENTRY)) if base.exists() else []


def scores_path(root: Optional[Path] = None) -> Path:
    return (root or paths.workspace()) / "quality-scores.json"


def assemble_review_request(root: Optional[Path] = None) -> Path:
    """组装质量审查请求：列出待评技能 + 确定性体检结果，交给 agent 打分。

    回写方式用「写一个 quality-scores.json」而非逐个跑 CLI——这样 headless agent
    只需 Write 文件权限（acceptEdits 即可），无需 Bash 权限。
    """
    dirs = _mine_dirs(root)
    out = scores_path(root)
    lines = [
        "# Quality Review Request\n",
        "请加载并执行 `skills/quality-review/SKILL.md`，对下列每个技能按 reusable/actionable/",
        "boundary 三维打分（各 1-5），独立挑剔，不因「自己写的」手软。\n",
        f"## 回写方式（重要）\n用 Write 工具写一个 JSON 文件到 `{out.as_posix()}`，格式：",
        '```json\n{"<技能名>": {"reusable":5,"actionable":4,"boundary":5,"note":"一句话评语"}, ...}\n```\n',
        "## 待评技能（含确定性体检提示）\n",
    ]
    for d in dirs:
        flags = floor_flags(d)
        hint = f"  <- 体检提示: {', '.join(flags)}" if flags else ""
        lines.append(f"- `{d.name}`  路径 `{(d / SKILL_ENTRY).as_posix()}`{hint}")
    lines.append("\n## 要求\n- 脱敏遗漏在 note 里优先标出；重叠建议并入但不自行合并；三维独立打分，别一个印象糊三格。")
    req = (root or paths.workspace()) / "quality-review-request.md"
    req.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return req


def load_scores(path=None, root: Optional[Path] = None) -> int:
    """读取 agent 写的 quality-scores.json，逐个回写 evolution.json。返回写入数。"""
    import json

    p = Path(path) if path else scores_path(root)
    if not p.exists():
        return 0
    data = json.loads(p.read_text(encoding="utf-8"))
    n = 0
    for name, q in data.items():
        d = paths.vault_mine(root) / name
        if not (d / SKILL_ENTRY).exists():
            continue
        save_quality(d, int(q["reusable"]), int(q["actionable"]), int(q["boundary"]),
                     note=str(q.get("note", "")))
        n += 1
    return n


def review_all(root: Optional[Path] = None) -> Dict[str, Dict]:
    out: Dict[str, Dict] = {}
    for d in _mine_dirs(root):
        q = get_evolution(d).get("quality")
        out[d.name] = {
            "flags": floor_flags(d),
            "quality": q,
            "below_floor": bool(q and q.get("avg", 5) < QUALITY_FLOOR),
        }
    return out
