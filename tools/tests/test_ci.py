"""CI 自动闸：干净 Inert 过；注入/Active/脱敏命中拒；扫描器异常 fail-closed；真实种子过。"""
from pathlib import Path

from memoket import ci, paths

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def test_gate_clean_inert_passes():
    r = ci.gate_skill(FIXTURES / "capability" / "inert-simple")
    assert r["ok"], r


def test_gate_injection_blocks():
    r = ci.gate_skill(FIXTURES / "malicious" / "injection-override")
    assert not r["ok"]
    assert any("injection" in b for b in r["blocks"]), r["blocks"]


def test_gate_active_blocks():
    r = ci.gate_skill(FIXTURES / "capability" / "active-scripts")
    assert not r["ok"]
    assert any("capability" in b for b in r["blocks"]), r["blocks"]


def test_gate_redaction_blocks():
    r = ci.gate_skill(FIXTURES / "malicious" / "pii-leak")
    assert not r["ok"]
    assert any("redaction" in b for b in r["blocks"]), r["blocks"]


def test_fail_closed_on_missing_skill():
    # 不存在的目录（无 SKILL.md）-> 扫描器异常 -> block（无绿不合）
    r = ci.gate_skill(FIXTURES / "does-not-exist")
    assert not r["ok"]
    assert any("scanner_error" in b for b in r["blocks"]), r["blocks"]


def test_real_seeds_pass_gate():
    dirs = ci.discover_skills([paths.curated_dir()])
    assert dirs
    report = ci.gate_skills(dirs)
    assert report["ok"], report["blocked"]
