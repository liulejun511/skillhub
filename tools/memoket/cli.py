"""memoket CLI：参数解析与命令分发。

确定性机械层的命令在此落地；尚未实现的命令打印提示并退出 2。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List

from memoket import __version__, paths
from memoket.skill import SKILL_ENTRY


# ───────────────────────── helpers ─────────────────────────

def _iter_skill_dirs(*roots: Path) -> List[Path]:
    found: List[Path] = []
    for root in roots:
        if root.exists():
            for md in sorted(root.rglob(SKILL_ENTRY)):
                found.append(md.parent)
    return found


def _print_validation(label: str, result) -> bool:
    """打印一个技能的校验结果，返回是否有问题。"""
    from memoket.validate import has_issues

    bad = has_issues(result)
    status = "FAIL" if bad else "OK"
    print(f"[{status}] {label}")
    if bad:
        for layer, issues in result.items():
            for issue in issues:
                print(f"    {layer}: {issue}")
    return bad


# ───────────────────────── commands ─────────────────────────

def cmd_new(args) -> int:
    from memoket.scaffold import new_skill

    path = new_skill(args.name)
    print(f"已创建技能脚手架: {path}")
    return 0


def cmd_validate(args) -> int:
    from memoket.validate import validate_skill

    if args.path:
        targets = [Path(args.path)]
    else:
        targets = _iter_skill_dirs(paths.vault(), paths.skills_dir())
    if not targets:
        print("没有可校验的技能。")
        return 0

    any_bad = False
    for target in targets:
        result = validate_skill(target, adapters=args.adapter or [])
        any_bad |= _print_validation(str(target), result)
    return 1 if any_bad else 0


def cmd_build(args) -> int:
    from memoket.build import build_skill

    out = build_skill(args.path, args.adapter)
    print(f"已构建到: {out}")
    return 0


def cmd_search(args) -> int:
    from memoket.registry import search_registry

    results = search_registry(args.keyword or "")
    if not results:
        print("无匹配技能。")
        return 0
    for e in results:
        tags = ", ".join(e.get("tags", []))
        print(f"{e['name']}  v{e['version']}  [{tags}]\n    {e['description']}")
    return 0


def cmd_install(args) -> int:
    from memoket.install import install_skill

    target = install_skill(args.name)
    print(f"已安装（quarantine 隔离中，审阅后用 `memoket trust {args.name}` 激活）: {target}")
    return 0


def cmd_trust(args) -> int:
    from memoket.install import trust_skill

    entry = trust_skill(args.name, allow_scripts=args.allow_scripts)
    extra = "，已授权脚本执行" if entry.get("scripts_allowed") else ""
    print(f"已激活: {args.name}{extra}")
    return 0


def cmd_update(args) -> int:
    from memoket.install import update_skill

    outcome = update_skill(args.name)
    msg = {"updated": "已更新", "skip": "已是最新，跳过", "local-newer": "本地版本更新，跳过"}
    print(f"{args.name}: {msg.get(outcome, outcome)}")
    return 0


def cmd_fork(args) -> int:
    from memoket.install import fork_installed

    dst = fork_installed(args.name)
    print(f"已 fork 到: {dst}（已脱离 upstream，后续 update 不影响）")
    return 0


def cmd_distill(args) -> int:
    from memoket.distill import assemble_distill_request

    req = assemble_distill_request(args.material, args.name)
    print(f"已组装提炼请求: {req}\n请让 Claude Code 执行它（加载 skills/distill）。")
    return 0


def cmd_evolve(args) -> int:
    from memoket.distill import assemble_evolve_request

    req = assemble_evolve_request(args.skill, args.material)
    print(f"已组装精炼请求: {req}\n请让 Claude Code 执行它（加载 skills/evolve）。")
    return 0


def cmd_ingest(args) -> int:
    from memoket.ingest import ingest

    staged = ingest(args.user, since=args.since, source=args.source,
                    from_path=getattr(args, "from_path", None))
    if not staged:
        print("无新素材（用 `memoket connectors` 查看可用素材源及其配置）。")
        return 0
    print(f"已拉取 {len(staged)} 条素材到 .work/：")
    for p in staged:
        print(f"  {p.name}")
    return 0


def cmd_mcp(args) -> int:
    from memoket.mcp_server import serve

    return serve()


def cmd_connectors(args) -> int:
    from memoket.connectors import available, get_connector

    print("素材源连接器（--source 或 MEMOKET_SOURCE 选择）：")
    for name in available():
        conn = get_connector(name)
        try:
            ok = conn.test()
        except Exception:
            ok = False
        status = "可用" if ok else "未配置/不可达"
        print(f"  {name:14s} [{status}]")
    from memoket.adapters import available as adapters_available

    print("运行时适配器（build --adapter 选择）：")
    for name in adapters_available():
        print(f"  {name}")
    return 0


def cmd_cycle(args) -> int:
    import datetime as _dt

    from memoket import cycle

    now = _dt.datetime.now(_dt.timezone.utc).isoformat()
    if args.finalize:
        summ = cycle.finalize(args.user, now)
        print(f"轨道完成。技能 {len(summ['skills'])} 个：{', '.join(summ['skills']) or '（无）'}")
        if summ["validation_fail"]:
            print("校验未过（未推进水位）：")
            for d, issues in summ["validation_fail"].items():
                print(f"  [FAIL] {d}")
                for i in issues:
                    print(f"      {i}")
            return 1
        if summ["redaction_flags"]:
            print("脱敏告警（draft 阶段仅提示，publish 时阻断）：")
            for name, n in summ["redaction_flags"].items():
                print(f"  {name}: {n} 处疑似 PII/机密")
        print(f"水位已推进: {summ['watermark_advanced']}")
        print("\n" + summ["report"])
        return 0

    staged = cycle.stage(args.user, since=args.since, source=args.source,
                         from_path=getattr(args, "from_path", None))
    if not staged:
        print("无新素材（用 `memoket connectors` 查看可用素材源及其配置）。")
        return 0
    print(f"已拉取 {len(staged)} 条素材到 .work/（工具拉取，read-only）：")
    for p in staged:
        print(f"  {p.name}")
    print(
        "\n下一步（智能步骤）：让 agent 加载 `skills/triage` + `skills/distill`，"
        "对上面素材做分诊与提炼，把草稿写入 vault/mine/。\n"
        f"完成后运行：memoket cycle --user {args.user} --finalize"
    )
    return 0


def cmd_watermark(args) -> int:
    from memoket import watermark

    if args.action == "set":
        watermark.advance(args.value, user_id=args.user)
        print(f"水位已设为: {args.value}")
    else:
        print(f"当前水位: {watermark.get_last_processed() or '（无）'}")
    return 0


def cmd_report(args) -> int:
    from memoket.report import report

    print(report())
    return 0


def cmd_dashboard(args) -> int:
    from memoket import dashboard

    print(dashboard.render_text())
    return 0


def cmd_triggers_report(args) -> int:
    import datetime as _dt

    from memoket import dashboard

    delta = dashboard.daily_delta(save=not args.no_save)
    label = _dt.datetime.now().strftime("%Y-%m-%d")
    text = dashboard.render_daily_report(label, delta)
    print(text)
    if args.feishu:
        from memoket.feishu_notify import notify
        try:
            notify(text, user=args.feishu_user, email=args.feishu_email)
            print("\n[已通过飞书机器人发送]")
        except Exception as exc:
            print(f"\n[飞书发送失败] {exc}", file=sys.stderr)
            return 1
    return 0


def cmd_archive(args) -> int:
    from memoket.lifecycle import archive_skill

    dst = archive_skill(args.name)
    print(f"已归档（未删除，可 restore）: {dst}")
    return 0


def cmd_restore(args) -> int:
    from memoket.lifecycle import restore_skill

    dst = restore_skill(args.name)
    print(f"已恢复到: {dst}")
    return 0


def cmd_garden(args) -> int:
    from memoket.garden import health_report, coverage_diagnosis

    if getattr(args, "action", "show") == "run":
        from memoket.garden import assemble_garden_request, apply_proposals
        from memoket.driver import drive_headless, is_headless_available

        req = assemble_garden_request()
        print(f"已组装园艺请求: {req}")
        if args.drive and is_headless_available():
            prompt = ("你在 memoket-skills 仓库根目录。严格按下面这份请求执行："
                      "加载并遵循 skills/garden/SKILL.md，产出园艺提案，"
                      "用 Write 工具写成 garden-proposals.json（格式见请求）。\n\n")
            prompt += req.read_text(encoding="utf-8")
            ok, out = drive_headless(prompt, cwd=paths.workspace(), timeout=600)
            print(f"headless 园艺 ok={ok}")
        result = apply_proposals()
        print(f"自动执行（归档，可逆）: {len(result['applied'])} 项")
        for a in result["applied"]:
            print(f"  archive {a['skill']} — {a['reason'][:50]}")
        if result["proposals"]:
            print(f"待你确认的提案（merge/split，需改内容）: {len(result['proposals'])} 项")
            for pr in result["proposals"]:
                print(f"  {pr.get('action')} {pr.get('targets')} -> {pr.get('into','')} — {pr.get('reason','')[:50]}")
        return 0

    rep = health_report(soft_cap=args.soft_cap)
    print(f"技能总数: {rep['total']}  陈旧: {len(rep['stale'])}  陈旧占比: {rep['stale_ratio']}")
    if rep["stale"]:
        print("  陈旧候选: " + ", ".join(rep["stale"]))
    cov = coverage_diagnosis()
    print(f"覆盖象限: {cov['domains']} 个  最大象限占比: {cov['skew']}" +
          ("  <- 扎堆（建议补其它象限）" if cov["skewed"] else ""))
    for dom, names in sorted(cov["buckets"].items(), key=lambda x: -len(x[1])):
        print(f"  {dom}: {len(names)}  ({', '.join(names)})")
    print(f"是否建议园艺: {'是' if rep['should_garden'] or cov['skewed'] else '否'}（智能合并/拆分/打回请执行 skills/garden）")
    return 0


def cmd_signals(args) -> int:
    from memoket.signals import read_signals

    sigs = read_signals()
    if not sigs:
        print("暂无信号。")
        return 0
    from collections import Counter

    counts = Counter(s["kind"] for s in sigs)
    for kind, n in counts.most_common():
        print(f"{kind}: {n}")
    return 0


def cmd_eval(args) -> int:
    from memoket import evals

    action = getattr(args, "action", "list") or "list"
    if action == "list":
        cases = evals.load_cases()
        print(f"评测集用例数: {len(cases)}")
        for c in cases:
            print(f"  {c['name']}: 期望 {c['expected_verdict']}")
        return 0
    if action == "score":
        scores = evals.score_current()
        passed = sum(1 for v in scores.values() if v)
        print(f"评测打分: {passed}/{len(scores)} 通过")
        for name, ok in scores.items():
            print(f"  [{'OK' if ok else 'FAIL'}] {name}")
        return 0 if passed == len(scores) else 1
    if action == "baseline":
        scores = evals.set_baseline()
        print(f"已锁基线: {sum(1 for v in scores.values() if v)}/{len(scores)} 通过")
        return 0
    if action == "check":
        reg = evals.check_against_baseline()
        if reg["ok"]:
            print(f"评测无退化（{reg['before_pass']} → {reg['after_pass']}）{reg.get('note', '')}")
            return 0
        print(f"评测退化，拒绝：退化用例 {reg['regressions']}；{reg['before_pass']} → {reg['after_pass']}")
        return 1
    return 0


def _resolve_skill_dir(name):
    for base in (paths.vault_mine(), paths.vault_installed()):
        d = base / name
        if (d / "SKILL.md").exists():
            return d
    return None


def cmd_publish(args) -> int:
    from memoket.publish import publish_skill

    entry = publish_skill(args.name)
    print(f"已发布到 registry: {entry['name']} v{entry['version']}")
    return 0


def cmd_use(args) -> int:
    import datetime as _dt

    from memoket.lifecycle import record_use

    d = _resolve_skill_dir(args.name)
    if d is None:
        print(f"找不到技能: {args.name}", file=sys.stderr)
        return 1
    rec = record_use(d, _dt.datetime.now(_dt.timezone.utc).isoformat())
    print(f"已记录用量: {args.name}（used_count={rec['used_count']}）")
    return 0


def cmd_profile(args) -> int:
    from memoket.profile import ensure_profile

    p = ensure_profile()
    print(f"价值档案: {p}")
    return 0


def cmd_index(args) -> int:
    from memoket import index

    if args.near:
        for name, score in index.nearest(args.near, k=args.k):
            print(f"{score:.3f}  {name}")
    else:
        idx = index.build_index()
        print(f"已建索引，技能数: {len(idx)}")
    return 0


def cmd_migrate(args) -> int:
    from memoket.migrate import migrate_all

    migrated = migrate_all()
    print(f"已迁移 {len(migrated)} 个技能" + ("：" + ", ".join(migrated) if migrated else ""))
    return 0


def cmd_audit(args) -> int:
    from memoket.audit import aggregate_validate

    report = aggregate_validate(adapters=args.adapter or [])
    if not report:
        print("聚合校验通过：通用层 + 适配器层 + 个人库一致性 + 隐私回归。")
        return 0
    print("聚合校验失败：")
    for target, issues in report.items():
        print(f"[FAIL] {target}")
        for issue in issues:
            print(f"    {issue}")
    return 1


def cmd_quality(args) -> int:
    from memoket.quality import review_all, save_quality, QUALITY_FLOOR

    action = getattr(args, "action", "show") or "show"

    if action == "set":
        d = _resolve_skill_dir(args.name)
        if d is None:
            print(f"找不到技能: {args.name}", file=sys.stderr)
            return 1
        q = save_quality(d, args.reusable, args.actionable, args.boundary, note=args.note or "")
        print(f"已写入 {args.name} 质量分：均分 {q['avg']}")
        return 0

    if action == "review":
        from memoket.quality import assemble_review_request, load_scores
        from memoket.driver import drive_headless, is_headless_available

        req = assemble_review_request()
        print(f"已组装质量审查请求: {req}")
        if args.drive and is_headless_available():
            prompt = ("你在 memoket-skills 仓库根目录。严格按下面这份请求执行："
                      "加载并遵循 skills/quality-review/SKILL.md，对每个技能三维打分，"
                      "并用 Write 工具把结果写成 quality-scores.json（格式见请求）。\n\n")
            prompt += req.read_text(encoding="utf-8")
            ok, out = drive_headless(prompt, cwd=paths.workspace(), timeout=600)
            print(f"headless 审查 ok={ok}")
            n = load_scores()
            print(f"已回写 {n} 个技能的质量分。")
        else:
            print("请让 Claude 执行它（加载 skills/quality-review），或加 --drive 自动唤起 headless。")
        return 0

    if action == "load":
        from memoket.quality import load_scores
        n = load_scores(args.name)  # name 复用为可选文件路径
        print(f"已从 scores 文件回写 {n} 个技能的质量分。")
        return 0

    # 默认 show：体检报告
    report = review_all()
    flagged = {n: r for n, r in report.items() if r["flags"] or r["below_floor"]}
    print(f"技能质量体检：{len(report)} 个，{len(flagged)} 个有待改进")
    for name, r in report.items():
        q = r["quality"]
        qs = f"均分 {q['avg']}" if q else "未评分"
        mark = "  <- 待改进" if (r["flags"] or r["below_floor"]) else ""
        print(f"  [{qs}] {name}{mark}")
        for f in r["flags"]:
            print(f"      - {f}")
    print(f"\n（确定性体检；1-5 三维打分由 agent 按 skills/quality-review 写入，低于 {QUALITY_FLOOR} 进 digest）")
    return 1 if flagged else 0


def cmd_review(args) -> int:
    from memoket.review import list_review_branches, stale_review_branches

    branches = list_review_branches()
    if not branches:
        print("无 review 分支。")
        return 0
    stale = set(stale_review_branches(args.stale_days * 86400))
    for b in branches:
        flag = "  <- 超期未审阅" if b in stale else ""
        print(f"{b}{flag}")
    return 0


def _cmd_not_implemented(name, help_text):
    def _handler(args) -> int:
        print(f"memoket {name}: 尚未实现 — {help_text}", file=sys.stderr)
        return 2

    return _handler


# 命令名 -> (help, 是否已实现的 handler 或 None)
_IMPLEMENTED = {
    "new": cmd_new,
    "validate": cmd_validate,
    "build": cmd_build,
    "search": cmd_search,
    "install": cmd_install,
    "trust": cmd_trust,
    "update": cmd_update,
    "fork": cmd_fork,
    "distill": cmd_distill,
    "evolve": cmd_evolve,
    "ingest": cmd_ingest,
    "connectors": cmd_connectors,
    "mcp": cmd_mcp,
    "cycle": cmd_cycle,
    "watermark": cmd_watermark,
    "report": cmd_report,
    "archive": cmd_archive,
    "restore": cmd_restore,
    "garden": cmd_garden,
    "signals": cmd_signals,
    "dashboard": cmd_dashboard,
    "triggers-report": cmd_triggers_report,
    "eval": cmd_eval,
    "publish": cmd_publish,
    "use": cmd_use,
    "profile": cmd_profile,
    "index": cmd_index,
    "migrate": cmd_migrate,
    "audit": cmd_audit,
    "review": cmd_review,
    "quality": cmd_quality,
}

_PENDING = {}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="memoket",
        description="自演变的个人成长型技能工具（确定性机械层）",
    )
    parser.add_argument("--version", action="store_true", help="打印版本并退出")
    sub = parser.add_subparsers(dest="command", metavar="<command>")

    p_new = sub.add_parser("new", help="脚手架：生成空技能")
    p_new.add_argument("name", help="技能名（kebab-case）")

    p_val = sub.add_parser("validate", help="两层校验：通用层 + 适配器层")
    p_val.add_argument("path", nargs="?", help="技能路径；省略则校验 vault/ 与 skills/ 全部")
    p_val.add_argument("--adapter", action="append", help="附加校验某适配器层，可多次")

    p_build = sub.add_parser("build", help="适配器构建到目标运行时形态")
    p_build.add_argument("path", help="技能路径")
    p_build.add_argument("--adapter", default="claude-code", help="目标适配器（默认 claude-code）")

    p_search = sub.add_parser("search", help="查询 registry")
    p_search.add_argument("keyword", nargs="?", default="", help="关键词（省略列全部）")

    p_install = sub.add_parser("install", help="安装外部技能（落地即 quarantine）")
    p_install.add_argument("name", help="registry 中的技能名")

    p_trust = sub.add_parser("trust", help="审阅后激活 quarantine 技能")
    p_trust.add_argument("name", help="技能名")
    p_trust.add_argument("--allow-scripts", action="store_true", help="同时授权脚本执行")

    p_update = sub.add_parser("update", help="对照 registry 更新已安装技能")
    p_update.add_argument("name", help="技能名")

    p_fork = sub.add_parser("fork", help="把 installed 技能 fork 到 mine（编辑前）")
    p_fork.add_argument("name", help="技能名")

    p_distill = sub.add_parser("distill", help="组装提炼请求交给 Claude Code")
    p_distill.add_argument("material", help="素材文件路径（转写/上下文等）")
    p_distill.add_argument("--name", required=True, help="新技能名（kebab-case）")

    p_evolve = sub.add_parser("evolve", help="组装精炼请求交给 Claude Code")
    p_evolve.add_argument("skill", help="已有技能路径")
    p_evolve.add_argument("material", help="新素材文件路径")

    p_ingest = sub.add_parser("ingest", help="增量拉取素材到 .work/")
    p_ingest.add_argument("--user", required=True, help="用户 id")
    p_ingest.add_argument("--since", help="起始时间（ISO；省略则用水位）")
    p_ingest.add_argument("--source", help="素材源连接器名（省略则 MEMOKET_SOURCE/自动推断）")
    p_ingest.add_argument("--from", dest="from_path", help="一次性文本输入：文件或目录路径（优先于连接器，不走水位）")

    p_cycle = sub.add_parser("cycle", help="跑一轮演化循环（拉素材 → [agent 提炼] → 轨道收尾）")
    p_cycle.add_argument("--user", required=True, help="用户 id")
    p_cycle.add_argument("--since", help="起始时间（ISO；省略则用水位）")
    p_cycle.add_argument("--source", help="素材源连接器名（省略则 MEMOKET_SOURCE/自动推断）")
    p_cycle.add_argument("--from", dest="from_path", help="一次性文本输入：文件或目录路径（优先于连接器，不走水位）")
    p_cycle.add_argument("--finalize", action="store_true", help="提炼完成后跑轨道：校验/脱敏/水位/report")

    sub.add_parser("connectors", help="列出素材源连接器与运行时适配器及配置状态")
    sub.add_parser("mcp", help="启动 MCP server（stdio）：把 vault 技能暴露给任何 MCP 客户端")

    p_wm = sub.add_parser("watermark", help="查看/推进演化水位")
    p_wm.add_argument("action", nargs="?", choices=["show", "set"], default="show")
    p_wm.add_argument("value", nargs="?", help="set 时的时间戳")
    p_wm.add_argument("--user", help="set 时可同时记录 user_id")

    sub.add_parser("report", help="汇总本轮变更生成 digest")

    p_arch = sub.add_parser("archive", help="归档技能（不删除，可恢复）")
    p_arch.add_argument("name", help="技能名")
    p_rest = sub.add_parser("restore", help="从 archive 恢复技能")
    p_rest.add_argument("name", help="技能名")
    p_garden = sub.add_parser("garden", help="库健康/覆盖诊断（show）或跑园艺（run [--drive]）")
    p_garden.add_argument("action", nargs="?", choices=["show", "run"], default="show")
    p_garden.add_argument("--soft-cap", type=int, help="软上限，超过触发强制园艺")
    p_garden.add_argument("--drive", action="store_true", help="run 时自动唤起 headless Claude 产出提案")
    sub.add_parser("signals", help="查看已收集的优化信号统计")
    sub.add_parser("dashboard", help="技能触发板：哪些被触发用了、哪些没被触发")
    p_tr = sub.add_parser("triggers-report", help="今日触发增量日报（可推送飞书）")
    p_tr.add_argument("--feishu", action="store_true", help="通过飞书机器人发送")
    p_tr.add_argument("--feishu-user", help="收件人 open_id")
    p_tr.add_argument("--feishu-email", help="收件人邮箱（自动解析 open_id）")
    p_tr.add_argument("--no-save", action="store_true", help="不更新快照（测试用，不消耗当日增量）")
    p_eval = sub.add_parser("eval", help="评测闸：list/score/baseline/check")
    p_eval.add_argument("action", nargs="?", choices=["list", "score", "baseline", "check"],
                        default="list", help="list 列用例 / score 打分 / baseline 锁基线 / check 回归检查")

    p_pub = sub.add_parser("publish", help="发布 mine 技能到 registry（先过脱敏闸）")
    p_pub.add_argument("name", help="技能名")
    p_use = sub.add_parser("use", help="记录一次技能用量（适配器回写约定）")
    p_use.add_argument("name", help="技能名")
    sub.add_parser("profile", help="确保并显示用户价值档案路径")
    p_idx = sub.add_parser("index", help="构建技能检索索引 / 查近邻")
    p_idx.add_argument("--near", help="给定文本/技能名，查最相似技能")
    p_idx.add_argument("-k", type=int, default=5, help="返回 top-k")
    sub.add_parser("migrate", help="按当前格式契约迁移存量技能")
    p_audit = sub.add_parser("audit", help="聚合校验（通用+适配器+一致性+隐私回归）")
    p_audit.add_argument("--adapter", action="append", help="附加校验某适配器层")
    p_review = sub.add_parser("review", help="列出 review 分支（标注超期）")
    p_review.add_argument("--stale-days", type=int, default=7, help="超期阈值（天）")
    p_q = sub.add_parser("quality", help="技能内容质量：show 体检 / review 唤起 agent 打分 / set 回写分")
    p_q.add_argument("action", nargs="?", choices=["show", "review", "set", "load"], default="show")
    p_q.add_argument("name", nargs="?", help="set 时的技能名")
    p_q.add_argument("reusable", nargs="?", type=int, help="set 时 可复用 1-5")
    p_q.add_argument("actionable", nargs="?", type=int, help="set 时 可执行 1-5")
    p_q.add_argument("boundary", nargs="?", type=int, help="set 时 边界 1-5")
    p_q.add_argument("--note", help="set 时一句话评语")
    p_q.add_argument("--drive", action="store_true", help="review 时自动唤起 headless Claude")

    for name, help_text in _PENDING.items():
        sub.add_parser(name, help=help_text)
    return parser


def main(argv=None) -> int:
    # 根治 Windows GBK 控制台对中文/箭头/emoji 的 UnicodeEncodeError：统一 UTF-8 输出。
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.version:
        print(__version__)
        return 0
    if not args.command:
        parser.print_help()
        return 0

    handler = _IMPLEMENTED.get(args.command)
    if handler is None:
        return _cmd_not_implemented(args.command, _PENDING.get(args.command, ""))(args)
    return handler(args)
