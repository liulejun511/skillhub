"""claude-code 适配器：把通用技能映射成 Claude Code 技能目录形态。

Claude Code 技能约定：一个目录含 SKILL.md，frontmatter 至少有 name + description，
正文为 Markdown 指令。通用技能几乎无需额外字段即可构建。
"""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import List

from memoket.skill import SkillPackage

# 从源技能包一并复制的可选资源目录。
_COPY_DIRS = ("scripts", "reference")


class ClaudeCodeAdapter:
    name = "claude-code"

    def required_fields(self) -> List[str]:
        # 通用技能直接可用，无额外必需字段。
        return []

    def build(self, skill: SkillPackage, out_dir: Path) -> Path:
        target = out_dir / (skill.name or "unnamed-skill")
        target.mkdir(parents=True, exist_ok=True)

        front_lines = ["---", f"name: {skill.name}", f"description: {skill.description}"]
        if skill.version:
            front_lines.append(f"version: {skill.version}")
        front_lines.append("---")
        content = "\n".join(front_lines) + "\n\n" + skill.body.rstrip() + "\n"
        (target / "SKILL.md").write_text(content, encoding="utf-8")

        # 复制附带资源（若源技能是目录）
        if skill.path is not None:
            src_root = skill.path.parent
            for sub in _COPY_DIRS:
                src = src_root / sub
                if src.is_dir():
                    shutil.copytree(src, target / sub, dirs_exist_ok=True)
        return target
