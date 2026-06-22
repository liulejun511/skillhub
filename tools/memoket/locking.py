"""文件锁：防止两个循环或循环+手动操作并发写 vault/水位（设计 H6）。"""
from __future__ import annotations

import os
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

from memoket import paths
from memoket.errors import MemoketError


class Locked(MemoketError):
    """工作区已被另一进程锁定。"""


@contextmanager
def file_lock(root: Optional[Path] = None, timeout: float = 0.0, poll: float = 0.05):
    """获取工作区独占锁；超时未得则抛 Locked。timeout=0 表示不等待。"""
    work = paths.work_dir(root)
    work.mkdir(parents=True, exist_ok=True)
    lock_path = work / "workspace.lock"
    deadline = time.monotonic() + timeout
    fd = None
    while True:
        try:
            fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            break
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise Locked(f"工作区被锁定: {lock_path}")
            time.sleep(poll)
    try:
        os.write(fd, str(os.getpid()).encode())
        yield lock_path
    finally:
        if fd is not None:
            os.close(fd)
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass
