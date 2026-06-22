"""注入/危险语句扫描（L1 安全闸的一半，与 redaction 同形）。

扫技能正文里的提示注入与外发/取凭证语句。命中分两档：
- severity="block"：高置信注入/外发，CI 直接拒并标行（设计 R4.3）。
- severity="warn"：可疑但可能合法（读凭证、curl POST、长 base64），下放人审。

仅启发式正则：抬高攻击成本的过滤器，不是证明安全的闸门——提示注入无法被自动
检测 100% 覆盖（设计 R4.5），承重墙是人工策展合入。已知盲区（同形字 homoglyph、
跨文件拆分、复杂改写）留待人审与未来增强。
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List
import re

_PATTERNS = {
    # 覆写/无视既有指令——经典提示注入
    "injection_override": (re.compile(
        r"(?i)\b(ignore|disregard|forget|override)\b[^.\n]{0,40}?"
        r"\b(previous|above|prior|earlier|all|your|system)\b[^.\n]{0,25}?"
        r"\b(instruction|instructions|prompt|prompts|guideline|guidelines|rule|rules|direction|directions)\b"
    ), "block"),
    "injection_override_zh": (re.compile(
        r"(忽略|无视|忽视|忘记)[^。\n]{0,20}?(以上|上述|上面|之前|前面|先前|所有)?[^。\n]{0,12}?(指令|指示|要求|规则|提示词|系统提示)"
    ), "block"),
    # 套取系统提示/原始指令
    "system_prompt_leak": (re.compile(
        r"(?i)\b(reveal|print|show|output|repeat|display|expose|dump)\b[^.\n]{0,30}?"
        r"\b(system\s*prompt|your\s+(instructions|prompt|guidelines)|initial\s+(prompt|instructions))\b"
    ), "block"),
    "system_prompt_leak_zh": (re.compile(
        r"(输出|打印|展示|泄露|告诉我|复述)[^。\n]{0,16}?(系统提示|你的(指令|提示|系统提示)|原始(指令|提示))"
    ), "block"),
    # 把数据外发到网络——明确的 exfil 动作 + URL/端点
    "exfil_network": (re.compile(
        r"(?i)\b(send|post|upload|exfiltrate|transmit|forward|leak)\b[^.\n]{0,50}?"
        r"(https?://|webhook|to\s+(this|the|my|an?)\s+(url|server|endpoint|address))"
    ), "block"),
    # 读取凭证/密钥文件——可疑但可能合法，交人审
    "credential_read": (re.compile(
        r"(?i)(\.env\b|~/\.ssh|id_rsa|/etc/passwd|aws_secret_access_key|aws_access_key_id|"
        r"\.aws/credentials|process\.env|os\.environ|secret[_-]?key|private[_-]?key)"
    ), "warn"),
    # curl/wget POST 外发——可能是教学示例，交人审
    "network_post": (re.compile(
        r"(?i)\b(curl|wget|Invoke-WebRequest|fetch|requests\.(?:post|get))\b[^.\n]{0,60}?"
        r"(-X\s*POST|--data|-d\s|\bPOST\b)"
    ), "warn"),
    # 超长 base64 串——可能藏命令/载荷，交人审
    "base64_blob": (re.compile(r"[A-Za-z0-9+/]{60,}={0,2}"), "warn"),
}

# 扫描时跳过的二进制/非文本后缀。
_BINARY_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".gz", ".ico", ".woff", ".woff2"}


def scan_text(text: str, file: str = "SKILL.md") -> List[Dict]:
    """对一段文本扫描，返回 [{type, match, line, file, severity}]（空 = 干净）。"""
    findings: List[Dict] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        for kind, (pattern, severity) in _PATTERNS.items():
            for m in pattern.finditer(line):
                findings.append({
                    "type": kind, "match": m.group(0)[:120],
                    "line": lineno, "file": file, "severity": severity,
                })
    return findings


def scan_skill(skill_dir) -> List[Dict]:
    """扫一个技能目录下的全部文本文件（SKILL.md + reference/ 等），合并 findings。

    注入可能藏在 reference/ 等附带文件里，故全量扫，不只扫 SKILL.md（设计 R4 加固）。
    """
    base = Path(skill_dir)
    findings: List[Dict] = []
    for f in sorted(base.rglob("*")):
        if not f.is_file() or f.suffix.lower() in _BINARY_SUFFIXES:
            continue
        try:
            text = f.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue  # 二进制或不可读，跳过
        findings.extend(scan_text(text, file=str(f.relative_to(base))))
    return findings


def has_block(findings: List[Dict]) -> bool:
    """是否存在 block 档命中（CI 据此拒绝）。"""
    return any(f["severity"] == "block" for f in findings)
