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
    """Names of curated (installable) skills in the marketplace tree."""
    from memoket import paths
    from memoket.skill import SKILL_ENTRY

    curated = paths.curated_dir(root)
    if not curated.exists():
        return []
    return sorted({md.parent.name for md in curated.rglob(SKILL_ENTRY)})


def _available_skill_dirs(home: Optional[Path] = None) -> List[Path]:
    """Skill dirs that COULD actually fire on THIS machine: user-level (~/.claude/skills/)
    + each installed plugin's skills (installed_plugins.json → installPath/skills/*)."""
    base = Path(home or os.path.expanduser("~")) / ".claude"
    dirs: List[Path] = []

    user_skills = base / "skills"
    if user_skills.exists():
        dirs += [d for d in sorted(user_skills.iterdir()) if (d / "SKILL.md").exists()]

    installed = base / "plugins" / "installed_plugins.json"
    try:
        data = json.loads(installed.read_text(encoding="utf-8"))
        for entries in (data.get("plugins") or {}).values():
            for e in entries:
                skills_dir = Path(e.get("installPath", "")) / "skills"
                if skills_dir.exists():
                    dirs += [d for d in sorted(skills_dir.iterdir()) if (d / "SKILL.md").exists()]
    except Exception:
        pass

    return dirs


def available_skill_names(home: Optional[Path] = None) -> List[str]:
    """Names of skills that CAN be invoked on this machine. 'Unused' is only meaningful
    relative to this set — never against the whole marketplace catalog."""
    return sorted({d.name for d in _available_skill_dirs(home)})


# 「常驻/纪律型」技能：描述里写明「写任何代码就适用 / 每次改文件都适用」的那类。它们靠
# description 常驻生效，极少作为显式 Skill 调用触发——所以在报告里不应被算进「闲置」。
_RESIDENT_MARKERS = (
    "any code", "writing or changing any", "before and after the edit", "any repository file",
    "写代码", "写函数", "改逻辑", "改动任何", "任何文件", "每次",
)


def resident_skill_names(home: Optional[Path] = None) -> List[str]:
    """Available skills whose description marks them as always-on/resident discipline
    (apply to ~every edit). They fire rarely as explicit invocations BY DESIGN."""
    out = set()
    for d in _available_skill_dirs(home):
        try:
            txt = (d / "SKILL.md").read_text(encoding="utf-8")
        except OSError:
            continue
        head = (txt.split("---", 2)[1] if txt.count("---") >= 2 else txt[:800]).lower()
        if any(m in head for m in _RESIDENT_MARKERS):
            out.add(d.name)
    return sorted(out)


def activity_by_day(projects_dir: Optional[Path] = None, days: Optional[int] = None) -> Dict[str, int]:
    """{date -> total tool_use calls}, deduped by message uuid (so resumed/duplicated
    transcripts don't double-count), windowed to last N local days. This is the
    denominator that makes skill-fire counts interpretable: few fires on a low-activity
    day is normal; few fires on a high-activity day is the real warning sign."""
    cutoff = None
    if days is not None:
        cutoff = (datetime.now().astimezone() - timedelta(days=days - 1)).strftime("%Y-%m-%d")
    base = _projects_dir(projects_dir)
    if not base.exists():
        return {}
    out: Dict[str, int] = defaultdict(int)
    seen = set()
    for f in sorted(base.rglob("*.jsonl")):
        try:
            handle = f.open(encoding="utf-8")
        except OSError:
            continue
        with handle:
            for line in handle:
                if '"tool_use"' not in line:  # cheap prefilter
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                uid = obj.get("uuid")
                if uid and uid in seen:
                    continue
                ts = obj.get("timestamp")
                date = _local_date(ts) if ts else None
                if not date or (cutoff and date < cutoff):
                    continue
                msg = obj.get("message") or {}
                content = msg.get("content") if isinstance(msg, dict) else None
                if not isinstance(content, list):
                    continue
                n = sum(1 for c in content if isinstance(c, dict) and c.get("type") == "tool_use")
                if n:
                    if uid:
                        seen.add(uid)
                    out[date] += n
    return dict(sorted(out.items()))


def render_report(projects_dir: Optional[Path] = None, days: int = 7,
                  known_skills: Optional[List[str]] = None,
                  resident_skills: Optional[List[str]] = None) -> str:
    """Human-readable daily report. Shows skill fires AGAINST total tool activity per day
    (so few fires on a quiet/non-coding day reads as normal, not as 'broken'), then totals,
    then skills not explicitly invoked — split into on-demand vs resident/discipline so the
    always-on skills don't look idle."""
    by_day = counts_by_day(projects_dir, days=days)
    act = activity_by_day(projects_dir, days=days)
    tot = totals(by_day)
    lines = [f"Skill usage — last {days} day(s)", ""]

    fire_days = {d: sum(s.values()) for d, s in by_day.items()}
    all_days = sorted(set(act) | set(fire_days))
    if all_days:
        lines.append("Per-day (skill fires in context of total tool activity):")
        lines.append(f"  {'date':10} {'activity':>8} {'fires':>6}   skills")
        for d in all_days:
            sk = by_day.get(d, {})
            names = ", ".join(f"{n}×{c}" for n, c in sorted(sk.items(), key=lambda x: (-x[1], x[0]))) or "—"
            lines.append(f"  {d:10} {act.get(d, 0):>8} {fire_days.get(d, 0):>6}   {names}")
        lines.append("  ↳ few fires on a low-activity / non-coding day is normal; "
                     "worry only if activity is high but fires ≈ 0.")
    else:
        lines.append("No activity recorded in this window.")

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
            resident = set(resident_skills or [])
            on_demand = [s for s in unused if s not in resident]
            res = [s for s in unused if s in resident]
            lines += ["", f"Not explicitly invoked (last {days}d):"]
            if on_demand:
                lines.append("  on-demand (notice if it stays here): " + ", ".join(on_demand))
            if res:
                lines.append("  resident/discipline (fires rarely by design — normal): " + ", ".join(res))

    return "\n".join(lines) + "\n"
