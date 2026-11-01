"""Generated resident-rules file for Codex and Pi (ticket 1413).

The generator reads the resident definition from resident_census, drops
claude-code.md, strips HTML comments. Every write targets a temp HOME.
"""

import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

import runtime_rules as rr  # noqa: E402
import resident_census as rc  # noqa: E402


def _lifecycle():
    spec = importlib.util.spec_from_file_location("lifecycle_rr", REPO / "adapters" / "lifecycle.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_build_has_resident_rules_without_claude_code_or_comments():
    out = rr.build(REPO / "rules")
    assert "# Workflow" in out and "# Git Discipline" in out and "# Guards" in out
    assert "# Claude Code idiosyncrasies" not in out
    assert "<!--" not in out and "-->" not in out
    assert "last-reviewed" not in out


def test_build_covers_exactly_the_resident_set(tmp_path):
    rules = tmp_path / "rules"
    rules.mkdir()
    (rules / "a.md").write_text("# A\n<!-- hidden -->\nbody a\n")
    (rules / "claude-code.md").write_text("# CC\nccbody\n")
    (rules / "cond.md").write_text("---\npaths: ['**/*.tex']\n---\ncondbody\n")
    out = rr.build(rules)
    assert "body a" in out and "hidden" not in out
    assert "ccbody" not in out and "condbody" not in out
    assert out.startswith(rr.MARKER)


def test_real_resident_set_matches_census():
    names = {p.name for p in rr.resident(REPO / "rules")}
    census = {p.name for p in (REPO / "rules").rglob("*.md") if rc.is_auto_loaded(p)}
    assert names == census - {"claude-code.md"}


def test_write_creates_updates_and_refuses_hand_written(tmp_path):
    rules = tmp_path / "rules"
    rules.mkdir()
    (rules / "a.md").write_text("one\n")
    dest = tmp_path / "home" / ".codex" / "AGENTS.md"
    assert rr.write(rules, dest) == "skipped"  # runtime dir absent
    dest.parent.mkdir(parents=True)
    assert rr.write(rules, dest) == "written"
    assert rr.write(rules, dest) == "unchanged"
    (rules / "a.md").write_text("two\n")
    assert rr.write(rules, dest) == "written" and "two" in dest.read_text()
    dest.write_text("my own notes\n")
    assert rr.write(rules, dest) == "refused"
    assert dest.read_text() == "my own notes\n"


def test_installer_step_rebuilds_for_codex_and_pi(tmp_path, monkeypatch):
    home = tmp_path / "home"
    (home / ".codex").mkdir(parents=True)
    (home / ".pi" / "agent").mkdir(parents=True)
    monkeypatch.setenv("HOME", str(home))
    lc = _lifecycle()
    assert lc.install_runtime_rules() == 0
    want = rr.build(REPO / "rules")
    assert (home / ".codex" / "AGENTS.md").read_text() == want
    assert (home / ".pi" / "agent" / "AGENTS.md").read_text() == want
    (home / ".codex" / "AGENTS.md").write_text("stale\n")  # hand edit: refused, not clobbered
    assert lc.install_runtime_rules() == 1
    assert (home / ".codex" / "AGENTS.md").read_text() == "stale\n"
