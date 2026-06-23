# 贡献一个技能 / Contributing a skill

技能 = 一个带 `SKILL.md` 的目录(**纯指令,无脚本/代码**)。几种投法,从最省事的开始。

## 已经在 Claude 里写过技能?（最常见)

你的技能就在本地 `~/.claude/skills/<名>/SKILL.md`。两种上传:

**① 复制粘贴(零安装,任何人都能用)**
打开那个 `SKILL.md` → 全选复制 → 贴进下面 **[➕ Add a skill](#一键加一个新技能从零写)** 的编辑器 → **Propose changes**。完事。

**② 一条命令(跳过复制粘贴)**
用本仓根目录的 **`upload-skill.py`** —— 它读你本地的技能,**自动打开浏览器、内容已预填**,你点 Propose changes 就开 PR。怎么拿到它(任选一种):

```bash
# 只下这一个文件,不用 clone 整个仓
curl -O https://raw.githubusercontent.com/liulejun511/skillhub/main/upload-skill.py
python upload-skill.py <你的技能名>
```

或在 GitHub 上打开 [`upload-skill.py`](upload-skill.py) → 点 **Raw** → 另存。

> 拿不到脚本也没关系 —— ① 那条复制粘贴不用装任何东西,永远能用。

## 一键加一个新技能(从零写)

点 **[➕ Add a skill](https://github.com/liulejun511/skillhub/new/main?filename=sandbox/skills/my-skill/SKILL.md&value=---%0Aname%3A%20my-skill%0Adescription%3A%20Use%20when%20...%20%28one%20line%3A%20when%20should%20Claude%20reach%20for%20this%20skill%3F%29%0Aversion%3A%200.1.0%0A---%0A%0A%23%20My%20Skill%0A%0AWhat%20this%20skill%20makes%20Claude%20do%20%E2%80%94%20the%20judgment%20focus%2C%20rules%2C%20and%20the%20output%20shape.%0AKeep%20it%20instructions-only%20%28no%20scripts%20/%20code%29.%0A)** —— 编辑器里**路径和模板都已填好**。把 `my-skill` 改成你的技能名、写内容、点 **Propose changes** —— **GitHub 自动帮你 fork + 开 PR**,CI 自动检查。

## 其它方式

- **填个表单**:开 [**Submit a skill** issue](https://github.com/liulejun511/skillhub/issues/new?template=submit-skill.yml),填技能名 / 触发场景 / 正文即可。
- **自己 fork 提 PR**:Fork → 加 `sandbox/skills/<名>/SKILL.md` → Pull Request。
- **clone 了本仓**:`PYTHONPATH=tools python -m memoket submit <名>`(拷进 sandbox 并立刻过闸),过了 `git add sandbox/ && git commit && git push`。

## SKILL.md 最小格式

```markdown
---
name: your-skill-name
description: Use when ...（一句话说清「什么时候该用」——这是 Claude 自动触发的依据)
version: 0.1.0
---

# 标题

（正文：这个技能让 Claude 怎么做、判断重点、规则、产出长啥样)
```

## 规矩(CI 会自动查,过不了不能合)

- **仅纯指令(Inert)**:不能带 `scripts/`、`hooks/`、`bin/`、MCP 等会自动运行的代码。
- **无敏感信息**:真实人名 / 密钥 / 内部代号 / 具名分支 / 仓内脚本路径会被脱敏闸拦下。
- **`description` 要有触发场景**("Use when …"),否则浮现不出来。

## 合入之后

投稿先以 PR 落到 `sandbox/skills/`(**暂存区,不可安装**),过 CI + 维护者审。**只有被收进 curated(`plugins/`)的才发布、才能一键装**——维护者用 `memoket promote <名>` 收进去。未审的停在 PR / 暂存,不对外发布。已发布技能可在 [`CATALOG.md`](CATALOG.md) 一页浏览。
