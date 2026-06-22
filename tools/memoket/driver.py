"""distill/evolve 的 agent 驱动器。

工具的「智能」由一个 Claude agent 执行。两种模式：
- headless：shell 调 `claude -p` 无人值守执行（需 CLI 已 `claude /login`）。
- inline：当前会话里的 agent 按请求文件执行（headless 不可用时的回退）。

设计取舍：headless 不可用不报错，而是返回明确状态，让循环回退到 inline。
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Tuple


def is_headless_available() -> bool:
    """`claude` CLI 是否在 PATH 上（不保证已登录）。"""
    return shutil.which("claude") is not None


def drive_headless(prompt: str, cwd: Optional[Path] = None, timeout: int = 900,
                   permission_mode: str = "acceptEdits") -> Tuple[bool, str]:
    """用 headless `claude -p` 执行一段提示。

    返回 (ok, output)。未安装/未登录/超时/非零退出 → ok=False，output 含原因。
    跨平台：prompt 经 stdin 传入（避开巨型多行 prompt 的命令行引号问题）；
    Windows 上 `claude` 是 .cmd 脚本，须经 cmd /c 调起。
    permission_mode：默认 acceptEdits，让被唤起的 agent 能写技能草稿文件
    （提炼/精炼的本职就是产出 SKILL.md；只授权编辑，不授权任意命令）。
    """
    exe = shutil.which("claude")
    if exe is None:
        return False, "headless 不可用：PATH 上没有 `claude` CLI。"
    flags = ["-p", "--permission-mode", permission_mode]
    if os.name == "nt":
        cmd = [os.environ.get("COMSPEC", "cmd.exe"), "/c", exe, *flags]
    else:
        cmd = [exe, *flags]
    try:
        proc = subprocess.run(
            cmd,
            input=prompt,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            encoding="utf-8",       # 别用本地 GBK：prompt 含中文/符号（Windows 默认编码会炸）
            errors="replace",
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return False, f"headless 超时（>{timeout}s）。"
    out = (proc.stdout or "") + (proc.stderr or "")
    if "Not logged in" in out or "please run /login" in out.lower():
        return False, "headless 未登录：请在 CLI 执行 `claude /login` 后再试。"
    if proc.returncode != 0:
        return False, f"headless 退出码 {proc.returncode}：{out[:300]}"
    return True, out
