"""脱敏闸：发布前检出疑似 PII/机密。

启发式（正则）层；更细的语义判断由 agent 在发布前补充。检出即阻止发布并标位置。
"""
from __future__ import annotations

import re
from typing import Dict, List

_PATTERNS = {
    "email": re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),
    "url": re.compile(r"https?://\S+"),
    "phone": re.compile(r"(?<!\d)(?:\+?\d[\d\s-]{8,}\d)(?!\d)"),
    "money": re.compile(r"[$￥€£]\s?\d[\d,]*(?:\.\d+)?|\b\d[\d,]*\s?(?:美元|万元|元|块)\b"),
    "id_number": re.compile(r"(?<!\d)\d{15,18}(?!\d)"),
    # 内部代号易漏网：具名远端分支 / 仓内具体脚本路径。占位符（含 <…>）不算。
    "branch_ref": re.compile(r"\borigin/(?!<)[A-Za-z][\w.-]*"),
    "repo_path": re.compile(r"\b(?:tools|app|src|scripts)/(?!<)[\w./-]+\.\w+"),
}


def scan(text: str) -> List[Dict]:
    """返回 [{type, match, line}] 列表（空 = 干净）。"""
    findings: List[Dict] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        for kind, pat in _PATTERNS.items():
            for m in pat.finditer(line):
                findings.append({"type": kind, "match": m.group(0), "line": lineno})
    return findings
