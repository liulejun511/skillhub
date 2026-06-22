"""工作区路径布局。

工具运行在一个「工作区」（默认即仓库根，可用 MEMOKET_HOME 覆盖）。
schemas/ 随包发布，按包相对路径定位；vault/ 等用户数据按工作区定位。
"""
from __future__ import annotations

import os
from pathlib import Path

# 包所在仓库根（dev 模式下 memoket/ 与 schemas/ 同级于此）。
PACKAGE_ROOT = Path(__file__).resolve().parents[1]


def workspace() -> Path:
    """当前工作区根：MEMOKET_HOME 或包根。"""
    env = os.environ.get("MEMOKET_HOME")
    return Path(env).resolve() if env else PACKAGE_ROOT


def vault(root: Path | None = None) -> Path:
    return (root or workspace()) / "vault"


def vault_mine(root: Path | None = None) -> Path:
    return vault(root) / "mine"


def vault_installed(root: Path | None = None) -> Path:
    return vault(root) / "installed"


def vault_archive(root: Path | None = None) -> Path:
    return vault(root) / "archive"


def skills_dir(root: Path | None = None) -> Path:
    """工具自带技能（distill/evolve/garden/...）。"""
    return (root or workspace()) / "skills"


def registry_path(root: Path | None = None) -> Path:
    return (root or workspace()) / "registry.json"


def lockfile_path(root: Path | None = None) -> Path:
    return (root or workspace()) / "memoket.lock"


def watermark_path(root: Path | None = None) -> Path:
    return (root or workspace()) / "watermark.json"


def kernel_path(root: Path | None = None) -> Path:
    return (root or workspace()) / "KERNEL.lock"


def signals_dir(root: Path | None = None) -> Path:
    return (root or workspace()) / "signals"


def eval_dir(root: Path | None = None) -> Path:
    return (root or workspace()) / "eval"


def index_path(root: Path | None = None) -> Path:
    return (root or workspace()) / "index" / "skills.json"


def profile_path(root: Path | None = None) -> Path:
    return (root or workspace()) / "profile" / "values.md"


def work_dir(root: Path | None = None) -> Path:
    """提炼瞬态工作区（gitignored）。"""
    return (root or workspace()) / ".work"


def build_dir(root: Path | None = None) -> Path:
    return (root or workspace()) / "build"
