"""ingest：经素材源连接器增量拉取素材到 .work/。

素材源是即插即用的 SourceConnector（memoket.connectors）：file / generic-sql /
claude-chat / capsoul-db / …。核心不含任何产品专属细节（R15.2）。

连接器选择优先级：显式 source 参数 > MEMOKET_SOURCE 环境变量 > 兼容推断
（设了 MEMOKET_DB_DSN → capsoul-db，否则 file）。
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Callable, List, Optional, Union

from memoket import paths, watermark
from memoket.connectors import SourceConnector, get_connector

# 兼容旧签名：测试/调用方可直接传 (user_id, since) -> List[Path] 的可调用对象
LegacySource = Callable[[str, Optional[str]], List[Path]]
SourceSpec = Union[str, SourceConnector, LegacySource, None]


def resolve_source(source: SourceSpec = None, from_path: Optional[Path] = None
                   ) -> Union[SourceConnector, LegacySource]:
    """把 source 规格解析为可拉取对象。

    from_path：一次性「指哪吃哪」——直接给一个文本文件或目录，优先于一切配置。
    """
    if from_path is not None:
        from memoket.connectors.file_dir import FileDirConnector

        return FileDirConnector(source_dir=Path(from_path))
    if source is None:
        env = os.environ.get("MEMOKET_SOURCE")
        if env:
            return get_connector(env)
        # 兼容推断：老用法里设了 DB DSN 即走 Capsoul 库
        if os.environ.get("MEMOKET_DB_DSN"):
            return get_connector("capsoul-db")
        return get_connector("file")
    if isinstance(source, str):
        return get_connector(source)
    return source  # SourceConnector 实例或遗留 callable


def file_source(user_id: str, since: Optional[str], source_dir: Optional[Path] = None) -> List[Path]:
    """兼容旧接口：file 连接器的函数形态（既有测试/脚本在用）。"""
    from memoket.connectors.file_dir import FileDirConnector

    return FileDirConnector(source_dir=source_dir).pull(user_id, since)


def ingest(user_id: str, since: Optional[str] = None, root: Optional[Path] = None,
           source: SourceSpec = None, from_path: Optional[Path] = None) -> List[Path]:
    """增量拉取素材到 .work/，返回 staged 文件路径列表。

    不推进水位——由循环成功收尾后再推进（幂等，设计 H6）。
    from_path 为一次性文本输入（文件或目录），优先于连接器配置，且不受水位过滤。
    """
    if since is None and from_path is None:
        since = watermark.get_last_processed(root)
    src = resolve_source(source, from_path=from_path)
    if hasattr(src, "pull"):
        items = src.pull(user_id, since)
    else:
        items = src(user_id, since)

    work = paths.work_dir(root)
    work.mkdir(parents=True, exist_ok=True)
    staged: List[Path] = []
    for item in items:
        dst = work / item.name
        if Path(item).resolve() != dst.resolve():
            shutil.copy(item, dst)
        staged.append(dst)
    return staged
