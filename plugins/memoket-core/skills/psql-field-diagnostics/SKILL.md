---
name: psql-field-diagnostics
description: >-
  用于在 psql 里手工排查 PostgreSQL 数据/性能问题：看表结构、类型转换报错、ILIKE 慢查询、
  读 EXPLAIN、只读安全习惯。一份排障时不再卡语法的现场工具箱。Use when hand-investigating data or perf issues in psql.
version: 0.1.0
format_version: 1
status: draft
origin: distilled
author: liulejun
tags: [postgresql, sql, debugging, gap-fill]
---

# psql 现场诊断工具箱

## 为何优秀 / 有益
补足型技能：排障时经常要直连 psql 查数据，但 psql 元命令、类型规则、性能判读这些「现场技能」不熟会反复卡壳（拼写、类型不匹配、`\x` 用法、不知道为什么慢）。把高频招式固化成一张随手可查的卡，让注意力留给问题本身而不是语法。

## 任务 (Task)
用 psql 高效完成一次数据/性能排查：看结构 → 查数据 → 判性能 → 全程只读安全。

## 判断重点 (Judgment focus)
- **看结构**：`\d 表名`（列+索引）、`\dt`（列表）、`\x on` 单独一行执行（宽行竖排）、`\pset pager off`（关分页）。
- **类型错误指纹**：`operator does not exist: text = bigint` → 列是 text，值要加引号 `tenant_id = '123'`；psql 元命令和 SQL 不能写在同一行。
- **为什么慢**：`ILIKE '%x%'` 前置通配符 = 全表扫描，必慢；判读用 `EXPLAIN (ANALYZE, BUFFERS)`，看 `Seq Scan`（全扫）还是 `Index Scan`，看 `Execution Time` 而非 cost。
- **慢的出路**（按代价排序）：限定扫描范围（按租户/时间先过滤）→ trigram/GIN 索引 → 预计算字段（如行号物化）→ 全文检索。
- **排序与分页**：要「最新在前」明确 `ORDER BY ... DESC`；大偏移分页慢，优先 keyset（记上一页边界值）。

## 可复制命令块 (Copy-paste)
```sql
-- 只读 + 关分页 + 宽行竖排（每条单独一行执行）
SET default_transaction_read_only = on;
\pset pager off
\x on

-- 看结构
\d 表名

-- 判性能：看 Seq Scan / Index Scan 与 Execution Time（非 cost）
EXPLAIN (ANALYZE, BUFFERS)
SELECT ... FROM 表 WHERE tenant_id = '租户' AND col ILIKE '%关键词%';

-- 先限范围再放开（避免一上来全表）
SELECT ... WHERE tenant_id = '租户' ORDER BY id DESC LIMIT 5;
```
```bash
# 命令行连库（确认环境后再连），随手查只读
PGOPTIONS='-c default_transaction_read_only=on' \
  psql 'postgresql://user@host:5432/db' -c "SELECT count(*) FROM 表 WHERE tenant_id='租户';"
```

## 规则 (Rules)
- 诊断会话默认只读：`SET default_transaction_read_only = on` 或只发 SELECT；连库前确认连的是哪个环境。
- 性能结论必须出自 EXPLAIN ANALYZE 真实输出，不靠感觉。
- 查询先在小范围验证语法（LIMIT 5），再放开跑。
- 复杂 SQL 写进文件保存，别在终端里现敲长查询。

## 不适用 (Not for)
- **生产写操作 / DDL**：本技能是只读诊断，迁移、加索引等改库动作走变更流程，不在此列。
- **应用层 ORM 性能**：问题在代码侧 N+1、连接池时，先看应用，不是闷头调 SQL。
- **非 PostgreSQL**：MySQL/SQLite 的元命令与执行计划读法不同，别照搬 `\d`/`EXPLAIN ANALYZE` 格式。

## 输出 / 行动结构 (Output / Action)
1. **环境确认** — 连的哪个库、只读与否。
2. **结构速览** — 涉及表的关键列与索引。
3. **诊断查询 + 证据** — SQL 与 EXPLAIN 关键行。
4. **结论与出路** — 慢/错在哪一层，按代价给改进选项。
