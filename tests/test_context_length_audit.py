"""Sessions-over-ceiling report of scripts/trace-compact-audit.py (ticket 1499).

Fixture transcripts only: the transcript format is the runtime's, parsed in the
audit script alone.
"""

import importlib.util
import json
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
    return tca.audit_corpus(root, **kw)


# --- the whole prompt, not cache reads ---------------------------------------

def test_turn_context_is_the_whole_prompt(tmp_path):
    f = _session(tmp_path, "s", [_turn("m1", 9, inp=1_000, cache_read=200_000, creation=30_000)])
    ev = tca.parse_trajectory(f)["events"][0]
    assert ev["prompt"] == 231_000
    assert ev["cache_read"] == 200_000


def test_threshold_applies_to_the_prompt_not_the_cache_read(tmp_path):
    # cache read alone is below 230K; the whole prompt is above.
    rows = [_turn(f"m{i}", 9, cache_read=200_000, creation=40_000) for i in range(30)]
    _session(tmp_path, "s", rows)
    out = _audit(tmp_path)["sessions"]
    assert out["levels"]["230000"]["sessions"] == 1
    legacy = _audit(tmp_path, metric="cache_read")["sessions"]
    assert legacy["levels"]["230000"]["sessions"] == 0
    assert "cache_read" in legacy["metric"] and "cache_read" not in out["metric"]


# --- window ------------------------------------------------------------------

def test_turns_outside_the_window_are_not_counted(tmp_path):
    old = [_turn(f"o{i}", 1, cache_read=500_000) for i in range(40)]  # 9 days before NOW
    new = [_turn(f"n{i}", 9, cache_read=100_000) for i in range(5)]
    _session(tmp_path, "s", old + new)
    out = _audit(tmp_path, days=3)
    assert out["sessions"]["with_turns"] == 1
    assert out["sessions"]["levels"]["230000"]["sessions"] == 0  # the old turns do not count
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
    assert out["sessions"]["levels"]["230000"]["sessions"] == 1
    assert out["sessions_with_missed_runs"] == 1


def test_only_main_transcripts_are_sessions(tmp_path):
    _session(tmp_path, "s", [_turn(f"m{i}", 9, cache_read=300_000) for i in range(3)])
    _session(tmp_path, "s", [_turn(f"a{i}", 9, cache_read=300_000) for i in range(30)], agent="a1")
    out = _audit(tmp_path)
    assert out["sessions"]["with_turns"] == 1
    assert out["sessions"]["levels"]["230000"]["sessions"] == 0


# --- main model and per-model thresholds -------------------------------------

def test_main_model_is_the_most_used_and_reported(tmp_path):
    rows = [_turn(f"o{i}", 9, cache_read=300_000, model="claude-opus-5-5") for i in range(30)]
    rows += [_turn("h", 9, cache_read=300_000, model="claude-haiku-5-5")]
    _session(tmp_path, "s", rows)
    out = _audit(tmp_path)["sessions"]
    assert out["levels"]["230000"]["by_model"] == {"claude-opus-5-5": 1}


def test_ceiling_comes_from_the_route_data_per_model():
    c = tca.load_ceilings(CEILINGS)
    assert tca.ceiling_for("claude-opus-5-5", c) == 450_000
    assert tca.ceiling_for("gpt-6.1-sol", c) == 450_000
    assert tca.ceiling_for("claude-fable-5-1", c) == 550_000
    assert tca.ceiling_for("gpt-6-astra", c) == 550_000
    assert tca.ceiling_for("claude-haiku-5-5", c) == 230_000
    assert tca.ceiling_for("", c) == 230_000
    assert tca.ceiling_for("console-model", c) == 230_000  # a word match, not a substring


def test_sessions_over_their_own_model_ceiling(tmp_path):
    ceilings = {
        "default_tokens": 230_000,
        "interface_session": [{"models": ["opus"], "tokens": 450_000}, {"models": ["fable"], "tokens": 550_000}],
    }
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
    assert _audit(tmp_path)["missed_runs"] == 0  # opus ceiling 450K
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
         "--codex-home", str(tmp_path / "nope-codex")],
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
         "--codex-home", str(tmp_path / "nope-codex"), "--since", "2026-11-01"],
        capture_output=True, text=True,
    )
    assert done.returncode == 0, done.stderr
    out = done.stdout
    assert "whole prompt" in out
    assert "sessions with at least one turn: 1" in out
    assert "30 or more turns at or above 450K: 1" in out
    assert "30 or more turns at or above 550K: 0" in out


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
    alone = _audit(tmp_path / "claude")["sessions"]
    assert _runtime(out, "Claude Code")["sessions_with_turns"] == alone["with_turns"] == 1


def test_codex_input_tokens_already_hold_the_cached_part(tmp_path):
    # 440K input of which 300K cached: adding the cached part again would cross 450K.
    _codex_session(tmp_path / "codex", "x", [(9, 440_000, 300_000)] * 30)
    out = _both(tmp_path, roots={"Claude Code": None})
    assert out["sessions"]["over_own_ceiling"]["sessions"] == 0
    assert out["sessions"]["levels"]["230000"]["sessions"] == 1


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
    assert out["sessions"]["levels"]["230000"]["sessions"] == 0


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
    assert "Codex" not in out["sessions"]["levels"]["230000"]["by_runtime"]
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


def test_output_names_pi_as_not_read_and_the_host(tmp_path):
    _codex_session(tmp_path / "codex", "x", [(9, 100_000, 0)])
    out = _both(tmp_path)
    assert _runtime(out, "Pi")["status"] == "not read"
    assert "Pi" in out["runtimes_not_read"]
    assert out["host"]
    table = tca.render_table(out)
    assert out["host"] in table and "Pi" in table


@pytest.mark.integration
def test_cli_reads_codex_beside_an_absent_claude_code_corpus(tmp_path):
    _codex_session(tmp_path / "codex", "x", [(9, 500_000, 0)] * 30)
    done = subprocess.run(
        [sys.executable, str(SCRIPTS / "trace-compact-audit.py"), "--projects-dir", str(tmp_path / "nope"),
         "--codex-home", str(tmp_path / "codex"), "--since", "2026-11-01"],
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
