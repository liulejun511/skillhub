"""claude-chat 连接器：Claude Code 会话记录作为素材源（收编自临时脚本）。

从 ~/.claude/projects/*/*.jsonl 抽取对话，保留**双方发言**（USER 提问 + AI 回答的
简要），保留换行与完整长度，便于提炼「我怎么想 + 别人/AI 怎么答」的双边证据。
since 按会话文件 mtime 增量。

可调（环境变量）：
- MEMOKET_CHAT_INCLUDE_ASSISTANT=0 仅抽 user 侧（默认含 assistant 摘要）
- MEMOKET_CHAT_MAX_CHARS 单条最大字符（默认 4000，0=不截断）
"""
from __future__ import annotations

import datetime as _dt
import glob
import json
import os
import re
from pathlib import Path
from typing import List, Optional

from memoket import paths

_SKIP_RE = re.compile(r"^(<local-command|<command-|Caveat:|\[Request interrupted)")
_MAX_SESSIONS = 30
_MIN_LEN = 6


class ClaudeChatConnector:
    name = "claude-chat"

    def _projects_dir(self) -> Path:
        return Path(os.environ.get("MEMOKET_CLAUDE_PROJECTS", os.path.expanduser("~/.claude/projects")))

    def _out_dir(self) -> Path:
        d = paths.work_dir() / "_claude_chat"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _texts(self, content) -> List[str]:
        if isinstance(content, str):
            return [content]
        if isinstance(content, list):
            return [it.get("text", "") for it in content
                    if isinstance(it, dict) and it.get("type") == "text"]
        return []

    def pull(self, user_id: str, since: Optional[str]) -> List[Path]:
        include_assistant = os.environ.get("MEMOKET_CHAT_INCLUDE_ASSISTANT", "1") != "0"
        max_chars = int(os.environ.get("MEMOKET_CHAT_MAX_CHARS", "4000"))

        projdir = self._projects_dir()
        files = sorted(
            glob.glob(str(projdir / "*" / "*.jsonl")), key=os.path.getmtime, reverse=True
        )[:_MAX_SESSIONS]
        if since:
            try:
                since_ts = _dt.datetime.fromisoformat(since.replace("Z", "+00:00")).timestamp()
                files = [f for f in files if os.path.getmtime(f) > since_ts]
            except ValueError:
                pass

        out = self._out_dir()
        written: List[Path] = []
        for f in files:
            session = Path(f).stem[:8]
            turns: List[str] = []
            try:
                with open(f, encoding="utf-8") as fh:
                    for line in fh:
                        try:
                            obj = json.loads(line)
                        except Exception:
                            continue
                        role = obj.get("type")
                        if role == "user":
                            tag = "USER"
                        elif role == "assistant" and include_assistant:
                            tag = "AI"
                        else:
                            continue
                        for t in self._texts((obj.get("message") or {}).get("content")):
                            t = t.strip()
                            if not t or len(t) < _MIN_LEN:
                                continue
                            if _SKIP_RE.match(t) or (t.startswith("<") and "system-reminder" in t[:60]):
                                continue
                            # 保留换行；仅在超长时截断（保留首尾，不腰斩）。
                            if max_chars and len(t) > max_chars:
                                t = t[: max_chars // 2] + "\n…[截断]…\n" + t[-max_chars // 2:]
                            turns.append(f"{tag}: {t}")
            except Exception:
                continue
            if turns:
                fpath = out / f"chat_{session}.transcript"
                fpath.write_text(
                    f"# session {session} (project: {Path(f).parent.name})\n\n"
                    + "\n\n".join(turns) + "\n",
                    encoding="utf-8",
                )
                written.append(fpath)
        return written

    def test(self) -> bool:
        return self._projects_dir().exists()
