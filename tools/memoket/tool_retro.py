"""工具自我优化的安全闸：把「受保护内核」与「评测不退化」两道闸合一。

tool-retro 在提交任何对工具自身的改动前，必须通过本闸（设计 H1 + H3）。
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from memoket import kernel
from memoket.errors import MemoketError
from memoket.evals import regression_check


class ToolChangeRejected(MemoketError):
    """工具自我优化改动被安全闸拒绝。"""


def guard_tool_change(
    changed_paths: List[str],
    eval_before: Dict[str, bool],
    eval_after: Dict[str, bool],
    root: Optional[Path] = None,
) -> Dict:
    """两道闸：① 不得触及受保护内核；② 评测集不得退化。任一不过即拒。"""
    # 闸 1：受保护内核
    kernel.assert_changes_allowed(changed_paths, root)  # 触及即抛 KernelViolation
    # 闸 2：评测回归
    reg = regression_check(eval_before, eval_after)
    if not reg["ok"]:
        raise ToolChangeRejected(
            f"评测退化，拒绝合入。退化用例: {reg['regressions']}；"
            f"通过数 {reg['before_pass']} → {reg['after_pass']}"
        )
    return reg
