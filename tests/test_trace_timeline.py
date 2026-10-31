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


def test_unique_prefix_resolves_live_and_archive_and_ambiguous_lists_candidates(tmp_path):
    live = build_live(tmp_path / "live")
    other = "11111111-ffff-bbbb-cccc-000000000009"
    put(live["claude"][0] / "proj" / f"{other}.jsonl", claude_rows(other, 0, 10))
    archive = tmp_path / "archive"
    packed = archive / "claude" / "proj" / "33333333-aaaa-bbbb-cccc-000000000003.jsonl.zst"
    packed.parent.mkdir(parents=True)
    packed.write_bytes(b"")
    tree = tl.Tree(live, archive)
    assert tl.resolve_session(tree, "11111111-a") == SID
    assert tl.resolve_session(tree, SID) == SID
    assert tl.resolve_session(tree, "3333") == "33333333-aaaa-bbbb-cccc-000000000003"  # archive only
    with pytest.raises(SystemExit) as raised:
        tl.resolve_session(tree, "1111")
    assert SID in str(raised.value) and other in str(raised.value)
    assert tl.resolve_session(tree, "zzzz") == "zzzz"  # unknown: collect reports it


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
    for needle in ('<h1>', 'id="mm"', "'wheel'", "'mousedown'", "data-band", "one model turn", "wall-clock"):
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


def test_json_gains_only_a_class_field_on_tool_events(tmp_path):
    tree = tl.Tree(build_live(tmp_path), tmp_path / "archive")
    doc = render(tree, [])
    base = {"pointer", "runtime", "agent", "model", "tokens", "shadow_usd", "cost_source", "exit"}
    for e in doc["traceEvents"]:
        if e.get("ph") != "X":
            continue
        extra = set(e["args"]) - base
        if e["cat"] == "tool":
            assert e["args"]["class"] == "other" and extra <= {"class", "detail"}
        else:
            assert "class" not in e["args"]


def test_html_colours_tools_by_class_with_legend_tooltip_and_model_labels(tmp_path):
    tree = tl.Tree(build_live(tmp_path), tmp_path / "archive")
    doc = render(tree, [])
    tool = next(e for e in doc["traceEvents"] if e.get("cat") == "tool")
    tool["args"]["class"] = "tests"
    page = tl.render_html(doc, SID)
    assert tl._CLASS_COLORS["tests"] in page and "class: tests" in page
    colours = [c for _cap, entries in tl._LEGEND for _n, c, _m, _o in entries]
    assert len(colours) == len(set(colours))  # no two legend entries share a colour
    assert set(tl._CLASS_COLORS.values()) <= set(colours)
    for _cap, entries in tl._LEGEND:
        for name, _c, _m, _o in entries:
            assert f"{name}: " in page
    assert 'id="grip"' in page and "data-fb=" in page and "idle" not in page
    assert 'id="lab"' in page and 'id="cur"' in page and "position:sticky" in page
    assert 'data-m="claude-sonnet-5-5"' in page or 'data-m=""' in page
    assert "style=" not in page.split("<svg id=\"tl\"")[1].split("</svg>")[0]


# ---- delegation mode and launch connectors (ticket 1397) --------------------------------------------

te = tl.te


def test_delegation_mode_rule_from_the_recorded_result():
    info = te.delegation_info
    assert info("Agent", {"isAsync": True, "status": "async_launched", "agentId": "a1"}) == ("launch", "a1")
    assert info("Skill", {"status": "forked", "background": True, "agentId": "a2"}) == ("launch", "a2")
    assert info("Skill", {"status": "forked", "agentId": "a3"}) == ("blocking", "a3")
    assert info("Agent", {"status": "completed", "agentId": "a4"}) == ("blocking", "a4")
    assert info("Skill", {"success": True, "commandName": "merge"}) == (None, None)  # inline skill
    assert info("Skill", None) == (None, None) and info("Bash", {"agentId": "x"}) == (None, None)


def delegation_session(tmp_path, results):
    """Parent session with one Agent/Skill call per `results` item ((tool, result dict, call end s)) and one
    child file per agentId named in them; call i starts at second 10+i*10."""
    root = tmp_path / "claude"
    sub = root / "proj" / SID / "subagents"
    rows = [{"type": "user", "timestamp": "2026-01-01T00:00:00.000Z", "sessionId": SID, "message": {"content": "go"}}]

    def t(sec):
        return f"2026-01-01T00:{sec // 60:02d}:{sec % 60:02d}.000Z"
    for i, (tool, result, end) in enumerate(results):
        start = 10 + i * 10
        rows.append({"type": "assistant", "timestamp": t(start), "sessionId": SID, "message": {
            "id": f"m{i}", "model": "claude-sonnet-5-5", "usage": {"input_tokens": 1, "output_tokens": 1},
            "content": [{"type": "tool_use", "id": f"tu{i}", "name": tool, "input": {}}]}})
        rows.append({"type": "user", "timestamp": t(end), "sessionId": SID, "toolUseResult": result, "message": {
            "content": [{"type": "tool_result", "tool_use_id": f"tu{i}", "content": "ok"}]}})
        child = (result or {}).get("agentId") if isinstance(result, dict) else None
        if child and child != "ghost":  # "ghost": a recorded child with no transcript
            put(sub / f"agent-{child}.jsonl", claude_rows(child, start + 2, start + 8, with_tool=False))
            (sub / f"agent-{child}.meta.json").write_text(json.dumps({"description": child, "parentAgentId": None}))
    rows.append({"type": "user", "timestamp": t(100), "sessionId": SID, "message": {"content": "end"}})
    put(root / "proj" / f"{SID}.jsonl", rows)
    return tl.Tree({"claude": [root]}, tmp_path / "archive")


def delegations(doc):
    return {e["name"] + e["args"]["pointer"]["call_id"]: e["args"] for e in doc["traceEvents"]
            if e.get("cat") == "tool"}


def test_delegation_calls_carry_mode_and_matched_child_additively(tmp_path):
    tree = delegation_session(tmp_path, [
        ("Agent", {"isAsync": True, "status": "async_launched", "agentId": "ca"}, 11),
        ("Skill", {"status": "forked", "agentId": "cb"}, 28),
        ("Skill", {"success": True, "commandName": "merge"}, 31),
        ("Agent", {"isAsync": True, "status": "async_launched", "agentId": "ghost"}, 41)])
    doc = tl.render(tl.collect(tree, SID, []))
    got = delegations(doc)
    assert got["Agenttu0"]["delegation"] == "launch" and got["Agenttu0"]["child_agent"] == "ca"
    assert got["Skilltu1"]["delegation"] == "blocking" and got["Skilltu1"]["child_agent"] == "cb"
    assert "delegation" not in got["Skilltu2"] and "child_agent" not in got["Skilltu2"]
    # a recorded child that is not in the tree is an unmatched launch: mode kept, no link
    assert got["Agenttu3"]["delegation"] == "launch" and "child_agent" not in got["Agenttu3"]
    base = {"pointer", "runtime", "agent", "model", "tokens", "shadow_usd", "cost_source", "exit", "class", "detail"}
    for args in got.values():
        assert set(args) - base <= {"delegation", "child_agent", "returned_us"}


def test_child_matched_by_meta_tool_use_id_and_timing_fallback(tmp_path):
    tree = delegation_session(tmp_path, [("Agent", {"status": "x"}, 11), ("Agent", {"status": "x"}, 28)])
    for n in (0, 1):  # no agentId in either result: only the child's meta names its launching call
        sub = tmp_path / "claude" / "proj" / SID / "subagents"
        put(sub / f"agent-k{n}.jsonl", claude_rows(f"k{n}", 12 + n * 10, 18 + n * 10, with_tool=False))
        (sub / f"agent-k{n}.meta.json").write_text(json.dumps({"description": f"k{n}", "toolUseId": f"tu{n}"}))
    got = delegations(tl.render(tl.collect(tree, SID, [])))
    assert got["Agenttu0"]["child_agent"] == "k0" and got["Agenttu0"]["delegation"] == "launch"  # returned at 11 < 18
    assert got["Agenttu1"]["child_agent"] == "k1" and got["Agenttu1"]["delegation"] == "blocking"  # returned at 28 >= 28


def test_html_hatches_blocking_draws_link_data_and_has_the_toggle(tmp_path):
    tree = delegation_session(tmp_path, [
        ("Agent", {"isAsync": True, "status": "async_launched", "agentId": "ca"}, 11),
        ("Skill", {"status": "forked", "agentId": "cb"}, 28),
        ("Agent", {"isAsync": True, "status": "async_launched", "agentId": "ghost"}, 41)])
    page = tl.render_html(tl.render(tl.collect(tree, SID, [])), SID)
    assert 'id="lk" checked' in page and 'id="links"' in page and 'id="hatch"' in page
    assert page.count('fill="url(#hatch)"') == 1  # the one blocking call
    assert "delegation: blocking" in page and "delegation: launch" in page
    links = json.loads(page.split('id="linkdata">')[1].split("</script>")[0])
    assert len(links) == 1 and links[0][1] < links[0][3]  # the unmatched launch draws none; ends at the child's start
    assert "2 launches, 1 linked to a child lane" in page
    assert "http://" not in page.replace("http://www.w3.org/2000/svg", "") and "https://" not in page


def test_launch_bar_ends_at_its_return_in_html_while_json_keeps_the_completion_length(tmp_path):
    tree = delegation_session(tmp_path, [
        ("Agent", {"isAsync": True, "status": "async_launched", "agentId": "ca"}, 11)])
    path = tmp_path / "claude" / "proj" / f"{SID}.jsonl"
    note = {"type": "queue-operation", "operation": "enqueue", "timestamp": "2026-01-01T00:01:00.000Z",
            "content": "<task-notification><tool-use-id>tu0</tool-use-id></task-notification>"}
    rows = [json.loads(x) for x in path.read_text().splitlines()]
    put(path, rows[:-1] + [note, rows[-1]])
    doc = tl.render(tl.collect(tree, SID, []))
    call = next(e for e in doc["traceEvents"] if e.get("cat") == "tool")
    assert call["dur"] == 50_000_000  # call start 10 s, completion notification at 60 s: the JSON bar length
    assert call["args"]["returned_us"] == 11_000_000  # offset of the return from t0: 1 s after the call start
    page = tl.render_html(doc, SID)
    assert 'data-d="1.0"' in page and 'data-d="50.0"' not in page
    assert "returned after: 1.0s" in page and "completed after: 50.0s" in page
