"""Skill 包：解析与数据模型。

一个技能 = 一个目录，入口 `SKILL.md`（YAML frontmatter + Markdown 正文）。
本模块只做「解析为结构化对象」与「结构性错误」；必填字段/触发场景等
逻辑校验在 memoket.validate（任务 3）。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from memoket.errors import (
    EmptyBodyError,
    MalformedFrontmatterError,
    MissingFrontmatterError,
    SkillNotFoundError,
)

# 当前格式契约版本；技能未声明 format_version 时按此默认（迁移 runner 见 R14/任务 19）。
CURRENT_FORMAT_VERSION = 1

# 合法生命周期状态（与 evolution.json.lifecycle 同步）。
LIFECYCLE_STATES = ("draft", "active", "deprecated", "archived")

SKILL_ENTRY = "SKILL.md"

# 匹配开头的 frontmatter：以 `---` 行起始，到下一行 `---` 结束，其后为正文。
# 兼容 \n 与 \r\n。
_FRONTMATTER_RE = re.compile(
    r"^---[ \t]*\r?\n(?P<fm>.*?)\r?\n---[ \t]*(?:\r?\n(?P<body>.*))?$",
    re.DOTALL,
)
_STARTS_FRONTMATTER_RE = re.compile(r"^---[ \t]*\r?\n")


@dataclass
class SkillPackage:
    """解析后的技能包。缺失的可选字段为 None / 空集合。

    必填字段（name/description/version）若缺失，在此为 None —— 由 validate 层报告，
    解析层不在此处抛错，以便校验能一次列出所有缺口。
    """

    name: Optional[str]
    description: Optional[str]
    version: Optional[str]
    body: str
    format_version: int = CURRENT_FORMAT_VERSION
    author: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    origin: Optional[str] = None
    status: str = "draft"
    locales: Dict[str, Any] = field(default_factory=dict)
    adapters: Dict[str, Any] = field(default_factory=dict)
    # 原始 frontmatter（保留未知字段，供前向兼容/调试）。
    frontmatter: Dict[str, Any] = field(default_factory=dict)
    # 来源文件路径（SKILL.md），可能为 None（从字符串解析时）。
    path: Optional[Path] = None

    @classmethod
    def from_frontmatter(
        cls,
        data: Dict[str, Any],
        body: str,
        path: Optional[Path] = None,
    ) -> "SkillPackage":
        tags = data.get("tags") or []
        if isinstance(tags, str):
            tags = [tags]
        return cls(
            name=data.get("name"),
            description=data.get("description"),
            version=data.get("version"),
            body=body.strip(),
            format_version=data.get("format_version", CURRENT_FORMAT_VERSION),
            author=data.get("author"),
            tags=list(tags),
            origin=data.get("origin"),
            status=data.get("status") or "draft",
            locales=data.get("locales") or {},
            adapters=data.get("adapters") or {},
            frontmatter=dict(data),
            path=Path(path) if path is not None else None,
        )

    def adapter_fields(self, adapter_name: str) -> Dict[str, Any]:
        """取某适配器的扩展字段命名空间 adapters.<name>.*（缺失则空 dict）。"""
        value = self.adapters.get(adapter_name) or {}
        return value if isinstance(value, dict) else {}


def _split_frontmatter(text: str, where: str) -> tuple[str, str]:
    """拆出 (frontmatter 文本, 正文)。结构性错误显式抛出。"""
    if not _STARTS_FRONTMATTER_RE.match(text):
        raise MissingFrontmatterError(f"{where}: 文件未以 YAML frontmatter（开头的 ---）起始")
    match = _FRONTMATTER_RE.match(text)
    if not match:
        raise MalformedFrontmatterError(f"{where}: frontmatter 缺少闭合的 --- 行")
    return match.group("fm"), (match.group("body") or "")


def parse_skill_text(text: str, where: str = "<string>") -> SkillPackage:
    """从字符串解析一个技能。"""
    fm_text, body = _split_frontmatter(text, where)
    try:
        data = yaml.safe_load(fm_text)
    except yaml.YAMLError as exc:
        raise MalformedFrontmatterError(f"{where}: frontmatter YAML 解析失败: {exc}") from exc
    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise MalformedFrontmatterError(f"{where}: frontmatter 必须是键值映射，实际为 {type(data).__name__}")
    if not body.strip():
        raise EmptyBodyError(f"{where}: frontmatter 之后的 Markdown 正文为空")
    return SkillPackage.from_frontmatter(data, body, None)


def serialize_skill(frontmatter: Dict[str, Any], body: str) -> str:
    """把 frontmatter + 正文重新组装成 SKILL.md 文本（用于迁移/locale 同步等改写）。"""
    fm = yaml.safe_dump(frontmatter, sort_keys=False, allow_unicode=True).rstrip("\n")
    return f"---\n{fm}\n---\n\n{body.rstrip()}\n"


def write_skill(skill_dir, frontmatter: Dict[str, Any], body: str) -> Path:
    """把改写后的技能写回 <skill_dir>/SKILL.md。"""
    skill_md = Path(skill_dir) / SKILL_ENTRY
    skill_md.write_text(serialize_skill(frontmatter, body), encoding="utf-8")
    return skill_md


def parse_skill(path) -> SkillPackage:
    """从路径解析一个技能。

    path 可为技能目录（含 SKILL.md）或 SKILL.md 文件本身。
    """
    p = Path(path)
    skill_md = p / SKILL_ENTRY if p.is_dir() else p
    if not skill_md.exists():
        raise SkillNotFoundError(f"找不到技能入口文件: {skill_md}")
    text = skill_md.read_text(encoding="utf-8")
    pkg = parse_skill_text(text, where=str(skill_md))
    pkg.path = skill_md
    return pkg
