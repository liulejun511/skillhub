"""feishu 连接器：飞书/Lark 云文档或群消息作为素材源。

配置（环境变量，R13.1 非交互注入）：
- MEMOKET_FEISHU_APP_ID / MEMOKET_FEISHU_APP_SECRET   应用凭证（必填）
- MEMOKET_FEISHU_MODE   docs（默认，拉云文档）| messages（拉群消息）
- MEMOKET_FEISHU_CHAT_ID   messages 模式必填：目标群 chat_id
- MEMOKET_FEISHU_MAX   每轮最多条数（默认 50）

需要在飞书开放平台为应用开通对应权限并发布版本：
- docs 模式：drive:drive:readonly（列文件）+ docx:document:readonly（读正文）
- messages 模式：im:message:readonly + im:chat:readonly（读群消息）

只读：本连接器只调读取类接口，绝不写飞书。素材进 .work/（gitignored）。
"""
from __future__ import annotations

import json
import os
import re
import urllib.request
from pathlib import Path
from typing import List, Optional

from memoket import paths
from memoket.errors import MemoketError

_BASE = "https://open.feishu.cn/open-apis"


def _sanitize(name: str, fallback: str) -> str:
    name = (name or "").strip() or fallback
    name = re.sub(r"[^\w一-鿿\- ]", "_", name)[:60].strip().replace(" ", "_")
    return name or fallback


def _post(url: str, payload: dict, token: Optional[str] = None) -> dict:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers)
    return json.loads(urllib.request.urlopen(req, timeout=30).read())


def _get(url: str, token: str) -> dict:
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + token})
    return json.loads(urllib.request.urlopen(req, timeout=30).read())


def tenant_token(app_id: str, app_secret: str) -> str:
    r = _post(f"{_BASE}/auth/v3/tenant_access_token/internal",
              {"app_id": app_id, "app_secret": app_secret})
    if r.get("code") != 0:
        raise MemoketError(f"飞书 token 获取失败: {r.get('msg')}")
    return r["tenant_access_token"]


class FeishuConnector:
    name = "feishu"

    def _out_dir(self) -> Path:
        d = paths.work_dir() / "_feishu"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _token(self) -> str:
        app_id = os.environ.get("MEMOKET_FEISHU_APP_ID")
        secret = os.environ.get("MEMOKET_FEISHU_APP_SECRET")
        if not app_id or not secret:
            raise MemoketError("feishu 连接器需要 MEMOKET_FEISHU_APP_ID 与 MEMOKET_FEISHU_APP_SECRET。")
        return tenant_token(app_id, secret)

    def pull(self, user_id: str, since: Optional[str]) -> List[Path]:
        mode = os.environ.get("MEMOKET_FEISHU_MODE", "docs")
        token = self._token()
        if mode == "messages":
            return self._pull_messages(token)
        return self._pull_docs(token)

    # ── docs：列云文档 → 取纯文本 ─────────────────────────────
    def _pull_docs(self, token: str) -> List[Path]:
        maxn = int(os.environ.get("MEMOKET_FEISHU_MAX", "50"))
        listing = _get(f"{_BASE}/drive/v1/files?page_size={maxn}", token)
        if listing.get("code") != 0:
            raise MemoketError(f"飞书列文件失败（检查 drive 权限）: {listing.get('msg')}")
        out, written = self._out_dir(), []
        for f in (listing.get("data") or {}).get("files", []):
            if f.get("type") != "docx":
                continue
            tok = f.get("token")
            raw = _get(f"{_BASE}/docx/v1/documents/{tok}/raw_content", token)
            text = (raw.get("data") or {}).get("content", "")
            if not text.strip():
                continue
            title = f.get("name") or tok
            body = f"# {title}\n# feishu_doc={tok}\n\n{text.strip()}\n"
            fp = out / f"{_sanitize(title, tok)}.transcript"
            fp.write_text(body, encoding="utf-8")
            written.append(fp)
        return written

    # ── messages：拉群消息 → 文本 ────────────────────────────
    def _pull_messages(self, token: str) -> List[Path]:
        chat_id = os.environ.get("MEMOKET_FEISHU_CHAT_ID")
        if not chat_id:
            raise MemoketError("messages 模式需要 MEMOKET_FEISHU_CHAT_ID。")
        maxn = int(os.environ.get("MEMOKET_FEISHU_MAX", "50"))
        url = (f"{_BASE}/im/v1/messages?container_id_type=chat"
               f"&container_id={chat_id}&page_size={maxn}&sort_type=ByCreateTimeDesc")
        r = _get(url, token)
        if r.get("code") != 0:
            raise MemoketError(f"飞书拉消息失败（检查 im 权限）: {r.get('msg')}")
        lines = []
        for m in (r.get("data") or {}).get("items", []):
            sender = (m.get("sender") or {}).get("id", "user")
            body = (m.get("body") or {}).get("content", "")
            try:
                txt = json.loads(body).get("text", "")
            except Exception:
                txt = body
            if txt and txt.strip():
                lines.append(f"{sender}: {txt.strip()}")
        if not lines:
            return []
        out = self._out_dir()
        fp = out / f"chat_{_sanitize(chat_id, 'feishu')}.transcript"
        fp.write_text(f"# feishu chat {chat_id}\n\n" + "\n".join(reversed(lines)) + "\n", encoding="utf-8")
        return [fp]

    def test(self) -> bool:
        self._token()  # 凭证可换 token 即视为连通（权限在 pull 时报）
        return True
