#!/usr/bin/env python3
"""Empirical test-quality utility — flakiness / independence / speed.

The CHEAP, DETERMINISTIC tier of the test-quality family (siblings: 0182
mutation oracles, 0183 LLM judge). Every signal here is produced by *re-running
the existing suite* — no mutation, no LLM, zero tokens — so these are the only
test-quality checks fast enough to gate a single PR.

Three lenses, one entry point:

  * flakiness    run the unchanged suite N times; a test whose verdict varies
                 across runs is flaky. Flaky tests train teams to ignore red,
                 and you cannot mutation-test a flaky suite — so this lens is
                 also the PRECONDITION gate that 0182's maw-audit (formerly fang-audit) calls before
                 it spends a token. Exposed as the `flakiness` subcommand with a
                 hard exit-code contract (see below).
  * independence run the suite shuffled; a test whose verdict depends on order
                 is not isolated. The reference Go runner randomizes order via
                 `-shuffle`. Parallel execution (`go test -p`, or another
                 runner's equivalent) surfaces shared-state races and is a
                 documented runner extension: a runner that emits per-test
                 records under parallel execution feeds the same lenses
                 unchanged — no lens code changes needed.
  * speed        time each test; flag the slow tail so the fast feedback loop
                 stays fast.

Architecture (only the Runner touches a subprocess; everything else is pure and
fixture-testable):

  Runner   spawns the test command (N times / shuffled). Injected, so a stub
           replaces it in tests.
  Adapter  parses a runner's machine-readable output into TestRecord rows.
           The Go adapter parses `go test -json`. Documented interface below.
  Lenses   pure functions over the parsed records.
  Ratchet  pure diff of (current findings) against a baseline of known-bad
           test identities; fail only on regressions the diff introduced.

Test identity — the join key shared with 0182/0183 — is the string
``<package>::<TestName>`` (``::<TestName>`` when the adapter has no package).

Exit-code contract (this is a GATE, not just a probe):

  report mode   (`run`)        always exit 0, emit the full JSON report.
  gate mode     (`flakiness`,  exit 0 when clean, exit 2 when the lens (after
                `gate`)         the ratchet) finds a regression. JSON still on
                                stdout. 0182 shells out to `flakiness` and keys
                                on this exit code — language-agnostic, robust to
                                this file's hyphenated, non-importable name.

The Runner interface for a new language is a callable:

    runner(*, shuffle: bool, seed: int | None) -> str   # raw runner output

paired with an Adapter ``parse(raw: str) -> list[TestRecord]``. Implement those
two and the lenses + ratchet work unchanged. See ``GoAdapter`` /
``GoTestRunner`` for the reference Go implementation.
"""

import argparse
import json
import logging
import random
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

log = logging.getLogger("test-quality")

# Exit code a gate-mode invocation returns when it finds a regression. Distinct
# from 1 so a crash (argparse / uncaught exception) is not mistaken for "flaky".
EXIT_REGRESSION = 2

# Terminal go-test actions, mapped to our normalized verdicts.
_GO_TERMINAL = {"pass": "pass", "fail": "fail", "skip": "skip"}


# ── data model ───────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class TestRecord:
    """One test's outcome in one run of the suite."""

    identity: str  # "<package>::<TestName>" — the cross-tool join key
    verdict: str  # "pass" | "fail" | "skip"
    duration: float  # seconds; 0.0 if the runner reports none


@dataclass
class RunResult:
    """All records from a single suite run, plus how it was invoked."""

    records: list[TestRecord]
    shuffle: bool = False
    seed: int | None = None


# ── Go adapter ───────────────────────────────────────────────────────────────


def go_identity(package: str | None, test: str | None) -> str:
    """Build the cross-tool test identity from go-test's package + test name."""
    pkg = package or ""
    name = test or ""
    return f"{pkg}::{name}"


class GoAdapter:
    """Parse `go test -json` output into TestRecord rows.

    `go test -json` emits one JSON object per line (the test2json event stream).
    We key on the documented fields ``Action`` (run/output/pass/fail/skip/...),
    ``Package``, ``Test`` and ``Elapsed``. Events without a ``Test`` field are
    package-level and ignored — we report per-test, not per-package. The verdict
    is the terminal Action for each test identity; ``Elapsed`` on that terminal
    event is the duration in seconds.
    """

    @staticmethod
    def parse(raw: str) -> list[TestRecord]:
        records: list[TestRecord] = []
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                # go test prepends plain build-error lines before the JSON
                # stream; skip anything that is not a JSON event.
                continue
            action = event.get("Action")
            test = event.get("Test")
            if not test or action not in _GO_TERMINAL:
                continue
            records.append(
                TestRecord(
                    identity=go_identity(event.get("Package"), test),
                    verdict=_GO_TERMINAL[action],
                    duration=float(event.get("Elapsed") or 0.0),
                )
            )
        return records


class GoTestRunner:
    """Runner adapter for a Go package tree: `go test -count=1 -json [...]`.

    This is the ONLY layer that spawns a subprocess. `-count=1` defeats Go's
    test cache so each invocation actually re-executes (essential for the
    flakiness lens). `-shuffle` randomizes intra-package test order for the
    independence lens.
    """

    def __init__(self, package_dir: str, pattern: str = "./...", timeout: int = 600):
        self.package_dir = package_dir
        self.pattern = pattern
        self.timeout = timeout

    def __call__(self, *, shuffle: bool = False, seed: int | None = None) -> str:
        cmd = ["go", "test", "-count=1", "-json"]
        if shuffle:
            cmd.append(f"-shuffle={seed if seed is not None else 'on'}")
        cmd.append(self.pattern)
        log.debug("running: %s (cwd=%s)", " ".join(cmd), self.package_dir)
        proc = subprocess.run(
            cmd,
            cwd=self.package_dir,
            capture_output=True,
            text=True,
            check=False,
            timeout=self.timeout,
        )
        # A failing suite is normal input here, so we don't raise on returncode;
        # the JSON stream carries the verdicts.
        return proc.stdout


# ── core: run the suite N times via an injected (runner, adapter) ─────────────


def collect_runs(
    runner,
    adapter,
    *,
    n: int,
    shuffle: bool = False,
    seed: int | None = None,
    rng: random.Random | None = None,
) -> list[RunResult]:
    """Invoke `runner` n times, parse each via `adapter`.

    `runner` and `adapter` are injected so tests pass a stub and never spawn a
    real toolchain. When `shuffle` is set, each run gets a distinct seed
    (derived from `rng`) so order varies run-to-run.
    """
    rng = rng or random.Random(seed)
    runs: list[RunResult] = []
    for _ in range(max(1, n)):
        run_seed = rng.randrange(2**31) if shuffle else seed
        raw = runner(shuffle=shuffle, seed=run_seed)
        runs.append(
            RunResult(records=adapter.parse(raw), shuffle=shuffle, seed=run_seed)
        )
    return runs


# ── lenses (pure functions over RunResult lists) ─────────────────────────────


def _verdicts_by_identity(runs: list[RunResult]) -> dict[str, list[str]]:
    by_id: dict[str, list[str]] = defaultdict(list)
    for run in runs:
        for rec in run.records:
            by_id[rec.identity].append(rec.verdict)
    return by_id


def flakiness_lens(runs: list[RunResult]) -> dict:
    """A test is flaky if its verdict is not identical across all N runs.

    A test that is missing from some runs (appears, then doesn't) is also
    non-deterministic and is flagged.
    """
    n_runs = len(runs)
    by_id = _verdicts_by_identity(runs)
    flaky: list[dict] = []
    for identity, verdicts in sorted(by_id.items()):
        distinct = sorted(set(verdicts))
        inconsistent_presence = len(verdicts) != n_runs
        if len(distinct) > 1 or inconsistent_presence:
            flaky.append(
                {
                    "identity": identity,
                    "verdicts": verdicts,
                    "distinct": distinct,
                    "runs_seen": len(verdicts),
                    "runs_total": n_runs,
                }
            )
    return {
        "lens": "flakiness",
        "runs": n_runs,
        "tests": len(by_id),
        "flaky": flaky,
        "stable": len(by_id) - len(flaky),
    }


def independence_lens(
    ordered: list[RunResult], shuffled: list[RunResult]
) -> dict:
    """A test is order-dependent when shuffling changes its behaviour.

    Two signatures, both flagged:
    - stable in BOTH directions but the verdicts disagree (deterministic
      order dependence);
    - stable under fixed order but UNSTABLE under shuffle (the canonical
      isolation bug: the verdict depends on which neighbours ran first).
      Reported with shuffled="unstable" plus the observed verdicts.

    A test already unstable under fixed order is flakiness, not order
    dependence — the flakiness lens (which sees the ordered runs) owns it.
    """
    ordered_v = _verdicts_by_identity(ordered)
    shuffled_v = _verdicts_by_identity(shuffled)

    def stable_verdict(verdicts: list[str]) -> str | None:
        s = set(verdicts)
        return next(iter(s)) if len(s) == 1 else None

    dependent: list[dict] = []
    for identity in sorted(set(ordered_v) | set(shuffled_v)):
        o = stable_verdict(ordered_v.get(identity, []))
        shuffled_verdicts = shuffled_v.get(identity, [])
        s = stable_verdict(shuffled_verdicts)
        if o is None:
            continue  # unstable under fixed order = flaky, owned by flakiness_lens
        if s is not None and o != s:
            dependent.append(
                {"identity": identity, "ordered": o, "shuffled": s}
            )
        elif s is None and shuffled_verdicts:
            dependent.append(
                {
                    "identity": identity,
                    "ordered": o,
                    "shuffled": "unstable",
                    "shuffled_verdicts": shuffled_verdicts,
                }
            )
    return {
        "lens": "independence",
        "ordered_runs": len(ordered),
        "shuffled_runs": len(shuffled),
        "order_dependent": dependent,
    }


def speed_lens(runs: list[RunResult], *, slow_seconds: float, top: int = 10) -> dict:
    """Max observed duration per test; flag the slow tail above a threshold."""
    max_dur: dict[str, float] = {}
    for run in runs:
        for rec in run.records:
            if rec.duration > max_dur.get(rec.identity, -1.0):
                max_dur[rec.identity] = rec.duration
    ranked = sorted(max_dur.items(), key=lambda kv: kv[1], reverse=True)
    slow = [
        {"identity": i, "duration": d, "suggest_tag": True}
        for i, d in ranked
        if d >= slow_seconds
    ]
    return {
        "lens": "speed",
        "threshold_seconds": slow_seconds,
        "slowest": [{"identity": i, "duration": d} for i, d in ranked[:top]],
        "slow_tail": slow,
    }


# ── ratchet (pure diff against a baseline of known-bad identities) ───────────


@dataclass
class Baseline:
    """Known-bad test identities, partitioned by lens. New regressions are bad
    identities NOT already recorded here."""

    flaky: set = field(default_factory=set)
    order_dependent: set = field(default_factory=set)
    slow: set = field(default_factory=set)

    @classmethod
    def load(cls, path: Path) -> "Baseline":
        if not path.exists():
            return cls()
        data = json.loads(path.read_text())
        return cls(
            flaky=set(data.get("flaky", [])),
            order_dependent=set(data.get("order_dependent", [])),
            slow=set(data.get("slow", [])),
        )

    def to_json(self) -> dict:
        return {
            "flaky": sorted(self.flaky),
            "order_dependent": sorted(self.order_dependent),
            "slow": sorted(self.slow),
        }


def current_bad(report: dict) -> Baseline:
    """Extract the set of currently-bad identities from a full report."""
    return Baseline(
        flaky={f["identity"] for f in report["flakiness"]["flaky"]},
        order_dependent={
            f["identity"] for f in report["independence"]["order_dependent"]
        },
        slow={f["identity"] for f in report["speed"]["slow_tail"]},
    )


def ratchet(report: dict, baseline: Baseline) -> dict:
    """Regressions = currently-bad identities not present in the baseline."""
    cur = current_bad(report)
    new_flaky = sorted(cur.flaky - baseline.flaky)
    new_order = sorted(cur.order_dependent - baseline.order_dependent)
    new_slow = sorted(cur.slow - baseline.slow)
    regressed = bool(new_flaky or new_order or new_slow)
    return {
        "regressed": regressed,
        "new_flaky": new_flaky,
        "new_order_dependent": new_order,
        "new_slow": new_slow,
        "baselined": {
            "flaky": sorted(baseline.flaky & cur.flaky),
            "order_dependent": sorted(baseline.order_dependent & cur.order_dependent),
            "slow": sorted(baseline.slow & cur.slow),
        },
    }


# ── top-level orchestration: the single entry point that runs all 3 lenses ───


def build_report(
    runner,
    adapter,
    *,
    n: int,
    slow_seconds: float,
    seed: int | None = None,
    rng: random.Random | None = None,
) -> dict:
    """Run all three lenses from one set of suite invocations."""
    rng = rng or random.Random(seed)
    ordered = collect_runs(runner, adapter, n=n, shuffle=False, seed=seed, rng=rng)
    shuffled = collect_runs(runner, adapter, n=n, shuffle=True, seed=seed, rng=rng)
    return {
        "n": n,
        "flakiness": flakiness_lens(ordered),
        "independence": independence_lens(ordered, shuffled),
        "speed": speed_lens(ordered, slow_seconds=slow_seconds),
    }


# ── CLI ──────────────────────────────────────────────────────────────────────


def _make_go(args) -> tuple:
    runner = GoTestRunner(
        package_dir=str(Path(args.package_dir).expanduser().resolve()),
        pattern=args.pattern,
        timeout=args.timeout,
    )
    return runner, GoAdapter()


def _emit(report: dict) -> None:
    print(json.dumps(report, indent=2))


def cmd_run(args) -> int:
    """report mode: full report, optional ratchet gate. Exit reflects ratchet."""
    runner, adapter = _make_go(args)
    report = build_report(
        runner, adapter, n=args.runs, slow_seconds=args.slow_seconds, seed=args.seed
    )
    if args.baseline:
        baseline = Baseline.load(Path(args.baseline))
        rr = ratchet(report, baseline)
        report["ratchet"] = rr
        if args.update_baseline:
            Path(args.baseline).write_text(
                json.dumps(current_bad(report).to_json(), indent=2) + "\n"
            )
            report["ratchet"]["baseline_updated"] = True
        _emit(report)
        return EXIT_REGRESSION if rr["regressed"] and not args.update_baseline else 0
    _emit(report)
    return 0


def cmd_flakiness(args) -> int:
    """GATE: the reusable flakiness precheck 0182 shells out to.

    Exit 0 = suite is stable (or all flakiness is baselined). Exit
    EXIT_REGRESSION = new flakiness found. JSON report on stdout either way.
    """
    runner, adapter = _make_go(args)
    runs = collect_runs(runner, adapter, n=args.runs, shuffle=False, seed=args.seed)
    lens = flakiness_lens(runs)
    flaky_ids = {f["identity"] for f in lens["flaky"]}
    new_flaky = sorted(flaky_ids)
    if args.baseline:
        baseline = Baseline.load(Path(args.baseline))
        new_flaky = sorted(flaky_ids - baseline.flaky)
        lens["baselined_flaky"] = sorted(flaky_ids & baseline.flaky)
    lens["new_flaky"] = new_flaky
    lens["gate"] = "fail" if new_flaky else "pass"
    _emit(lens)
    return EXIT_REGRESSION if new_flaky else 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Empirical test-quality utility: flakiness / independence / speed. "
            "Re-runs an existing suite; zero LLM tokens."
        )
    )
    p.add_argument(
        "--log-level",
        default="WARNING",
        help="Python logging level for diagnostics (default: WARNING)",
    )
    sub = p.add_subparsers(dest="command", required=True)

    def add_runner_args(sp, *, with_lens_args: bool, with_ratchet: bool):
        sp.add_argument(
            "--adapter",
            choices=["go"],
            default="go",
            help="Runner/parser adapter (default: go)",
        )
        sp.add_argument(
            "--package-dir",
            required=True,
            help="Directory the test command runs in (e.g. a Go module root)",
        )
        sp.add_argument(
            "--pattern", default="./...", help="Go package pattern (default: ./...)"
        )
        sp.add_argument(
            "--runs",
            type=int,
            default=3,
            help="Times to re-run the suite (bounds runtime; default: 3)",
        )
        sp.add_argument(
            "--seed", type=int, default=None, help="Base RNG seed (reproducibility)"
        )
        sp.add_argument(
            "--timeout",
            type=int,
            default=600,
            help="Per-run subprocess timeout, seconds (default: 600)",
        )
        if with_lens_args:
            sp.add_argument(
                "--slow-seconds",
                type=float,
                default=1.0,
                help="Duration at/above which a test is slow-tail (default: 1.0)",
            )
        if with_ratchet:
            sp.add_argument(
                "--baseline",
                default=None,
                help="Path to a baseline JSON of known-bad identities (ratchet)",
            )
            sp.add_argument(
                "--update-baseline",
                action="store_true",
                help="Rewrite the baseline from current findings; never gates",
            )

    run_p = sub.add_parser(
        "run", help="Run all three lenses; emit full JSON report (report mode)"
    )
    add_runner_args(run_p, with_lens_args=True, with_ratchet=True)
    run_p.set_defaults(func=cmd_run)

    fl_p = sub.add_parser(
        "flakiness",
        help="GATE: re-run N times; exit nonzero on new flakiness (0182 precheck)",
    )
    add_runner_args(fl_p, with_lens_args=False, with_ratchet=False)
    fl_p.add_argument(
        "--baseline",
        default=None,
        help="Baseline JSON; flakiness already listed does not gate",
    )
    fl_p.set_defaults(func=cmd_flakiness)

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, str(args.log_level).upper(), logging.WARNING),
        format="%(levelname)s %(name)s: %(message)s",
    )
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
