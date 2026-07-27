"""Tests for scripts/trace-compact-audit.py — missed compact/clear detector (ticket 0239)."""

import importlib.util
import json
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"

spec = importlib.util.spec_from_file_location(
    "trace_compact_audit", SCRIPTS / "trace-compact-audit.py"
)
tca = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tca)


def _assistant_row(msg_id, cache_read, model="claude-opus-4-8", ts_str="2026-06-09T10:00:00.000Z"):
    return {
        "type": "assistant",
        "timestamp": ts_str,
        "message": {
            "id": msg_id,
            "model": model,
            "role": "assistant",
            "usage": {
                "input_tokens": 10,
                "output_tokens": 10,
                "cache_read_input_tokens": cache_read,
                "cache_creation_input_tokens": 0,
            },
            "content": [{"type": "text", "text": "x"}],
        },
    }


def _compact_row(post_tokens=12_000):
    return {
        "type": "system",
        "subtype": "compact_boundary",
        "timestamp": "2026-06-09T10:30:00.000Z",
        "compactMetadata": {"trigger": "auto", "preTokens": 170_000, "postTokens": post_tokens},
    }


def _clear_row():
    return {
        "type": "user",
        "timestamp": "2026-06-09T10:30:00.000Z",
        "message": {
            "role": "user",
            "content": "<command-name>/clear</command-name>\n<command-message>clear</command-message>",
        },
    }


def _write(tmp_path, rows, name="session.jsonl"):
    f = tmp_path / name
    f.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    return f


def _ramp(n, cache_read=400_000, prefix="msg"):
    return [_assistant_row(f"{prefix}_{i}", cache_read) for i in range(n)]


def test_flags_uncompacted_ramp(tmp_path):
    """The ticket's mandated fixture: a >=30-turn high-cache_read run with no
    compact_boundary is flagged."""
    traj = tca.parse_trajectory(_write(tmp_path, _ramp(35)))
    runs = tca.find_missed_runs(traj["events"], min_run=30, threshold=300_000)
    assert len(runs) == 1
    assert runs[0]["length"] == 35


def test_compacted_ramp_not_flagged(tmp_path):
    """Same ramp with a compact_boundary mid-run: both segments are under
    min_run, so nothing is flagged."""
    rows = _ramp(17, prefix="a") + [_compact_row()] + _ramp(17, prefix="b")
    traj = tca.parse_trajectory(_write(tmp_path, rows))
    runs = tca.find_missed_runs(traj["events"], min_run=30, threshold=300_000)
    assert runs == []


def test_clear_breaks_run(tmp_path):
    rows = _ramp(17, prefix="a") + [_clear_row()] + _ramp(17, prefix="b")
    traj = tca.parse_trajectory(_write(tmp_path, rows))
    runs = tca.find_missed_runs(traj["events"], min_run=30, threshold=300_000)
    assert runs == []


def test_below_threshold_turn_breaks_run(tmp_path):
    rows = _ramp(17, prefix="a") + [_assistant_row("low", 50_000)] + _ramp(17, prefix="b")
    traj = tca.parse_trajectory(_write(tmp_path, rows))
    runs = tca.find_missed_runs(traj["events"], min_run=30, threshold=300_000)
    assert runs == []


def test_turns_deduped_by_message_id(tmp_path):
    """One message spans multiple JSONL rows: one turn event, not three."""
    rows = [_assistant_row("dup", 400_000)] * 3 + [_assistant_row("other", 400_000)]
    traj = tca.parse_trajectory(_write(tmp_path, rows))
    turns = [e for e in traj["events"] if e["kind"] == "turn"]
    assert len(turns) == 2


def test_synthetic_records_not_turns(tmp_path):
    rows = [_assistant_row("s1", 400_000, model="<synthetic>")]
    traj = tca.parse_trajectory(_write(tmp_path, rows))
    assert [e for e in traj["events"] if e["kind"] == "turn"] == []


def test_post_compact_reads_collected(tmp_path):
    """The first turn after each compact_boundary feeds the corpus median."""
    rows = _ramp(2, prefix="a") + [_compact_row()] + [_assistant_row("after", 15_000)]
    traj = tca.parse_trajectory(_write(tmp_path, rows))
    assert traj["post_compact_reads"] == [15_000]
    assert traj["post_compact_tokens"] == [12_000]


def test_recoverable_usd_upper_bound():
    """31 Opus turns at 400K vs a 20K post-compact counterfactual: the first
    turn pays for the compaction, the remaining 30 each save 380K cache_read."""
    turns = [{"kind": "turn", "cache_read": 400_000, "model": "claude-opus-4-8"}] * 31
    usd = tca.run_recoverable_usd(turns, median_post=20_000)
    expected = 30 * 380_000 * tca.ts.PRICING["opus"]["cache_read"] / 1_000_000
    assert abs(usd - expected) < 1e-9


def test_recoverable_usd_never_negative():
    turns = [{"kind": "turn", "cache_read": 10_000, "model": "claude-opus-4-8"}] * 5
    assert tca.run_recoverable_usd(turns, median_post=20_000) == 0.0


def test_quoted_clear_does_not_break_run(tmp_path):
    """Trace text quoted in a user message keeps the JSON-escaped newline as
    a literal backslash-n: not a real /clear, must not break the run."""
    quoted = {
        "type": "user",
        "timestamp": "2026-06-09T10:30:00.000Z",
        "message": {
            "role": "user",
            "content": "look: <command-name>/clear</command-name>\\n<command-message>clear</command-message>",
        },
    }
    rows = _ramp(17, prefix="a") + [quoted] + _ramp(17, prefix="b")
    traj = tca.parse_trajectory(_write(tmp_path, rows))
    runs = tca.find_missed_runs(traj["events"], min_run=30, threshold=300_000)
    assert len(runs) == 1
    assert runs[0]["length"] == 34


def test_clear_detected_in_list_form_content(tmp_path):
    listy = {
        "type": "user",
        "timestamp": "2026-06-09T10:30:00.000Z",
        "message": {
            "role": "user",
            "content": [{"type": "text", "text": _clear_row()["message"]["content"]}],
        },
    }
    rows = _ramp(17, prefix="a") + [listy] + _ramp(17, prefix="b")
    traj = tca.parse_trajectory(_write(tmp_path, rows))
    assert tca.find_missed_runs(traj["events"], min_run=30, threshold=300_000) == []


def test_malformed_lines_tolerated(tmp_path):
    f = tmp_path / "bad.jsonl"
    f.write_text("{not json\n" + json.dumps(_assistant_row("ok", 400_000)) + "\n")
    traj = tca.parse_trajectory(f)
    assert len([e for e in traj["events"] if e["kind"] == "turn"]) == 1


def test_cli_flags_present():
    src = (SCRIPTS / "trace-compact-audit.py").read_text()
    for flag in ("--projects-dir", "--days", "--threshold", "--min-run", "--output", "--json"):
        assert flag in src, f"missing CLI flag {flag}"
    assert "ArgumentParser" in src


# --- corpus-wide dedup of forked/resumed sessions ----------------------------
# parse_trajectory dedups turns by message id within ONE file. A fork or resume
# replays the parent's records verbatim into a NEW file, so the per-file set
# never sees them and every inherited turn is counted twice. On the 2026-07-27
# census this overstated recoverable compaction by 27% ($285.33 -> $208.99,
# same corpus, 12 missed runs -> 8).

from datetime import datetime, timezone  # noqa: E402


def _ts(minute):
    return datetime(2026, 6, 9, 10, minute, tzinfo=timezone.utc)


def _traj(events, first_ts):
    return {"events": events, "first_ts": first_ts}


def _turn(msg_id, cache_read=400_000):
    return {
        "kind": "turn",
        "cache_read": cache_read,
        "model": "claude-opus-4-8",
        "msg_id": msg_id,
    }


def test_fork_inherited_turns_counted_once():
    """The child replays the parent's turns; only the parent keeps them."""
    parent = _traj([_turn("a"), _turn("b")], _ts(0))
    child = _traj([_turn("a"), _turn("b"), _turn("c")], _ts(5))
    trajectories = [("p", "parent", "main", parent), ("p", "child", "main", child)]

    dropped = tca.drop_inherited_turns(trajectories)

    assert dropped == 2
    assert [e["msg_id"] for e in parent["events"]] == ["a", "b"]
    assert [e["msg_id"] for e in child["events"]] == ["c"], (
        "child must keep only the turns it actually added"
    )


def test_dedup_is_oldest_first_regardless_of_input_order():
    """Attribution must follow session start time, not iteration order — the
    trace-file walk gives no ordering guarantee, so a child listed first would
    otherwise steal the parent's turns and leave the parent empty."""
    parent = _traj([_turn("a"), _turn("b")], _ts(0))
    child = _traj([_turn("a"), _turn("b"), _turn("c")], _ts(5))
    trajectories = [("p", "child", "main", child), ("p", "parent", "main", parent)]

    tca.drop_inherited_turns(trajectories)

    assert [e["msg_id"] for e in parent["events"]] == ["a", "b"]
    assert [e["msg_id"] for e in child["events"]] == ["c"]


def test_dedup_preserves_compact_and_clear_events():
    """A fork genuinely re-enters compact/clear state — those events are not
    inherited spend and must survive, or run detection silently re-merges runs
    that were really broken."""
    parent = _traj([_turn("a"), {"kind": "compact"}], _ts(0))
    child = _traj([_turn("a"), {"kind": "clear"}, _turn("z")], _ts(5))
    trajectories = [("p", "parent", "main", parent), ("p", "child", "main", child)]

    tca.drop_inherited_turns(trajectories)

    assert [e["kind"] for e in child["events"]] == ["clear", "turn"]
    assert [e["kind"] for e in parent["events"]] == ["turn", "compact"]


def test_turns_without_message_id_are_never_dropped():
    """Defensive: an unidentifiable turn cannot be proven inherited, so keep it
    rather than silently under-report."""
    a = _traj([{"kind": "turn", "cache_read": 1, "model": "m"}], _ts(0))
    b = _traj([{"kind": "turn", "cache_read": 1, "model": "m"}], _ts(5))
    trajectories = [("p", "a", "main", a), ("p", "b", "main", b)]

    assert tca.drop_inherited_turns(trajectories) == 0
    assert len(a["events"]) == 1 and len(b["events"]) == 1


def test_distinct_sessions_are_not_deduped():
    """Two unrelated sessions share no message ids — nothing may be dropped."""
    a = _traj([_turn("a1"), _turn("a2")], _ts(0))
    b = _traj([_turn("b1"), _turn("b2")], _ts(5))
    trajectories = [("p", "a", "main", a), ("p", "b", "main", b)]

    assert tca.drop_inherited_turns(trajectories) == 0
