---
name: kiro-skill
description: >-
  Interactive spec-driven feature development workflow from idea to implementation.
  Use when the user mentions Kiro, K神, .kiro/specs, feature specs, requirements,
  EARS acceptance criteria, design documents, implementation plans, task lists,
  需求文档, 设计文档, 实现计划, or executing a single task from a Kiro-style spec.
  Also use by default before writing business code or product feature code,
  including backend business logic, user-facing workflows, product behavior,
  domain rules, data model changes, API behavior changes, or frontend business
  flows, unless the user explicitly requests a small mechanical edit, test-only
  change, typo fix, formatting-only change, or direct hotfix without planning.
  Creates requirements.md, design.md, and tasks.md under .kiro/specs/{feature-name}/
  with explicit approval between phases and one-task-at-a-time execution.
---

# Kiro: Spec-Driven Development Workflow

把产品/业务想法拆成可评审、可执行、可逐步实现的规格文档。默认产物放在 `.kiro/specs/{feature-name}/`，目录名使用 kebab-case。

## 什么时候使用

- 新功能、业务逻辑、产品行为、用户路径、领域规则。
- API 行为、数据模型、跨模块行为、前端业务流程。
- 用户提到 Kiro、K神、spec、需求文档、设计文档、实现计划、任务列表。
- 执行 `.kiro/specs/{feature-name}/tasks.md` 里的某个任务。

不用强制进入 Kiro 的情况：

- 错别字、格式、import、注释、依赖小版本。
- 纯测试期望更新。
- 期望行为已经明确的小范围 bugfix。
- 用户明确说跳过规划、直接 hotfix。

## 总流程

1. **Requirements**：写 `requirements.md`，用用户故事 + EARS 验收标准定义要做什么。
2. **Design**：需求获批后写 `design.md`，说明怎么做、改哪些边界、如何验证。
3. **Tasks**：设计获批后写 `tasks.md`，拆成可执行、测试优先、增量的小任务。
4. **Execute**：用户指定任务后，一次只执行一个 task；完成后停止等待 review。

每个阶段都需要用户明确批准后才能进入下一阶段。不要把需求、设计、任务、实现合并成一次交付。

## Phase 1 · Requirements

创建或更新 `.kiro/specs/{feature-name}/requirements.md`。

不要先连续追问。根据用户已给信息先生成初稿，再标出少量待确认点。

使用这个结构：

```markdown
# Requirements Document

## Introduction

[功能摘要：解决什么问题，用户是谁，成功结果是什么]

## Requirements

### Requirement 1

**User Story:** As a [role], I want [feature], so that [benefit]

#### Acceptance Criteria

1. WHEN [event] THEN [system] SHALL [response]
2. IF [condition] THEN [system] SHALL [response]
3. WHILE [state] [system] SHALL [response]
```

EARS 常用句式：

- `WHEN [event] THEN [system] SHALL [response]`
- `IF [condition] THEN [system] SHALL [response]`
- `WHILE [state] [system] SHALL [response]`
- `WHERE [feature] [system] SHALL [response]`
- `[system] SHALL [response]`

写完后必须询问：`需求看起来可以吗？如果可以，我再进入设计阶段。`

## Phase 2 · Design

前置条件：`requirements.md` 已存在且用户明确批准。

创建或更新 `.kiro/specs/{feature-name}/design.md`。设计阶段可以先读代码、查文档、搜索实现模式，但不要另建 research 文件；把关键结论写入对话或设计文档。

使用这个结构：

```markdown
# Feature Design

## Overview

[总体方案和关键取舍]

## Architecture

[组件关系、数据流；复杂时用 Mermaid]

## Components and Interfaces

[模块职责、函数/API 边界、输入输出契约]

## Data Models

[数据结构、状态、持久化变化]

## Error Handling

[失败场景、恢复策略、日志/监控]

## Testing Strategy

[单测、集成、回归、手工验证重点]
```

写完后必须询问：`设计看起来可以吗？如果可以，我再生成实现任务。`

## Phase 3 · Tasks

前置条件：`requirements.md` 和 `design.md` 已存在且用户明确批准。

创建或更新 `.kiro/specs/{feature-name}/tasks.md`。任务只包含写代码、改代码、测试代码相关事项；不要包含发布、培训、市场沟通、人工验收流程。

任务格式：

```markdown
# Implementation Plan

- [ ] 1. Set up core interfaces
  - Define the minimal boundary used by later tasks
  - Add focused tests for the interface contract
  - _Requirements: 1.1, 1.2_

- [ ] 2. Implement feature behavior
  - [ ] 2.1 Add the service logic
    - Implement the smallest useful behavior
    - Cover success and failure paths
    - _Requirements: 2.1_
```

任务要求：

- 最多两层层级，子任务用 `1.1`、`1.2`。
- 每项必须是 checkbox。
- 每项都要能独立执行并验证。
- 优先测试驱动，避免大跳步。
- 每项引用对应 requirement。

写完后必须询问：`任务看起来可以吗？` 获批后停止，不自动实现。

## Phase 4 · Execute

执行任务前必须先读：

- `.kiro/specs/{feature-name}/requirements.md`
- `.kiro/specs/{feature-name}/design.md`
- `.kiro/specs/{feature-name}/tasks.md`

执行规则：

- 如果用户指定 task，只做该 task。
- 如果 task 有子任务，先做子任务。
- 一次只做一个 task，不自动顺手做下一个。
- 严格按 design 的边界实现；保持最小代码。
- 完成后更新对应 checkbox（如用户希望维护任务进度），然后停止等待 review。

## 与 code-change-guardrails 协同

- 进入实际改代码时，仍必须遵守 `code-change-guardrails` 的改前确认、契约扫描、最小 diff、验证和交付格式。
- 如果 Kiro 规划发现 Breaking API、Schema、Prompt 输出结构、默认值或错误语义变化，先让用户确认，不直接实现。
- 业务代码默认先 Kiro 规划；Tiny 机械修改不用强制规划。

## 附加参考

- 工作流图见 [workflow-diagrams.md](workflow-diagrams.md)。
- 语气和代码哲学见 [kiro-identity.md](kiro-identity.md)。
