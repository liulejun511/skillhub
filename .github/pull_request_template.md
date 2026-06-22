<!-- 投稿（进 sandbox）或晋级（sandbox → curated）都用本模板。删掉不相关的一节。 -->

## 类型
- [ ] 投稿新技能到 **sandbox**（未策展）
- [ ] **晋级** sandbox 技能进 curated `skillhub`

## 为什么 / 改了什么
<!-- 这个技能解决什么、触发场景是什么；晋级则说明它凭什么够格 -->

## 自查（投稿）
- [ ] 技能在 `sandbox/skills/<name>/`，含 `SKILL.md`（`description` 带触发场景 "Use when …"）
- [ ] **仅 Inert**：无 `scripts/`、`hooks/`、`bin/`、MCP 等可执行组件
- [ ] 本地 `PYTHONPATH=tools python -m memoket gate sandbox/skills/<name>` 全绿
- [ ] 无真实 PII / 凭证 / 内部代号 / 具名分支 / 仓内脚本路径（脱敏闸会查）

## 晋级清单（仅晋级 PR）
- [ ] CI 自动闸全绿（L0 + 脱敏 + 注入 + 能力分级）
- [ ] **人工策展评审**通过：内容质量达标、provenance（作者/来源）可信
- [ ] 用 `memoket promote <name> --sha <40位commit> --repo <owner>/skillhub` 完成「移树 + 置 active + curated 源钉 SHA」
- [ ] 移动与 marketplace.json 改动在同一 commit（可回滚 = revert 本 PR 的 merge commit）

> 晋级**绝不自动**：必须由维护者人工 review 后合入（设计 R2.4 / R4.5）。
