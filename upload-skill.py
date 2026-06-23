#!/usr/bin/env python3
"""Upload a local Claude skill to skillhub as a ready-to-merge PR — in one step.

Reads your skill from ~/.claude/skills/<name>/SKILL.md (or a path you give),
then opens your browser to a GitHub editor with it already filled in. Click
"Propose changes" and GitHub forks the repo + opens a PR for you. CI checks it.

No clone, no `gh`, no copy-paste.  Python standard library only.

    python upload-skill.py <skill-name>            # from ~/.claude/skills/<name>/
    python upload-skill.py path/to/skill-dir       # or an explicit folder
"""
import os
import sys
import webbrowser
from pathlib import Path
from urllib.parse import quote

REPO = "liulejun511/skillhub"
URL_LIMIT = 7000  # keep the whole URL comfortably within browser limits


def _open(url: str) -> None:
    # Set UPLOAD_SKILL_DRYRUN=1 to print the URL instead of launching a browser.
    if os.environ.get("UPLOAD_SKILL_DRYRUN"):
        print(url)
    else:
        webbrowser.open(url)


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python upload-skill.py <skill-name | path-to-skill-dir>")
        return 2

    arg = sys.argv[1]
    skill_dir = Path(arg)
    if not (skill_dir / "SKILL.md").exists():
        skill_dir = Path(os.path.expanduser("~")) / ".claude" / "skills" / arg

    md = skill_dir / "SKILL.md"
    if not md.exists():
        print(f"Skill not found: {arg} (not a folder with SKILL.md, and not in ~/.claude/skills/)")
        return 1

    name = skill_dir.name
    content = md.read_text(encoding="utf-8")
    base = f"https://github.com/{REPO}/new/main?filename=sandbox/skills/{name}/SKILL.md"
    url = f"{base}&value={quote(content)}"

    if len(url) <= URL_LIMIT:
        print(f"Opening your browser for skill '{name}', pre-filled. Click 'Propose changes' to open a PR.")
        _open(url)
    else:
        print(f"Skill '{name}' is long, so the URL can't carry it. One manual step:")
        print(f"  1) Open your skill file and copy all of it: {md}")
        print(f"  2) Paste into this blank editor, then click 'Propose changes':")
        print(f"     {base}")
        _open(base)
    return 0


if __name__ == "__main__":
    sys.exit(main())
