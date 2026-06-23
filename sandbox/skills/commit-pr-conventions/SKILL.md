---
name: commit-pr-conventions
description: >-
  Project conventions for writing git commit messages and pull request
  descriptions. Use this whenever composing or rewriting a commit message,
  running `git commit`, squashing/rebasing commits before opening or updating a
  PR, or creating/editing a pull request or its description (via `gh`, the
  GitHub API, or the web UI). Apply it even when the user only says things like
  "commit this", "push it", "open a PR", "update the PR", "clean up the
  commits", or "把这些提交合并一下" without explicitly mentioning conventions.
---

# Commit & PR Conventions

Goal: history and PRs that a reviewer can grasp fast. Commits explain *why* a
change exists; PR descriptions guide *how to review* it. Keep both lean.

## When to commit & push — ask first, every time

Do NOT commit-and-push to a remote, force-push, or create/update a PR on your
own. Default to preparing the change locally — make the edits, run build/tests,
show the diff and a short plan — then **wait for the user's explicit go**
("commit" / "push" / "提 PR"). Sending anything to the remote is the gated step.

- **Approval does not carry over.** A "yes, push" in one context authorizes
  *that* push only. The next push / force-push / PR needs its own explicit
  instruction, even inside the same task. Don't infer "push" from "do the work".
- **The gated action is the outward one** (push / force-push / open or update a
  PR), not the coding. Even when the broader task was approved, hold the remote step.
- **Local prep needs no permission**: edits, build/lint/compile checks, drafting
  commit messages, showing diffs. Hold the actual `git push` (and usually the
  `git commit` too) until told.
- `force-push` always uses `--force-with-lease`.

## Commit messages

Write commit messages in **English** (the chat may be in Chinese, the commit is
not). Follow **Conventional Commits**:

```
type(scope): short imperative subject

Optional body: what changed and why, wrapped ~72 cols. A few lines or a few
bullets — not a wall of text. Skip the body entirely for trivial changes.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
```

- **type**: `feat` / `fix` / `refactor` / `perf` / `docs` / `test` / `chore` /
  `build` / `ci`. **scope** is the area touched (e.g. `metrics`, `db`, `auth`),
  optional but helpful.
- **`refactor` is for LARGE / structural changes only** — restructuring or moving
  modules, reworking an architecture, splitting a bundled commit. A small change
  (a one-line tweak, a rename, dropping/renaming a field, adjusting a metric
  dimension) is **not** a refactor: use **`fix`** (or `feat` if it genuinely adds
  a capability). Don't reach for `refactor` just because the change isn't a bug fix.
- **subject**: imperative mood ("add", not "added"/"adds"), ≤ ~70 chars, no
  trailing period. It should read as "this commit will _<subject>_".
- **body**: only the *why* and the non-obvious *what*. The diff already shows
  the line-level what — don't restate it. If the change is self-explanatory,
  no body is fine.
- **Every commit ends with** the trailer line exactly:
  `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`
- **One concern per commit — split, don't bundle.** A commit does exactly one
  thing. If the work spans several concerns (e.g. shared infra + per-feature
  instrumentation + a refactor + a dead-code removal), split it into one commit
  each — 3-5 small coherent commits beat one large opaque one a reviewer (or the
  user, who needs to follow the business) can't grasp. Unrelated drive-by fixes
  (a crash guard, a typo) get their **own** commit, or at minimum an explicit
  callout in the body — never silently folded into a feature commit.
  Squash the other direction: WIP / "fix typo" / "address review" noise collapses
  into the coherent commit it belongs to before opening or updating a PR. When
  the branch is already one clean commit, amend rather than stack; force-push
  with `--force-with-lease`.
- **Splitting an existing bundled commit** (keeps the work, rewrites history):
  `git reset --mixed <parent>` to drop the changes back into the working tree,
  then `git add` the files for each concern and commit them one group at a time.
  Before force-pushing, diff the new tip against the original commit — it should
  be **identical** (or differ only by intended cleanup), proving you split, not
  altered. Splitting a pushed branch needs a `--force-with-lease`; confirm first.

**Example 1**
Input: added cost/usage logging across the AI backend, lots of WIP commits
Output:
```
feat(metrics): instrument AI cost/usage for the ops dashboard

Emit structured log_metric events with attribution (trace/domain/feature/
tenant/conversation) auto-injected via request_context, plus per-call LLM
cost computed from config prices. Rollup lives in the ops repo.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
```

**Example 2**
Input: fixed a connection being held open during a slow transcription call
Output:
```
fix(db): release pooled connection before slow transcribe() call

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
```

## PR descriptions

A reviewer should understand the PR in under a minute. Lead with intent, point
them at where to start, and make it skimmable. **Simplified Chinese is fine**
for the team — match the audience.

Use this structure (drop sections that don't apply):

```markdown
## 这个 PR 做了什么 / What & why
1–2 句：解决什么问题、带来什么变化。

## 从这里开始看 / Start review here
- `path/to/key_file.py` — 核心入口/最该先读的地方
- `path/to/other.py` — 次要但关键

## 改了什么 / Changes
- 按模块/主题列要点，可读性优先（必要时用小表格）

## 怎么验证的 / Verification
- 测试 / 手动 / predev 跑了哪些，结果如何

## 不在范围内 / Out of scope
- 明确没做、留待后续的事
```

Principles:
- **Lead with the point**, not a changelog. The first two lines should let a
  reviewer decide if they even need to read on.
- **"Start review here" is the highest-value section** — it saves the reviewer
  from reverse-engineering the entry point from a file list.
- **Skimmable beats exhaustive.** Bullets and short tables over prose. If a
  section would be a wall of text, it's too detailed for a PR description.
- State how it was **verified** — reviewers trust changes they can see were
  exercised.

## Quick checklist before committing / opening a PR

- [ ] Commit subject is English, Conventional-Commits, imperative, ≤ ~70 chars
- [ ] Body explains *why* (or is omitted for trivial changes), no diff-restating
- [ ] `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>` trailer present
- [ ] Branch squashed to clean logical commit(s); force-push uses `--force-with-lease`
- [ ] PR leads with what+why, has a "start review here" pointer, is skimmable, states verification
