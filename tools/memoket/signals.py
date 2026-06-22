"""优化信号：把工具运行中的摩擦记录下来，作为「优化工具」的反馈。

强约束：信号**只记指标/原因，不含个人素材内容**（设计 H4 / R6.2）。
过长的字段会被拒绝，避免夹带原文。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from memoket import paths
from memoket.errors import MemoketError

# 单字段最大长度——超过视为可能夹带素材原文，拒绝写入。
MAX_FIELD_LEN = 240

SIGNAL_KINDS = (
    "reject",            # 质量闸打回
    "validate_fail",     # 校验失败
    "structural_edit",   # 用户对草稿的结构性修改（删/加了哪节）
    "cli_exception",     # CLI 异常
    "digest_decision",   # digest 采纳/否决
    "garden_merge",      # 园艺反复合并同类重复
    "tool_friction",     # 工具自身的摩擦/缺陷（连接器有损、检索失灵等），喂 tool-retro
)


def _signals_file(root: Optional[Path]) -> Path:
    d = paths.signals_dir(root)
    d.mkdir(parents=True, exist_ok=True)
    return d / "signals.jsonl"


def _assert_no_raw_content(data: Dict) -> None:
    for k, v in data.items():
        if isinstance(v, str) and len(v) > MAX_FIELD_LEN:
            raise MemoketError(
                f"signals 字段 '{k}' 过长（{len(v)}>{MAX_FIELD_LEN}）——疑似夹带素材原文，已拒绝。"
            )


def append_signal(kind: str, data: Optional[Dict] = None, root: Optional[Path] = None) -> Dict:
    if kind not in SIGNAL_KINDS:
        raise MemoketError(f"未知信号类型: {kind}")
    record = {"kind": kind, **(data or {})}
    _assert_no_raw_content(record)
    with _signals_file(root).open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


def read_signals(root: Optional[Path] = None) -> List[Dict]:
    p = _signals_file(root)
    if not p.exists():
        return []
    return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]
