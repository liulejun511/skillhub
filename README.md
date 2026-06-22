# skillhub

**A community skill hub for Claude — human-curated, usage-ranked, security-reviewed.**

Write a Claude skill, contribute it via PR into the sandbox, let usage + quality signals show what's actually good, and have it curated (with a security review) into the marketplace anyone can install.

> 🚧 Early scaffold. Full design under [`.kiro/specs/skill-hub/`](.kiro/specs/skill-hub/).

## Install (native Claude Code marketplace)

```bash
/plugin marketplace add liulejun511/skillhub      # once published to GitHub
/plugin install memoket-core@skillhub             # curated, security-reviewed

# the uncurated sandbox is a SEPARATE marketplace you opt into deliberately:
/plugin install skillhub-sandbox@skillhub-sandbox # unreviewed — install at your own risk
```

> Needs a recent Claude Code (team auto-install via `settings.json` has a known bug, [#32606](https://github.com/anthropics/claude-code/issues/32606)); if a plugin doesn't appear, fall back to the manual `add` + `install` above. See the spec's design doc for the version-gated specifics.

Or, for a team, in `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "skillhub": { "source": { "source": "github", "repo": "liulejun511/skillhub" } }
  },
  "enabledPlugins": { "memoket-core@skillhub": true }
}
```

## What's here

```
.claude-plugin/marketplace.json   curated catalog (marketplace "skillhub")
plugins/memoket-core/skills/      curated seed skills (psql / pr-description / evidence)
sandbox/                          uncurated catalog (marketplace "skillhub-sandbox") — PR skills here
  .claude-plugin/marketplace.json   separate marketplace name = the install-time "unreviewed" signal
  skills/                           contributions land here (Inert-only in v1)
.github/workflows/sandbox-ci.yml  fail-closed CI gate (validate + redaction/injection scan + capability)
.github/pull_request_template.md  contribution + promotion checklist
tools/memoket/                    authoring + CI tooling (validate, redaction, injection_scan,
                                  classify, ci gate, marketplace check, promote)
tools/tests/                      test suite — offline: PYTHONPATH=tools python tools/tests/run_all.py
.kiro/specs/skill-hub/            the spec (requirements / design / tasks)
```

## Principles

- **Ride native distribution** — Claude Code's own plugin marketplace; no reinvented registry.
- **Human-curated, AI-assisted welcome** — what we reject is *unsupervised* bulk extraction, not AI help; a named author curates each skill, and usage + review decide what's good.
- **Two axes** — popularity (stars/installs/dependents) vs quality (re-use/ratings/curation); don't collapse them.
- **Security first** — Inert (instructions-only) vs Active (bundled code) split; layered review; never auto-promote.
- **Team seed, built to open** — prove it with a team's real skills + usage, then open to everyone.

## License

MIT (see LICENSE).
