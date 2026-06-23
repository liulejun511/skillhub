"""skillhub CLI：参数解析与命令分发（创作/CI 侧工具）。

只保留 hub 在 git 树上做校验/质量/格式的命令；安装与运行时由 Claude Code 原生
plugin marketplace 承担，不在本包内。
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


def _resolve_skill_dir(name):
    return paths.find_skill(name)


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
        targets = _iter_skill_dirs(*paths.skill_roots())
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


def cmd_migrate(args) -> int:
    from memoket.migrate import migrate_all

    migrated = migrate_all()
    print(f"已迁移 {len(migrated)} 个技能" + ("：" + ", ".join(migrated) if migrated else ""))
    return 0


def cmd_audit(args) -> int:
    from memoket.audit import aggregate_validate

    report = aggregate_validate(adapters=args.adapter or [])
    if not report:
        print("聚合校验通过：通用层 + 适配器层 + 隐私回归。")
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
        from memoket.quality import assemble_review_request

        req = assemble_review_request()
        print(f"已组装质量审查请求: {req}\n请让 Claude 加载 quality-review 技能执行它。")
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
    print(f"\n（确定性体检；1-5 三维打分由 agent 按 quality-review 写入，低于 {QUALITY_FLOOR} 进 digest）")
    return 1 if flagged else 0


def cmd_gate(args) -> int:
    from memoket import ci

    if args.path:
        dirs = [Path(p) for p in args.path]
    else:
        dirs = ci.discover_skills()
    if not dirs:
        print("没有可过闸的技能。")
        return 0
    report = ci.gate_skills(dirs)
    print(ci.format_report(report))
    return 0 if report["ok"] else 1


def cmd_marketplace_check(args) -> int:
    from memoket.marketplace import validate_marketplace_file

    any_bad = False
    for path in args.path:
        errors = validate_marketplace_file(path)
        if errors:
            any_bad = True
            print(f"[FAIL] {path}")
            for e in errors:
                print(f"    {e}")
        else:
            print(f"[OK] {path}")
    return 1 if any_bad else 0


def cmd_promote(args) -> int:
    from memoket.promote import promote_skill

    r = promote_skill(args.name, args.sha, repo=args.repo)
    print(f"已晋级 {r['skill']} → 独立插件 {r['plugin_dir']}（status=active；源钉 SHA {r['sha'][:12]}…）")
    print("这只是改了工作区；请提一个晋级 PR 并由维护者人工 review 后合入（绝不自动晋级）。")
    return 0


def cmd_submit(args) -> int:
    from memoket.submit import submit_skill

    r = submit_skill(args.name)
    rep = r["report"]
    print(f"已放入 sandbox: {r['dst']}")
    for w in rep["warns"]:
        print(f"  ⚠ {w}（warn，人审时看）")
    if rep["ok"]:
        print("✓ 过闸通过，可以投稿了。下一步：")
        print('  git add sandbox/ && git commit -m "add skill" && git push  → 再开 PR（自己的仓直接 push 即可）')
        return 0
    print("✗ 过闸未过，先修这些再投：")
    for b in rep["blocks"]:
        print(f"    - {b}")
    return 1


def cmd_catalog(args) -> int:
    from memoket.catalog import write_catalog

    out = write_catalog()
    print(f"已生成技能目录: {out}")
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


# 命令名 -> handler
_IMPLEMENTED = {
    "new": cmd_new,
    "validate": cmd_validate,
    "build": cmd_build,
    "migrate": cmd_migrate,
    "audit": cmd_audit,
    "quality": cmd_quality,
    "gate": cmd_gate,
    "marketplace-check": cmd_marketplace_check,
    "promote": cmd_promote,
    "submit": cmd_submit,
    "catalog": cmd_catalog,
    "archive": cmd_archive,
    "restore": cmd_restore,
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="skillhub",
        description="skillhub 技能校验/质量/格式工具（创作 + CI 侧）",
    )
    parser.add_argument("--version", action="store_true", help="打印版本并退出")
    sub = parser.add_subparsers(dest="command", metavar="<command>")

    p_new = sub.add_parser("new", help="脚手架：生成空技能")
    p_new.add_argument("name", help="技能名（kebab-case）")

    p_val = sub.add_parser("validate", help="两层校验：通用层 + 适配器层")
    p_val.add_argument("path", nargs="?", help="技能路径；省略则校验全部技能")
    p_val.add_argument("--adapter", action="append", help="附加校验某适配器层，可多次")

    p_build = sub.add_parser("build", help="适配器构建到目标运行时形态")
    p_build.add_argument("path", help="技能路径")
    p_build.add_argument("--adapter", default="claude-code", help="目标适配器（默认 claude-code）")

    sub.add_parser("migrate", help="按当前格式契约迁移存量技能")

    p_audit = sub.add_parser("audit", help="聚合校验（通用 + 适配器 + 隐私回归）")
    p_audit.add_argument("--adapter", action="append", help="附加校验某适配器层")

    p_q = sub.add_parser("quality", help="技能内容质量：show 体检 / review 唤起 agent 打分 / set 回写分 / load 读回")
    p_q.add_argument("action", nargs="?", choices=["show", "review", "set", "load"], default="show")
    p_q.add_argument("name", nargs="?", help="set 时的技能名（load 时为可选文件路径）")
    p_q.add_argument("reusable", nargs="?", type=int, help="set 时 可复用 1-5")
    p_q.add_argument("actionable", nargs="?", type=int, help="set 时 可执行 1-5")
    p_q.add_argument("boundary", nargs="?", type=int, help="set 时 边界 1-5")
    p_q.add_argument("--note", help="set 时一句话评语")

    p_gate = sub.add_parser("gate", help="CI 自动闸（fail-closed）：L0+L1+能力分级，任一 block 退出 1")
    p_gate.add_argument("path", nargs="*", help="技能路径，可多个；省略则过闸全部 sandbox+curated 技能")

    p_mc = sub.add_parser("marketplace-check", help="校验 marketplace.json 结构")
    p_mc.add_argument("path", nargs="+", help="一个或多个 marketplace.json 路径")

    p_prom = sub.add_parser("promote", help="晋级 sandbox 技能成 curated 独立插件（移树 + 置 active + 源钉 SHA）")
    p_prom.add_argument("name", help="sandbox 技能名")
    p_prom.add_argument("--sha", required=True, help="curated 源要钉的 40 位 commit SHA")
    p_prom.add_argument("--repo", required=True, help="github 源 owner/repo，如 liulejun511/skillhub")

    p_sub = sub.add_parser("submit", help="一键投稿：把现成技能放进 sandbox 并过闸")
    p_sub.add_argument("name", help="技能名（~/.claude/skills/ 下）或技能目录路径")

    sub.add_parser("catalog", help="生成 CATALOG.md（所有技能描述一页浏览）")

    p_arch = sub.add_parser("archive", help="归档技能（不删除，可恢复）")
    p_arch.add_argument("name", help="技能名")
    p_rest = sub.add_parser("restore", help="从 archive 恢复技能")
    p_rest.add_argument("name", help="技能名")

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
    return handler(args)
