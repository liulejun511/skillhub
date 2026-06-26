#!/usr/bin/env python3
r"""Daily skill-usage report → push to Feishu. Schedule this once (see below).

Reads your local Claude Code transcripts, counts per-skill Skill invocations over
the last N days, and pushes the report to Feishu. Hardened to run under Task
Scheduler (no console): writes a log file and forces a clean exit.

Env:
  FEISHU_TO_EMAIL     recipient (your Feishu email) — required to push
  FEISHU_APP_ID/SECRET  app creds; if unset, auto-reused from a configured lark MCP
  SKILLHUB_USAGE_DAYS   window, default 7

Schedule (Windows Task Scheduler — runs LOCALLY; the transcripts are local):
  (PowerShell) Register-ScheduledTask -TaskName skillhub-usage -Action (
      New-ScheduledTaskAction -Execute (Get-Command python).Source `
        -Argument '"D:\skillhub\tools\usage-daily.py"') `
    -Trigger (New-ScheduledTaskTrigger -Daily -At 9:00am)
(macOS/Linux: `0 9 * * * python /path/to/tools/usage-daily.py`.)
"""
import os
import sys
from datetime import datetime

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)                         # put tools/ on sys.path
_LOG = os.path.join(_HERE, "..", ".work", "usage-daily.log")

for _stream in (sys.stdout, sys.stderr):          # survive a GBK / no-console host
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def _log(line: str) -> None:
    try:
        os.makedirs(os.path.dirname(_LOG), exist_ok=True)
        with open(_LOG, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now().isoformat(timespec='seconds')}  {line}\n")
    except Exception:
        pass


def main() -> None:
    try:
        from memoket import usage
        from memoket.notify import notify_feishu

        days = int(os.environ.get("SKILLHUB_USAGE_DAYS", "7"))
        try:
            known = usage.available_skill_names()
            resident = usage.resident_skill_names()
        except Exception:
            known = resident = None
        text = usage.render_report(days=days, known_skills=known, resident_skills=resident)
        ok, detail = notify_feishu(text)
        _log(f"run ok days={days} feishu={'sent' if ok else 'skipped'} ({detail})")
        try:
            print(text)
            print(f"[feishu] {'sent' if ok else 'skipped'} — {detail}")
        except Exception:
            pass
    except Exception as exc:
        _log(f"ERROR {exc!r}")


if __name__ == "__main__":
    main()
    sys.stdout.flush() if hasattr(sys.stdout, "flush") else None
    os._exit(0)   # force a clean exit code under Task Scheduler (avoid teardown CTRL-C status)
