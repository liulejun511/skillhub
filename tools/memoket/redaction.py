"""脱敏闸：发布前检出疑似 PII/机密。

启发式（正则）层；更细的语义判断由 agent 在发布前补充。检出即阻止发布并标位置。
"""
from __future__ import annotations

import os
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

# 公开文档/参考域名白名单：技能正文合法引用这些不算泄露。
# 可用 SKILLHUB_URL_ALLOWLIST（逗号分隔 host）追加团队自有文档域名。
_DEFAULT_URL_ALLOWLIST = {
    "code.claude.com", "docs.claude.com", "claude.com",
    "docs.anthropic.com", "anthropic.com",
    "modelcontextprotocol.io",
}
_HOST_RE = re.compile(r"https?://([^/\s:]+)", re.IGNORECASE)


def _url_allowlist() -> set:
    extra = {h.strip().lower() for h in os.environ.get("SKILLHUB_URL_ALLOWLIST", "").split(",") if h.strip()}
    return _DEFAULT_URL_ALLOWLIST | extra


def _url_is_allowed(url: str) -> bool:
    """白名单 host 或其子域的 URL 视为合法引用，不计为泄露。"""
    m = _HOST_RE.match(url)
    if not m:
        return False
    host = m.group(1).lower()
    return any(host == allowed or host.endswith("." + allowed) for allowed in _url_allowlist())


def scan(text: str) -> List[Dict]:
    """返回 [{type, match, line}] 列表（空 = 干净）。白名单文档 URL 不计入。"""
    findings: List[Dict] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        for kind, pat in _PATTERNS.items():
            for m in pat.finditer(line):
                if kind == "url" and _url_is_allowed(m.group(0)):
                    continue
                findings.append({"type": kind, "match": m.group(0), "line": lineno})
    return findings
