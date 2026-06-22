"""generic-sql 连接器：通用 PostgreSQL 素材源（查询模板可配，不绑任何产品 schema）。

配置（环境变量，R13.1 非交互注入）：
- MEMOKET_SQL_DSN     连接串 postgresql://user:pwd@host:port/db
- MEMOKET_SQL_QUERY   查询模板，可用占位符 %(user_id)s 与 %(since)s；
                      约定返回列：第 1 列=唯一 id，第 2 列=标题（可空），第 3 列=文本内容。
- MEMOKET_SQL_LIMIT   最多行数（默认 200）

强只读保证：default_transaction_read_only=on + readonly session + 连接后断言。
每行 → 一个素材文件（写入连接器自己的临时输出目录）。
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import List, Optional

from memoket import paths
from memoket.errors import MemoketError


def _sanitize(name: str, fallback: str) -> str:
    name = (name or "").strip() or fallback
    name = re.sub(r"[^\w一-鿿\- ]", "_", name)[:60].strip().replace(" ", "_")
    return name or fallback


def open_readonly_pg(dsn: str):
    """打开一个强制只读的 PostgreSQL 连接（连接级 + 会话级 + 断言三重保险）。"""
    import psycopg2  # 惰性导入：不用 SQL 源时核心不依赖驱动

    conn = psycopg2.connect(dsn, connect_timeout=15, options="-c default_transaction_read_only=on")
    conn.set_session(readonly=True, autocommit=True)
    cur = conn.cursor()
    cur.execute("SHOW transaction_read_only;")
    if cur.fetchone()[0] != "on":
        conn.close()
        raise MemoketError("DB 会话非只读，已中止（保护数据库）。")
    return conn


class GenericSqlConnector:
    name = "generic-sql"

    def _out_dir(self) -> Path:
        d = paths.work_dir() / "_generic_sql"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def pull(self, user_id: str, since: Optional[str]) -> List[Path]:
        dsn = os.environ.get("MEMOKET_SQL_DSN")
        query = os.environ.get("MEMOKET_SQL_QUERY")
        if not dsn or not query:
            raise MemoketError("generic-sql 连接器需要 MEMOKET_SQL_DSN 与 MEMOKET_SQL_QUERY。")
        limit = int(os.environ.get("MEMOKET_SQL_LIMIT", "200"))

        conn = open_readonly_pg(dsn)
        written: List[Path] = []
        try:
            cur = conn.cursor()
            cur.execute(query, {"user_id": user_id, "since": since})
            out = self._out_dir()
            for row in cur.fetchmany(limit):
                rid, title, text = row[0], (row[1] if len(row) > 1 else None), (row[2] if len(row) > 2 else None)
                if text is None and title is None:
                    continue
                body = f"# {title or '(untitled)'}\n# id={rid}\n\n{(text or '').strip()}\n"
                fpath = out / f"{rid}_{_sanitize(str(title or ''), 'item')}.transcript"
                fpath.write_text(body, encoding="utf-8")
                written.append(fpath)
        finally:
            conn.close()
        return written

    def test(self) -> bool:
        dsn = os.environ.get("MEMOKET_SQL_DSN")
        if not dsn:
            return False
        conn = open_readonly_pg(dsn)
        conn.close()
        return True
