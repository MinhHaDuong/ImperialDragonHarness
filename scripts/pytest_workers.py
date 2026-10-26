#!/usr/bin/env python3
"""Print the pytest-xdist flag for this host: `-n N`, or nothing for serial.

One rule for the Makefile and CI (ticket 1215): workers = the CPUs this
process may run on (affinity-aware, so a restricted runner is not over-counted),
clamped to [FLOOR, CAP]. Logical CPUs, not physical cores: the suite is
subprocess-heavy and SMT siblings paid on a 4-core host. The numbers and the
measurements behind them are in tickets/1215-*.erg; do not restate them
elsewhere.

Override: IDH_TEST_WORKERS=N forces N (0 forces serial), unclamped.
Serial fall-back: pytest-xdist not importable.
"""

import importlib.util
import os
import sys

FLOOR = 2
CAP = 24


def usable_cpus() -> int:
    try:
        return len(os.sched_getaffinity(0))
    except AttributeError:  # no affinity API (macOS)
        return os.cpu_count() or 1


def workers(cpus: int, override: str | None, have_xdist: bool) -> int:
    """Worker count; 0 means serial."""
    if not have_xdist:
        return 0
    if override not in (None, ""):
        try:
            return max(0, int(override))
        except ValueError:
            pass  # a typo must not silently pick a number: fall through to the rule
    return max(FLOOR, min(CAP, cpus))


def main() -> int:
    n = workers(
        usable_cpus(),
        os.environ.get("IDH_TEST_WORKERS"),
        importlib.util.find_spec("xdist") is not None,
    )
    if n:
        print(f"-n {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
