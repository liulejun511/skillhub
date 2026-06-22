"""capsoul-db 连接器：Capsoul/memoket 后端数据库素材源（产品专属，自核心迁出）。

这是「产品细节止于连接器」的范例：conversations/lines/participants 等表结构
只存在于本文件，核心与其他连接器对其零感知（R15.2）。

配置：MEMOKET_DB_DSN（强只读连接）、MEMOKET_DB_MAX_CONVS（默认 200）。
拉取偏好更干净的信号：conversations.summary 优先，并附说话人归属的转写明细。
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import List, Optional

from memoket import paths
from memoket.connectors.generic_sql import open_readonly_pg
from memoket.errors import MemoketError


def _sanitize(name: str, fallback: str) -> str:
    name = (name or "").strip() or fallback
    name = re.sub(r"[^\w一-鿿\- ]", "_", name)[:60].strip().replace(" ", "_")
    return name or fallback


class CapsoulDbConnector:
    name = "capsoul-db"

    def _out_dir(self) -> Path:
        d = paths.work_dir() / "_db_pull"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def pull(self, user_id: str, since: Optional[str]) -> List[Path]:
        dsn = os.environ.get("MEMOKET_DB_DSN")
        if not dsn:
            raise MemoketError("capsoul-db 连接器需要环境变量 MEMOKET_DB_DSN。")
        max_convs = int(os.environ.get("MEMOKET_DB_MAX_CONVS", "200"))

        conn = open_readonly_pg(dsn)
        written: List[Path] = []
        try:
            cur = conn.cursor()
            params: list = [user_id]
            since_clause = ""
            if since:
                since_clause = " AND started_at > %s"
                params.append(since)
            params.append(max_convs)
            cur.execute(
                "SELECT id, audio_id, title, summary, started_at, language_code "
                "FROM conversations WHERE tenant_id = %s" + since_clause +
                " ORDER BY started_at NULLS LAST, id LIMIT %s;",
                params,
            )
            convs = cur.fetchall()
            out = self._out_dir()
            for cid, audio_id, title, summary, started_at, lang in convs:
                cur.execute(
                    "SELECT COALESCE(p.confirmed_name, p.name, l.speaker_id_in_audio, 'Speaker'), l.text "
                    "FROM lines l LEFT JOIN participants p "
                    "ON p.tenant_id = l.tenant_id AND p.id = l.participant_id "
                    "WHERE l.tenant_id = %s AND l.conversation_id = %s "
                    "ORDER BY l.started_offset_ms NULLS LAST, l.id;",
                    (user_id, cid),
                )
                rows = cur.fetchall()
                transcript = "\n".join(f"{spk}: {txt}" for spk, txt in rows if txt and txt.strip())
                if not (summary and summary.strip()) and not transcript.strip():
                    continue
                header = (
                    f"# {title or '(untitled)'}\n"
                    f"# conversation_id={cid} audio_id={audio_id} started_at={started_at} lang={lang}\n"
                )
                summary_block = f"\n## Summary\n{summary.strip()}\n" if summary and summary.strip() else ""
                body = f"{header}{summary_block}\n## Transcript\n{transcript}\n"
                fpath = out / f"{cid}_{_sanitize(title, 'conversation')}.transcript"
                fpath.write_text(body, encoding="utf-8")
                written.append(fpath)
        finally:
            conn.close()
        return written

    def test(self) -> bool:
        dsn = os.environ.get("MEMOKET_DB_DSN")
        if not dsn:
            return False
        conn = open_readonly_pg(dsn)
        conn.close()
        return True
