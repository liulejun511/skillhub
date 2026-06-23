"""两层校验：通用层 + 适配器层。

- 通用层：frontmatter 符合 schema + description 含触发场景 + 正文非空。
- 适配器层：目标适配器所需的 adapters.<name>.* 扩展字段齐全。
二者互不阻塞、分别报告（设计 R2.4）。
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Sequence

from memoket.errors import FrontmatterError, EmptyBodyError, SkillNotFoundError
from memoket.schema import iter_schema_errors
from memoket.skill import SkillPackage, parse_skill

# 触发场景标志词（en/zh）；description 至少含其一，体现「何时用」。
# 放宽以接纳真实 Claude 技能的多样写法（Use this / whenever / Triggers on / 触发场景 等）。
_TRIGGER_PATTERNS = [
    r"\buse (when|this|it|for|to)\b",
    r"\bwhen(ever)?\b",
    r"\btriggers? (on|when|whenever)\b",
    r"用于", r"用来", r"何时", r"该用", r"当(你|需要|遇到|你想|出现)",
    r"适用于", r"适合", r"触发",
]
_TRIGGER_RE = re.compile("|".join(_TRIGGER_PATTERNS), re.IGNORECASE)


def has_trigger_scene(description: str | None) -> bool:
    return bool(description) and bool(_TRIGGER_RE.search(description))


def validate_universal(skill: SkillPackage) -> List[str]:
    """通用层校验，返回问题列表（空 = 通过）。"""
    issues: List[str] = []
    # schema：必填字段 / 类型 / 命名 / 版本 / 未知字段
    issues.extend(iter_schema_errors(skill.frontmatter))
    # 触发场景（schema 难表达，单独查）
    if skill.description and not has_trigger_scene(skill.description):
        issues.append("description: 缺少触发场景（应含 'Use when …' 或「用于/何时/适用于」等）")
    # 正文
    if not skill.body.strip():
        issues.append("body: Markdown 正文为空")
    return issues


def validate_adapter(skill: SkillPackage, adapter_name: str) -> List[str]:
    """适配器层校验：目标适配器所需扩展字段是否齐全。"""
    from memoket.adapters import get_adapter  # 延迟导入避免环依赖

    adapter = get_adapter(adapter_name)
    issues: List[str] = []
    fields = skill.adapter_fields(adapter.name)
    for required in adapter.required_fields():
        if required not in fields:
            issues.append(
                f"adapters.{adapter.name}.{required}: 缺少 {adapter.name} 适配器所需字段"
            )
    return issues


def validate_skill(path, adapters: Sequence[str] = ()) -> Dict[str, List[str]]:
    """校验单个技能，返回 {layer -> issues}。

    layer: 'universal' 或 'adapter:<name>'。解析层错误归入 'parse'。
    """
    result: Dict[str, List[str]] = {}
    try:
        skill = parse_skill(path)
    except (FrontmatterError, EmptyBodyError, SkillNotFoundError) as exc:
        result["parse"] = [str(exc)]
        return result
    result["universal"] = validate_universal(skill)
    for name in adapters:
        result[f"adapter:{name}"] = validate_adapter(skill, name)
    return result


def has_issues(result: Dict[str, List[str]]) -> bool:
    return any(issues for issues in result.values())
