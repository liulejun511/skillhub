# Skill Usage Analytics — Design

## 目标 / Goal

每天统计**各个 skill 的触发次数**,定时推给维护者,看清「哪个 skill 真有人用、哪个没人碰」,据此迭代(留/删/改/晋级)。

## 核心难点(先说清,免得建个采不到数的东西)

前面已反复确认:**原生安装的 skill,在 native 运行路径上不写任何 per-skill 用量**。Claude 的技能调度器不认识 skillhub,旧的 memoket MCP(会写 surfaced/used 计数)已删且是 opt-in。所以「触发次数」不能靠运行时埋点拿。

**但有一条可靠的事后信号**:Claude Code 把每次会话写成 transcript(`~/.claude/projects/**/*.jsonl`)。**一次 skill 触发 = 一条 `tool_use`、`name=="Skill"`、`input=={"skill":"<名>"}` 的记录**,带顶层 ISO `timestamp` 和唯一 `uuid`。实测可解析、可去重、不误判(只认 `name=="Skill"` 读 `input.skill`,不会把文件内容里的 `"name":"..."` 算进去)。

→ **采集 = 扫本地 transcript,数 Skill 调用。** 无需 hook、无需 MCP、无需遥测服务器。

## 架构

```
~/.claude/projects/**/*.jsonl
   │  扫描 + 过滤(name=="Skill")+ uuid 去重 + 本地时区按天分桶
   ▼
usage.counts_by_day()  →  {date: {skill: count}}
   │  + totals()、curated_skill_names()(标出「装了但没用」)
   ▼
usage.render_report(days=7)  →  纯文本报告
   │  notify.notify_feishu()(env 取密钥,未配则跳过)
   ▼
飞书消息 / stdout
   ▲
   │  每天定时(Windows 任务计划,本地跑 tools/usage-daily.py)
```

## 组件

- **`tools/memoket/usage.py`** — 解析与聚合(核心,纯本地、无依赖)。
  - `iter_invocations()`:扫 transcript,产出 `{skill,date,ts,uuid}`,uuid 去重。
  - `counts_by_day(days=N)`:`{date:{skill:count}}`,按本地时区分天,可限窗口。
  - `totals()` / `curated_skill_names()` / `render_report()`。
- **`tools/memoket/notify.py`** — 飞书推送(纯 urllib;`FEISHU_APP_ID/SECRET/TO_EMAIL` 从 env 读,**绝不入库**;未配齐返回 `(False, "...not set...")`,调用方跳过,不报错)。
- **CLI `memoket usage [--days N] [--feishu]`** — 任何用户都能看自己机器的 skill 用量。
- **`tools/usage-daily.py`** — 定时 runner(报告 + 推送),给任务计划调用。

## 范围(诚实划定)

- **本机用量**:统计的是**你这台机器**的 transcript = 你自己的 skill 使用。✅ 已实现、已在真机验证。
- **跨用户汇总**(「全社区哪个 skill 火」):是另一个 opt-in 难题——每个用户在自己机器跑同一套、自愿上报到某处汇总。**不在本版**;但本设计天然支持「人人本地可跑」,将来加一个自愿上报端点即可。

## 报告样式(实测真机输出)

```
Skill usage — last 7 day(s)

Most recent active day (2026-06-23):
     1  bug-trigger-analysis
Totals (last 7 day(s)):
    14  bug-trigger-analysis
     4  code-change-guardrails
     ...
Installed but unused (last 7d): evidence-before-adoption, pr-description-craft, ...
```

## 部署:每天自动推送

> Claude 云端定时(routine/cron)**读不到本地 transcript**,所以必须用**本地**调度。

1. 收件人:设 `FEISHU_TO_EMAIL`(你的飞书邮箱)。**App 凭据**优先读 `FEISHU_APP_ID/SECRET` env;读不到则**自动复用已配置的 lark/feishu MCP 的 `-a`/`-s`**(`~/.claude.json`)——已连飞书机器人的话啥都不用填。可选 `SKILLHUB_USAGE_DAYS`(默认 7)。
2. 建每日任务(Windows):
   ```
   schtasks /create /tn skillhub-usage /sc daily /st 09:00 ^
     /tr "python \"D:\capsoul\skillhub\tools\usage-daily.py\""
   ```
   (macOS/Linux:`0 9 * * * python /path/to/tools/usage-daily.py`)
3. 没配飞书也行——runner 会把报告打印出来(任务计划里可重定向到日志文件)。

## 注意 / Caveats

- **格式依赖**:transcript 的内部结构(`tool_use`/`name=="Skill"`/`input.skill`)是 Claude Code 内部格式,版本升级若变,解析需跟着调(已用最小假设、并加测试守卫)。
- **只数「触发」**:统计的是 skill 被调用次数,不含「被检索到但没用」(native 路径拿不到 surfaced)。
- **本地、隐私安全**:只抽取 skill 名 + 日期,不读会话内容、不外传(除非你显式配飞书推给自己)。

## 测试

`tools/tests/test_usage.py`:计数与合计、uuid 去重、忽略非 Skill 工具、按天窗口过滤、报告含技能名与「装了没用」、空 transcript。全过(随包 `run_all.py`)。

## 未来迭代

- 跨用户自愿汇总(opt-in 上报端点)。
- 趋势(周对比、上升/下降)、take-rate(若将来能拿到 surfaced)。
- 把「装了没用」喂回 catalog / 晋级决策(R3 双轴里的「质量轴」本地信号)。
