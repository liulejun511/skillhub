# Implementation Plan

> **执行状态（2026-06-22）**：任务 1–7 + 8.1 已完成并验证（33/33 离线测试通过：脱敏白名单 5 / 注入扫描 8 / 能力分级 6 / CI 闸 6 / marketplace 校验 5 / 晋级 helper 3）。**仅 8.2（真机 `/plugin` 安装 + 团队 settings.json 实测）待你在目标 Claude Code 版本上手动验证。** 改动未提交，等你确认。

> 原则：测试优先、每项独立可验、最小 diff。所有 pytest 经 **WSL + `D:\capsoul\CapsoulAI\.venv`** 跑（Windows 直跑无法 import）。被 prune 的模块连同其测试一起删，删后以「kept 集导入通过 + 其测试绿」为验收。

## 阶段一 · 清场：把 memoket 降为 CI/创作工具

- [ ] 1. 砍掉自演变大脑、剥离运行时模块
  - [ ] 1.1 删除 prune 清单模块及其测试
    - 删 `distill cycle garden ingest connectors/* driver evals kernel tool_retro signals watermark profile budget locking review report locales`
    - 从 `cli.py` 移除对应子命令（distill/evolve/ingest/cycle/watermark/garden/signals/eval/`quality review --drive`/`garden run --drive`），改写 `__init__.py` 与 `cli.py` 顶部的「自演变」叙述
    - 验收：`python -m memoket --help` 不再出现已删命令；kept 模块 import 无 `ModuleNotFoundError`
    - _Requirements: 复用与砍掉条款_
  - [ ] 1.2 把 `install/lockfile/integrity` 移出 v1 运行时
    - v1 不用自建安装/quarantine（原生 marketplace 取代）；删除这三者及其测试，并清掉 `semver` 仅服务 `update_skill` 的死调用（`semver` 本身可留作工具）
    - 验收：仓内无任何 kept 模块 import 这三个；说明留 git 历史可恢复（将来自愿遥测层若需要）
    - _Requirements: 1.2, 1.3（运行时改由原生承担）_

- [ ] 2. 把路径模型从 vault 重指到 git 树（sandbox/ + plugins/）
  - [ ] 2.1 重写 `paths.py` 的工作区布局
    - 去掉 `watermark_path/kernel_path/signals_dir/eval_dir/work_dir` 等死路径；新增「sandbox 技能树」与「curated 技能树（plugins/）」的定位；`MEMOKET_HOME`/vault 命名改成 hub 语义
    - 先写 `tests/test_paths.py` 锁定新定位契约，再改实现
    - _Requirements: 2.1, 5.2_
  - [ ] 2.2 重指依赖 vault 的 kept 模块
    - `audit.py`：`_ALLOWED_TOP` 与 `_privacy_regression` 不再硬编码旧 distill 产物；遍历 sandbox/plugins 技能目录
    - `quality.py`：`assemble_review_request` 指向 hub 技能目录而非 `vault/mine`
    - 验收：`aggregate_validate` 与 `quality` 在 sandbox/plugins 样例目录上跑通
    - _Requirements: 5.2, 5.3_

## 阶段二 · 自动闸（L0 + L1，fail-closed）

- [ ] 3. 脱敏与格式校验校准
  - [ ] 3.1 给 `redaction.scan` 加 URL 白名单
    - 先写测试：引用 `code.claude.com`/`docs.claude.com` 等合法文档 URL **不**误杀，外发型可疑 URL 仍命中
    - 再实现白名单机制（可配置）
    - _Requirements: 4.2(L1), 5.4_
  - [ ] 3.2 调和 `status: draft` 与 publish 的 active-only 规则
    - 决策落地：`validate` 不强制 active；晋级流程在合入时把 status 置 `active`（或放宽断言，二选一并加测试覆盖）
    - 验收：种子（draft）能过 sandbox 校验，晋级后为 active
    - _Requirements: 5.1, 2.4_

- [ ] 4. 新写注入/危险语句扫描器（v1 唯一新代码件）
  - [ ] 4.1 建红队语料 + 期望判定（先于实现）
    - `tests/fixtures/malicious/`：注入语句（"忽略以上"/"disregard your instructions"）、外发 URL、读 `.env`/`~/.ssh`/凭证、base64+curl/POST、改写绕过、homoglyph、跨 `reference/` 文件藏指令；各附期望命中
    - `tests/test_injection_scan.py`：语料中每个坏样本必须被命中；干净样本零误报（回归守卫）
    - _Requirements: 4.2(L1), 4.3_
  - [ ] 4.2 实现 `injection_scan.py`
    - 仿 `redaction._PATTERNS` 结构，返回 `[{type,match,line,file}]`；**扫 SKILL.md + 所有打包文本含 `reference/`**
    - 高置信命中 = FAIL 并标注行；低置信 = WARN 下放人审
    - 验收：4.1 全绿
    - _Requirements: 4.2(L1), 4.3_

- [ ] 5. 能力分级：v1 拦截 Active
  - [ ] 5.1 建分级 fixture（先于实现）
    - 正负样本：纯 Inert；带 `scripts/`/`hooks/`/`bin/`/`mcpServers/` 的 Active；以及「自称 inert 却带代码目录」的 manifest-不符样本（必须判失败）
    - _Requirements: 4.1_
  - [ ] 5.2 实现分级 + Active 拒收
    - 扩展可执行目录标记集；检出 Active → v1 在入口 FAIL，附「Active 暂不收，仅收 Inert」清晰提示；manifest 不符 = 硬失败
    - _Requirements: 4.1_

## 阶段三 · CI 编排与两层 marketplace

- [ ] 6. sandbox PR 的 CI 运行器（fail-closed）
  - [ ] 6.1 marketplace.json schema 校验 + 测试
    - 加（或引用）Claude Code marketplace schema；写测试：curated 与 sandbox 两个 catalog 都有效；损坏样本被拒
    - _Requirements: 1.1, 2.2_
  - [ ] 6.2 聚合运行器：跑 L0+L1(脱敏+注入)+质量体检(advisory)+Active 拒收
    - 单入口对 PR 变更的技能逐个跑；**任一 block 或扫描器异常 → 非零退出（fail-closed）**；输出机读结果供 PR 评论
    - 写测试：命中脱敏/注入/Active 时确实非零；干净时零；扫描器抛错时非零
    - _Requirements: 2.2, 4.2, 4.3_
  - [ ] 6.3 GitHub Actions 工作流接入
    - 在 sandbox PR 上调用 6.2，把结论贴到 PR；标注「sandbox=未审」
    - _Requirements: 2.2, 2.3_

- [ ] 7. 两个具名 marketplace 的落地
  - [ ] 7.1 建 sandbox marketplace.json
    - `sandbox/.claude-plugin/marketplace.json`（name `skillhub-sandbox`），相对路径源、skills-only、`description` 前缀 `[SANDBOX/UNREVIEWED]` + `category:"sandbox"`/`tags:["unreviewed"]`
    - _Requirements: 2.1, 2.3, 4.1_
  - [ ] 7.2 curated entry 转 github 源 + SHA 钉死
    - 把根 marketplace.json 的种子 entry 从相对路径改为 `{source:"github", repo, sha}`；写一个小 helper 在晋级时把 entry 的 sha 盖成合入 commit
    - 验收：curated entry 带 40 位 sha；测试校验 entry 形态
    - _Requirements: 1.3_
  - [ ] 7.3 晋级 PR 模板 + 移树 helper
    - PR 模板：晋级 = 移 sandbox 技能树到 `plugins/` + 在 curated catalog 加 SHA 钉死 entry + 从 sandbox catalog 移除；勾选项含「人工策展 + provenance 核对」
    - helper 脚本执行上述文件移动（人执行、人合入，**不自动晋级**）
    - _Requirements: 2.4, 2.5, 4.4_

## 阶段四 · 收尾验证

- [ ] 8. 端到端与回退验证
  - [ ] 8.1 负向 CI 集成测试
    - 构造一个含脱敏/注入命中的假晋级 PR 输入，断言 6.2 阻断；构造干净 Inert 断言通过
    - _Requirements: 2.2, 4.3_
  - [ ] 8.2 原生安装 + 团队接入验证清单（可执行检查 + 文档）
    - 脚本/清单：全新会话 `/plugin marketplace add` + `/plugin install memoket-core@skillhub` 三种子可触发；团队 settings.json（`extraKnownMarketplaces`+`enabledPlugins`）**在目标 CC 版本实测**，失败则用手动 `add`+`install` 回退（因 #32606）
    - 记录硬性最低 CC 版本
    - _Requirements: 1.1, 1.4, 6.3_

---

## 不在 v1（留接缝，勿在本轮实现）

- 团队自愿 **opt-in 用量遥测**（重挂 `mcp_server` + `lifecycle`/`dashboard` 写 `evolution.json`，看板/飞书推送）— R3.2/R3.4
- **公开信号抓取**（GitHub stars/forks/dependents → `registry` 的 `public_signals` 槽）与全套防刷 — R3.3
- **Active 技能全链**（L1 代码静态扫 Pass-B、L2 blast-radius、L4 无网/限 FS 沙盒 jail、N 评审多数投票）— R4.1/R4.2，待出现真实 Active 需求再建

—

任务看起来可以吗？
