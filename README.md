# skillhub

**A community skill hub for Claude — human-authored, usage-ranked, security-reviewed.**

Write a Claude skill, contribute it via PR into the sandbox, let usage + quality signals show what's actually good, and have it curated (with a security review) into the marketplace anyone can install.

> 🚧 Early scaffold. Full design under [`.kiro/specs/skill-hub/`](.kiro/specs/skill-hub/).

## Install (native Claude Code marketplace)

```bash
/plugin marketplace add liulejun511/skillhub      # once published to GitHub
/plugin install memoket-core@skillhub
```

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
.claude-plugin/marketplace.json   the marketplace catalog (lists plugins)
plugins/memoket-core/             a curated plugin (seed skills)
  .claude-plugin/plugin.json
  skills/                         psql-field-diagnostics, pr-description-craft, evidence-before-adoption
tools/                            salvaged reuse from the previous project (validate, redaction,
                                  quality review, usage tracking) — to be pruned/wired per design
.kiro/specs/skill-hub/            the spec (requirements / design / tasks)
```

## Principles

- **Ride native distribution** — Claude Code's own plugin marketplace; no reinvented registry.
- **Human-authored, not auto-distilled** — people write skills; usage + curation decide what's good.
- **Two axes** — popularity (stars/installs/dependents) vs quality (re-use/ratings/curation); don't collapse them.
- **Security first** — Inert (instructions-only) vs Active (bundled code) split; layered review; never auto-promote.
- **Team seed, built to open** — prove it with a team's real skills + usage, then open to everyone.

## License

MIT (see LICENSE).
