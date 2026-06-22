"""file 连接器：本地文件/目录作为素材源——**通用底座，零配置可用**。

文本优先契约：任何人不需要数据库/任何外部系统，把文本文件丢进 `inbox/`
（或用 MEMOKET_SOURCE_DIR 指定目录）即可被 ingest/cycle 捡到。
since 按文件 mtime 增量。
"""
from __future__ import annotations

import datetime as _dt
import os
from pathlib import Path
from typing import List, Optional

from memoket import paths


def inbox_dir(root: Optional[Path] = None) -> Path:
    """零配置素材收件箱：<workspace>/inbox/（gitignored，自动创建）。"""
    d = (root or paths.workspace()) / "inbox"
    d.mkdir(parents=True, exist_ok=True)
    return d


class FileDirConnector:
    name = "file"

    def __init__(self, source_dir: Optional[Path] = None) -> None:
        self._source_dir = source_dir

    def _dir(self) -> Path:
        if self._source_dir is not None:
            return Path(self._source_dir)
        env = os.environ.get("MEMOKET_SOURCE_DIR")
        return Path(env) if env else inbox_dir()

    def pull(self, user_id: str, since: Optional[str]) -> List[Path]:
        d = self._dir()
        if not d.exists():
            return []
        if d.is_file():
            files = [d]
        else:
            files = sorted(p for p in d.iterdir() if p.is_file())
        if since:
            try:
                since_ts = _dt.datetime.fromisoformat(since.replace("Z", "+00:00")).timestamp()
                files = [f for f in files if f.stat().st_mtime > since_ts]
            except ValueError:
                pass
        return files

    def test(self) -> bool:
        return self._dir().exists()
