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


def classify(text):
    """Return the set of repository-memory kinds named in text (native paths removed)."""
    kept = " ".join(t for t in text.split() if NATIVE not in t)
    return {k for k, p in PAT.items() if p.search(kept)}


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
                    elif name == "Bash":
                        chan, target = "shell", inp.get("command")
                    else:
                        continue
                    for k in classify(target or ""):
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
            is_call = payload.get("type") in CALL_TYPES or (
                payload.get("role") == "assistant" and "toolCall" in text
            )
            if is_call:
                for k in classify(text.replace("\\/", "/")):
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
    ctl = sum(r["index"] + r["topics"] for k, r in table.items() if k[2] == "main-maintenance")
    if ctl > 0:
        print("CONTROL OK: maintenance sessions with a memory read:", ctl)
        return 0
    print("CONTROL FAILED: no maintenance session read repository memory; the probe is blind or the window empty")
    return 1


if __name__ == "__main__":
    sys.exit(main())
