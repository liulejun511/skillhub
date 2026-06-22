"""publish：把 mine 里的技能发布到 registry（先过脱敏闸）。

仅 status=active 且通过脱敏闸的技能可发布（设计 H2 / R9.3）。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

from memoket import paths, redaction
from memoket.errors import MemoketError
from memoket.skill import parse_skill


class RedactionBlocked(MemoketError):
    """发布被脱敏闸阻止（检出疑似 PII/机密）。"""


def publish_skill(name: str, root: Optional[Path] = None) -> Dict:
    skill_dir = paths.vault_mine(root) / name
    if not (skill_dir / "SKILL.md").exists():
        raise MemoketError(f"vault/mine 中无此技能: {name}")
    skill = parse_skill(skill_dir)

    if skill.status != "active":
        raise MemoketError(f"仅 active 技能可发布，当前 status={skill.status}")

    findings = redaction.scan(f"{skill.description or ''}\n{skill.body}")
    if findings:
        detail = "; ".join(f"{f['type']}@L{f['line']}:{f['match']}" for f in findings)
        raise RedactionBlocked(f"脱敏闸阻止发布（疑似 PII/机密）：{detail}")

    entry = {
        "name": skill.name,
        "description": skill.description,
        "version": skill.version,
        "source": {"type": "local", "path": f"vault/mine/{name}"},
        "tags": skill.tags,
    }
    _upsert_registry(entry, root)
    return entry


def _upsert_registry(entry: Dict, root: Optional[Path]) -> None:
    p = paths.registry_path(root)
    data = json.loads(p.read_text(encoding="utf-8")) if p.exists() else []
    for i, e in enumerate(data):
        if e.get("name") == entry["name"]:
            data[i] = entry
            break
    else:
        data.append(entry)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
