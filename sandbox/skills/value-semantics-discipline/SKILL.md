---
name: value-semantics-discipline
description: >-
  General code-writing standard for eliminating ambiguity in the implicit
  contracts that every value and interface carries — meaning, unit, base/offset,
  range, nullability/absence, ordering, lifecycle, error behavior. Use when
  writing or changing ANY code: choosing a representation, default, or sentinel;
  deciding how to signal absent/empty/error; naming a variable or field; sorting
  or iterating; computing or storing a value others consume. Triggers on: 写代码,
  写函数, 改逻辑, 接口设计, 字段设计, 默认值, 缺失, null, 哨兵, 边界, 下标, 起点,
  单位, 顺序, 命名, 错误处理, 歧义, 契约, representation, default, sentinel,
  nullability, boundary, off-by-one, ordering, naming, contract, ambiguity,
  edge case. Core rule: surface every implicit contract and make it explicit,
  consistent end-to-end, and verified against consumers BEFORE writing — never
  let an approximation that merely "runs" stand in for a precise, unambiguous one.
---

# 写代码:消除隐式约定的歧义

面向用户输出一律用**简体中文**。本 skill 是**通用写代码规范**(不是针对某个案例),核心一句话:

> **每个值、每个接口都带着一堆"没明说的约定"——含义、单位、起点、范围、缺失怎么表示、顺序、生命周期、出错怎么办。Bug 和歧义,几乎都来自把这些约定留成隐式、或前后不一致。规范就是:动笔前把这些约定一一摆明,做到「显式表达 + 全链路一致 + 对着消费方验证」,别用"能跑"的近似糊弄过去。**

每次写 / 改代码都要过这套纪律。配合:`code-change-guardrails`(改动流程)、`precompute-derived-fields`(派生值)、`solve-at-the-right-layer`(放对层)、`bug-trigger-analysis`(判 bug)。

## 反模式(本规范要消灭的)
- "先 `or 0` / `?? -1` / `|| ''` 兜一下,能跑就行" —— 兜底值和合法值撞了语义。
- "下标嘛,大概从这开始" —— base(0/1)、单位、范围没说清,跨层对不上。
- "排序差不多就行" —— 按可能并列的键排,顺序不可复现。
- "这个值我这儿也算一遍" —— 同一概念多处各算,边角必漂。
- 名字 / 类型不带含义,靠读代码的人猜。

## 通用检查清单(写到带"隐含约定"的东西就逐条过)

**1. 把隐含约定显式化**
含义、单位(ms/s、字节/字符、含税/不含税)、起点(0/1-based)、范围、可空性、编码、时区——用**类型、命名、注释/契约**写明,别让人猜。

**2. 缺失与边界:显式且无歧义**
- "无 / 未知 / 不适用"优先用 `null` 或专门的空类型,**慎用 `0 / -1 / "" / 空集`这种可能和合法值混淆的哨兵**。
- 动笔前主动列边界:空、零、最小 / 最大、溢出、单元素、重复值、首 / 尾元素——每个都问"这里会怎样"。
- 自检一句:**"我这个表示'缺失 / 异常'的值,会不会刚好长得像一个合法值?"** 会 → 换 `null` 或显式报错。

**3. 改表示前,先看消费方与契约**
谁读它、怎么用(当下标跳转?做算术?仅展示?持久化?)、契约允许什么(可空?范围?类型?)。**先 trace 到消费方,再定表示**,不凭手感。

**4. 一致性 + 单一真值**
同一概念用同一种表示;派生值只在一处算、所有人读它,别多处各用不同逻辑算一遍(联动 `precompute-derived-fields`)。重构掉一处"现场算"时,核对它和别处结果是否一致(base / 单位 / 缺失处理对得上)。

**5. 顺序 / 迭代确定性**
按**可能并列**的键排序必加唯一 tiebreak,否则不可复现;不依赖 map/set 迭代顺序、不依赖"恰好如此"的隐式顺序。

**6. 命名不误导**
名字诚实反映单位 / 起点 / 含义:`timeout_ms` 而非 `timeout`、`is_disabled` 别和 `is_enabled` 混、把约定带进名字或类型。

**7. 边界用具体小例子验证**
off-by-one、空集、null、首尾元素——用一个**最小例子手算一遍**再下笔(盯 `<=` vs `<`、`count+1`、`start=0/1`、`len` vs 末位下标)。

**8. 错误路径显式**
不静默吞异常、不用魔法返回值掩盖失败;失败要可见、可判别,别让调用方拿到一个"看着正常"的错值。

## 交付纪律(给用户看的产物,不只是脑内)
引入 / 改动 表示、默认值、兜底、可空字段、排序 时,回复里**显式交代**:
- **这个值的约定**:含义 / 单位 / 起点 / 范围;
- **缺失映射成啥**,且为什么不会被误当合法值;
- **和谁保持一致**(消费方 / 其它产同概念的地方);
- 若加了 tiebreak / 改了排序:说明并列时按谁排、是否影响返回内容。

> 总纲:**动笔前先回答清楚「含义是什么、缺了怎么表示、从几 / 什么单位起、并列谁先、谁还在算同一个数、出错怎么暴露」——答不全,就别写。**

---
*一个典型触发(举例,非本质):给 1-based 的 `line_index` 用 `or 0` 兜 NULL——`0` 会被当成"第 0 / 第一行"。按本规范:先看字段是 `Optional`(允许 null)、再看消费方拿它当下标 → 应落 `None`,不传 `0`。任何"缺失兜底 / 下标 / 排序 / 单位"的场景同理。*
