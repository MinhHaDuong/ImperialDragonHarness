"""Ticket 1520: one definition of the transcript roots, used by the archive and the audit's readers."""
import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import transcript_spool as spool  # noqa: E402


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def world(tmp_path, monkeypatch):
    for key, sub in (("CODEX_HOME", "codex"), ("PI_CODING_AGENT_DIR", "pi"), ("CLAUDE_CONFIG_DIR", "claude")):
        monkeypatch.setenv(key, str(tmp_path / sub))
    monkeypatch.setenv("IDH_ARCHIVE_ROOT", str(tmp_path / "archive"))
    return tmp_path


def touch(path, text, mtime):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    os.utime(path, (mtime, mtime))
    return path


def test_codex_has_both_directories_and_the_home_flag_keeps_its_meaning(world):
    names = dict(spool.named_roots("codex"))
    assert names["sessions"] == world / "codex/sessions"
    assert names["archived_sessions"] == world / "codex/archived_sessions"
    other = dict(spool.named_roots("codex", codex_home=world / "elsewhere"))
    assert other["archived_sessions"] == world / "elsewhere/archived_sessions"
    assert spool.named_root("claude", "projects") == world / "claude/projects"


def test_unknown_archive_root_fails_the_spool_only(tmp_path, monkeypatch):
    monkeypatch.delenv("IDH_ARCHIVE_ROOT", raising=False)
    monkeypatch.delenv("DATASETS_DIR", raising=False)
    monkeypatch.setattr(spool, "ENV_FILE", tmp_path / "absent.conf")
    monkeypatch.setenv("PI_CODING_AGENT_DIR", str(tmp_path / "pi"))
    named = dict(spool.named_roots("pi"))
    assert named["live"] == tmp_path / "pi/sessions"
    assert isinstance(named["spool"], RuntimeError)
    assert spool.source_roots("pi") == [tmp_path / "pi/sessions"]
    with pytest.raises(RuntimeError):
        spool.named_root("pi", "spool")


def test_source_roots_include_archived_sessions(world):
    assert world / "codex/archived_sessions" in spool.source_roots("codex")


@pytest.mark.parametrize("runtime, rel, expected", [
    ("codex", "rollout-2026-a.jsonl.zst", "archived_sessions"),
    ("codex", "2026/10/31/rollout-2026-a.jsonl.zst", "sessions"),
    ("pi", "s.jsonl.zst", "spool"),
    ("pi", "--p--/s.jsonl.zst", "live"),
    ("claude", "-p/aaa.jsonl.zst", "projects"),
    ("vibe", "20260101T000000Z-1/session/m.json.zst", "spool"),
])
def test_source_of_is_a_pure_function_of_the_relative_path(runtime, rel, expected):
    assert spool.source_of(runtime, rel) == expected
    assert spool.source_of(runtime, Path(rel.removesuffix(".zst"))) == expected


def test_the_pi_spool_is_flat_per_the_routes_file():
    routes = json.loads((SCRIPTS.parent / "skills/route/routes.json").read_text())
    pi = [v["spool"] for v in routes_values(routes) if v.get("spool", {}).get("runtime") == "pi"]
    assert pi and all(entry["per_seat"] is False for entry in pi)


def routes_values(node):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from routes_values(value)
    elif isinstance(node, list):
        for value in node:
            yield from routes_values(value)


def test_one_rollout_in_two_places_resolves_to_the_longer_newer_copy(world):
    stale = touch(world / "codex/sessions/2026/10/31/rollout-x.jsonl", "short\n", 1000)
    fresh = touch(world / "codex/archived_sessions/rollout-x.jsonl", "short and longer\n", 2000)
    other = touch(world / "codex/sessions/2026/11/01/rollout-y.jsonl", "y\n", 1500)
    assert spool.one_per_rollout([stale, fresh, other]) == sorted([fresh, other])
    same_time = touch(world / "codex/archived_sessions/rollout-z.jsonl", "aa\n", 3000)
    longer = touch(world / "codex/sessions/rollout-z.jsonl", "aaaa\n", 3000)
    assert spool.one_per_rollout([same_time, longer]) == [longer]


def test_zst_copies_count_with_their_plain_names(world):
    packed = touch(world / "archive/raw/h/codex/rollout-x.jsonl.zst", "z", 2000)
    plain = touch(world / "codex/sessions/rollout-x.jsonl", "plain", 1000)
    assert spool.one_per_rollout([plain, packed]) == [packed]


def test_timeline_find_prefers_the_newer_codex_copy(world):
    timeline = _load(SCRIPTS / "trace_timeline.py", "trace_timeline_t1520")
    stale = touch(world / "codex/sessions/2026/10/31/rollout-1-abc.jsonl", "short\n", 1000)
    fresh = touch(world / "codex/archived_sessions/rollout-1-abc.jsonl", "short and longer\n", 2000)
    tree = timeline.Tree(live={"codex": [world / "codex/sessions", world / "codex/archived_sessions"]},
                         archive=world / "archive/raw/h")
    assert tree.find("codex", "**/rollout-*-abc.jsonl") == ("rollout-1-abc.jsonl", fresh)
    stale.unlink()
    assert tree.find("codex", "**/rollout-*-abc.jsonl") == ("rollout-1-abc.jsonl", fresh)


def test_corpora_read_codex_through_the_one_definition(world, monkeypatch):
    corpora = _load(SCRIPTS / "trace_corpora.py", "trace_corpora_t1520")
    touch(world / "codex/sessions/2026/10/31/rollout-1-abc.jsonl", "short\n", 1000)
    fresh = touch(world / "codex/archived_sessions/rollout-1-abc.jsonl", "short and longer\n", 2000)
    assert corpora.corpus_files(corpora.CODEX, world / "codex") == [fresh]
    roots = corpora.default_roots()
    assert roots[corpora.CLAUDE] == world / "claude/projects"
    assert roots[corpora.PI] == world / "pi/sessions"
    assert roots[corpora.PI_SPOOL] == spool.named_root("pi", "spool")
    # a root added to the one definition is walked with no second edit
    extra = world / "codex/extra_sessions"
    monkeypatch.setitem(spool.NAMED_ROOTS["codex"], "extra", lambda: extra)
    added = touch(extra / "rollout-2-def.jsonl", "e\n", 3000)
    assert extra in spool.source_roots("codex")
    assert added in spool.one_per_rollout(p for _, d in spool.named_roots("codex") for p in Path(d).rglob("rollout-*.jsonl"))


def test_the_audit_reads_its_roots_from_the_one_definition(world):
    audit = _load(SCRIPTS / "trace-compact-audit.py", "trace_compact_audit_t1520")
    row = {"type": "session_meta", "payload": {"id": "abc", "source": "cli", "cwd": "/p"}}
    for name, mtime in (("sessions/2026/10/31", 1000), ("archived_sessions", 2000)):
        touch(world / "codex" / name / "rollout-1-abc.jsonl", json.dumps(row) + "\n", mtime)
    got = list(audit.read_codex(world / "codex"))
    assert len(got) == 1 and got[0][1] == "abc"
    assert audit.default_roots()["Claude Code"] == world / "claude/projects"
    assert audit.default_roots()["Codex"] == world / "codex"
