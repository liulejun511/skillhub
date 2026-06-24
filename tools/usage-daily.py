#!/usr/bin/env python3
"""Daily skill-usage report → push to Feishu. Schedule this once (see below).

What it does: reads your local Claude Code transcripts, counts per-skill Skill
invocations over the last N days, prints the report, and pushes it to Feishu if
the FEISHU_* env vars are set (otherwise just prints — never errors on missing creds).

Env:
  FEISHU_TO_EMAIL     recipient (your Feishu email) — required to push
  FEISHU_APP_ID/SECRET  app creds; if unset, auto-reused from a configured lark MCP
  SKILLHUB_USAGE_DAYS   window, default 7

Schedule (Windows Task Scheduler — runs LOCALLY, since the transcripts are local):
  schtasks /create /tn skillhub-usage /sc daily /st 09:00 ^
    /tr "python \"D:\\capsoul\\skillhub\\tools\\usage-daily.py\""
(macOS/Linux: a cron line `0 9 * * * python /path/to/tools/usage-daily.py`.)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # put tools/ on sys.path

from memoket import usage          # noqa: E402
from memoket.notify import notify_feishu  # noqa: E402


def main() -> int:
    days = int(os.environ.get("SKILLHUB_USAGE_DAYS", "7"))
    try:
        known = usage.curated_skill_names()
    except Exception:
        known = None
    text = usage.render_report(days=days, known_skills=known)
    print(text)
    ok, detail = notify_feishu(text)
    print(f"[feishu] {'sent' if ok else 'skipped'} — {detail}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
