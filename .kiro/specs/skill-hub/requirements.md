# Requirements Document

## Introduction

`skillhub` 是一个**面向所有程序员的 Claude 技能注册中心**——让人**手写**好用的 Claude skill，通过 **PR 贡献**进入一个**沙盒**，靠**用量与质量信号**判断哪些「火、好用」，再经**人工策展 + 安全评审**晋级进**正式 marketplace**，供任何人一键安装。

**关键定位（由前期讨论锁定）**：

- **骑 Claude Code 原生 plugin marketplace 做分发**（`.claude-plugin/marketplace.json` + `/plugin marketplace add`），**不重造 npm/分发体系**。
- **技能由人手写**，不做 AI 自动提炼——自动提炼（distill/evolve/triage/cycle/garden 自动合并/素材连接器/「自演变」叙事）经验证价值低，**明确砍掉**。
- **北极星是公开**（给所有程序员用），但**第一个里程碑是团队规模的核心**：团队的真实 skill + 真实用量 = 公开版的种子与证明。设计从第一天就「为公开而生」。
- **复用** 旧仓 `memoket-skills` 已验证的：用量/触发统计、`SKILL.md` 格式 + 校验、脱敏闸（redaction）、安装隔离（quarantine）、质量评审范式（quality-review）。

**成功标准**：① 任何人能在自己的 Claude 里一行 `add` 这个 marketplace 并装上技能；② 贡献者能把一个 skill 通过 PR 提进 sandbox，并在达标 + 审查通过后晋级进 marketplace；③ 安全评审能拦住注入/恶意代码类技能；④ 团队内能看到「哪个技能火、哪个没人用」以驱动策展。

### 名词

- **Skill**：一个 Claude 技能（`SKILL.md` 包；可作为原生 plugin 内的技能分发）。
- **Sandbox**：`sandbox/` 区，PR 即收、低门槛、未经策展，安装时显著标注「未审」。
- **Marketplace**：`.claude-plugin/marketplace.json` 列出的**已策展**技能，经安全评审 + 质量达标。
- **Inert 技能**：纯指令（仅 SKILL.md，无脚本/hook/MCP/bin）。
- **Active 技能**：打包了可执行组件（scripts/hooks/bin/MCP）。
- **晋级（promotion）**：sandbox → marketplace，靠「用量/质量证据 + 安全评审 + 人工 PR 合入」。

## Requirements

### Requirement 1 · 原生分发（不重造）

**User Story:** 作为任何程序员，我想用 Claude Code 原生方式一行装上 hub 里的技能，不被迫学一套新工具。

#### Acceptance Criteria

1. THE 仓库 SHALL 提供合法的 `.claude-plugin/marketplace.json`，使任何人可 `/plugin marketplace add <repo>` 后安装其中技能。
2. THE 技能 SHALL 以 Claude Code 原生 plugin/skill 结构组织，安装后由 Claude 原生加载（不依赖自建运行时）。
3. THE 系统 SHALL 不自建分发/下载体系；安装、更新、版本均走原生 plugin 机制（支持 git source + commit SHA 钉死）。
4. WHERE 团队接入 THE 仓库 SHALL 提供可复制的 `.claude/settings.json` 片段（`extraKnownMarketplaces` + `enabledPlugins`）。

### Requirement 2 · 贡献与晋级流（sandbox → marketplace）

**User Story:** 作为贡献者，我想把我写的好用 skill 提交进来，并在它被证明好用后晋级到正式市场。

#### Acceptance Criteria

1. THE 系统 SHALL 设 `sandbox/`（人人可 PR 提交）与 `marketplace/`（已策展）两区物理隔离。
2. WHEN 贡献者提交一个 skill 的 PR 到 `sandbox/` THEN CI SHALL 自动跑结构校验 + 安全静态扫 + 能力分级，并把结论贴在 PR 上。
3. THE 从 sandbox 安装的技能 SHALL 在元数据/展示上明确标注「未策展/未审」，与 marketplace 技能区分。
4. WHEN 一个 sandbox 技能满足晋级标准（见 R3 质量 + R4 安全）THEN 晋级 SHALL 通过「一个把它从 sandbox 移入 marketplace 的 PR + 人工评审合入」完成，绝不自动晋级。
5. THE 每次晋级/下架 SHALL 留 git 痕迹，可追溯、可回滚。

### Requirement 3 · 「火不火 / 好不好用」的双轴判断

**User Story:** 作为策展者/用户，我想分清一个技能是「热门」还是「真好用」，据此决定晋级与采用。

#### Acceptance Criteria

1. THE 系统 SHALL 用**两个轴**评估技能，不压成单一分数：**热度**（采纳广度）与**质量**（用了还留/被依赖/评分）。
2. WHERE 团队内运行（安装可控）THE 系统 SHALL 用**运行时触发用量**（被检索 surfaced / 被取用 used）作为真实使用信号（复用旧仓触发统计）。
3. WHERE 公开规模（安装不可控）THE 系统 SHALL 改用可白拿的公开信号：GitHub stars/forks、安装数（若经 registry/CLI）、**被依赖/被引用数**、用户评分、人工策展徽章；**不依赖运行时遥测**。
4. THE 系统 SHALL **不做公开遥测**作为核心机制（开发者 opt-in 率低）；至多在未来留「团队内优先、自愿」的可选项，不在第一版实现。
5. THE 晋级决策 SHALL 以上述信号为**证据**输入人工评审，而非由单一用量阈值自动决定（防热度≠质量、防小众精品被埋）。
6. THE 系统 SHALL 提供防刷措施：评分需登录、按账号年龄/多样性加权、把最难刷的「被依赖数」与「人工 verified」置于显著位置。

### Requirement 4 · 安全评审（重点）

**User Story:** 作为用户，我装别人的技能时必须确信它不会注入劫持我的 agent、不会窃取我的数据。

#### Acceptance Criteria

1. THE 系统 SHALL 先按 **Inert（纯指令）/ Active（带 scripts/hooks/bin/MCP）** 给每个技能分级，并据此决定审查强度（Active 必须重审）。
2. THE 安全评审 SHALL 为分层流水线：
   - **L0 结构校验**：格式/必填字段合规（复用 validate）。
   - **L1 静态扫描**：正文扫提示注入模式（"忽略以上"、可疑外发 URL、读取凭证/.env、curl/POST 外发）；代码扫网络调用/越权写文件/eval/subprocess/混淆/硬编码密钥（扩展 redaction）。
   - **L2 能力分级**：判定 Inert/Active 与 blast radius。
   - **L3 对抗式 AI 评审**：多个独立 reviewer agent 以「能否劫持/外泄/带偏」审，多数判定（复用 quality-review 范式）。
   - **L4 人工 PR + 沙盒**：Active 技能必须人工评审 + 在无网络/限定 FS 沙盒中跑过，方可晋级。
   - **L5 运行时纵深防御**：安装即 quarantine（脚本默认不运行，需显式授权）；source 钉 commit SHA；升版必重审；提供下架/吊销机制。
3. IF 静态扫或对抗式评审判定高风险 THEN 系统 SHALL 阻止晋级并在 PR 标出具体风险位置。
4. THE 系统 SHALL 记录技能**作者身份/来源（provenance）**；匿名/低信誉来源 SHALL 受更严审查或仅限 sandbox。
5. THE 系统 SHALL 承认「提示注入无法被自动检测 100% 覆盖」，故 marketplace 准入 SHALL 强制人工策展 + verified 等级，不得仅凭自动扫放行。

### Requirement 5 · 技能格式与质量基线（复用）

**User Story:** 作为贡献者，我想有清晰的技能格式与质量门槛，写出来的技能可被校验、可被一致评估。

#### Acceptance Criteria

1. THE 技能 SHALL 用统一 `SKILL.md`（YAML frontmatter + Markdown 正文）格式，含必填 name/description（含触发场景）/version。
2. THE 系统 SHALL 提供 `validate`（结构 + 适配器层）作为 CI 与本地一致的门槛。
3. THE 系统 SHALL 提供内容质量评估（可复用/可执行/边界 三维 + 脱敏复查，复用 quality-review 范式），低于门槛者不得晋级。
4. THE 发布/晋级前 SHALL 过脱敏闸（无真实人名/金额/tenant id/内部代号/具名分支/仓内脚本路径）。

### Requirement 6 · 团队种子 / 为公开而生

**User Story:** 作为发起人，我想先让团队真实用起来（拿到真实用量与种子技能），但架构从一开始就能无缝开放给所有人。

#### Acceptance Criteria

1. THE 第一阶段 SHALL 以团队为种子：导入现有人工技能（如旧仓的高分技能、外部好指南整理稿），积累真实运行时用量。
2. THE 架构 SHALL 不含任何只对单一团队成立的硬编码；从 sandbox/marketplace、贡献流、信任模型到 marketplace.json 均按「公开可用」设计。
3. WHEN 团队阶段验证通过 THEN 开放 SHALL 仅为「把 marketplace 仓库公开 + 公布 add 链接」，无需重构。

## 复用与砍掉（来自旧仓 memoket-skills）

- **复用**：用量/触发统计与触发板、`SKILL.md` 格式 + `validate`、redaction 脱敏、quarantine 安装隔离、quality-review 质量评审范式。
- **砍掉**：自动提炼大脑（distill/evolve/triage/cycle）、garden 自动合并、面向自动 ingest 的素材连接器、「自演变」整体叙事。

## 待确认点（Open Questions）

1. **仓库/品牌名**：暂用 `skillhub`，是否定这个名（影响 marketplace name 与 add 链接）？
2. **第一版种子技能**：先导入旧仓哪些（3 个标杆 psql/pr-description/evidence？）+ 是否纳入外部指南整理稿？
3. **团队接入方式**：团队成员靠 `extraKnownMarketplaces` 自动装，还是先手动 `add`？
4. **Active 技能第一版是否直接禁止**（只收 Inert，把安全难题推后），还是一开始就支持 Active + 全套 L4 沙盒审？
5. **公开评分/stars 抓取**：第一版是否就接 GitHub API 拉 stars/dependents，还是团队阶段先只用运行时用量、公开信号留到开放阶段？

—

需求看起来可以吗？如果可以，我再进入设计阶段。（也可以直接回上面 5 个待确认点，我据此修订。）
