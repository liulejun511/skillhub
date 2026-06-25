# skillhub 技能目录 / Skill Catalog

> 自动生成（`python -m memoket catalog`），勿手改。每个技能 = 一个可独立安装的插件。

## Curated（已策展，可一键安装）（11）

### commit-pr-conventions

Project conventions for writing git commit messages and pull request descriptions. Use this whenever composing or rewriting a commit message, running `git commit`, squashing/rebasing commits before opening or updating a PR, or creating/editing a pull request or its description (via `gh`, the GitHub API, or the web UI). Apply it even when the user only says things like "commit this", "push it", "open a PR", "update the PR", "clean up the commits", or "把这些提交合并一下" without explicitly mentioning conventions.

### evidence-before-adoption

用于在接受/合并一个改动、性能主张或自动化（AI/同事）工作汇报之前，强制先拿真实数据证据再放行：自己跑 EXPLAIN ANALYZE、重复计时取样、前后行数对账、原始触发路径复现，并审「到底谁真跑了什么、是端到端跑通还是只跑了一段」。触发场景：有人说「更快了/修好了/自动化跑通了」要你信；回归取证（以前好的现在坏了、A/B 复现、时间线锚定变更窗口）；判断证据是否可证伪、环境/分支对不对。Use when deciding whether to trust or merge a change, a perf claim, or an automation report before there is real evidence.

`verification`  `performance`  `discipline`  `strength`

### kiro-skill

Interactive spec-driven feature development workflow from idea to implementation. Use when the user mentions Kiro, K神, .kiro/specs, feature specs, requirements, EARS acceptance criteria, design documents, implementation plans, task lists, 需求文档, 设计文档, 实现计划, or executing a single task from a Kiro-style spec. Also use by default before writing business code or product feature code, including backend business logic, user-facing workflows, product behavior, domain rules, data model changes, API behavior changes, or frontend business flows, unless the user explicitly requests a small mechanical edit, test-only change, typo fix, formatting-only change, or direct hotfix without planning. Creates requirements.md, design.md, and tasks.md under .kiro/specs/{feature-name}/ with explicit approval between phases and one-task-at-a-time execution.

### owasp-security

Use when reviewing code for security vulnerabilities, implementing authentication/authorization, handling user input, or discussing web application security. Covers OWASP Top 10:2025, ASVS 5.0, LLM Top 10 (2025), and Agentic AI security (2026).

`security`  `owasp`  `code-review`

### pr-description-craft

用于提交 PR / MR 前撰写或审查其标题与描述：强制「为什么改 / 改了什么 / 怎么验证」 三段式，让 reviewer 不看代码就能判断要不要细看、从哪看起。触发场景：写 PR 描述、 写 commit/MR 说明、嫌标题只有一句 "fix bug"、reviewer 反复追问改动意图时。 Use when writing or reviewing a pull/merge request title and description.

`code-review`  `change-hygiene`  `communication`  `strength`

### psql-field-diagnostics

用于在 psql 里手工排查 PostgreSQL 数据/性能问题：看表结构、类型转换报错、ILIKE 慢查询、 读 EXPLAIN、只读安全习惯。一份排障时不再卡语法的现场工具箱。Use when hand-investigating data or perf issues in psql.

`postgresql`  `sql`  `debugging`  `gap-fill`

### solve-at-the-right-layer

动手优化 / 打补丁 / 加绕过之前的强制一问：我是在对的"层"解决吗？能"消除"问题 （改结构、换它发生的位置）而不是"缓解"它（把可能放错地方的活做得更快/更稳）吗？ 触发场景：优化慢路径；加缓存 / 索引 / 重试 / 特殊 case / workaround；在同一处反复打补丁仍撞墙； 为"读时现算"提速；做"该把这个计算 / 状态放在哪一层"的取舍。 讨论 缓解 vs 消除 / mitigate vs eliminate / 在上游解决 / 换个层 / 改对地方 / 别在症状层打补丁 / altitude / root cause layer / 预计算 / 物化 / 冗余字段 / counter cache。 配合 value-semantics-discipline（把值弄对）、code-change-guardrails（落地）、kiro-skill（规划）。

### test-driven-development

Use when implementing any feature or bugfix, before writing implementation code

`testing`  `tdd`  `discipline`

### using-git-worktrees

Use when starting feature work that needs isolation from current workspace or before executing implementation plans - ensures an isolated workspace exists via native tools or git worktree fallback

`git`  `worktree`  `workflow`

### value-semantics-discipline

General code-writing standard for eliminating ambiguity in the implicit contracts that every value and interface carries — meaning, unit, base/offset, range, nullability/absence, ordering, lifecycle, error behavior. Use when writing or changing ANY code: choosing a representation, default, or sentinel; deciding how to signal absent/empty/error; naming a variable or field; sorting or iterating; computing or storing a value others consume. Triggers on: 写代码, 写函数, 改逻辑, 接口设计, 字段设计, 默认值, 缺失, null, 哨兵, 边界, 下标, 起点, 单位, 顺序, 命名, 错误处理, 歧义, 契约, representation, default, sentinel, nullability, boundary, off-by-one, ordering, naming, contract, ambiguity, edge case. Core rule: surface every implicit contract and make it explicit, consistent end-to-end, and verified against consumers BEFORE writing — never let an approximation that merely "runs" stand in for a precise, unambiguous one.

### verification-before-completion

Use when about to claim work is complete, fixed, or passing, before committing or creating PRs - requires running verification commands and confirming output before making any success claims; evidence before assertions always

`verification`  `discipline`  `quality`

## Pending submissions（暂存待审，未发布、不可装）（0）

_（暂无）_

