"""Tests for scripts/census/repo-memory-reads.py on fixture transcripts."""

import importlib.util
import json
from pathlib import Path

CENSUS = Path(__file__).resolve().parent.parent / "scripts" / "census"
spec = importlib.util.spec_from_file_location("repo_memory_reads", CENSUS / "repo-memory-reads.py")
rmr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rmr)

REPO = "/home/u/proj/memory/"


def tool(name, **inp):
    return {"type": "assistant", "timestamp": "2026-10-20T10:00:00Z",
            "message": {"content": [{"type": "tool_use", "name": name, "input": inp}]}}


def user(text, ts="2026-10-20T09:00:00Z"):
    return {"type": "user", "timestamp": ts, "message": {"content": text}}


def write(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))


def claude_tree(root, with_maint_read=True):
    d = root / "-x-agents"
    write(d / "a.jsonl", [user("hi"), tool("Read", file_path=REPO + "topics/a.md")])
    write(d / "b.jsonl", [user("hi"), tool("Read", file_path="/home/u/.claude/projects/-x/memory/MEMORY.md")])
    write(d / "c.jsonl", [user("see memory/topics/a.md"), tool("Bash", command="ls")])
    write(d / "d.jsonl", [user("old", "2026-10-01T00:00:00Z"), tool("Read", file_path=REPO + "topics/a.md")])
    rows = [user("<command-name>/roar</command-name>")]
    if with_maint_read:
        rows += [tool("Bash", command="cat " + REPO + "journal/x.md memory/MEMORY.md"),
                 tool("Read", file_path=REPO + "topics/a.md")]
    write(d / "m.jsonl", rows)
    write(d / "s.jsonl", [user("<command-name>/smelt</command-name>")] + [tool("Read", file_path=REPO + "MEMORY.md")])
    write(d / "sess" / "subagents" / "agent-1.jsonl", [user("x"), tool("Read", file_path=REPO + "MEMORY.md")])
    return root


def run(tmp_path, **kw):
    root = claude_tree(tmp_path / "cl", **kw)
    args = rmr.argparse.Namespace(since="2026-10-15", host="h", claude_root=str(root),
                                  codex_root=str(tmp_path / "none"), pi_root=str(tmp_path / "none"),
                                  project_filter="-agents")
    return rmr.census(args)


def test_claude_counts_exclude_native_mentions_and_old_sessions(tmp_path):
    t = run(tmp_path)
    w = t[("claude", "h", "main-working")]
    assert (w["sessions"], w["topics"], w["index"], w["read"], w["shell"]) == (3, 1, 0, 1, 0)
    m = t[("claude", "h", "main-maintenance")]
    # roar and smelt both classify as maintenance
    assert (m["sessions"], m["index"], m["topics"], m["read"], m["shell"]) == (2, 2, 1, 2, 1)
    s = t[("claude", "h", "subagent")]
    assert (s["sessions"], s["index"], s["read"]) == (1, 1, 1)


def test_smelt_and_dream_are_maintenance_keywords():
    for w in ("smelt", "dream", "hoard", "roar", "lair", "brood"):
        assert rmr.CLAUDE_MAINT.search('"skill": "%s"' % w)
        assert rmr.TEXT_MAINT.search("please run %s now" % w)
    assert not rmr.CLAUDE_MAINT.search('"skill": "hunt"')


def test_codex_and_pi_fixtures(tmp_path):
    cdx = tmp_path / "cdx"
    def mk(name, rows):
        write(cdx / name, rows)

    marker = {"payload": {"role": "user", "content": "Project memory boundary"}}
    call = {"payload": {"type": "function_call", "arguments": json.dumps({"cmd": "cat memory/topics/b.md"})}}
    mk("1.jsonl", [marker, call])
    mk("2.jsonl", [marker])
    mk("3.jsonl", [call])
    pi = tmp_path / "pi"
    write(pi / "p.jsonl", [marker, {"message": {"role": "assistant", "content": [
        {"type": "toolCall", "arguments": {"command": "cat memory/MEMORY.md"}}]}}])
    args = rmr.argparse.Namespace(since="2020-01-01", host="h", claude_root=str(tmp_path / "none"),
                                  codex_root=str(cdx), pi_root=str(pi), project_filter="-agents")
    t = rmr.census(args)
    c = t[("codex", "h", "main-working")]
    assert (c["sessions"], c["topics"]) == (2, 1)
    p = t[("pi", "h", "main-working")]
    assert (p["sessions"], p["index"]) == (1, 1)


def test_control_fails_when_maintenance_reads_nothing(tmp_path, capsys):
    root = claude_tree(tmp_path / "cl", with_maint_read=False)
    # drop the smelt session too: no maintenance read remains
    (root / "-x-agents" / "s.jsonl").unlink()
    argv = ["--since", "2026-10-15", "--host", "h", "--claude-root", str(root),
            "--codex-root", str(tmp_path / "n"), "--pi-root", str(tmp_path / "n")]
    assert rmr.main(argv) == 1
    assert "CONTROL FAILED" in capsys.readouterr().out


def test_control_ok_line(tmp_path, capsys):
    root = claude_tree(tmp_path / "cl")
    argv = ["--since", "2026-10-15", "--host", "h", "--claude-root", str(root),
            "--codex-root", str(tmp_path / "n"), "--pi-root", str(tmp_path / "n")]
    assert rmr.main(argv) == 0
    assert "CONTROL OK" in capsys.readouterr().out


def test_writes_and_git_are_not_reads():
    for cmd in ("printf x > memory/MEMORY.md", "cat <<EOF >> memory/MEMORY.md\nhi\nEOF",
                "echo y | tee memory/topics/a.md", "git add memory/MEMORY.md", "git diff memory/topics/a.md",
                "git log -- memory/MEMORY.md", "sed -i s/a/b/ memory/MEMORY.md",
                "apply_patch '*** Update File: memory/MEMORY.md'"):
        assert rmr.shell_kinds(cmd) == set(), cmd
    for cmd in ("cat memory/MEMORY.md", "head -5 memory/MEMORY.md", "sed -n 1,5p memory/MEMORY.md",
                "rg foo memory/topics/", "ls memory/topics/", "cd x && grep -n a memory/MEMORY.md | wc -l"):
        assert rmr.shell_kinds(cmd), cmd
    assert rmr.shell_kinds("cat memory/MEMORY.md > /tmp/o") == {"index"}


def test_write_only_and_git_only_sessions_count_zero(tmp_path):
    d = tmp_path / "cl" / "-x-agents"
    write(d / "w.jsonl", [user("hi"), tool("Bash", command="printf x > " + REPO + "MEMORY.md"),
                          tool("Write", file_path=REPO + "MEMORY.md"), tool("Edit", file_path=REPO + "topics/a.md")])
    write(d / "g.jsonl", [user("hi"), tool("Bash", command="git add memory/MEMORY.md"),
                          tool("Bash", command="git diff -- memory/topics/a.md")])
    args = rmr.argparse.Namespace(since="2026-10-15", host="h", claude_root=str(tmp_path / "cl"),
                                  codex_root=str(tmp_path / "n"), pi_root=str(tmp_path / "n"), project_filter="-agents")
    w = rmr.census(args)[("claude", "h", "main-working")]
    assert (w["sessions"], w["index"], w["topics"], w["either"]) == (2, 0, 0, 0)


def test_codex_apply_patch_and_pi_prose(tmp_path):
    marker = {"payload": {"role": "user", "content": "Project memory boundary"}}
    cdx = tmp_path / "cdx"
    write(cdx / "1.jsonl", [marker, {"payload": {"type": "custom_tool_call", "name": "apply_patch",
                                                 "input": "*** Update File: memory/MEMORY.md"}}])
    write(cdx / "2.jsonl", [marker, {"payload": {"type": "function_call", "name": "shell",
                                                 "arguments": json.dumps({"command": ["bash", "-lc", "cat memory/MEMORY.md"]})}}])
    pi = tmp_path / "pi"
    write(pi / "p.jsonl", [marker, {"message": {"role": "assistant", "content": [
        {"type": "text", "text": "I will read memory/MEMORY.md"},
        {"type": "toolCall", "name": "bash", "arguments": {"command": "ls"}}]}}])
    args = rmr.argparse.Namespace(since="2020-01-01", host="h", claude_root=str(tmp_path / "none"),
                                  codex_root=str(cdx), pi_root=str(pi), project_filter="-agents")
    t = rmr.census(args)
    assert t[("codex", "h", "main-working")]["either"] == 1
    assert t[("pi", "h", "main-working")]["either"] == 0


def test_control_counts_unique_sessions(tmp_path, capsys):
    d = tmp_path / "cl" / "-x-agents"
    write(d / "m.jsonl", [user("<command-name>/roar</command-name>"),
                          tool("Read", file_path=REPO + "MEMORY.md"), tool("Read", file_path=REPO + "topics/a.md")])
    argv = ["--since", "2026-10-15", "--host", "h", "--claude-root", str(tmp_path / "cl"),
            "--codex-root", str(tmp_path / "n"), "--pi-root", str(tmp_path / "n")]
    assert rmr.main(argv) == 0
    assert "CONTROL OK: maintenance sessions with a memory read: 1\n" in capsys.readouterr().out
