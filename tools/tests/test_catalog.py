"""catalog 生成：覆盖真实策展技能,带名字+描述,且 sandbox 区不报错。"""
from memoket import catalog


def test_render_lists_curated_seeds():
    text = catalog.render()
    for name in ("pr-description-craft", "psql-field-diagnostics", "evidence-before-adoption"):
        assert name in text, f"目录缺少 {name}"
    assert "Curated" in text and "Pending" in text


def test_collect_carries_description():
    rows = {r["name"]: r for r in catalog.collect()}
    assert "pr-description-craft" in rows
    # 描述被压成单行且非空(可视化要点)
    desc = rows["pr-description-craft"]["description"]
    assert desc and "\n" not in desc


def test_render_is_deterministic():
    assert catalog.render() == catalog.render()
