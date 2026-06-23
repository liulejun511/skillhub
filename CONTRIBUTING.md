# 贡献一个技能 / Contributing a skill

技能 = 一个带 `SKILL.md` 的目录(**纯指令,无脚本/代码**)。两种投法,挑简单的那个。

## 最快：一键加一个技能(零 git、零 fork、零本地配置)

点 **[➕ Add a skill](https://github.com/liulejun511/skillhub/new/main?filename=sandbox/skills/my-skill/SKILL.md&value=---%0Aname%3A%20my-skill%0Adescription%3A%20Use%20when%20...%20%28one%20line%3A%20when%20should%20Claude%20reach%20for%20this%20skill%3F%29%0Aversion%3A%200.1.0%0A---%0A%0A%23%20My%20Skill%0A%0AWhat%20this%20skill%20makes%20Claude%20do%20%E2%80%94%20the%20judgment%20focus%2C%20rules%2C%20and%20the%20output%20shape.%0AKeep%20it%20instructions-only%20%28no%20scripts%20/%20code%29.%0A)** —— 它打开 GitHub 编辑器,**路径和模板都已填好**。把 `my-skill` 改成你的技能名、写内容、点 **Propose changes** —— **GitHub 自动帮你 fork + 开 PR**,CI 自动检查。浏览器里点几下就投了,不用懂 git、不用手动 fork。

## 或者：填个表单

开一个 [**Submit a skill** issue](https://github.com/liulejun511/skillhub/issues/new?template=submit-skill.yml),把技能名 / 触发场景 / 正文填进去即可。

## 或者：自己 fork 提 PR

打开仓库 → **Fork** → 在你的 fork 里加 `sandbox/skills/<名>/SKILL.md` → 提 **Pull Request** → CI 自动检查。

## 路子二：本地一条命令(已 clone 仓的话)

```bash
PYTHONPATH=tools python -m memoket submit <你的技能名>
```

它会把 `~/.claude/skills/<名>/` 或你指定路径的技能**拷进 `sandbox/skills/`、立刻过一遍闸**,告诉你过没过。过了就:

```bash
git add sandbox/ && git commit -m "add skill: <名>" && git push
# 然后在 GitHub 上开 PR(自己的仓直接 push 即可)
```

## SKILL.md 最小格式

```markdown
---
name: your-skill-name
description: Use when ...（一句话说清「什么时候该用」——这是 Claude 自动触发的依据）
version: 0.1.0
---

# 标题

（正文：这个技能让 Claude 怎么做、判断重点、规则、产出长啥样）
```

## 规矩(CI 会自动查,过不了不能合)

- **仅纯指令(Inert)**:不能带 `scripts/`、`hooks/`、`bin/`、MCP 等会自动运行的代码。
- **无敏感信息**:真实人名/密钥/内部代号/具名分支/仓内脚本路径会被脱敏闸拦下。
- **`description` 要有触发场景**("Use when …"),否则浮现不出来。

## 合入之后

技能先进 **sandbox**(`skillhub-sandbox`,未策展、可装但标「未审」)。好用的会经一个**人工策展的晋级 PR** 移进 curated 的 `skillhub`,人人可一键装。所有技能可在 [`CATALOG.md`](CATALOG.md) 一页浏览。
