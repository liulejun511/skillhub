"""评测护栏：自修改不退化的命门。

eval/cases/*.json 是黄金集：每例给「素材摘要 + 期望判定 + 期望特征」。
agent 跑出 actual（verdict + traits），这里做确定性打分与回归判定。
tool-retro 的任何改动须在评测集上**不退化**才能进 review（设计 H3）。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from memoket import paths


def load_cases(root: Optional[Path] = None) -> List[Dict]:
    d = paths.eval_dir(root) / "cases"
    if not d.exists():
        return []
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(d.glob("*.json"))]


def score_case(case: Dict, actual: Dict) -> bool:
    """单例打分：判定一致 + 期望特征全覆盖。

    actual: {"verdict": "distill"|"reject", "traits": [...]}
    """
    if actual.get("verdict") != case.get("expected_verdict"):
        return False
    expected_traits = set(case.get("expected_traits", []))
    actual_traits = set(actual.get("traits", []))
    return expected_traits.issubset(actual_traits)


def run_suite(cases: List[Dict], outputs: Dict[str, Dict]) -> Dict[str, bool]:
    """跑整套：outputs 为 {case_name -> actual}。缺输出记为失败。"""
    scores: Dict[str, bool] = {}
    for case in cases:
        name = case["name"]
        actual = outputs.get(name)
        scores[name] = bool(actual) and score_case(case, actual)
    return scores


def load_outputs(root: Optional[Path] = None) -> Dict[str, Dict]:
    """读取 agent 对各用例的判定 eval/outputs/<case>.json（{verdict, traits}）。

    这是「智能」部分：tool-retro 跑时由 agent 按当前 distill 大脑对每个用例判定并写出。
    """
    d = paths.eval_dir(root) / "outputs"
    if not d.exists():
        return {}
    out: Dict[str, Dict] = {}
    for p in sorted(d.glob("*.json")):
        out[p.stem] = json.loads(p.read_text(encoding="utf-8"))
    return out


def _score_path(root: Optional[Path]) -> Path:
    return paths.eval_dir(root) / "score.json"


def _baseline_path(root: Optional[Path]) -> Path:
    return paths.eval_dir(root) / "baseline.json"


def score_current(root: Optional[Path] = None) -> Dict[str, bool]:
    """用当前 outputs 跑整套并落盘 score.json。"""
    scores = run_suite(load_cases(root), load_outputs(root))
    p = _score_path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(scores, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return scores


def set_baseline(root: Optional[Path] = None) -> Dict[str, bool]:
    """把当前 score 锁为基线（tool-retro 改动前调用）。"""
    scores = score_current(root)
    _baseline_path(root).write_text(
        json.dumps(scores, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return scores


def check_against_baseline(root: Optional[Path] = None) -> Dict:
    """改动后调用：当前 score 对照基线做回归判定。无基线视为通过（首次）。"""
    bp = _baseline_path(root)
    before = json.loads(bp.read_text(encoding="utf-8")) if bp.exists() else {}
    after = score_current(root)
    if not before:
        return {"ok": True, "regressions": [], "before_pass": 0,
                "after_pass": sum(1 for v in after.values() if v), "note": "无基线，首次跑"}
    return regression_check(before, after)


def regression_check(before: Dict[str, bool], after: Dict[str, bool]) -> Dict:
    """回归判定：任一原本通过的用例变为失败即退化；总通过数不得下降。"""
    regressions = [name for name, ok in before.items() if ok and not after.get(name, False)]
    before_pass = sum(1 for v in before.values() if v)
    after_pass = sum(1 for v in after.values() if v)
    ok = not regressions and after_pass >= before_pass
    return {
        "ok": ok,
        "regressions": regressions,
        "before_pass": before_pass,
        "after_pass": after_pass,
    }
