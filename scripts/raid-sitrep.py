#!/usr/bin/env python3
"""Print a one-screen raid sitrep from durable state: the raid log, git, the forge.

Reads no conversation, so any runtime, a shell (`watch -n 900`) or a timer can
run it. Exit 0: every part was read. Exit 2: some part could not be read; the
sitrep says `UNREADABLE <part>` in its place and prints no all-clear.
A clean run appends a SITREP line to the log (the next sitrep reports breakers
after it); `--no-mark` skips that.
"""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

from raid_gate_state import classify, marker_path, read_marker
from raid_log import append, log_path, parse

TERMINAL = {"merged", "escalated"}


def sh(*cmd: str, cwd: Path | None = None) -> str:
    done = subprocess.run(cmd, capture_output=True, text=True, timeout=30, cwd=cwd)
    if done.returncode != 0:
        raise RuntimeError(done.stderr.strip() or f"{cmd[0]} exit {done.returncode}")
    return done.stdout


def minutes(seconds: float) -> str:
    return f"{int(seconds // 60)}m"


def worktrees() -> list[Path]:
    paths = [Path(l[9:]) for l in sh("git", "worktree", "list", "--porcelain").splitlines()
             if l.startswith("worktree ")]
    return paths


def open_prs() -> list[dict]:
    # harness-extension-point: the forge CLI
    return json.loads(sh("gh", "pr", "list", "--state", "open",
                         "--json", "number,headRefName,title"))


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--now", type=float, default=None, help="epoch seconds (tests)")
    parser.add_argument("--no-forge", action="store_true", help="skip the forge read, say so")
    parser.add_argument("--no-mark", action="store_true", help="do not append a SITREP line")
    args = parser.parse_args(argv)
    now = args.now if args.now is not None else time.time()
    out, unreadable = [], []

    def fail(part: str, why: str = "") -> None:
        unreadable.append(part)
        out.append(f"UNREADABLE {part}" + (f": {why}" if why else ""))

    events = []
    path = None
    try:
        path = log_path()
        events, bad = parse(path.read_text())
        for number in bad:
            fail(f"log line {number}", str(path))
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        fail("log", str(error))

    starts = [e for e in events if e[1] == "RAID_START"]
    queue = [e for e in events if e[1] == "QUEUE"]
    gate_max = 1800.0
    if starts:
        start, _, fields = starts[-1]
        try:
            deadline = float(fields["deadline"])
            gate_max = float(fields.get("gate_max", gate_max))
            out.append(f"time: elapsed {minutes(now - start)} of {minutes(deadline - start)} "
                       f"budget, {minutes(max(deadline - now, 0))} left")
        except (KeyError, ValueError):
            fail("deadline", "RAID_START lacks a numeric deadline=")
    elif events or path is not None and path.exists():
        fail("RAID_START", "no RAID_START line in the log")

    waves = [e for e in events if e[1] == "WAVE"]
    prs: dict[str, tuple[str, str]] = {}
    for _, kind, fields in events:
        if kind == "PR" and "n" in fields:
            prs[fields["n"]] = (fields.get("ticket", "?"), fields.get("step", "?"))
    inflight: list[str] = []
    if waves:
        _, _, wf = waves[-1]
        tickets = [t for t in wf.get("tickets", "").split(",") if t]
        out.append(f"wave {wf.get('n', '?')}: tickets {', '.join(tickets) or 'none'}")
        state = {t: step for t, step in prs.values()}
        inflight = [t for t in tickets if state.get(t) not in TERMINAL]
    elif events:
        out.append("wave: none recorded yet")
    for n, (ticket, step) in prs.items():
        out.append(f"  PR {n} (ticket {ticket}): {step}")

    last_mark = max((e[0] for e in events if e[1] == "SITREP"), default=0)
    fired = [e for e in events if e[1] == "BREAKER" and e[0] > last_mark]
    for when, _, fields in fired:
        out.append(f"breaker: {fields.get('kind', '?')} ticket {fields.get('ticket', '?')} "
                   f"({minutes(now - when)} ago)")
    if events and not fired:
        out.append("breakers: none logged since the last sitrep")

    try:
        for tree in worktrees():
            gate = read_marker(marker_path(tree))
            if gate is not None:
                status = classify(time.time(), time.time(), gate, 600, int(gate_max))
                if status.startswith("GATE"):
                    out.append(f"gate heartbeat: {status} in {tree.name}")
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        fail("git", str(error))

    if args.no_forge:
        out.append("forge: skipped (--no-forge)")
    else:
        try:
            listed = open_prs()
            out.append("forge open PRs: " + (", ".join(
                f"#{p['number']} {p['headRefName']}" for p in listed) or "none"))
        except (OSError, RuntimeError, ValueError, KeyError, subprocess.SubprocessError) as error:
            fail("forge", str(error))

    if not queue:
        if events:
            fail("queue", "no QUEUE line in the log")
    if not unreadable:
        pending = int(queue[-1][2].get("n", "x")) if queue[-1][2].get("n", "").isdigit() else None
        if pending is None:
            fail("queue", "QUEUE line lacks a numeric n=")
        elif inflight:
            out.append(f"NEXT wait: in flight {', '.join(inflight)}")
        elif pending > 0:
            out.append(f"NEXT resume wave: nothing in flight, {pending} queued")
        else:
            out.append("NEXT wrap-up: nothing in flight, queue empty")

    print("\n".join(["SITREP " + time.strftime("%H:%M", time.localtime(now))] + out))
    if unreadable:
        return 2
    if not args.no_mark and path is not None:
        append("SITREP", {}, path, now=now)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
