"""marketplace.json 校验：真实 curated catalog 合法；缺字段/坏 sha 被拒。"""
from memoket import paths
from memoket.marketplace import iter_marketplace_errors, validate_marketplace_file


def test_curated_marketplace_valid():
    errs = validate_marketplace_file(paths.workspace() / ".claude-plugin" / "marketplace.json")
    assert errs == [], errs


def test_missing_required_fields_rejected():
    assert iter_marketplace_errors({"name": "x"})  # 缺 owner/plugins


def test_plugin_missing_source_rejected():
    bad = {"name": "skillhub", "owner": {"name": "x"}, "plugins": [{"name": "p"}]}
    assert iter_marketplace_errors(bad)


def test_bad_sha_rejected():
    bad = {
        "name": "skillhub", "owner": {"name": "x"},
        "plugins": [{"name": "p", "source": {"source": "github", "sha": "not-a-sha"}}],
    }
    assert iter_marketplace_errors(bad)


def test_good_github_sha_ok():
    good = {
        "name": "skillhub", "owner": {"name": "x"},
        "plugins": [{"name": "p", "source": {"source": "github", "repo": "o/r",
                                              "sha": "0123456789abcdef0123456789abcdef01234567"}}],
    }
    assert iter_marketplace_errors(good) == []
