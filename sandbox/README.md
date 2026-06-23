# sandbox/ — 投稿暂存区(不可安装)

这里**不是一个可安装的 marketplace**。它只是**投稿暂存区**:投稿的技能先以 PR 的形式落到 `sandbox/skills/<name>/SKILL.md`,过 CI 闸、由维护者审。

**只有审过、被收进 curated(`plugins/`)的技能才会发布、才能被安装。** 暂存在这里的东西**装不了**——这是有意的:未审的不对外发布。

## 投稿流程

1. 把技能加到 `sandbox/skills/<your-skill>/SKILL.md`(纯指令,无脚本/代码),提 PR。
   - 最省事:用仓库 README 里的 **[➕ Add a skill]** 一键链接,或 `upload-skill.py`。
2. CI 自动检查(结构 + 脱敏 + 注入扫 + 仅 Inert),结论贴 PR 上。
3. 维护者审。够好 → 用 `memoket promote <name>` 收进 `plugins/`(curated)→ 发布、人人可装。

详见仓库根的 [CONTRIBUTING.md](../CONTRIBUTING.md)。
