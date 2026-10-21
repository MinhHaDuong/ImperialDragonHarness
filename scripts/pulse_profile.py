#!/usr/bin/env python3
"""Profile a test suite's per-test durations; compare two profiles; bound a speed-up.

The input is a record the project's own runner produced in the environment agents
really use: a JUnit XML file (`pytest --junitxml=FILE`) or a JSON file holding
`{"records": [{"nodeid": ..., "duration": ...}]}`. `profile` reports how
concentrated the time is, and `--workers N` adds a lower bound on wall time for
N workers. `compare` sets two records side by side, for the follow-up visit.

Every figure here is arithmetic over the record. The worker bound is derived,
not measured: it ignores start-up, collection and fixture contention, so a real
run lands above it.
"""

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

TOP_COUNTS = (1, 5, 10, 25, 50)


@dataclass
class Profile:
    count: int
    total: float
    share_of_top: dict[int, float]
    over_one_second: int
    over_ten_seconds: int
    files: list[tuple[str, float]]
    tests: list[tuple[str, float]]
    durations: dict[str, float]


def _from_junit(path: Path) -> list[tuple[str, float]]:
    root = ET.parse(path).getroot()
    return [
        (f"{case.get('classname', '')}::{case.get('name', '')}", float(case.get("time") or 0))
        for case in root.iter("testcase")
    ]


def _from_json(path: Path) -> list[tuple[str, float]]:
    data = json.loads(path.read_text())
    records = data.get("records") if isinstance(data, dict) else data
    if not isinstance(records, list):
        raise ValueError(f"{path}: expected a list of records or {{'records': [...]}}")
    return [(str(r["nodeid"]), float(r["duration"])) for r in records]


def load(path: Path) -> list[tuple[str, float]]:
    """Read (test id, seconds) pairs; raise ValueError for anything not a timed record."""
    try:
        pairs = _from_json(path) if path.suffix == ".json" else _from_junit(path)
    except (ET.ParseError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise ValueError(f"{path}: not a readable duration record ({exc})") from exc
    if not pairs:
        raise ValueError(f"{path}: no timed tests in the record")
    return pairs


def _file_of(test_id: str) -> str:
    return test_id.split("::", 1)[0]


def profile(pairs: list[tuple[str, float]]) -> Profile:
    durations: dict[str, float] = {}
    for test_id, seconds in pairs:
        durations[test_id] = durations.get(test_id, 0.0) + seconds
    tests = sorted(durations.items(), key=lambda item: -item[1])
    total = sum(durations.values())
    per_file: dict[str, float] = {}
    for test_id, seconds in durations.items():
        per_file[_file_of(test_id)] = per_file.get(_file_of(test_id), 0.0) + seconds
    return Profile(
        count=len(tests),
        total=total,
        share_of_top={n: (sum(s for _, s in tests[:n]) / total if total else 0.0) for n in TOP_COUNTS},
        over_one_second=sum(1 for _, s in tests if s > 1),
        over_ten_seconds=sum(1 for _, s in tests if s > 10),
        files=sorted(per_file.items(), key=lambda item: -item[1]),
        tests=tests,
        durations=durations,
    )


def worker_bound(prof: Profile, workers: int) -> float:
    """Lower bound on wall time: perfect packing, but never below the longest test."""
    longest = prof.tests[0][1] if prof.tests else 0.0
    return max(prof.total / workers, longest)


def compare(before: Profile, after: Profile) -> dict:
    files_before, files_after = dict(before.files), dict(after.files)
    moved = sorted(
        ((name, files_after.get(name, 0.0) - files_before.get(name, 0.0))
         for name in set(files_before) | set(files_after)),
        key=lambda item: -abs(item[1]),
    )
    return {
        "before_total_s": round(before.total, 1),
        "after_total_s": round(after.total, 1),
        "total_delta_s": round(after.total - before.total, 1),
        "tests_before": before.count,
        "tests_after": after.count,
        "tests_removed": len(set(before.durations) - set(after.durations)),
        "tests_added": len(set(after.durations) - set(before.durations)),
        "files": [(name, round(delta, 1)) for name, delta in moved[:5] if delta],
    }


def _print_profile(prof: Profile, top: int, workers: int | None) -> None:
    print(f"{prof.count} tests, {prof.total:.1f} s in total (serial sum of recorded durations)")
    print(f"over 1 s: {prof.over_one_second}, over 10 s: {prof.over_ten_seconds}")
    shares = ", ".join(f"top {n}: {share:.0%}" for n, share in prof.share_of_top.items() if n <= prof.count)
    print(f"share of the total in the slowest tests -> {shares}")
    print(f"slowest {top} tests:")
    for test_id, seconds in prof.tests[:top]:
        print(f"  {seconds:8.1f} s  {test_id[:100]}")
    print(f"slowest {min(top, len(prof.files))} files:")
    for name, seconds in prof.files[:top]:
        print(f"  {seconds:8.1f} s  {name[:100]}")
    if workers:
        print(f"lower bound on wall time with {workers} workers: {worker_bound(prof, workers):.1f} s "
              f"(derived: max(total / workers, longest test); ignores start-up, collection "
              f"and fixture contention)")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    one = sub.add_parser("profile", help="concentration of time in one record")
    one.add_argument("record", type=Path)
    one.add_argument("--top", type=int, default=10)
    one.add_argument("--workers", type=int, help="also print the worker lower bound")
    one.add_argument("--json", action="store_true")
    two = sub.add_parser("compare", help="two records side by side")
    two.add_argument("before", type=Path)
    two.add_argument("after", type=Path)
    two.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command == "compare":
            change = compare(profile(load(args.before)), profile(load(args.after)))
            print(json.dumps(change, indent=2) if args.json else
                  "\n".join(f"{key}: {value}" for key, value in change.items()))
            return 0
        prof = profile(load(args.record))
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    if args.json:
        print(json.dumps({"count": prof.count, "total_s": round(prof.total, 1),
                          "share_of_top": prof.share_of_top, "over_1s": prof.over_one_second,
                          "over_10s": prof.over_ten_seconds,
                          "slowest": [(t, round(s, 1)) for t, s in prof.tests[:args.top]]}, indent=2))
    else:
        _print_profile(prof, args.top, args.workers)
    return 0


if __name__ == "__main__":
    sys.exit(main())
