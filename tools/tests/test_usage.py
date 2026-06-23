"""用量解析:数 Skill 触发、按 uuid 去重、忽略非 Skill 工具、按天窗口过滤、报告含技能名。"""
import json
import shutil
import tempfile
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

from memoket import usage


def _entry(uuid, ts, skill=None, tool="Skill"):
    inp = {"skill": skill} if skill is not None else {"path": "x"}
    return json.dumps({
        "type": "assistant", "uuid": uuid, "timestamp": ts,
        "message": {"content": [{"type": "tool_use", "name": tool, "input": inp}]},
    })


@contextmanager
def _projects(lines):
    root = Path(tempfile.mkdtemp())
    try:
        d = root / "proj-a"
        d.mkdir(parents=True)
        (d / "s1.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
        yield root
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _ts(days_ago=0):
    return (datetime.now(timezone.utc) - timedelta(days=days_ago)).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def test_counts_and_totals():
    lines = [
        _entry("u1", _ts(0), "foo"),
        _entry("u2", _ts(0), "foo"),
        _entry("u3", _ts(0), "bar"),
        _entry("u4", _ts(0), tool="Read"),   # not a skill → ignored
    ]
    with _projects(lines) as root:
        tot = usage.totals(usage.counts_by_day(root))
        assert tot == {"foo": 2, "bar": 1}, tot


def test_dedup_by_uuid():
    # same uuid appearing twice (e.g., transcript duplicated) counts once
    lines = [_entry("dup", _ts(0), "foo"), _entry("dup", _ts(0), "foo")]
    with _projects(lines) as root:
        assert usage.totals(usage.counts_by_day(root)) == {"foo": 1}


def test_days_window_excludes_old():
    lines = [_entry("recent", _ts(0), "foo"), _entry("old", _ts(100), "bar")]
    with _projects(lines) as root:
        tot = usage.totals(usage.counts_by_day(root, days=7))
        assert tot == {"foo": 1}, tot          # 100 天前的被窗口排除


def test_render_report_mentions_skills():
    lines = [_entry("u1", _ts(0), "foo"), _entry("u2", _ts(0), "foo"), _entry("u3", _ts(0), "bar")]
    with _projects(lines) as root:
        text = usage.render_report(root, days=7, known_skills=["foo", "bar", "never-used"])
        assert "foo" in text and "bar" in text
        assert "Totals" in text
        assert "never-used" in text            # installed-but-unused 列出来


def test_empty_when_no_transcripts():
    with _projects([]) as root:
        assert usage.counts_by_day(root) == {}
        assert "No skill invocations" in usage.render_report(root)
