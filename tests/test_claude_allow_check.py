"""Read-only allow-rule check (ticket 1331): present, missing, unreadable."""

import importlib.util
import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.adherence

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "claude-allow-check.py"
spec = importlib.util.spec_from_file_location("claude_allow_check", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def _write(tmp_path, obj):
    p = tmp_path / "settings.json"
    p.write_text(json.dumps(obj))
    return p


def test_all_present(tmp_path):
    p = _write(tmp_path, {"permissions": {"allow": ["Bash", *mod.REQUIRED]}})
    before = p.read_text()
    assert mod.check(p) == (0, [])
    assert p.read_text() == before


def test_missing_listed(tmp_path):
    p = _write(tmp_path, {"permissions": {"allow": [mod.REQUIRED[0]]}})
    code, missing = mod.check(p)
    assert code == 1 and missing == list(mod.REQUIRED[1:])


def test_no_permissions_block_is_missing_not_unreadable(tmp_path):
    assert mod.check(_write(tmp_path, {}))[0] == 1


@pytest.mark.parametrize("content", [None, "{not json", "[]", '{"permissions": {"allow": "x"}}'])
def test_unreadable_is_distinct(tmp_path, content):
    p = tmp_path / "settings.json"
    if content is not None:
        p.write_text(content)
    assert mod.check(p) == (2, [])
