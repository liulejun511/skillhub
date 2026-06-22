# skillhub-sandbox（未策展区）

人人可 PR 投稿技能到这里。**它是一个独立的 marketplace（`skillhub-sandbox`），与已策展的 `skillhub` 物理隔离**——装的时候你会看见 `plugin@skillhub-sandbox`，与 `plugin@skillhub` 一眼可分。

## 投稿一个技能

1. 把技能放到 `sandbox/skills/<your-skill>/SKILL.md`（可带 `reference/` 文档，**不可带** `scripts/`、`hooks/`、`bin/`、MCP 等可执行组件——v1 沙盒**仅收 Inert/纯指令**）。
2. 本地自查：
   ```bash
   PYTHONPATH=tools python -m memoket gate sandbox/skills/<your-skill>
   ```
3. 提 PR。CI 会跑结构校验 + 脱敏/注入扫 + 能力分级（fail-closed，红了不能合）。

## 风险提示

沙盒技能**未经安全评审**。安装前请自行审阅 `SKILL.md`。好用且过审的会经一个**人工策展的晋级 PR**移入 curated 的 `skillhub`（届时源会钉到 commit SHA）。

## 安装（自担风险）

```bash
/plugin marketplace add liulejun511/skillhub        # 注意：sandbox 是独立 marketplace
/plugin install skillhub-sandbox@skillhub-sandbox
```
