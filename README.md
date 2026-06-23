# skillhub

**A community skill hub for Claude — human-curated, usage-ranked, security-reviewed.**

Write a Claude skill, contribute it via PR into the sandbox, let usage + quality signals show what's actually good, and have it curated (with a security review) into the marketplace anyone can install.

> 🚧 Early scaffold. Full design under [`.kiro/specs/skill-hub/`](.kiro/specs/skill-hub/).

## Install (native Claude Code marketplace)

The repo is **public** — anyone can install it. Use the **HTTPS URL** form: the bare
`owner/repo` shorthand makes Claude Code clone over SSH, which fails if you haven't trusted
GitHub's SSH key.

```bash
/plugin marketplace add https://github.com/liulejun511/skillhub.git

# Each skill is its OWN plugin — install only the ones you want:
/plugin install pr-description-craft@skillhub
/plugin install psql-field-diagnostics@skillhub
/plugin install evidence-before-adoption@skillhub
/reload-plugins                            # activate without a restart
```

Browse what every skill does first in **[`CATALOG.md`](CATALOG.md)** (auto-generated), or in
the plugin browser before installing — no need to take all of them. Skills are
**model-invoked**: they surface automatically by their "Use when …" triggers; you don't call
them by name. Uninstall any one independently with `/plugin uninstall <skill>@skillhub`.

### For a team

Check this into the repo's `.claude/settings.json` so members are prompted to install when
they trust the folder:

```json
{
  "extraKnownMarketplaces": {
    "skillhub": { "source": { "source": "github", "repo": "liulejun511/skillhub" } }
  },
  "enabledPlugins": { "pr-description-craft@skillhub": true, "evidence-before-adoption@skillhub": true }
}
```

> Needs a recent Claude Code. The auto-prompt flow has a known bug
> ([#32606](https://github.com/anthropics/claude-code/issues/32606)); if a plugin doesn't
> appear, fall back to the manual `add` + `install` above.

### Sandbox (uncurated) — a separate marketplace

The sandbox is a **separate** marketplace (`skillhub-sandbox`) you opt into deliberately;
see [`sandbox/README.md`](sandbox/README.md) for how to add it.

### Troubleshooting install

- **`Host key verification failed` / SSH error** — the `owner/repo` shorthand clones over
  SSH. Use the **HTTPS URL** above, or trust GitHub once with `ssh -T git@github.com`.
- **`Connection was reset` / SSL errors** — your network (often a corporate proxy) is
  intercepting TLS and resetting the plugin's clone. Either point Claude Code at a **local
  clone** — `git clone https://github.com/liulejun511/skillhub.git`, then
  `/plugin marketplace add <path-to-clone>` — or configure your corporate CA for git/curl.
- **Desktop app** — the GUI can't add a *new* GitHub marketplace; run the `add` once in the
  CLI (or use the `settings.json` above), then install from **+ → Plugins** and `/reload-plugins`.

## What's here

```
.claude-plugin/marketplace.json   curated catalog (marketplace "skillhub")
plugins/<skill>/                  ONE plugin per skill — install each independently
  .claude-plugin/plugin.json        its browser-visible description (the "what does this do")
  skills/<skill>/SKILL.md
CATALOG.md                        auto-generated index of every skill — browse before installing
sandbox/                          uncurated catalog (marketplace "skillhub-sandbox") — PR skills here
.github/workflows/sandbox-ci.yml  fail-closed CI gate (validate + redaction/injection scan + capability)
.github/pull_request_template.md  contribution + promotion checklist
tools/memoket/                    authoring + CI tooling (validate, redaction, injection_scan,
                                  classify, ci gate, marketplace check, promote, catalog)
tools/tests/                      test suite — offline: PYTHONPATH=tools python tools/tests/run_all.py
.kiro/specs/skill-hub/            the spec (requirements / design / tasks)
```

## Contribute a skill

人人可投稿,挑简单的:**GitHub 网页** Fork → 加 `sandbox/skills/<name>/SKILL.md` → 开 PR(CI 自动检查);或**本地一条命令** `PYTHONPATH=tools python -m memoket submit <name>`。详见 **[CONTRIBUTING.md](CONTRIBUTING.md)**。

## Principles

- **Ride native distribution** — Claude Code's own plugin marketplace; no reinvented registry.
- **Human-curated, AI-assisted welcome** — what we reject is *unsupervised* bulk extraction, not AI help; a named author curates each skill, and usage + review decide what's good.
- **Two axes** — popularity (stars/installs/dependents) vs quality (re-use/ratings/curation); don't collapse them.
- **Security first** — Inert (instructions-only) vs Active (bundled code) split; layered review; never auto-promote.
- **Team seed, built to open** — prove it with a team's real skills + usage, then open to everyone.

## License

MIT (see LICENSE).
