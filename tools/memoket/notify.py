"""把一段文本推到飞书 / Lark（用于每日技能用量报告）。

凭据从环境变量读，**绝不硬编码、不入库**：
    FEISHU_APP_ID, FEISHU_APP_SECRET, FEISHU_TO_EMAIL   （收件人邮箱身份）
可选 FEISHU_BASE（默认国内 open.feishu.cn；海外 Lark 用 open.larksuite.com）。
未配齐则返回 (False, "...not configured...")，调用方据此跳过——不报错。
纯标准库（urllib），无第三方依赖。
"""
from __future__ import annotations

import json
import os
import urllib.request
from typing import Optional, Tuple


def _creds_from_lark_mcp() -> Tuple[Optional[str], Optional[str]]:
    """Fallback: reuse an already-configured `lark`/feishu MCP server's app_id/secret
    from ~/.claude.json (its `-a`/`-s` args), so a Feishu-bot user can push without
    setting FEISHU_APP_ID/SECRET. Returns (None, None) if not found."""
    try:
        cfg = json.load(open(os.path.expanduser("~/.claude.json"), encoding="utf-8"))
        for name, s in (cfg.get("mcpServers") or {}).items():
            args = [str(a) for a in (s.get("args") or [])]
            if "lark-mcp" in " ".join(args) or name.lower() in ("lark", "feishu"):
                aid = sec = None
                for i, a in enumerate(args):
                    if a == "-a" and i + 1 < len(args):
                        aid = args[i + 1]
                    if a == "-s" and i + 1 < len(args):
                        sec = args[i + 1]
                if aid and sec:
                    return aid, sec
    except Exception:
        pass
    return None, None


def _post(url: str, payload: dict, token: Optional[str] = None) -> dict:
    data = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json; charset=utf-8"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def notify_feishu(text: str, app_id: Optional[str] = None, app_secret: Optional[str] = None,
                  to_email: Optional[str] = None, base: Optional[str] = None) -> Tuple[bool, str]:
    """发送 text 到飞书。返回 (ok, detail)。未配齐凭据 → (False, 'not configured')。"""
    app_id = app_id or os.environ.get("FEISHU_APP_ID")
    app_secret = app_secret or os.environ.get("FEISHU_APP_SECRET")
    to_email = to_email or os.environ.get("FEISHU_TO_EMAIL")
    base = (base or os.environ.get("FEISHU_BASE") or "https://open.feishu.cn").rstrip("/")
    if not (app_id and app_secret):  # fall back to an existing lark MCP's creds
        a, s = _creds_from_lark_mcp()
        app_id, app_secret = app_id or a, app_secret or s
    if not (app_id and app_secret):
        return False, "no Feishu app creds (set FEISHU_APP_ID/SECRET or configure a lark MCP) — skipped"
    if not to_email:
        return False, "FEISHU_TO_EMAIL not set — skipped"

    try:
        tok = _post(f"{base}/open-apis/auth/v3/tenant_access_token/internal",
                    {"app_id": app_id, "app_secret": app_secret})
        if tok.get("code") != 0:
            return False, f"token error: {tok.get('code')} {tok.get('msg')}"
        token = tok["tenant_access_token"]
        res = _post(f"{base}/open-apis/im/v1/messages?receive_id_type=email",
                    {"receive_id": to_email, "msg_type": "text",
                     "content": json.dumps({"text": text}, ensure_ascii=False)},
                    token=token)
        if res.get("code") != 0:
            return False, f"send error: {res.get('code')} {res.get('msg')}"
        return True, "sent"
    except Exception as exc:
        return False, f"exception: {exc!r}"
