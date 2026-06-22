"""注入扫描：红队语料每个坏样本须命中预期档位/类型，干净样本与真实种子零误报。

这是注入扫描器的回归守卫——改 _PATTERNS 时不许漏掉已知坏样本。
"""
from pathlib import Path

from memoket import paths
from memoket.injection_scan import scan_skill, has_block

FIXTURES = Path(__file__).resolve().parent / "fixtures"
MALICIOUS = FIXTURES / "malicious"


def _types(findings):
    return {f["type"] for f in findings}


def test_injection_override_blocks():
    findings = scan_skill(MALICIOUS / "injection-override")
    assert has_block(findings), findings
    assert "injection_override" in _types(findings)
    assert "system_prompt_leak" in _types(findings)


def test_exfil_url_blocks():
    findings = scan_skill(MALICIOUS / "exfil-url")
    assert has_block(findings), findings
    assert "exfil_network" in _types(findings)


def test_chinese_injection_blocks():
    findings = scan_skill(MALICIOUS / "chinese-injection")
    assert has_block(findings), findings
    assert "injection_override_zh" in _types(findings)


def test_credential_read_warns_not_blocks():
    findings = scan_skill(MALICIOUS / "cred-read")
    assert not has_block(findings), findings  # 读凭证可疑但可能合法 -> 仅 warn
    assert "credential_read" in _types(findings)


def test_base64_blob_warns():
    findings = scan_skill(MALICIOUS / "base64-blob")
    assert "base64_blob" in _types(findings), findings


def test_payload_hidden_in_reference_is_caught():
    findings = scan_skill(MALICIOUS / "reference-hidden")
    assert has_block(findings), findings
    blocked_files = {f["file"] for f in findings if f["severity"] == "block"}
    assert any("notes.md" in f for f in blocked_files), blocked_files


def test_clean_fixture_no_findings():
    findings = scan_skill(FIXTURES / "clean" / "clean-docs-ref")
    assert findings == [], findings


def test_real_seeds_no_false_block():
    """真实策展种子绝不能因扫描器误报被 block（false-positive 回归守卫）。"""
    curated = paths.curated_dir()
    seed_dirs = [md.parent for md in curated.rglob("SKILL.md")]
    assert seed_dirs, "未找到策展种子，检查 paths.curated_dir()"
    for d in seed_dirs:
        findings = scan_skill(d)
        assert not has_block(findings), (str(d), findings)
