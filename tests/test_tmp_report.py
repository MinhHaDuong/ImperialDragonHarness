"""Positive controls for the report-only temporary candidate investigation."""

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("tmp_report", ROOT / "scripts/tmp_report.py")
report = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = report
SPEC.loader.exec_module(report)


def test_scan_ranks_candidates_and_excludes_tool_caches(tmp_path):
    temp = tmp_path / "tmp"
    cache = tmp_path / ".cache"
    (temp / "t9999-positive").mkdir(parents=True)
    (temp / "t9999-positive" / "blob").write_bytes(b"x" * 8192)
    (cache / "tmp-t1045").mkdir(parents=True)
    (cache / "tmp-t1045" / "blob").write_bytes(b"x" * 4096)
    (cache / "huggingface").mkdir()
    (cache / "huggingface" / "blob").write_bytes(b"x" * 16384)

    result = report.scan_candidates([temp, cache], known_cache_names={"huggingface"})

    assert [item["path"] for item in result["candidates"]] == [
        str(temp / "t9999-positive"), str(cache / "tmp-t1045")
    ]
    assert result["candidates"][0]["bytes"] >= 8192
    assert not any("huggingface" in item["path"] for item in result["candidates"])


def test_history_attribution_supports_home_spellings_and_redacts_secrets(tmp_path):
    candidate = tmp_path / ".cache" / "tmp-t2043"
    history = tmp_path / "history.jsonl"
    history.write_text(json.dumps({
        "sessionId": "session-positive",
        "cwd": str(tmp_path),
        "message": {"content": "mkdir -p $HOME/.cache/tmp-t2043 API_TOKEN=supersecret"},
    }) + "\n")

    matches = report.find_history_mentions(
        candidate,
        [history],
        home=tmp_path,
        candidate_mtime=0,
    )

    assert matches
    assert matches[0]["session"] == "session-positive"
    assert matches[0]["evidence"] == "attempted"
    assert "supersecret" not in matches[0]["excerpt"]
    assert "tmp-t2043" in matches[0]["excerpt"]


def test_disk_warning_uses_free_fraction_and_names_both_mounts():
    result = report.disk_warnings({
        "/tmp": {"total": 100, "free": 5},
        "/home": {"total": 1000, "free": 400},
    }, threshold=0.10)
    assert result == ["/tmp has 5% free"]


def test_runtime_history_roots_cover_codex_pi_and_claude(tmp_path):
    (tmp_path / ".codex/sessions/2026/10").mkdir(parents=True)
    (tmp_path / ".pi/agent/sessions").mkdir(parents=True)
    (tmp_path / ".claude/projects/proj/subagents").mkdir(parents=True)
    for path in (
        tmp_path / ".codex/sessions/2026/10/rollout.jsonl",
        tmp_path / ".pi/agent/sessions/pi.jsonl",
        tmp_path / ".claude/projects/proj/subagents/agent.jsonl",
    ):
        path.write_text("{}\n")
    files = report.history_files(tmp_path)
    assert {".codex/sessions/2026/10/rollout.jsonl", ".pi/agent/sessions/pi.jsonl", ".claude/projects/proj/subagents/agent.jsonl"} == {
        str(file).removeprefix(str(tmp_path) + "/") for file in files
    }


def test_codemeta_and_pi_session_records_carry_identity_to_later_events(tmp_path):
    target = tmp_path / ".cache/tmp-owned"
    codex = tmp_path / "codex.jsonl"
    codex.write_text(
        json.dumps({"type": "session_meta", "payload": {"id": "codex-thread", "cwd": str(tmp_path)}}) + "\n"
        + json.dumps({"type": "response_item", "payload": {"arguments": "cat $HOME/.cache/tmp-owned"}}) + "\n"
    )
    pi = tmp_path / "pi.jsonl"
    pi.write_text(
        json.dumps({"type": "session", "id": "pi-session", "cwd": str(tmp_path)}) + "\n"
        + json.dumps({"type": "message", "message": {"content": f"see {target}"}}) + "\n"
    )

    found = report.attribute_histories(
        [{"path": str(target), "mtime": 0}], [codex, pi], home=tmp_path
    )[str(target)]
    assert {match["session"] for match in found} == {"codex-thread", "pi-session"}
    assert all("arguments" not in match["excerpt"] for match in found)


def test_roar_scope_keeps_descendant_agents_and_excludes_reporter():
    matches = [
        {"session": "owner", "parent": None},
        {"session": "child", "parent": "owner"},
        {"session": "grandchild", "parent": "child"},
        {"session": "unrelated", "parent": None},
        {"session": "reporter", "parent": None},
    ]
    scoped = report.scope_history(matches, "roar", "owner", "reporter")
    assert [item["session"] for item in scoped] == ["owner", "child", "grandchild"]


def test_disk_warning_cli_surfaces_only_low_mounts(monkeypatch, capsys):
    monkeypatch.setattr(report, "disk_readings", lambda: {
        "/tmp": {"total": 100, "free": 5},
        "/home": {"total": 1000, "free": 400},
    })
    assert report.main(["--disk-warning"]) == 0
    assert capsys.readouterr().out == "Disk headroom warning: /tmp has 5% free (threshold: 10% free)\n"


def test_missing_disk_mount_is_reported_as_unknown(monkeypatch, capsys):
    monkeypatch.setattr(report, "disk_readings", lambda: {"/tmp": {"total": 100, "free": 80}})
    report.main(["--disk-warning"])
    assert capsys.readouterr().out == "Disk headroom warning: /home free space unknown (could not inspect mount) (threshold: 10% free)\n"


def test_codex_creation_requires_matching_call_id_and_explicit_zero_exit(tmp_path):
    target = tmp_path / "tmp-created"
    history = tmp_path / "codex.jsonl"
    history.write_text(
        json.dumps({"type": "session_meta", "payload": {"id": "creator"}}) + "\n"
        + json.dumps({"type": "response_item", "payload": {
            "type": "function_call", "call_id": "call-ok", "name": "exec_command",
            "arguments": json.dumps({"cmd": f"mkdir -p {target}", "workdir": str(tmp_path)}),
        }}) + "\n"
        + json.dumps({"type": "response_item", "payload": {
            "type": "function_call_output", "call_id": "other-call",
            "output": {"exit_code": 0},
        }}) + "\n"
        + json.dumps({"type": "response_item", "payload": {
            "type": "function_call_output", "call_id": "call-ok",
            "output": json.dumps({"exit_code": 0, "stdout": "", "stderr": ""}),
        }}) + "\n"
    )
    found = report.attribute_histories(
        [{"path": str(target), "mtime": 0}], [history], home=tmp_path
    )[str(target)]
    created = next(item for item in found if item["evidence"] == "created")
    assert created["session"] == "creator"
    assert created["call_line"] == 2
    assert created["line"] == 4


def test_claude_creation_requires_native_result_id_and_exit_zero(tmp_path):
    target = tmp_path / "tmp-claude-created"
    history = tmp_path / "claude.jsonl"
    history.write_text(
        json.dumps({"type": "assistant", "sessionId": "claude-creator", "message": {"content": [
            {"type": "tool_use", "id": "toolu-ok", "name": "Bash", "input": {"command": f"mkdir -p {target}"}},
        ]}}) + "\n"
        + json.dumps({"type": "user", "message": {"content": [
            {"type": "tool_result", "tool_use_id": "wrong-id", "is_error": False, "content": "exit code 0"},
        ]}}) + "\n"
        + json.dumps({"type": "user", "message": {"content": [
            {"type": "tool_result", "tool_use_id": "toolu-ok", "is_error": False, "content": "exit code 0"},
        ]}}) + "\n"
    )
    found = report.attribute_histories(
        [{"path": str(target), "mtime": 0}], [history], home=tmp_path
    )[str(target)]
    created = next(item for item in found if item["evidence"] == "created")
    assert created["session"] == "claude-creator"
    assert created["call_line"] == 1
    assert created["line"] == 3


def test_compound_or_nonzero_creation_commands_remain_attempts(tmp_path):
    target = tmp_path / "tmp-attempted"
    history = tmp_path / "codex.jsonl"
    history.write_text(
        json.dumps({"type": "response_item", "payload": {
            "type": "function_call", "call_id": "call-fail", "name": "bash",
            "arguments": f"mkdir -p {target} && echo done",
        }}) + "\n"
        + json.dumps({"type": "response_item", "payload": {
            "type": "function_call_output", "call_id": "call-fail",
            "output": {"exit_code": 1},
        }}) + "\n"
    )
    found = report.attribute_histories(
        [{"path": str(target), "mtime": 0}], [history], home=tmp_path
    )[str(target)]
    assert found
    assert all(item["evidence"] != "created" for item in found)


def test_nested_codex_subagent_parent_link_is_extracted():
    session, parent, _pid = report._identity({
        "type": "response_item",
        "payload": {"source": {"subagent": {"thread_spawn": {
            "thread_id": "child", "parent_thread_id": "owner"
        }}}},
    })
    assert session == "child"
    assert parent == "owner"


def test_claude_agent_id_is_child_of_its_session():
    session, parent, _pid = report._identity({
        "type": "user", "sessionId": "claude-parent", "agentId": "claude-child",
    })
    assert session == "claude-child"
    assert parent == "claude-parent"


def test_build_report_returns_after_enriching_candidates(tmp_path, monkeypatch):
    root = tmp_path / "tmp"
    (root / "candidate").mkdir(parents=True)
    (root / "candidate" / "file").write_bytes(b"x" * 1024)
    monkeypatch.setattr(report, "_default_roots", lambda _repo: [root])
    monkeypatch.setattr(report, "history_files", lambda *_a, **_k: ([], []))
    monkeypatch.setattr(report, "_references", lambda candidates, _repo: {
        item["path"]: {"git_log": False, "pull_requests": [], "verdict_files": []}
        for item in candidates
    })
    monkeypatch.setattr(report, "disk_readings", lambda: {})
    monkeypatch.setattr(report, "infer_test_provenance", lambda *_a: None)

    result = report.build_report("codex", "lair", None, str(tmp_path), floor_bytes=1)

    assert len(result["candidates"]) == 1
    assert result["candidates"][0]["path"] == str(root / "candidate")


def test_scan_aggregates_worktree_tmp_and_deduplicates_nested_roots(tmp_path):
    worktree_tmp = tmp_path / "worktree" / ".tmp"
    (worktree_tmp / "logs").mkdir(parents=True)
    (worktree_tmp / "logs" / "run.log").write_bytes(b"x" * 1024)
    parent = tmp_path / "tmp-root"
    nested = parent / "runtime"
    (nested / "owned").mkdir(parents=True)
    (nested / "owned" / "blob").write_bytes(b"y" * 1024)

    result = report.scan_candidates([worktree_tmp, parent, nested])
    paths = [item["path"] for item in result["candidates"]]
    assert str(worktree_tmp) in paths
    assert str(nested / "owned") in paths
    assert str(nested) not in paths


def test_scan_reports_roots_it_cannot_read(tmp_path, monkeypatch):
    blocked = tmp_path / "blocked"
    blocked.mkdir()
    real_scandir = report.os.scandir

    def fake_scandir(path):
        if str(path) == str(blocked):
            raise PermissionError(13, "fixture unreadable", str(blocked))
        return real_scandir(path)

    monkeypatch.setattr(report.os, "scandir", fake_scandir)
    result = report.scan_candidates([blocked])
    assert result["candidates"] == []
    assert result["unreadable"] == [str(blocked)]


def test_allocated_bytes_names_unreadable_nested_directory(tmp_path, monkeypatch):
    root = tmp_path / "tree"
    blocked = root / "nested"
    blocked.mkdir(parents=True)
    real_scandir = report.os.scandir

    def fake_scandir(path):
        if str(path) == str(blocked):
            raise PermissionError(13, "fixture unreadable", str(blocked))
        return real_scandir(path)

    monkeypatch.setattr(report.os, "scandir", fake_scandir)
    _bytes, _truncated, unreadable = report.allocated_bytes(root)
    assert str(blocked) in unreadable


def test_test_source_match_is_labeled_as_inference(tmp_path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests/test_temp.py").write_text(
        'tempfile.mkdtemp(prefix="glossary-0882-")\n'
    )
    result = report.infer_test_provenance(
        tmp_path / "glossary-0882-randomsuffix", tmp_path
    )
    assert result["evidence"] == "inferred"
    assert result["file"].endswith("test_temp.py")
    assert result["session"] is None
