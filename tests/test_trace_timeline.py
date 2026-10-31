"""Tests for scripts/trace_timeline.py: lanes, seats under their parent, archive fallback (ticket 1385).

Fixtures are hand-written rows, not excerpts of real transcripts.
"""
import importlib.util
import json
import shutil
import subprocess
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
spec = importlib.util.spec_from_file_location("trace_timeline_under_test", SCRIPTS / "trace_timeline.py")
tl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tl)

SID = "11111111-aaaa-bbbb-cccc-000000000001"
SEAT = "22222222-aaaa-bbbb-cccc-000000000002"


def put(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(r if isinstance(r, str) else json.dumps(r) for r in rows) + "\n"
    path.write_text(text, encoding="utf-8")


def claude_rows(sid, start_s, end_s, with_tool=True):
    """A session whose first row is at second `start_s` and last at `end_s`, one Bash call in between."""
    def t(sec):
        return f"2026-01-01T00:{sec // 60:02d}:{sec % 60:02d}.000Z"
    rows = [{"type": "user", "timestamp": t(start_s), "sessionId": sid, "message": {"content": "go"}}]
    if with_tool:
        rows += [
            {"type": "assistant", "timestamp": t(start_s + 1), "sessionId": sid, "message": {
                "id": f"m-{sid[:2]}", "model": "claude-sonnet-5-5", "usage": {"input_tokens": 1, "output_tokens": 1},
                "content": [{"type": "tool_use", "id": f"tu-{sid[:2]}", "name": "Bash", "input": {}}]}},
            {"type": "user", "timestamp": t(start_s + 2), "sessionId": sid, "message": {"content": [
                {"type": "tool_result", "tool_use_id": f"tu-{sid[:2]}", "content": "ok"}]}},
        ]
    rows.append({"type": "user", "timestamp": t(end_s), "sessionId": sid, "message": {"content": "end"}})
    return rows


def pi_rows(start_s, end_s):
    def t(sec):
        return f"2026-01-01T00:{sec // 60:02d}:{sec % 60:02d}.000Z"
    usage = {"input": 5, "output": 2, "cost": {"total": 0}}
    return [{"type": "session", "id": "pi-seat", "timestamp": t(start_s)},
            {"type": "message", "id": "e1", "timestamp": t(end_s), "message": {
                "role": "assistant", "model": "local", "usage": usage, "content": []}}]


def launch(child_runtime, child_session, start="2026-01-01T00:00:20Z", end="2026-01-01T00:00:40Z"):
    return {"ts_start": start, "ts_end": end, "host": "h", "parent_runtime": "claude", "parent_session": SID,
            "child_runtime": child_runtime, "child_session": child_session, "seat": "s", "exit": 0}


def build_live(root: Path):
    claude = root / "claude"
    put(claude / "proj" / f"{SID}.jsonl", claude_rows(SID, 0, 100))
    sub = claude / "proj" / SID / "subagents"
    for name, (a, b) in {"agent-a1": (10, 50), "agent-a2": (30, 70), "agent-a3": (80, 90)}.items():
        put(sub / f"{name}.jsonl", claude_rows(name, a, b, with_tool=False))
        (sub / f"{name}.meta.json").write_text(json.dumps({"description": name.upper(), "parentAgentId": None}))
    pi = root / "pi"
    put(pi / "seat.jsonl", pi_rows(25, 35))
    return {"claude": [claude], "pi": [pi]}


def lane_of(doc, label_prefix):
    (span,) = [e for e in doc["traceEvents"] if e.get("cat") == "agent" and e["name"].startswith(label_prefix)]
    return span["pid"], span


def render(tree, launches):
    return tl.render(tl.collect(tree, SID, launches))


def test_assign_lanes_greedy():
    lanes = tl.assign_lanes([("a", 0, 10), ("b", 5, 15), ("c", 10, 12), ("d", 20, 30)])
    assert lanes == {"a": 0, "b": 1, "c": 0, "d": 0}


def test_overlapping_subagents_get_distinct_lanes_and_calls_stay_in_lane(tmp_path):
    tree = tl.Tree(build_live(tmp_path), tmp_path / "archive")
    doc = render(tree, [])
    main = lane_of(doc, "claude 11111111")[0]
    p1, p2, p3 = (lane_of(doc, f"AGENT-A{i}")[0] for i in (1, 2, 3))
    assert len({main, p1, p2}) == 3  # all three overlap
    assert p3 in (p1, p2)  # a3 starts after a1 ended and reuses its lane
    call = [e for e in doc["traceEvents"] if e.get("cat") == "tool"][0]
    assert call["pid"] == main and call["tid"] >= 1
    assert call["args"]["pointer"] == {"file": f"proj/{SID}.jsonl", "call_id": "tu-11"}


def test_seat_named_by_a_launch_line_lands_under_its_parent(tmp_path):
    live = build_live(tmp_path)
    seat_path = tmp_path / "pi" / "seat.jsonl"
    tree = tl.Tree(live, tmp_path / "archive")
    doc = render(tree, [launch("pi", str(seat_path)), {"parent_session": "someone-else", "child_runtime": "pi",
                                                       "child_session": str(seat_path)}])
    pid, span = lane_of(doc, "s/pi")
    assert span["args"]["parent_agent"] == SID
    assert span["name"].endswith("(under claude 11111111)")
    assert pid != lane_of(doc, "claude 11111111")[0]  # overlaps its parent, so another lane
    assert len([e for e in doc["traceEvents"] if e.get("cat") == "agent" and e["name"].startswith("s/pi")]) == 1
    turn = [e for e in doc["traceEvents"] if e.get("cat") == "turn" and e["args"]["runtime"] == "pi"][0]
    assert turn["args"]["cost_source"] == "pi-recorded" and turn["args"]["shadow_usd"] == 0.0


def test_unpriced_model_renders_cost_unknown_and_missing_seat_keeps_a_span(tmp_path):
    live = build_live(tmp_path)
    rows = claude_rows(SID, 0, 100)
    rows[1]["message"]["model"] = "some-local-model"
    put(live["claude"][0] / "proj" / f"{SID}.jsonl", rows)
    doc = render(tl.Tree(live, tmp_path / "archive"), [launch("aider", "/nowhere/chat.md")])
    turn = [e for e in doc["traceEvents"] if e.get("cat") == "turn"][0]
    assert turn["args"]["shadow_usd"] == "cost unknown"
    pid, span = lane_of(doc, "s/aider")
    assert span["args"]["pointer"]["call_id"] is None and span["args"]["shadow_usd"] == "cost unknown"


def test_concurrent_seats_without_transcript_get_distinct_lanes(tmp_path):
    live = build_live(tmp_path)
    launches = [launch("codex", "not captured", "2026-01-01T00:00:20Z", "2026-01-01T00:01:00Z"),
                launch("codex", "not captured", "2026-01-01T00:00:30Z", "2026-01-01T00:01:10Z")]
    doc = render(tl.Tree(live, tmp_path / "archive"), launches)
    spans = [e for e in doc["traceEvents"] if e.get("cat") == "agent" and e["name"].startswith("s/codex")]
    assert len(spans) == 2
    assert spans[0]["pid"] != spans[1]["pid"]


def test_unknown_session_exits_with_a_message(tmp_path):
    with pytest.raises(SystemExit):
        tl.collect(tl.Tree({"claude": [tmp_path]}, tmp_path / "archive"), SID, [])


@pytest.mark.integration
@pytest.mark.skipif(shutil.which("zstd") is None, reason="zstd CLI missing")
def test_session_pruned_from_the_live_tree_renders_from_the_archive(tmp_path):
    live = build_live(tmp_path / "live")
    archive = tmp_path / "archive"
    for runtime, roots in live.items():
        for root in roots:
            for path in root.rglob("*"):
                if path.is_file():
                    dest = archive / runtime / (path.relative_to(root).as_posix() + ".zst")
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    subprocess.run(["zstd", "-q", "-o", str(dest), str(path)], check=True)
    seat_live = str(live["pi"][0] / "seat.jsonl")
    launches = [launch("pi", seat_live)]
    expected = render(tl.Tree(live, archive), launches)
    pruned = tl.Tree({"claude": [tmp_path / "empty"], "pi": [live["pi"][0]]}, archive)  # live tree: nothing
    pruned.live["pi"][0] = live["pi"][0]
    shutil.rmtree(live["claude"][0])
    shutil.rmtree(live["pi"][0])
    assert render(pruned, launches) == expected


@pytest.mark.integration
def test_cli_writes_trace_json(tmp_path):
    live = build_live(tmp_path / "live")
    launches = tmp_path / "launches.jsonl"
    launches.write_text(json.dumps(launch("claude", SEAT)) + "\n")
    out = tmp_path / "out.json"
    result = subprocess.run(
        ["python3", str(SCRIPTS / "trace_timeline.py"), SID, "--out", str(out), "--live-root",
         str(live["claude"][0]), "--archive-root", str(tmp_path / "arch"), "--launches", str(launches)],
        capture_output=True, text=True, env={"HOME": str(tmp_path), "PATH": "/usr/bin:/bin"})
    assert result.returncode == 0, result.stderr
    doc = json.loads(out.read_text())
    assert doc["traceEvents"] and "not found" in result.stderr  # the seat's transcript is absent: warned, span kept


def test_html_is_self_contained_and_matches_the_json_bars(tmp_path):
    tree = tl.Tree(build_live(tmp_path), tmp_path / "archive")
    doc = render(tree, [launch("pi", str(tmp_path / "pi" / "seat.jsonl"))])
    page = tl.render_html(doc, SID)
    import re
    assert not re.search(r"https?://(?!www\.w3\.org/2000/svg)", page)
    assert "<link" not in page and "<script src" not in page and " src=" not in page and " href=" not in page
    bars = [e for e in doc["traceEvents"] if e.get("ph") == "X"]
    assert page.count("<rect") == len(bars)
    lanes = {e["pid"] for e in bars}
    assert "\u21b3 calls" in page and "lane 1 / calls" not in page and len(lanes) >= 3
    assert "cost unknown" in page or "shadow USD: 0" in page
    for needle in ('<h1>', 'id="mm"', "'wheel'", "'mousedown'", "data-band", "one tool call", "wall-clock"):
        assert needle in page
    assert "pointer: " in page and "tu-11" in page and "model: claude-sonnet-5-5" in page


@pytest.mark.integration
def test_cli_html_leaves_json_byte_identical(tmp_path):
    live = build_live(tmp_path / "live")
    launches = tmp_path / "launches.jsonl"
    launches.write_text("")
    outs = {}
    for name, extra in (("plain", []), ("html", ["--html", str(tmp_path / "t.html")])):
        out = tmp_path / f"{name}.json"
        r = subprocess.run(["python3", str(SCRIPTS / "trace_timeline.py"), SID, "--out", str(out), "--live-root",
                            str(live["claude"][0]), "--archive-root", str(tmp_path / "arch"), "--launches",
                            str(launches)] + extra, capture_output=True, text=True,
                           env={"HOME": str(tmp_path), "PATH": "/usr/bin:/bin"})
        assert r.returncode == 0, r.stderr
        outs[name] = out.read_bytes()
    assert outs["plain"] == outs["html"]
    assert (tmp_path / "t.html").read_text().startswith("<!DOCTYPE html>")
