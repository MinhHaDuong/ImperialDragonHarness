#!/usr/bin/env python3
"""Profile tmp_report stages without printing candidate or history content.

The parent process enforces the hard wall-clock cap and kills the complete
worker process group on expiry. The worker emits aggregate stage counters only.
"""
import argparse
import importlib.util
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path


AGGREGATE_LINE = re.compile(
    r"stage=[a-z_]+(?: [a-z_]+=[A-Za-z0-9_.-]+)+$"
)


def _module():
    source = Path(__file__).with_name("tmp_report.py")
    spec = importlib.util.spec_from_file_location("tmp_report_profiled", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _emit_stage(name, started, **counts):
    elapsed = time.monotonic() - started
    fields = " ".join(f"{key}={value}" for key, value in counts.items())
    print(f"stage={name} elapsed={elapsed:.3f}s {fields}", flush=True)


def _worker(args):
    report = _module()
    stage = time.monotonic()
    scanned = report.scan_candidates(report._default_roots(args.repo))
    candidates = [item for item in scanned["candidates"] if item["bytes"] >= args.floor_bytes]
    _emit_stage(
        "candidate_scan", stage,
        candidates=len(candidates), unreadable=len(scanned["unreadable"]),
    )

    stage = time.monotonic()
    histories, history_unreadable = report.history_files(Path.home(), with_unreadable=True)
    history_bytes = 0
    for path in histories:
        try:
            history_bytes += path.stat().st_size
        except OSError:
            continue
    _emit_stage(
        "history_enumeration", stage,
        files=len(histories), bytes=history_bytes,
        unreadable=len(history_unreadable),
    )

    unreadable = []
    session_parents = {}
    scan_status = {}
    stage = time.monotonic()
    history_index = report.attribute_histories(
        candidates, histories, Path.home(), unreadable, session_parents,
        scan_status=scan_status,
        time_budget_seconds=args.history_budget_seconds,
    )
    if history_unreadable:
        scan_status["complete"] = False
    _emit_stage(
        "attribution", stage,
        matches=sum(len(items) for items in history_index.values()),
        ancestry_nodes=len(session_parents),
        files_scanned=scan_status.get("files_scanned", 0),
        files_total=scan_status.get("files_total", 0),
        complete=str(scan_status.get("complete", False)).lower(),
        unreadable=len(set(history_unreadable + unreadable)),
    )

    stage = time.monotonic()
    references = report._references(candidates, args.repo)
    known = sum(
        1 for item in references.values()
        if item.get("git_log") != "unknown"
        or item.get("pull_requests") != "unknown"
        or item.get("verdict_files") != "unknown"
    )
    _emit_stage("references", stage, candidates=len(references), known=known)

    stage = time.monotonic()
    checked = inferred = 0
    for item in candidates:
        matches = report.scope_history(
            history_index.get(item["path"], []), args.scope, args.session_id,
            args.exclude_session_id, session_parents,
        )
        if matches:
            continue
        checked += 1
        inferred += report.infer_test_provenance(Path(item["path"]), args.repo) is not None
    _emit_stage("inference", stage, checked=checked, inferred=inferred)
    return 0


def _kill_worker_group(process):
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=1)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".")
    parser.add_argument("--runtime", choices=("claude", "codex", "pi"), default="codex")
    parser.add_argument("--scope", choices=("roar", "lair"), default="lair")
    parser.add_argument("--session-id")
    parser.add_argument("--exclude-session-id")
    parser.add_argument("--floor-bytes", type=int, default=1024 * 1024)
    parser.add_argument("--history-budget-seconds", type=float, default=20.0)
    parser.add_argument("--max-seconds", type=float, default=75.0)
    parser.add_argument("--_worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.floor_bytes < 0 or args.history_budget_seconds < 0 or args.max_seconds <= 0:
        parser.error("byte floor and history budget must be non-negative; max-seconds must be positive")
    if args._worker:
        return _worker(args)

    command = [sys.executable, str(Path(__file__).resolve()), "--_worker"]
    for option, value in (
        ("--repo", args.repo), ("--runtime", args.runtime), ("--scope", args.scope),
        ("--floor-bytes", str(args.floor_bytes)),
        ("--history-budget-seconds", str(args.history_budget_seconds)),
    ):
        command.extend((option, value))
    if args.session_id:
        command.extend(("--session-id", args.session_id))
    if args.exclude_session_id:
        command.extend(("--exclude-session-id", args.exclude_session_id))

    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        text=True, start_new_session=True,
    )
    try:
        output, _ = process.communicate(timeout=args.max_seconds)
        timed_out = False
    except subprocess.TimeoutExpired:
        _kill_worker_group(process)
        output, _ = process.communicate()
        timed_out = True
    for line in output.splitlines():
        if AGGREGATE_LINE.fullmatch(line):
            print(line)
    status = "timeout" if timed_out else "complete" if process.returncode == 0 else "worker_error"
    print(f"profile_status={status} max_seconds={args.max_seconds:g}")
    return 124 if timed_out else process.returncode


if __name__ == "__main__":
    sys.exit(main())
