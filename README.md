# skillhub

**English** · [中文](#skillhub-中文)

A shared place to find and share **skills for Claude** — small, reusable instructions that make Claude better at one specific task (writing a PR, debugging SQL, and so on).

Each skill is its own plugin, so you **install only the ones you want**.

## Install

In the Claude Code CLI:

```bash
/plugin marketplace add https://github.com/liulejun511/skillhub.git
/plugin install pr-description-craft@skillhub      # pick any skill from the list below
/reload-plugins
```

- Browse every skill and what it does in **[CATALOG.md](CATALOG.md)** — or just run `/plugin`, find **skillhub**, and pick from the list.
- Once installed, a skill works on its own: Claude uses it automatically when it fits. You don't call it by name.
- Remove any one anytime: `/plugin uninstall <skill>@skillhub`.

## The skills

| Skill | What it does |
| --- | --- |
| `pr-description-craft` | Write a PR description a reviewer can judge fast — why, what, how-tested |
| `psql-field-diagnostics` | Debug PostgreSQL data and slow queries in `psql` |
| `evidence-before-adoption` | Get real proof before trusting a change, perf claim, or report |
| `commit-pr-conventions` | Conventional Commits + a skimmable PR-description format |
| `kiro-skill` | Spec-driven workflow: requirements → design → tasks → execute |
| `solve-at-the-right-layer` | Fix at the right layer — eliminate a problem, don't just mitigate it |
| `value-semantics-discipline` | Make every value's implicit contract explicit (units, nulls, ordering) |

## Share your own skill

**Already have a skill in `~/.claude/skills/`?** Upload it without copy-pasting:

```bash
curl -O https://raw.githubusercontent.com/liulejun511/skillhub/main/upload-skill.py
python upload-skill.py <your-skill-name>   # opens a pre-filled PR in your browser
```

**Writing a new one?** One click — no fork, no setup:

### [➕ Add a skill →](https://github.com/liulejun511/skillhub/new/main?filename=sandbox/skills/my-skill/SKILL.md&value=---%0Aname%3A%20my-skill%0Adescription%3A%20Use%20when%20...%20%28one%20line%3A%20when%20should%20Claude%20reach%20for%20this%20skill%3F%29%0Aversion%3A%200.1.0%0A---%0A%0A%23%20My%20Skill%0A%0AWhat%20this%20skill%20makes%20Claude%20do%20%E2%80%94%20the%20judgment%20focus%2C%20rules%2C%20and%20the%20output%20shape.%0AKeep%20it%20instructions-only%20%28no%20scripts%20/%20code%29.%0A)

It opens an editor with a starter template already filled in. Write your skill, click **Propose changes**, and the automatic checks run for you. Full guide: **[CONTRIBUTING.md](CONTRIBUTING.md)**.

## License

MIT — see [LICENSE](LICENSE).

<sub>How it works under the hood — a submission is a PR (not installable), reviewed, then promoted to the installable curated set; with automated security checks. Details: [`.kiro/specs/skill-hub/`](.kiro/specs/skill-hub/).</sub>

---

<a id="skillhub-中文"></a>

# skillhub(中文)

[English](#skillhub) · **中文**

一个**找 + 分享 Claude 技能**的地方 —— 小而可复用的指令,让 Claude 在某件具体事上做得更好(写 PR、排查 SQL 等)。

每个技能是**独立插件**,所以你**只装想要的**。

## 安装

在 Claude Code CLI 里:

```bash
/plugin marketplace add https://github.com/liulejun511/skillhub.git
/plugin install pr-description-craft@skillhub      # 从下面列表挑任意技能
/reload-plugins
```

- 所有技能和各自干啥,看 **[CATALOG.md](CATALOG.md)** —— 或直接跑 `/plugin`,找到 **skillhub**,挑着装。
- 装上后技能**自动按场景触发**,不用点名调用。
- 随时卸载某一个:`/plugin uninstall <技能名>@skillhub`。

## 有哪些技能

| 技能 | 干啥 |
| --- | --- |
| `pr-description-craft` | 写一份 reviewer 能快速判断的 PR 描述 —— 为什么改 / 改了什么 / 怎么验证 |
| `psql-field-diagnostics` | 在 `psql` 里排查 PostgreSQL 数据和慢查询 |
| `evidence-before-adoption` | 信一个改动 / 性能主张 / 汇报之前,先要真实证据 |
| `commit-pr-conventions` | Conventional Commits + 一套好读的 PR 描述格式 |
| `kiro-skill` | 规格驱动流程:需求 → 设计 → 任务 → 执行 |
| `solve-at-the-right-layer` | 在对的「层」解决 —— 消除问题,而不只是缓解 |
| `value-semantics-discipline` | 把每个值的隐含契约写明确(单位、空值、顺序) |

## 分享你自己的技能

**已经在 `~/.claude/skills/` 里有技能?** 一条命令上传,不用复制粘贴:

```bash
curl -O https://raw.githubusercontent.com/liulejun511/skillhub/main/upload-skill.py
python upload-skill.py <你的技能名>   # 自动在浏览器里打开预填好的 PR
```

**从零写一个?** 一键,无需 fork、无需配置:

### [➕ 加一个技能 →](https://github.com/liulejun511/skillhub/new/main?filename=sandbox/skills/my-skill/SKILL.md&value=---%0Aname%3A%20my-skill%0Adescription%3A%20Use%20when%20...%20%28one%20line%3A%20when%20should%20Claude%20reach%20for%20this%20skill%3F%29%0Aversion%3A%200.1.0%0A---%0A%0A%23%20My%20Skill%0A%0AWhat%20this%20skill%20makes%20Claude%20do%20%E2%80%94%20the%20judgment%20focus%2C%20rules%2C%20and%20the%20output%20shape.%0AKeep%20it%20instructions-only%20%28no%20scripts%20/%20code%29.%0A)

它会打开一个**已填好模板**的编辑器。写完你的技能,点 **Propose changes**,自动检查就替你跑了。详见 **[CONTRIBUTING.md](CONTRIBUTING.md)**。

## 许可

MIT —— 见 [LICENSE](LICENSE)。

<sub>背后怎么运作 —— 投稿是一个 PR(未发布、装不了),审过后晋级进可安装的 curated 集合;全程自动安全检查。详见 [`.kiro/specs/skill-hub/`](.kiro/specs/skill-hub/)。</sub>
