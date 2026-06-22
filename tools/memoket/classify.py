"""能力分级：判定技能 Inert（纯指令）/ Active（带可执行代码）。

v1 沙盒只收 Inert；Active 在 CI 入口被拒。判定纯结构化——看技能目录顶层有没有
可执行代码标记，不信 frontmatter 的自我声明（自称 inert 却带 scripts/ 仍判 Active）。
reference/ 下的代码示例算文档（不会被自动执行），不计为 Active 标记。
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

# 顶层出现即视为 Active 的目录（会被运行时自动加载/执行）。
_ACTIVE_DIRS = {"scripts", "hooks", "bin", "mcpServers", "commands", "agents", "lspServers"}
# 顶层出现即视为 Active 的配置文件。
_ACTIVE_FILES = {".mcp.json", "hooks.json", "mcp.json"}
# 顶层松散代码文件后缀。
_CODE_SUFFIXES = {".sh", ".bash", ".zsh", ".py", ".js", ".mjs", ".cjs", ".ts", ".rb", ".pl", ".bat", ".ps1", ".exe"}


def classify_skill(skill_dir) -> Dict:
    """返回 {"capability": "inert"|"active", "markers": [...]}。markers 非空即 Active。"""
    base = Path(skill_dir)
    markers: List[str] = []
    for entry in sorted(base.iterdir()):
        name = entry.name
        if entry.is_dir() and name in _ACTIVE_DIRS:
            markers.append(name + "/")
        elif entry.is_file() and (name in _ACTIVE_FILES or entry.suffix.lower() in _CODE_SUFFIXES):
            markers.append(name)
    return {"capability": "active" if markers else "inert", "markers": markers}


def is_active(skill_dir) -> bool:
    return classify_skill(skill_dir)["capability"] == "active"
