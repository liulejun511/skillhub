"""素材源连接器（SourceConnector）：即插即用的「素材进」侧。

与运行时适配器（memoket.adapters）对称的另一侧接口：
- RuntimeAdapter：技能 → 某运行时可消费形态（技能出）
- SourceConnector：某数据源 → 素材文件列表（素材进）

架构红线（R15.2/15.3）：核心不含任何特定产品的表结构/API 细节；
新增连接器不得要求改动核心格式、循环轨道与既有连接器。
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Protocol, runtime_checkable


@runtime_checkable
class SourceConnector(Protocol):
    """素材源连接器协议。

    pull(user_id, since) -> 素材文件路径列表（连接器自备临时输出目录；
    ingest 负责把文件复制进 .work/ 瞬态区，连接器不直接写 .work/ 根）。
    test() -> 连通性自检（init 向导用），失败抛异常或返回 False。
    """

    name: str

    def pull(self, user_id: str, since: Optional[str]) -> List[Path]: ...

    def test(self) -> bool: ...


_REGISTRY: Dict[str, "SourceConnector"] = {}


def register(connector: "SourceConnector") -> None:
    _REGISTRY[connector.name] = connector


def get_connector(name: str) -> "SourceConnector":
    if name not in _REGISTRY:
        raise KeyError(
            f"未知素材源连接器: {name}（可用: {', '.join(sorted(_REGISTRY)) or '无'}）"
        )
    return _REGISTRY[name]


def available() -> List[str]:
    return sorted(_REGISTRY)


# ── 注册内置连接器 ──────────────────────────────────────────────
from memoket.connectors.file_dir import FileDirConnector  # noqa: E402
from memoket.connectors.generic_sql import GenericSqlConnector  # noqa: E402
from memoket.connectors.claude_chat import ClaudeChatConnector  # noqa: E402
from memoket.connectors.capsoul_db import CapsoulDbConnector  # noqa: E402
from memoket.connectors.feishu import FeishuConnector  # noqa: E402

register(FileDirConnector())
register(GenericSqlConnector())
register(ClaudeChatConnector())
register(CapsoulDbConnector())
register(FeishuConnector())
