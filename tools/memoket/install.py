"""install / trust / update / fork：包管理与供应链安全。

安全（设计 H1）：装来的技能落地即 quarantine、脚本默认禁运；审阅后才激活。
"""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Optional

from memoket import lockfile, paths, registry, semver
from memoket.errors import ConflictError, MemoketError
from memoket.integrity import hash_package


def _resolve_source(entry: dict, root: Optional[Path]) -> Path:
    source = entry.get("source", {})
    if source.get("type") == "local":
        return (root or paths.workspace()) / source["path"]
    raise NotImplementedError(f"暂不支持的 source 类型: {source.get('type')}（远端 git 留待后续）")


def install_skill(name: str, root: Optional[Path] = None) -> Path:
    """安装外部技能到 vault/installed/，落地即 quarantine。"""
    entry = registry.find_entry(name, root)
    if entry is None:
        raise MemoketError(f"registry 中找不到技能: {name}")

    if (paths.vault_mine(root) / name).exists():
        raise ConflictError(
            f"已有同名「我编写的」技能，未覆盖: vault/mine/{name}（请重命名或显式处理）"
        )

    src = _resolve_source(entry, root)
    if not (src / "SKILL.md").exists():
        raise MemoketError(f"source 路径下无 SKILL.md: {src}")

    target = paths.vault_installed(root) / name
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(src, target)

    lock_entry = {
        "name": name,
        "version": entry.get("version"),
        "source": entry.get("source"),
        "integrity": hash_package(target),
        "provenance": _provenance(entry),
        "trust": "quarantine",
        "scripts_allowed": False,
    }
    lockfile.upsert_entry(lock_entry, root)
    return target


def _provenance(entry: dict) -> str:
    source = entry.get("source", {})
    if source.get("type") == "local":
        return f"local:{source.get('path')}"
    if source.get("type") == "git":
        return f"git:{source.get('url')}@{source.get('rev', 'HEAD')}"
    return "unknown"


def trust_skill(name: str, allow_scripts: bool = False, root: Optional[Path] = None) -> dict:
    """审阅后激活一个 quarantine 技能（可选授权脚本执行）。"""
    entry = lockfile.get_entry(name, root)
    if entry is None:
        raise MemoketError(f"未安装该技能: {name}")
    entry["trust"] = "active"
    entry["scripts_allowed"] = bool(allow_scripts)
    lockfile.upsert_entry(entry, root)
    return entry


def update_skill(name: str, root: Optional[Path] = None) -> str:
    """对照 registry 更新已安装技能。返回 'updated' / 'skip' / 'local-newer'。"""
    reg = registry.find_entry(name, root)
    lock = lockfile.get_entry(name, root)
    if reg is None or lock is None:
        raise MemoketError(f"无法更新（registry 或 lock 中缺失）: {name}")
    cmp = semver.compare(reg["version"], lock["version"])
    if cmp == 0:
        return "skip"
    if cmp < 0:
        return "local-newer"
    # registry 更新 → 重装并重新隔离（内容已变，安全起见重回 quarantine）
    install_skill(name, root)
    return "updated"


def fork_installed(name: str, root: Optional[Path] = None) -> Path:
    """把 installed 技能 fork 到 mine（编辑前的隔离），upstream update 不再影响本地改动。"""
    src = paths.vault_installed(root) / name
    if not (src / "SKILL.md").exists():
        raise MemoketError(f"未安装该技能，无法 fork: {name}")
    dst = paths.vault_mine(root) / name
    if dst.exists():
        raise ConflictError(f"vault/mine 已有同名技能: {name}")
    shutil.copytree(src, dst)
    # 脱离 upstream：移除 installed 副本与 lock 记录
    shutil.rmtree(src)
    lockfile.remove_entry(name, root)
    return dst
