"""MCP 运行时适配器：把 vault 技能暴露给任何 MCP 客户端（任务 21 / R15.5）。

零依赖实现：stdio 传输、按行 JSON-RPC 2.0。暴露三个工具：
- search_skills(query, limit)  按相关度检索可见技能
- get_skill(name)              取完整 SKILL.md 内容
- record_use(name)             用量回写（R11：喂园艺的 used_count）

安全（H1）：installed 且 trust != active（即 quarantine）的技能**不可见**——
不出现在检索、不可被 get/record；archived 技能在 vault/archive/ 天然不可见。

接入方式（任何 MCP 客户端）：
    claude mcp add memoket -- python -m memoket mcp
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from memoket import lockfile, paths
from memoket.skill import SKILL_ENTRY, parse_skill

PROTOCOL_FALLBACK = "2024-11-05"
SERVER_INFO = {"name": "memoket", "version": "0.1.0"}

TOOLS = [
    {
        "name": "search_skills",
        "description": (
            "Search the user's personal skill vault by relevance. "
            "Use when you need a reusable method/framework the user has distilled "
            "(work disciplines, debugging playbooks, review checklists...)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "What capability you are looking for"},
                "limit": {"type": "integer", "description": "Max results (default 5)"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_skill",
        "description": "Fetch the full SKILL.md content of one skill by exact name.",
        "inputSchema": {
            "type": "object",
            "properties": {"name": {"type": "string", "description": "Skill name (kebab-case)"}},
            "required": ["name"],
        },
    },
    {
        "name": "record_use",
        "description": (
            "Report that a skill was actually loaded/applied (usage write-back). "
            "Call once after you use a skill so library gardening sees real usage."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {"name": {"type": "string", "description": "Skill name (kebab-case)"}},
            "required": ["name"],
        },
    },
]


# ── 可见性（安全边界）──────────────────────────────────────────

def visible_skill_dirs(root: Optional[Path] = None) -> Dict[str, Path]:
    """可被 MCP 暴露的技能：mine 全部 + installed 中 trust=active 的。"""
    result: Dict[str, Path] = {}
    mine = paths.vault_mine(root)
    if mine.exists():
        for md in sorted(mine.rglob(SKILL_ENTRY)):
            result[md.parent.name] = md.parent
    installed = paths.vault_installed(root)
    if installed.exists():
        for md in sorted(installed.rglob(SKILL_ENTRY)):
            name = md.parent.name
            entry = lockfile.get_entry(name, root)
            if entry is not None and entry.get("trust") == "active":
                result[name] = md.parent
    return result


# ── 工具实现 ───────────────────────────────────────────────────

def tool_search_skills(query: str, limit: int = 5, root: Optional[Path] = None) -> List[Dict[str, Any]]:
    from memoket.index import tokens

    visible = visible_skill_dirs(root)
    q = tokens(query)
    scored = []
    for name, d in visible.items():
        try:
            skill = parse_skill(d)
        except Exception:
            continue
        if skill.status in ("deprecated", "archived"):
            continue
        # name/description 权重高于正文；评分 = query 覆盖度（命中的 query 词占比），
        # 比 Jaccard 更适合「短 query 找长技能」，分值可解释（0~1）。
        head = tokens(" ".join([skill.name or "", skill.description or ""]))
        body = tokens(skill.body)
        if not q:
            score = 0.0
        else:
            hit = len(q & head) + 0.5 * len(q & (body - head))
            score = hit / len(q)
        scored.append({
            "name": name,
            "description": skill.description or "",
            "status": skill.status,
            "version": skill.version or "",
            "score": round(score, 4),
        })
    scored.sort(key=lambda x: x["score"], reverse=True)
    top = scored[: max(1, int(limit))]
    # 只把「真正匹配上（score>0）」的记为 surfaced——0 分只是凑数填充，不算被检索到。
    _record_surface([s["name"] for s in top if s["score"] > 0], root)
    return top


def _record_surface(names, root):
    import datetime as _dt

    from memoket.lifecycle import record_surface

    when = _dt.datetime.now(_dt.timezone.utc).isoformat()
    visible = visible_skill_dirs(root)
    for n in names:
        if n in visible:
            try:
                record_surface(visible[n], when)
            except Exception:
                pass


def tool_get_skill(name: str, root: Optional[Path] = None) -> str:
    import datetime as _dt

    from memoket.lifecycle import record_use

    visible = visible_skill_dirs(root)
    if name not in visible:
        raise KeyError(f"skill not found or not visible: {name}")
    # 取完整技能内容 = 真正被取用 → 自动记一次触发（不依赖 agent 手动 record_use）。
    try:
        record_use(visible[name], _dt.datetime.now(_dt.timezone.utc).isoformat())
    except Exception:
        pass
    return (visible[name] / SKILL_ENTRY).read_text(encoding="utf-8")


def tool_record_use(name: str, root: Optional[Path] = None) -> Dict[str, Any]:
    import datetime as _dt

    from memoket.lifecycle import record_use

    visible = visible_skill_dirs(root)
    if name not in visible:
        raise KeyError(f"skill not found or not visible: {name}")
    rec = record_use(visible[name], _dt.datetime.now(_dt.timezone.utc).isoformat())
    return {"name": name, "used_count": rec.get("used_count"), "last_used_at": rec.get("last_used_at")}


# ── JSON-RPC 处理（与传输解耦，便于测试）────────────────────────

def _result(req_id, payload) -> Dict[str, Any]:
    return {"jsonrpc": "2.0", "id": req_id, "result": payload}


def _error(req_id, code: int, message: str) -> Dict[str, Any]:
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


def _tool_text(payload) -> Dict[str, Any]:
    text = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False, indent=2)
    return {"content": [{"type": "text", "text": text}], "isError": False}


def handle(message: Dict[str, Any], root: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """处理一条 JSON-RPC 消息；通知返回 None。"""
    method = message.get("method")
    req_id = message.get("id")
    params = message.get("params") or {}

    if method == "initialize":
        return _result(req_id, {
            "protocolVersion": params.get("protocolVersion") or PROTOCOL_FALLBACK,
            "capabilities": {"tools": {}},
            "serverInfo": SERVER_INFO,
        })
    if method in ("notifications/initialized", "notifications/cancelled"):
        return None
    if method == "ping":
        return _result(req_id, {})
    if method == "tools/list":
        return _result(req_id, {"tools": TOOLS})
    if method == "tools/call":
        tool = params.get("name")
        args = params.get("arguments") or {}
        try:
            if tool == "search_skills":
                payload = tool_search_skills(args["query"], args.get("limit", 5), root)
            elif tool == "get_skill":
                payload = tool_get_skill(args["name"], root)
            elif tool == "record_use":
                payload = tool_record_use(args["name"], root)
            else:
                return _error(req_id, -32602, f"unknown tool: {tool}")
            return _result(req_id, _tool_text(payload))
        except KeyError as exc:
            return _result(req_id, {"content": [{"type": "text", "text": str(exc)}], "isError": True})
        except Exception as exc:  # 工具内部错误以 isError 返回，不挂掉 server
            return _result(req_id, {"content": [{"type": "text", "text": f"error: {exc}"}], "isError": True})
    if req_id is None:
        return None  # 未知通知：忽略
    return _error(req_id, -32601, f"method not found: {method}")


def serve(root: Optional[Path] = None) -> int:
    """stdio 主循环：每行一条 JSON-RPC 消息。"""
    stdin = sys.stdin.buffer
    stdout = sys.stdout.buffer
    for raw in iter(stdin.readline, b""):
        raw = raw.strip()
        if not raw:
            continue
        try:
            message = json.loads(raw.decode("utf-8"))
        except Exception:
            continue
        response = handle(message, root)
        if response is not None:
            stdout.write(json.dumps(response, ensure_ascii=False).encode("utf-8") + b"\n")
            stdout.flush()
    return 0
