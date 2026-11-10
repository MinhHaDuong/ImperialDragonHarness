"""Sessions-over-ceiling report of scripts/trace-compact-audit.py (ticket 1499).

Fixture transcripts only: the transcript format is the runtime's, parsed in the
audit script alone.
"""

import importlib.util
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
CEILINGS = Path(__file__).resolve().parent.parent / "skills" / "route" / "ceilings.json"

spec = importlib.util.spec_from_file_location("tca_ctx", SCRIPTS / "trace-compact-audit.py")
tca = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tca)

NOW = datetime(2026, 11, 10, 12, 0, tzinfo=timezone.utc)

# The audit's logic is tested against ceilings of its own, which differ from
# the live file's, so the tests hold when the author changes a ceiling there.
CEIL = {
    "default_tokens": 210_000,
    "interface_session": [
        {"models": ["sol", "opus"], "tokens": 460_000},
        {"models": ["astra", "fable"], "tokens": 560_000},
    ],
}
LV = str(CEIL["default_tokens"])  # the lowest level row


def _turn(msg_id, day, *, cache_read=0, inp=0, creation=0, model="claude-opus-5-5"):
    return {
        "type": "assistant",
        "timestamp": f"2026-11-{day:02d}T10:00:00.000Z",
        "message": {
            "id": msg_id,
            "model": model,
            "role": "assistant",
            "usage": {
                "input_tokens": inp,
                "output_tokens": 5,
                "cache_read_input_tokens": cache_read,
                "cache_creation_input_tokens": creation,
            },
            "content": [{"type": "text", "text": "x"}],
        },
    }


def _session(root, sid, rows, project="-proj", agent=None):
    proj = root / project
    if agent is None:
        path = proj / f"{sid}.jsonl"
    else:
        path = proj / sid / "subagents" / f"agent-{agent}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    return path


def _audit(root, **kw):
    kw.setdefault("days", 28)
    kw.setdefault("min_run", 30)
    kw.setdefault("now", NOW)
    kw.setdefault("ceilings", CEIL)
    return tca.audit_corpus(root, **kw)


# --- the whole prompt, not cache reads ---------------------------------------

def test_turn_context_is_the_whole_prompt(tmp_path):
    f = _session(tmp_path, "s", [_turn("m1", 9, inp=1_000, cache_read=200_000, creation=30_000)])
    ev = tca.parse_trajectory(f)["events"][0]
    assert ev["prompt"] == 231_000
    assert ev["cache_read"] == 200_000


def test_threshold_applies_to_the_prompt_not_the_cache_read(tmp_path):
    # cache read alone is below the default ceiling; the whole prompt is above.
    rows = [_turn(f"m{i}", 9, cache_read=200_000, creation=40_000) for i in range(30)]
    _session(tmp_path, "s", rows)
    out = _audit(tmp_path)["sessions"]
    assert out["levels"][LV]["sessions"] == 1
    legacy = _audit(tmp_path, metric="cache_read")["sessions"]
    assert legacy["levels"][LV]["sessions"] == 0
    assert "cache_read" in legacy["metric"] and "cache_read" not in out["metric"]


# --- window ------------------------------------------------------------------

def test_turns_outside_the_window_are_not_counted(tmp_path):
    old = [_turn(f"o{i}", 1, cache_read=500_000) for i in range(40)]  # 9 days before NOW
    new = [_turn(f"n{i}", 9, cache_read=100_000) for i in range(5)]
    _session(tmp_path, "s", old + new)
    out = _audit(tmp_path, days=3)
    assert out["sessions"]["with_turns"] == 1
    assert out["sessions"]["levels"][LV]["sessions"] == 0  # the old turns do not count
    assert out["sessions"]["turns_in_window"] == 5


def test_session_wholly_outside_window_is_absent(tmp_path):
    _session(tmp_path, "s", [_turn("m", 1, cache_read=500_000)])
    assert _audit(tmp_path, days=3)["sessions"]["with_turns"] == 0


def test_since_date_sets_the_window_start(tmp_path):
    rows = [_turn("a", 2, cache_read=1), _turn("b", 5, cache_read=1)]
    _session(tmp_path, "s", rows)
    out = _audit(tmp_path, since="2026-11-03")
    assert out["sessions"]["turns_in_window"] == 1


# --- sessions versus runs -----------------------------------------------------

def test_two_runs_in_one_session_count_once(tmp_path):
    clear = {
        "type": "user",
        "timestamp": "2026-11-09T11:00:00.000Z",
        "message": {
            "role": "user",
            "content": "<command-name>/clear</command-name>\n<command-message>clear</command-message>",
        },
    }
    high = lambda p: [_turn(f"{p}{i}", 9, cache_read=500_000) for i in range(31)]  # noqa: E731
    _session(tmp_path, "s", high("a") + [clear] + high("b"))
    out = _audit(tmp_path)
    assert out["missed_runs"] == 2
    assert out["sessions"]["levels"][LV]["sessions"] == 1
    assert out["sessions_with_missed_runs"] == 1


def test_only_main_transcripts_are_sessions(tmp_path):
    _session(tmp_path, "s", [_turn(f"m{i}", 9, cache_read=300_000) for i in range(3)])
    _session(tmp_path, "s", [_turn(f"a{i}", 9, cache_read=300_000) for i in range(30)], agent="a1")
    out = _audit(tmp_path)
    assert out["sessions"]["with_turns"] == 1
    assert out["sessions"]["levels"][LV]["sessions"] == 0


# --- main model and per-model thresholds -------------------------------------

def test_main_model_is_the_most_used_and_reported(tmp_path):
    rows = [_turn(f"o{i}", 9, cache_read=300_000, model="claude-opus-5-5") for i in range(30)]
    rows += [_turn("h", 9, cache_read=300_000, model="claude-haiku-5-5")]
    _session(tmp_path, "s", rows)
    out = _audit(tmp_path)["sessions"]
    assert out["levels"][LV]["by_model"] == {"claude-opus-5-5": 1}


def test_ceiling_comes_from_the_route_data_per_model():
    c = CEIL
    assert tca.ceiling_for("claude-opus-5-5", c) == 460_000
    assert tca.ceiling_for("gpt-6.1-sol", c) == 460_000
    assert tca.ceiling_for("claude-fable-5-1", c) == 560_000
    assert tca.ceiling_for("gpt-6-astra", c) == 560_000
    assert tca.ceiling_for("claude-haiku-5-5", c) == 210_000
    assert tca.ceiling_for("", c) == 210_000
    assert tca.ceiling_for("console-model", c) == 210_000  # a word match, not a substring


def test_level_rows_are_the_distinct_ceilings_of_the_data_in_increasing_order():
    assert tca.levels_for(CEIL) == (210_000, 460_000, 560_000)
    other = {"default_tokens": 300_000, "interface_session": [{"models": ["x"], "tokens": 300_000},
                                                              {"models": ["y"], "tokens": 120_000}]}
    assert tca.levels_for(other) == (120_000, 300_000)


def test_level_rows_follow_the_ceilings_given_not_the_live_file(tmp_path):
    other = {"default_tokens": 100_000, "interface_session": [{"models": ["opus"], "tokens": 350_000}]}
    # past the fixture's default, under the live one
    _session(tmp_path, "s", [_turn(f"m{i}", 9, cache_read=120_000) for i in range(30)])
    out = _audit(tmp_path, ceilings=other)["sessions"]
    assert list(out["levels"]) == ["100000", "350000"]
    assert out["levels"]["100000"]["sessions"] == 1 and out["levels"]["350000"]["sessions"] == 0


def test_live_ceilings_file_sets_the_level_rows(tmp_path):
    live = tca.load_ceilings(CEILINGS)
    _session(tmp_path, "s", [_turn(f"m{i}", 9, cache_read=live["default_tokens"]) for i in range(30)])
    out = tca.audit_corpus(tmp_path, days=28, min_run=30, now=NOW)["sessions"]
    assert list(out["levels"]) == [str(lv) for lv in tca.levels_for(live)]


def test_sessions_over_their_own_model_ceiling(tmp_path):
    ceilings = CEIL
    at = lambda n, model: [_turn(f"{model}{i}", 9, cache_read=n, model=model) for i in range(30)]  # noqa: E731
    _session(tmp_path, "opus-under", at(400_000, "claude-opus-5-5"))
    _session(tmp_path, "opus-over", at(460_000, "claude-opus-5-5"))
    _session(tmp_path, "fable-under", at(500_000, "claude-fable-5-1"))
    _session(tmp_path, "haiku-over", at(240_000, "claude-haiku-5-5"))
    over = _audit(tmp_path, ceilings=ceilings)["sessions"]["over_own_ceiling"]
    assert over["sessions"] == 2
    assert over["by_model"] == {"claude-opus-5-5": 1, "claude-haiku-5-5": 1}
    assert {r["session_id"] for r in over["rows"]} == {"opus-over", "haiku-over"}


def test_explicit_threshold_overrides_the_per_model_one(tmp_path):
    rows = [_turn(f"m{i}", 9, cache_read=300_000) for i in range(30)]
    _session(tmp_path, "s", rows)
    assert _audit(tmp_path)["missed_runs"] == 0  # under the opus ceiling
    assert _audit(tmp_path, threshold=200_000)["missed_runs"] == 1


# --- could not look -----------------------------------------------------------

def test_unreadable_transcript_is_reported_not_counted_as_zero(tmp_path):
    _session(tmp_path, "good", [_turn("m", 9, cache_read=1)])
    (tmp_path / "-proj" / "broken.jsonl").mkdir()  # opening a directory raises OSError
    out = _audit(tmp_path)
    assert out["unreadable_files"] == 1
    assert out["sessions"]["with_turns"] == 1


def test_unparsable_lines_are_counted(tmp_path):
    f = _session(tmp_path, "s", [_turn("m", 9, cache_read=1)])
    f.write_text("{not json\n" + f.read_text())
    assert _audit(tmp_path)["unparsable_lines"] == 1


@pytest.mark.integration
def test_cli_missing_projects_dir_is_could_not_look(tmp_path):
    done = subprocess.run(
        [sys.executable, str(SCRIPTS / "trace-compact-audit.py"), "--projects-dir", str(tmp_path / "nope"),
         "--codex-home", str(tmp_path / "nope-codex"),
         "--pi-sessions", str(tmp_path / "nope-pi"), "--pi-spool", str(tmp_path / "nope-spool")],
        capture_output=True, text=True,
    )
    assert done.returncode == 2
    assert "could not look" in done.stderr + done.stdout


# --- the table of the design note, from one command --------------------------

@pytest.mark.integration
def test_cli_prints_the_note_table(tmp_path):
    rows = [_turn(f"m{i}", 9, cache_read=500_000) for i in range(30)]
    _session(tmp_path, "s", rows)
    done = subprocess.run(
        [sys.executable, str(SCRIPTS / "trace-compact-audit.py"), "--projects-dir", str(tmp_path),
         "--codex-home", str(tmp_path / "nope-codex"),
         "--pi-sessions", str(tmp_path / "nope-pi"), "--pi-spool", str(tmp_path / "nope-spool"), "--since", "2026-11-01"],
        capture_output=True, text=True,
    )
    assert done.returncode == 0, done.stderr
    out = done.stdout
    assert "whole prompt" in out
    assert "sessions with at least one turn: 1" in out
    live = tca.load_ceilings(CEILINGS)
    for lv in tca.levels_for(live):
        assert f"30 or more turns at or above {tca._fmt_k(lv)}: {int(500_000 >= lv)}" in out


# --- Codex sessions (ticket 1508) ---------------------------------------------
# Synthetic rollouts in the shape the reader parses: a session_meta, a
# turn_context naming the model, then one token_count event per model request.

def _codex_session(home, name, records, *, source="cli", model="gpt-6.1-sol", sub="sessions", reemit=False):
    """`records` are (day, input_tokens, cached_input_tokens) per model request."""
    src = {"subagent": {"thread_spawn": {"parent_thread_id": "p"}}} if source == "subagent" else source
    rows = [
        {"timestamp": "2026-11-01T00:00:00.000Z", "type": "session_meta",
         "payload": {"id": name, "cwd": "/work/proj", "source": src}},
        {"timestamp": "2026-11-01T00:00:00.000Z", "type": "turn_context", "payload": {"model": model}},
    ]
    cumulative = 0
    for day, inp, cached in records:
        last = {"input_tokens": inp, "cached_input_tokens": cached, "cache_write_input_tokens": 0,
                "output_tokens": 10, "reasoning_output_tokens": 0, "total_tokens": inp + 10}
        cumulative += inp + 10
        tc = {"timestamp": f"2026-11-{day:02d}T10:00:00.000Z", "type": "event_msg",
              "payload": {"type": "token_count", "info": {
                  "last_token_usage": last, "total_token_usage": {"total_tokens": cumulative},
                  "model_context_window": 475_000}}}
        rows.append(tc)
        if reemit:
            rows.append(tc)  # same cumulative total: a re-emission, not a request
    d = home / sub / "2026" / "11" / "01"
    if sub != "sessions":
        d = home / sub
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"rollout-2026-11-01T00-00-00-{name}.jsonl"
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    return path


def _both(tmp_path, **kw):
    """Audit a Claude Code root and a Codex home side by side."""
    roots = {"Claude Code": tmp_path / "claude", "Codex": tmp_path / "codex"}
    roots.update(kw.pop("roots", {}))
    return _audit(roots, **kw)


def _runtime(out, name):
    return next(r for r in out["runtimes"] if r["name"] == name)


def test_codex_session_past_its_ceiling_is_counted_under_codex(tmp_path):
    _session(tmp_path / "claude", "c", [_turn(f"m{i}", 9, cache_read=100_000) for i in range(5)])
    _codex_session(tmp_path / "codex", "x", [(9, 460_000, 400_000)] * 30)
    out = _both(tmp_path)
    over = out["sessions"]["over_own_ceiling"]
    assert over["sessions"] == 1
    assert over["by_runtime"] == {"Codex": 1}
    assert over["rows"][0]["runtime"] == "Codex"
    assert _runtime(out, "Codex")["status"] == "read"
    assert _runtime(out, "Codex")["sessions_with_turns"] == 1
    assert out["runtimes_read"] == ["Claude Code", "Codex"]
    assert out["runtimes_not_read"] == ["Pi", "Pi spool"]
    alone = _audit(tmp_path / "claude")["sessions"]
    assert _runtime(out, "Claude Code")["sessions_with_turns"] == alone["with_turns"] == 1


def test_codex_input_tokens_already_hold_the_cached_part(tmp_path):
    # 440K input of which 300K cached: adding the cached part again would cross the Opus ceiling.
    _codex_session(tmp_path / "codex", "x", [(9, 440_000, 300_000)] * 30)
    out = _both(tmp_path, roots={"Claude Code": None})
    assert out["sessions"]["over_own_ceiling"]["sessions"] == 0
    assert out["sessions"]["levels"][LV]["sessions"] == 1


def test_codex_exec_is_held_to_the_default_ceiling_cli_to_its_model(tmp_path):
    _codex_session(tmp_path / "codex", "ex", [(9, 300_000, 0)] * 30, source="exec")
    _codex_session(tmp_path / "codex", "cl", [(9, 300_000, 0)] * 30, source="cli")
    over = _both(tmp_path, roots={"Claude Code": None})["sessions"]["over_own_ceiling"]
    assert {r["session_id"] for r in over["rows"]} == {"ex"}
    assert over["by_rule"] == {"default": 1}


def test_codex_subagent_rollout_is_not_a_session(tmp_path):
    _codex_session(tmp_path / "codex", "sub", [(9, 300_000, 0)] * 30, source="subagent")
    out = _both(tmp_path, roots={"Claude Code": None})
    assert out["sessions"]["with_turns"] == 0
    assert _runtime(out, "Codex")["roles"] == {"subagent": 1}


def test_codex_turn_outside_the_window_is_not_counted(tmp_path):
    _codex_session(tmp_path / "codex", "x", [(1, 500_000, 0)] * 40 + [(9, 100_000, 0)] * 5)
    out = _both(tmp_path, roots={"Claude Code": None}, days=3)
    assert out["sessions"]["turns_in_window"] == 5
    assert out["sessions"]["levels"][LV]["sessions"] == 0


def test_codex_reemitted_token_count_is_one_request(tmp_path):
    _codex_session(tmp_path / "codex", "x", [(9, 300_000, 0)] * 20, reemit=True)
    out = _both(tmp_path, roots={"Claude Code": None})
    assert out["sessions"]["turns_in_window"] == 20


def test_codex_archive_is_read(tmp_path):
    _codex_session(tmp_path / "codex", "a", [(9, 100_000, 0)], sub="archived_sessions")
    out = _both(tmp_path, roots={"Claude Code": None})
    assert out["sessions"]["with_turns"] == 1


def test_absent_codex_corpus_is_could_not_look_and_claude_code_still_counted(tmp_path):
    _session(tmp_path / "claude", "c", [_turn(f"m{i}", 9, cache_read=500_000) for i in range(30)])
    out = _both(tmp_path)  # no codex directory was made
    codex = _runtime(out, "Codex")
    assert codex["status"] == "could not look"
    assert "Codex" in out["runtimes_not_read"] and "Codex" not in out["runtimes_read"]
    assert "Codex" not in out["sessions"]["levels"][LV]["by_runtime"]
    alone = _audit(tmp_path / "claude")
    assert out["sessions"]["levels"] == alone["sessions"]["levels"]
    assert out["sessions"]["with_turns"] == alone["sessions"]["with_turns"] == 1


def test_no_readable_corpus_at_all_is_could_not_look(tmp_path):
    with pytest.raises(tca.CouldNotLook):
        _both(tmp_path)


def test_missed_runs_stay_claude_code_only(tmp_path):
    _codex_session(tmp_path / "codex", "x", [(9, 500_000, 0)] * 40)
    out = _both(tmp_path, roots={"Claude Code": None})
    assert out["missed_runs"] == 0
    assert out["recoverable_usd_upper_bound"] == 0


def test_output_names_the_host_and_every_runtime(tmp_path):
    _codex_session(tmp_path / "codex", "x", [(9, 100_000, 0)])
    out = _both(tmp_path)
    assert _runtime(out, "Pi")["status"] == "not read"  # no root given
    assert out["host"]
    table = tca.render_table(out)
    assert out["host"] in table and "Pi" in table


@pytest.mark.integration
def test_cli_reads_codex_beside_an_absent_claude_code_corpus(tmp_path):
    _codex_session(tmp_path / "codex", "x", [(9, 500_000, 0)] * 30)
    done = subprocess.run(
        [sys.executable, str(SCRIPTS / "trace-compact-audit.py"), "--projects-dir", str(tmp_path / "nope"),
         "--codex-home", str(tmp_path / "codex"),
         "--pi-sessions", str(tmp_path / "nope-pi"), "--pi-spool", str(tmp_path / "nope-spool"), "--since", "2026-11-01"],
        capture_output=True, text=True,
    )
    assert done.returncode == 0, done.stderr
    assert "COULD NOT LOOK" in done.stdout and "Claude Code" in done.stdout


def test_codex_home_with_no_readable_rollout_is_could_not_look(tmp_path):
    _session(tmp_path / "claude", "c", [_turn("m", 9, cache_read=1)])
    (tmp_path / "codex" / "sessions" / "rollout-x.jsonl").mkdir(parents=True)  # opening raises OSError
    out = _both(tmp_path)
    assert _runtime(out, "Codex")["status"] == "could not look"
    assert "Codex" in out["runtimes_not_read"]
    assert out["sessions"]["with_turns"] == 1


# --- Pi sessions (ticket 1509) --------------------------------------------------
# Synthetic session logs: a `session` header, then tree entries with id/parentId.

def _pi_entry(eid, parent, day, usage=None, *, model="claude-opus-5-5", rid=None, role="assistant", error=False):
    msg = {"role": role, "model": model, "content": []}
    if usage is not None:
        msg["usage"] = {"input": usage[0], "output": 5, "cacheRead": usage[1], "cacheWrite": usage[2],
                        "totalTokens": sum(usage) + 5}
    if error:
        msg["errorMessage"] = "e"
    if rid:
        msg["responseId"] = rid
    return {"type": "message", "id": eid, "parentId": parent,
            "timestamp": f"2026-11-{day:02d}T10:00:00.000Z", "message": msg}


def _pi_session(root, name, usages, *, day=9, header_day=1, extra=(), parent_session=None, chain_ids=True):
    """One linear branch of assistant turns; `usages` are (input, cacheRead, cacheWrite)."""
    head = {"type": "session", "version": 3, "id": name, "cwd": "/work/proj",
            "timestamp": f"2026-11-{header_day:02d}T00:00:00.000Z"}
    if parent_session:
        head["parentSession"] = parent_session
    rows, parent = [head], None
    for i, u in enumerate(usages):
        eid = f"{name}-{i}"
        rows.append(_pi_entry(eid, parent, day, u, rid=f"r-{eid}"))
        parent = eid
    rows += list(extra)
    d = root / "--work-proj--"
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"2026-11-01T00-00-00-000Z_{name}.jsonl"
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    return path


def _pi(tmp_path, **kw):
    roots = {"Claude Code": tmp_path / "claude", "Pi": tmp_path / "pi", "Pi spool": tmp_path / "spool"}
    roots.update(kw.pop("roots", {}))
    return _audit(roots, **kw)


def test_pi_session_past_its_ceiling_counts_the_cache_fields(tmp_path):
    _session(tmp_path / "claude", "c", [_turn("m", 9, cache_read=1)])
    # input alone is tiny: only input + cacheRead + cacheWrite crosses the Opus ceiling
    _pi_session(tmp_path / "pi", "p", [(100, 400_000, 100_000)] * 30)
    out = _pi(tmp_path)
    over = out["sessions"]["over_own_ceiling"]
    assert over["by_runtime"] == {"Pi": 1}
    assert over["rows"][0]["peak"] == 500_100
    assert _runtime(out, "Pi")["status"] == "read" and _runtime(out, "Pi")["sessions_with_turns"] == 1
    assert "Pi" in out["runtimes_read"] and "Pi" not in out["runtimes_not_read"]
    assert out["sessions"]["by_runtime"]["Claude Code"] == 1


def test_pi_error_turns_are_not_turns(tmp_path):
    errs = [_pi_entry(f"e{i}", "p-0", 9, (0, 0, 0), rid=None, error=True) for i in range(40)]
    _pi_session(tmp_path / "pi", "p", [(10, 0, 0)], extra=errs)
    out = _pi(tmp_path)
    assert out["sessions"]["turns_in_window"] == 1
    assert out["sessions"]["long_sessions"] == 0


def test_pi_turns_are_dated_by_the_turn_not_the_header(tmp_path):
    _pi_session(tmp_path / "pi", "old", [(10, 0, 0)] * 3, day=1, header_day=9)  # header in, turns out
    _pi_session(tmp_path / "pi", "new", [(10, 0, 0)] * 4, day=9, header_day=1)  # header out, turns in
    out = _pi(tmp_path, since="2026-11-05")
    assert out["sessions"]["with_turns"] == 1
    assert out["sessions"]["turns_in_window"] == 4


def test_pi_live_root_takes_the_model_ceiling_spool_the_default(tmp_path):
    turns = [(100, 300_000, 0)] * 30  # past Opus's ceiling, over the default, under Opus
    _pi_session(tmp_path / "pi", "live", turns)
    _pi_session(tmp_path / "spool", "seat", turns)
    out = _pi(tmp_path)
    ceil = tca.ceiling_for("claude-opus-5-5", CEIL)
    assert ceil > 300_100  # the fixture sits under the model ceiling
    rows = {r["session_id"]: r for r in out["sessions"]["over_own_ceiling"]["rows"]}
    assert set(rows) == {"seat"}
    assert rows["seat"]["runtime"] == "Pi spool" and rows["seat"]["ceiling_rule"] == "default"
    assert rows["seat"]["role"] == "launched"
    assert _runtime(out, "Pi spool")["status"] == "read"


def test_pi_absent_root_is_could_not_look_and_the_rest_is_counted(tmp_path):
    _session(tmp_path / "claude", "c", [_turn("m", 9, cache_read=1)])
    _pi_session(tmp_path / "spool", "seat", [(10, 0, 0)])
    out = _pi(tmp_path)  # tmp_path/pi was never made
    assert _runtime(out, "Pi")["status"] == "could not look"
    assert "Pi" in out["runtimes_not_read"] and "Pi" not in out["sessions"]["by_runtime"]
    assert _runtime(out, "Pi spool")["status"] == "read"
    base = _audit({"Claude Code": tmp_path / "claude"})
    assert out["sessions"]["by_runtime"]["Claude Code"] == base["sessions"]["by_runtime"]["Claude Code"]


def test_pi_root_with_no_file_in_the_window_is_read_with_zero_sessions(tmp_path):
    (tmp_path / "pi").mkdir()
    _session(tmp_path / "claude", "c", [_turn("m", 9, cache_read=1)])
    out = _pi(tmp_path)
    assert _runtime(out, "Pi")["status"] == "read" and _runtime(out, "Pi")["sessions_with_turns"] == 0


def test_pi_clone_counts_only_the_new_turns(tmp_path):
    _pi_session(tmp_path / "pi", "a", [(10, 0, 0)] * 3)
    # the clone replays a's three entries (same responseIds), then adds two
    path = _pi_session(tmp_path / "pi", "b", [(10, 0, 0)] * 2, parent_session="a")
    rows = [json.loads(ln) for ln in path.read_text().splitlines()]
    replay = [json.loads(ln) for ln in (tmp_path / "pi" / "--work-proj--" / "2026-11-01T00-00-00-000Z_a.jsonl").read_text().splitlines()][1:]
    new = [_pi_entry("n0", "a-2", 9, (10, 0, 0), rid="r-n0"), _pi_entry("n1", "n0", 9, (10, 0, 0), rid="r-n1")]
    path.write_text("\n".join(json.dumps(r) for r in [rows[0]] + replay + new) + "\n")
    out = _pi(tmp_path)
    assert out["sessions"]["turns_in_window"] == 5
    assert out["inherited_turns_dropped"] == 3


def test_pi_abandoned_branch_is_not_a_turn(tmp_path):
    # a-0 -> a-1 (continued, last in file) ; a-0 -> x (abandoned, earlier in file)
    path = _pi_session(tmp_path / "pi", "a", [(10, 0, 0)] * 2)
    rows = [json.loads(ln) for ln in path.read_text().splitlines()]
    side = _pi_entry("x", "a-0", 9, (999_999, 0, 0), rid="r-x")
    path.write_text("\n".join(json.dumps(r) for r in [rows[0], rows[1], side, rows[2]]) + "\n")
    out = _pi(tmp_path)
    assert out["sessions"]["turns_in_window"] == 2
    assert out["sessions"]["levels"][LV]["sessions"] == 0


@pytest.mark.integration
def test_cli_reads_pi_roots(tmp_path):
    _pi_session(tmp_path / "pi", "p", [(100, 400_000, 100_000)] * 30)
    done = subprocess.run(
        [sys.executable, str(SCRIPTS / "trace-compact-audit.py"), "--projects-dir", str(tmp_path / "nope"),
         "--codex-home", str(tmp_path / "nope2"), "--pi-sessions", str(tmp_path / "pi"),
         "--pi-spool", str(tmp_path / "nope3"), "--since", "2026-11-01"],
        capture_output=True, text=True,
    )
    assert done.returncode == 0, done.stderr
    assert "Read: Pi under" in done.stdout and "COULD NOT LOOK at Pi spool" in done.stdout




# --- the other hosts, from this host's archive (ticket 1519) -------------------
# A fixture archive in a temporary directory: synthetic transcripts compressed with
# the zstd CLI under raw/<host>/<runtime>/, as transcript_archive.py lays them out.

ARCHIVED_AT = datetime(2026, 11, 8, 12, 0, tzinfo=timezone.utc).timestamp()


def _archive(src: Path, archive: Path, host: str, runtime: str, rel: str, *, mtime=ARCHIVED_AT, raw=None):
    """Compress `src` (or the bytes `raw`) to raw/<host>/<runtime>/<rel>.zst, stamped `mtime`."""
    dest = archive / "raw" / host / runtime / f"{rel}.zst"
    dest.parent.mkdir(parents=True, exist_ok=True)
    if raw is not None:
        dest.write_bytes(raw)
    else:
        subprocess.run(["zstd", "-q", "-f", "-o", str(dest), str(src)], check=True)
    os.utime(dest, (mtime, mtime))
    return dest


@pytest.fixture
def world(tmp_path, monkeypatch):
    """This host is `here`; its archive is tmp/archive; the local corpus is one Claude Code session."""
    monkeypatch.setattr(tca.transcript_spool, "host", lambda: "here")
    monkeypatch.setenv("IDH_ARCHIVE_ROOT", str(tmp_path / "archive"))
    (tmp_path / "archive" / "raw" / "here").mkdir(parents=True)
    _session(tmp_path / "claude", "s", [_turn(f"m{i}", 9, cache_read=500_000) for i in range(30)])
    return tmp_path


def _local(root, **kw):
    return _audit({"Claude Code": root / "claude"} if root else {}, require_one=False, **kw)


def _fleet(root, local=None):
    local = local or _local(root)
    return tca.audit_fleet(local, lambda roots: _audit(roots, require_one=False))


def _other_host_corpus(world, host="doudou"):
    """One session past its ceiling per runtime, archived for `host`."""
    src = world / "src"
    over = [_turn(f"d{i}", 9, cache_read=500_000) for i in range(30)]
    claude = _session(src / "claude", "ds", over)
    codex = _codex_session(src / "codex", "dx", [(9, 480_000, 400_000)] * 30, model="claude-opus-5-5")
    pi = _pi_session(src / "pi", "dp", [(100, 400_000, 100_000)] * 30)
    a = world / "archive"
    _archive(claude, a, host, "claude", "-proj/ds.jsonl")
    _archive(codex, a, host, "codex", f"2026/11/01/{codex.name}")
    _archive(pi, a, host, "pi", f"--work-proj--/{pi.name}")
    return src


def _host(out, name):
    return next(h for h in out["hosts"] if h["host"] == name)


@pytest.mark.integration
def test_session_past_its_ceiling_on_the_other_host_counts_under_that_host_and_runtime(world):
    _other_host_corpus(world)
    out = _fleet(world)
    doudou = _host(out, "doudou")
    assert doudou["source"] == "archive" and doudou["status"] == "read"
    assert doudou["sessions"]["over_own_ceiling"]["by_runtime"] == {"Claude Code": 1, "Codex": 1, "Pi": 1}
    assert out["sessions"]["over_own_ceiling"]["sessions"] == 4  # 1 here + 3 there
    assert out["sessions"]["by_runtime"] == {"Claude Code": 2, "Codex": 1, "Pi": 1}
    assert [h["host"] for h in out["hosts"]] == ["here", "doudou"]


@pytest.mark.integration
def test_the_host_names_its_newest_file_and_the_surfaces_its_copy_holds(world):
    _other_host_corpus(world)
    doudou = _host(_fleet(world), "doudou")
    assert doudou["newest_file"] == "2026-11-08"
    assert doudou["surfaces"] == {"Claude Code": 1, "Codex sessions": 1, "Pi": 1}
    assert doudou["surfaces_missing"] == ["Codex archived sessions", "Pi spool"]
    pi_spool = next(r for r in doudou["runtimes"] if r["name"] == "Pi spool")
    assert pi_spool["status"] == "not read"
    table = tca.render_table(_fleet(world))
    assert "2026-11-08" in table


@pytest.mark.integration
def test_a_rollout_archived_from_both_codex_roots_is_one_session(world):
    src = _other_host_corpus(world)
    rollout = next((src / "codex").rglob("rollout-*.jsonl"))
    _archive(rollout, world / "archive", "doudou", "codex", rollout.name)  # archived_sessions copy
    doudou = _host(_fleet(world), "doudou")
    assert doudou["sessions"]["by_runtime"]["Codex"] == 1
    assert doudou["surfaces"]["Codex archived sessions"] == 1


@pytest.mark.integration
def test_a_corrupt_archived_file_is_could_not_look_not_an_empty_session(world):
    _other_host_corpus(world)
    _archive(None, world / "archive", "doudou", "claude", "-proj/broken.jsonl", raw=b"not zstd at all")
    doudou = _host(_fleet(world), "doudou")
    assert doudou["unreadable_files"] == 1
    claude = next(r for r in doudou["runtimes"] if r["name"] == "Claude Code")
    assert claude["unreadable_files"] == 1 and claude["sessions_with_turns"] == 1


@pytest.mark.integration
def test_an_archived_file_older_than_the_window_is_not_decompressed(world):
    _other_host_corpus(world)
    old = datetime(2026, 9, 1, tzinfo=timezone.utc).timestamp()
    _archive(None, world / "archive", "doudou", "claude", "-proj/old.jsonl", raw=b"corrupt", mtime=old)
    doudou = _host(_fleet(world), "doudou")
    assert doudou["unreadable_files"] == 0
    assert doudou["surfaces"]["Claude Code"] == 2  # held, not read


def test_a_live_file_older_than_the_window_is_not_read(tmp_path):
    path = _session(tmp_path / "claude", "s", [_turn("m", 1, cache_read=1)])
    old = datetime(2026, 9, 1, tzinfo=timezone.utc).timestamp()
    os.utime(path, (old, old))
    _session(tmp_path / "claude", "t", [_turn("n", 9, cache_read=1)])
    assert _audit(tmp_path / "claude")["files_seen"] == 1


def test_a_host_whose_copy_holds_no_transcript_is_could_not_look(world):
    (world / "archive" / "raw" / "doudou" / "seat-raw").mkdir(parents=True)
    out = _fleet(world)
    doudou = _host(out, "doudou")
    assert doudou["status"] == "could not look" and "sessions" not in doudou
    assert out["sessions"]["with_turns"] == 1


def test_an_archive_with_no_other_host_names_the_fleet_not_available(world):
    out = _fleet(world)
    assert out["fleet"]["available"] is False
    assert out["sessions"]["with_turns"] == 1


def test_an_unresolvable_archive_root_names_the_fleet_not_available(world, monkeypatch):
    monkeypatch.delenv("IDH_ARCHIVE_ROOT")
    monkeypatch.delenv("DATASETS_DIR", raising=False)
    monkeypatch.setattr(tca.transcript_spool, "ENV_FILE", world / "no-such-file")
    out = _fleet(world)
    assert out["fleet"]["available"] is False
    assert out["sessions"]["with_turns"] == 1


@pytest.mark.integration
def test_local_unreadable_but_an_archived_host_readable_is_not_a_failure(world):
    _other_host_corpus(world)
    out = _fleet(None, local=_local(world / "nope"))
    assert out["hosts"][0]["status"] == "could not look"
    assert out["sessions"]["with_turns"] == 3


def test_nothing_readable_here_nor_in_the_archive_raises(world):
    with pytest.raises(tca.CouldNotLook):
        _fleet(None, local=_local(world / "nope"))


def _main(monkeypatch, capsys, argv):
    monkeypatch.setattr(sys, "argv", ["trace-compact-audit.py", *argv])
    code = tca.main()
    return code, capsys.readouterr().out


def _live_env(world, monkeypatch):
    """Default roots of this host point into the fixture world."""
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(world))  # projects = world/projects
    (world / "claude").rename(world / "projects")
    monkeypatch.setenv("CODEX_HOME", str(world / "nope-codex"))
    monkeypatch.setenv("PI_CODING_AGENT_DIR", str(world / "nope-pi"))


def _no_archive(*a, **k):
    raise AssertionError("the archive was read")


def test_cli_local_reads_no_archive(world, monkeypatch, capsys):
    _live_env(world, monkeypatch)
    monkeypatch.setattr(tca, "archive_host_entries", _no_archive)
    code, out = _main(monkeypatch, capsys, ["--local", "--since", "2026-11-01"])
    assert code == 0 and "Fleet:" not in out


def test_cli_explicit_corpus_roots_read_no_archive(world, monkeypatch, capsys):
    monkeypatch.setattr(tca, "archive_host_entries", _no_archive)
    code, _ = _main(monkeypatch, capsys, ["--projects-dir", str(world / "claude"), "--since", "2026-11-01"])
    assert code == 0


def test_cli_default_run_without_other_hosts_exits_zero(world, monkeypatch, capsys):
    _live_env(world, monkeypatch)
    code, out = _main(monkeypatch, capsys, ["--since", "2026-11-01"])
    assert code == 0 and "sessions with at least one turn: 1" in out


def test_cli_exit_is_nonzero_only_when_nothing_is_readable(world, monkeypatch, capsys):
    _live_env(world, monkeypatch)
    for d in (world / "projects").iterdir():
        for f in d.iterdir():
            f.unlink()
        d.rmdir()
    (world / "projects").rmdir()
    code, _ = _main(monkeypatch, capsys, ["--since", "2026-11-01"])
    assert code == 2
