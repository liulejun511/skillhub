"""Skill usage analytics — count how often each skill actually fired.

Source of truth: Claude Code session transcripts at ~/.claude/projects/**/*.jsonl.
A skill invocation is a tool_use entry with name=="Skill" and input={"skill": <name>};
each entry carries a top-level ISO-8601 `timestamp` and a unique `uuid`. We dedup by
uuid and bucket by LOCAL date. No hook, no MCP, no telemetry server — it just reads
your own local transcripts.

Scope: THIS machine's usage (your transcripts). Aggregating across users is a separate,
opt-in problem — each user would run this on their own machine and choose to share.
"""
from __future__ import annotations

import json
import os
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Iterator, List, Optional


def _projects_dir(projects_dir: Optional[Path] = None) -> Path:
    if projects_dir:
        return Path(projects_dir)
    return Path(os.path.expanduser("~")) / ".claude" / "projects"


def _local_date(ts: str) -> Optional[str]:
    """ISO-8601 (UTC, '...Z') → local YYYY-MM-DD. Python 3.10 needs the Z swap."""
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.astimezone().strftime("%Y-%m-%d")
    except Exception:
        return None


def iter_invocations(projects_dir: Optional[Path] = None) -> Iterator[Dict]:
    """Yield {skill, date, ts, uuid} for each Skill tool_use, deduped by uuid."""
    base = _projects_dir(projects_dir)
    if not base.exists():
        return
    seen = set()
    for f in sorted(base.rglob("*.jsonl")):
        try:
            handle = f.open(encoding="utf-8")
        except OSError:
            continue
        with handle:
            for line in handle:
                if '"Skill"' not in line:  # cheap prefilter; transcripts are large
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                msg = obj.get("message") or {}
                content = msg.get("content") if isinstance(msg, dict) else None
                if not isinstance(content, list):
                    continue
                for c in content:
                    if not (isinstance(c, dict) and c.get("type") == "tool_use" and c.get("name") == "Skill"):
                        continue
                    skill = (c.get("input") or {}).get("skill")
                    ts = obj.get("timestamp")
                    uid = obj.get("uuid")
                    if not skill or not ts:
                        continue
                    if uid and uid in seen:
                        continue
                    if uid:
                        seen.add(uid)
                    date = _local_date(ts)
                    if date:
                        yield {"skill": skill, "date": date, "ts": ts, "uuid": uid}


def counts_by_day(projects_dir: Optional[Path] = None, days: Optional[int] = None) -> Dict[str, Dict[str, int]]:
    """{date -> {skill -> count}}; if days given, keep only the last N local days."""
    cutoff = None
    if days is not None:
        cutoff = (datetime.now().astimezone() - timedelta(days=days - 1)).strftime("%Y-%m-%d")
    out: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for inv in iter_invocations(projects_dir):
        if cutoff and inv["date"] < cutoff:
            continue
        out[inv["date"]][inv["skill"]] += 1
    return {d: dict(s) for d, s in sorted(out.items())}


def totals(by_day: Dict[str, Dict[str, int]]) -> Dict[str, int]:
    t: Dict[str, int] = defaultdict(int)
    for skills in by_day.values():
        for sk, n in skills.items():
            t[sk] += n
    return dict(t)


def curated_skill_names(root: Optional[Path] = None) -> List[str]:
    """Names of curated (installable) skills, to flag installed-but-unused ones."""
    from memoket import paths
    from memoket.skill import SKILL_ENTRY

    curated = paths.curated_dir(root)
    if not curated.exists():
        return []
    return sorted({md.parent.name for md in curated.rglob(SKILL_ENTRY)})


def render_report(projects_dir: Optional[Path] = None, days: int = 7,
                  known_skills: Optional[List[str]] = None) -> str:
    """Human-readable daily report: most recent day + last-N-day totals + unused."""
    by_day = counts_by_day(projects_dir, days=days)
    tot = totals(by_day)
    lines = [f"Skill usage — last {days} day(s)", ""]

    if by_day:
        latest = max(by_day)
        lines.append(f"Most recent active day ({latest}):")
        for sk, n in sorted(by_day[latest].items(), key=lambda x: (-x[1], x[0])):
            lines.append(f"  {n:>4}  {sk}")
    else:
        lines.append("No skill invocations recorded in this window.")

    lines += ["", f"Totals (last {days} day(s)):"]
    if tot:
        for sk, n in sorted(tot.items(), key=lambda x: (-x[1], x[0])):
            lines.append(f"  {n:>4}  {sk}")
    else:
        lines.append("  (none)")

    if known_skills:
        used = {s for s in tot} | {s.split(":")[-1] for s in tot}
        unused = [s for s in known_skills if s not in used]
        if unused:
            lines += ["", f"Installed but unused (last {days}d): " + ", ".join(unused)]

    return "\n".join(lines) + "\n"
