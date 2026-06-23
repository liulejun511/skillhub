# 贡献一个技能 / Contributing a skill

技能 = 一个带 `SKILL.md` 的目录(**纯指令,无脚本/代码**)。两种投法,挑简单的那个。

## 路子一：GitHub 网页(零本地配置,最简单)

1. 打开仓库 → **Fork**。
2. 在你的 fork 里新建文件:`sandbox/skills/<你的技能名>/SKILL.md`,把内容贴进去(格式见下)。
3. 提一个 **Pull Request**。
4. **CI 自动检查**(格式 + 脱敏 + 注入扫 + 仅限纯指令),结论贴在 PR 上。绿了等维护者合入。

> 全程在浏览器里完成,不用装任何东西。

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
