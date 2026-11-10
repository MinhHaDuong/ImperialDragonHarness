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
        [sys.executable, str(SCRIPTS / "trace-compact-audit.py"), "--projects-dir", str(tmp_path / "nope")],
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
         "--since", "2026-11-01"],
        capture_output=True, text=True,
    )
    assert done.returncode == 0, done.stderr
    out = done.stdout
    assert "whole prompt" in out
    assert "sessions with at least one turn: 1" in out
    assert "30 or more turns at or above 450K: 1" in out
    assert "30 or more turns at or above 550K: 0" in out
