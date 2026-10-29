#!/usr/bin/env python3
"""Count sessions that read repository memory, per runtime, host and kind.

Repository memory is `memory/MEMORY.md` and `memory/topics/` inside a project
checkout. Paths under `.claude/projects/` are Claude Code's native
auto-memory and never count. Runtimes: Claude Code (main and subagent
transcripts), Codex and Pi (main sessions only; these stores hold no subagent
transcripts). Kinds: main-working, main-maintenance, subagent. A session is
maintenance when it invokes hoard, smelt, dream, roar, lair or brood (a
keyword heuristic for Codex and Pi).

The maintenance arm doubles as the positive control: its sessions read memory
by design, so a probe that sees none is blind and the run fails. Grep by
content is invisible to this probe. Rewritten from the frozen audit scans
conception/2026-10-29-memory-system-audit/{repo_mem_reads,codex_mem}.py.

Usage: repo-memory-reads.py --since 2026-10-15 [--host padme]
"""

import argparse
import collections
import datetime
import glob
import json
import os
import re
import shlex
import socket
import sys

PAT = {
    "index": re.compile(r"memory/MEMORY\.md"),
    "topics": re.compile(r"memory/topics/"),
}
NATIVE = ".claude/projects/"
MAINT_WORDS = "hoard|smelt|dream|roar|lair|brood"
CLAUDE_MAINT = re.compile(
    r'"(?:skill|command)"\s*:\s*"(?:%s)"|<command-name>/?(?:%s)<' % (MAINT_WORDS, MAINT_WORDS)
)
TEXT_MAINT = re.compile(r"\b(?:%s)\b" % MAINT_WORDS)
MARKER = "Project memory boundary"
CALL_TYPES = ("function_call", "custom_tool_call", "local_shell_call")
TS = re.compile(r'"timestamp"\s*:\s*"([0-9T:\-]+)')


READERS = {"cat", "head", "tail", "less", "more", "grep", "egrep", "fgrep", "rg", "ls", "nl", "bat", "sed", "awk", "wc", "tac"}
SPLIT = re.compile(r"&&|\|\||[;|\n]")


def classify(text):
    """Return the set of repository-memory kinds named in text (native paths removed)."""
    kept = " ".join(t for t in text.split() if NATIVE not in t)
    return {k for k, p in PAT.items() if p.search(kept)}


def shell_kinds(cmd):
    """Return the kinds a shell command reads: reader commands only.

    Redirection targets, writers (tee, apply_patch, sed -i), git subcommands and
    any other command naming the path are not reads.
    """
    kinds = set()
    for seg in SPLIT.split(cmd or ""):
        try:
            toks = shlex.split(seg)
        except ValueError:
            toks = seg.split()
        while toks and (re.match(r"\w+=", toks[0]) or toks[0] in ("sudo", "command", "time")):
            toks.pop(0)
        if not toks or os.path.basename(toks[0]) not in READERS:
            continue
        if toks[0] == "sed" and any(t.startswith("-i") or t == "--in-place" for t in toks):
            continue
        args, skip = [], False
        for t in toks[1:]:
            if skip:
                skip = False
            elif re.match(r"^\d*>", t) or re.match(r"^\d*<<", t):
                skip = re.fullmatch(r"\d*(>>?|<<-?)", t) is not None
            else:
                args.append(t)
        kinds |= classify(" ".join(args))
    return kinds


def call_commands(payload):
    """Return (read_paths, shell_commands) from a Codex or Pi tool call; writers yield nothing."""
    name = str(payload.get("name") or "")
    if name in ("apply_patch", "write", "edit", "Write", "Edit"):
        return [], []
    raw = payload.get("arguments", payload.get("input", payload.get("action")))
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except ValueError:
            return [], [raw] if "apply_patch" not in raw else []
    if not isinstance(raw, dict):
        return [], []
    cmd = raw.get("cmd", raw.get("command"))
    if isinstance(cmd, list):
        cmd = cmd[2] if len(cmd) >= 3 and cmd[1] in ("-lc", "-c") else " ".join(map(str, cmd))
    paths = [raw[k] for k in ("path", "file_path") if isinstance(raw.get(k), str)] if name in ("read", "Read") else []
    return paths, [cmd] if isinstance(cmd, str) else []


def scan_claude(path):
    """Return (hits, maintenance, first_timestamp); hits maps (channel, kind) to a count."""
    hits = collections.Counter()
    maint, first = False, None
    try:
        with open(path, "rb") as fh:
            for raw in fh:
                line = raw.decode("utf-8", "replace")
                if first is None:
                    m = TS.search(line)
                    if m:
                        first = m.group(1)
                if not maint and CLAUDE_MAINT.search(line):
                    maint = True
                if "memory/" not in line:
                    continue
                try:
                    obj = json.loads(line)
                except ValueError:
                    continue
                msg = obj.get("message")
                content = msg.get("content") if isinstance(msg, dict) else None
                if obj.get("type") != "assistant" or not isinstance(content, list):
                    continue
                for c in content:
                    if not isinstance(c, dict) or c.get("type") != "tool_use":
                        continue
                    inp = c.get("input") or {}
                    name = c.get("name")
                    if name == "Read":
                        chan, target = "read", inp.get("file_path")
                        kinds = classify(target or "")
                    elif name == "Bash":
                        chan, kinds = "shell", shell_kinds(inp.get("command"))
                    else:
                        continue
                    for k in kinds:
                        hits[(chan, k)] += 1
    except OSError:
        pass
    return hits, maint, first


def scan_codex(path):
    """Return (harness, hits, maintenance) for a Codex or Pi session file."""
    harness, maint = False, False
    hits = collections.Counter()
    with open(path, errors="replace") as fh:
        for line in fh:
            if MARKER in line:
                harness = True
            try:
                obj = json.loads(line)
            except ValueError:
                continue
            payload = obj.get("payload") or obj.get("message") or {}
            if not isinstance(payload, dict):
                continue
            text = json.dumps(payload)
            calls = [payload] if payload.get("type") in CALL_TYPES else []
            if payload.get("role") == "assistant" and isinstance(payload.get("content"), list):
                calls += [c for c in payload["content"] if isinstance(c, dict) and c.get("type") == "toolCall"]
            for call in calls:
                paths, cmds = call_commands(call)
                kinds = set().union(*(classify(p) for p in paths), *(shell_kinds(c) for c in cmds))
                for k in kinds:
                    hits[("shell", k)] += 1
            if payload.get("role") == "user" and MARKER not in text and TEXT_MAINT.search(text[:4000]):
                maint = True
    return harness, hits, maint


def add(table, key, hits):
    row = table[key]
    row["sessions"] += 1
    kinds = {k for (_, k) in hits}
    for k in kinds:
        row[k] += 1
    if kinds:
        row["either"] += 1
    for chan in {c for (c, _) in hits}:
        row[chan] += 1


def census(args):
    table = collections.defaultdict(collections.Counter)
    since_ts = datetime.datetime.fromisoformat(args.since).timestamp()
    for d in glob.glob(os.path.join(os.path.expanduser(args.claude_root), "*")):
        if args.project_filter not in os.path.basename(d):
            continue
        for f in glob.glob(d + "/*.jsonl") + glob.glob(d + "/*/subagents/*.jsonl"):
            hits, maint, first = scan_claude(f)
            if not first or first[:10] < args.since:
                continue
            if "/subagents/" in f:
                kind = "subagent"
            else:
                kind = "main-maintenance" if maint else "main-working"
            add(table, ("claude", args.host, kind), hits)
    for runtime, root in (("codex", args.codex_root), ("pi", args.pi_root)):
        for f in glob.glob(os.path.join(os.path.expanduser(root), "**", "*.jsonl"), recursive=True):
            if os.path.getmtime(f) < since_ts:
                continue
            harness, hits, maint = scan_codex(f)
            if not harness:
                continue
            kind = "main-maintenance" if maint else "main-working"
            add(table, (runtime, args.host, kind), hits)
    return table


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--since", required=True, help="YYYY-MM-DD")
    ap.add_argument("--host", default=socket.gethostname())
    ap.add_argument("--claude-root", default="~/.claude/projects")
    ap.add_argument("--codex-root", default="~/.codex/sessions")
    ap.add_argument("--pi-root", default="~/.pi/agent/sessions")
    ap.add_argument("--project-filter", default="-agents", help="Claude project dirs whose name contains this")
    args = ap.parse_args(argv)
    table = census(args)
    cols = ("sessions", "index", "topics", "read", "shell")
    print("runtime host kind | sessions reading-index reading-topics via-Read via-shell/call")
    for key in sorted(table):
        print(" ".join(key), "|", *[table[key][c] for c in cols])
    print("Claude Code: main and subagent transcripts. Codex, Pi: main sessions only (no subagent store).")
    print("Hosts scanned: %s. Others: run this command there with --host NAME." % args.host)
    ctl = sum(r["either"] for k, r in table.items() if k[2] == "main-maintenance")
    if ctl > 0:
        print("CONTROL OK: maintenance sessions with a memory read:", ctl)
        return 0
    print("CONTROL FAILED: no maintenance session read repository memory; the probe is blind or the window empty")
    return 1


if __name__ == "__main__":
    sys.exit(main())
