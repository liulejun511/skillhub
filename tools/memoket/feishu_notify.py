"""通过飞书机器人给指定用户发文本消息（用于触发日报推送）。

配置（环境变量）：
- MEMOKET_FEISHU_APP_ID / MEMOKET_FEISHU_APP_SECRET   机器人凭证
- MEMOKET_FEISHU_NOTIFY_USER   收件人 open_id（或用 resolve_open_id 由邮箱查）

只用发送/通讯录读取接口，不改任何飞书数据。
"""
from __future__ import annotations

import json
import os
import urllib.request
from typing import Optional

from memoket.connectors.feishu import tenant_token
from memoket.errors import MemoketError

_BASE = "https://open.feishu.cn/open-apis"


def resolve_open_id(email: str, token: str) -> Optional[str]:
    """用邮箱查 open_id（需 contact 读权限）。"""
    req = urllib.request.Request(
        f"{_BASE}/contact/v3/users/batch_get_id?user_id_type=open_id",
        data=json.dumps({"emails": [email]}).encode(),
        headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"},
    )
    d = json.loads(urllib.request.urlopen(req, timeout=20).read())
    if d.get("code") != 0:
        raise MemoketError(f"查 open_id 失败: {d.get('msg')}")
    items = (d.get("data") or {}).get("user_list") or []
    return items[0].get("user_id") if items else None


def send_text(receive_id: str, text: str, token: str, id_type: str = "open_id") -> dict:
    """发一条文本消息。id_type 可为 open_id / email / chat_id 等。"""
    req = urllib.request.Request(
        f"{_BASE}/im/v1/messages?receive_id_type={id_type}",
        data=json.dumps({
            "receive_id": receive_id,
            "msg_type": "text",
            "content": json.dumps({"text": text}, ensure_ascii=False),
        }).encode(),
        headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"},
    )
    d = json.loads(urllib.request.urlopen(req, timeout=20).read())
    if d.get("code") != 0:
        raise MemoketError(f"飞书发送失败: code={d.get('code')} {d.get('msg')}")
    return d


def notify(text: str, user: Optional[str] = None, email: Optional[str] = None,
           chat: Optional[str] = None) -> dict:
    """发报告。优先级：open_id(user) > 群(chat) > 邮箱直发(email)。

    邮箱直发用 receive_id_type=email，无需 contact 查 open_id（只要 im 发送权限）。
    """
    app_id = os.environ.get("MEMOKET_FEISHU_APP_ID")
    secret = os.environ.get("MEMOKET_FEISHU_APP_SECRET")
    if not app_id or not secret:
        raise MemoketError("需要 MEMOKET_FEISHU_APP_ID / MEMOKET_FEISHU_APP_SECRET。")
    token = tenant_token(app_id, secret)

    user = user or os.environ.get("MEMOKET_FEISHU_NOTIFY_USER")
    chat = chat or os.environ.get("MEMOKET_FEISHU_NOTIFY_CHAT")
    email = email or os.environ.get("MEMOKET_FEISHU_NOTIFY_EMAIL")
    if user:
        return send_text(user, text, token, "open_id")
    if chat:
        return send_text(chat, text, token, "chat_id")
    if email:
        return send_text(email, text, token, "email")  # 直发，免 open_id 查询
    raise MemoketError("没有收件人（设 MEMOKET_FEISHU_NOTIFY_USER / _CHAT / _EMAIL 之一）。")
