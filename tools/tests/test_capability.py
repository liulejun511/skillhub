"""能力分级：Inert/Active 正负样本；自称 inert 却带代码目录须判 Active（=拒）。"""
from pathlib import Path

from memoket import paths
from memoket.classify import classify_skill, is_active

CAP = Path(__file__).resolve().parent / "fixtures" / "capability"


def test_inert_simple():
    assert classify_skill(CAP / "inert-simple")["capability"] == "inert"


def test_inert_with_reference_code_is_still_inert():
    # reference/ 下的代码示例是文档，不计为 Active 标记
    result = classify_skill(CAP / "inert-with-reference")
    assert result["capability"] == "inert", result


def test_active_scripts_is_active():
    result = classify_skill(CAP / "active-scripts")
    assert result["capability"] == "active", result
    assert "scripts/" in result["markers"]


def test_manifest_mismatch_claims_inert_but_active():
    # SKILL.md 自称 instructions-only，却带 scripts/ -> 结构判定 Active（不信声明）
    assert is_active(CAP / "active-scripts")


def test_active_mcp_is_active():
    result = classify_skill(CAP / "active-mcp")
    assert result["capability"] == "active", result
    assert ".mcp.json" in result["markers"]


def test_real_seeds_are_inert():
    curated = paths.curated_dir()
    seed_dirs = [md.parent for md in curated.rglob("SKILL.md")]
    assert seed_dirs
    for d in seed_dirs:
        assert not is_active(d), (str(d), classify_skill(d))
