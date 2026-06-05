"""Tests for scripts/test-quality.py — the empirical test-quality utility.

The module is loaded via importlib (hyphenated filename, not importable),
exactly like tests/test_project_state.py loads project-state.py.

Design under test: only the Runner layer spawns a subprocess. Every lens, the
Go adapter, and the ratchet are pure, so these tests inject a StubRunner /
parse recorded JSON and never touch a real Go toolchain. One CLI-level test
drives the `flakiness` and `run` subcommands end-to-end through a stub.
"""

import importlib.util
import json
import sys
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
FIXTURES = Path(__file__).resolve().parent / "fixtures"

spec = importlib.util.spec_from_file_location("test_quality", SCRIPTS / "test-quality.py")
tq = importlib.util.module_from_spec(spec)
sys.modules["test_quality"] = tq
spec.loader.exec_module(tq)


# ── stub runner/adapter: feed canned outputs, exercise lenses without Go ──────


class StubRunner:
    """Returns a pre-scripted raw output per call. `scripts` is a list of raw
    strings; calls beyond the list repeat the last. Records how it was called."""

    def __init__(self, scripts):
        self._scripts = scripts
        self.calls = []

    def __call__(self, *, shuffle=False, seed=None):
        idx = min(len(self.calls), len(self._scripts) - 1)
        self.calls.append({"shuffle": shuffle, "seed": seed})
        return self._scripts[idx]


def _line(action, test, pkg="pkg", elapsed=0.0):
    return json.dumps(
        {"Action": action, "Test": test, "Package": pkg, "Elapsed": elapsed}
    )


def _raw(*verdicts, durations=None):
    """Build a fake go-json blob: verdicts is (test_name, action) tuples."""
    durations = durations or {}
    lines = []
    for name, action in verdicts:
        lines.append(_line("run", name))
        lines.append(_line(action, name, elapsed=durations.get(name, 0.0)))
    return "\n".join(lines)


# ── Go adapter (fixture-tested; never invokes go) ────────────────────────────


def test_go_adapter_parses_recorded_fixture():
    raw = (FIXTURES / "go_test_mixed.json").read_text()
    records = tq.GoAdapter.parse(raw)
    by_id = {r.identity: r for r in records}
    assert by_id["gqdemo::TestAlpha"].verdict == "pass"
    assert by_id["gqdemo::TestBeta"].verdict == "pass"
    assert by_id["gqdemo::TestGammaFails"].verdict == "fail"
    assert by_id["gqdemo::TestSkipped"].verdict == "skip"
    # Exactly the four per-test terminal events; package-level events dropped.
    assert len(records) == 4


def test_go_adapter_ignores_package_events_and_build_noise():
    raw = "\n".join(
        [
            "# gqdemo  (a non-JSON build line go prepends)",
            _line("output", "TestX"),  # non-terminal: ignored
            _line("pass", "TestX", elapsed=0.5),
            json.dumps({"Action": "pass", "Package": "gqdemo", "Elapsed": 1.2}),  # no Test
        ]
    )
    records = tq.GoAdapter.parse(raw)
    assert len(records) == 1
    assert records[0].identity == "pkg::TestX"
    assert records[0].duration == 0.5


def test_go_identity_handles_missing_package():
    assert tq.go_identity(None, "TestFoo") == "::TestFoo"


# ── flakiness lens ───────────────────────────────────────────────────────────


def test_flakiness_lens_flags_varying_verdict():
    runs = [
        tq.RunResult(tq.GoAdapter.parse(_raw(("TestA", "pass"), ("TestB", "pass")))),
        tq.RunResult(tq.GoAdapter.parse(_raw(("TestA", "pass"), ("TestB", "fail")))),
    ]
    out = tq.flakiness_lens(runs)
    flaky_ids = {f["identity"] for f in out["flaky"]}
    assert flaky_ids == {"pkg::TestB"}
    assert out["stable"] == 1


def test_flakiness_lens_flags_inconsistent_presence():
    runs = [
        tq.RunResult(tq.GoAdapter.parse(_raw(("TestA", "pass"), ("TestB", "pass")))),
        tq.RunResult(tq.GoAdapter.parse(_raw(("TestA", "pass")))),  # B missing
    ]
    out = tq.flakiness_lens(runs)
    flaky_ids = {f["identity"] for f in out["flaky"]}
    assert "pkg::TestB" in flaky_ids


def test_flakiness_lens_stable_suite_has_no_flakes():
    raw = _raw(("TestA", "pass"), ("TestB", "fail"))
    runs = [tq.RunResult(tq.GoAdapter.parse(raw)) for _ in range(4)]
    out = tq.flakiness_lens(runs)
    assert out["flaky"] == []
    assert out["stable"] == 2


# ── independence lens ────────────────────────────────────────────────────────


def test_independence_lens_flags_order_dependent_test():
    ordered = [tq.RunResult(tq.GoAdapter.parse(_raw(("TestA", "pass"))))]
    shuffled = [
        tq.RunResult(tq.GoAdapter.parse(_raw(("TestA", "fail"))), shuffle=True)
    ]
    out = tq.independence_lens(ordered, shuffled)
    ids = {d["identity"] for d in out["order_dependent"]}
    assert ids == {"pkg::TestA"}


def test_independence_lens_ignores_intrinsically_flaky_test():
    # Test is flaky under fixed order (pass then fail) -> not order-dependent.
    ordered = [
        tq.RunResult(tq.GoAdapter.parse(_raw(("TestA", "pass")))),
        tq.RunResult(tq.GoAdapter.parse(_raw(("TestA", "fail")))),
    ]
    shuffled = [tq.RunResult(tq.GoAdapter.parse(_raw(("TestA", "fail"))), shuffle=True)]
    out = tq.independence_lens(ordered, shuffled)
    assert out["order_dependent"] == []


# ── speed lens ───────────────────────────────────────────────────────────────


def test_speed_lens_flags_slow_tail():
    raw = _raw(
        ("Fast", "pass"),
        ("Slow", "pass"),
        durations={"Fast": 0.1, "Slow": 3.0},
    )
    runs = [tq.RunResult(tq.GoAdapter.parse(raw))]
    out = tq.speed_lens(runs, slow_seconds=1.0)
    slow_ids = {s["identity"] for s in out["slow_tail"]}
    assert slow_ids == {"pkg::Slow"}
    assert out["slowest"][0]["identity"] == "pkg::Slow"


def test_speed_lens_takes_max_duration_across_runs():
    runs = [
        tq.RunResult(tq.GoAdapter.parse(_raw(("T", "pass"), durations={"T": 0.2}))),
        tq.RunResult(tq.GoAdapter.parse(_raw(("T", "pass"), durations={"T": 2.5}))),
    ]
    out = tq.speed_lens(runs, slow_seconds=1.0)
    assert {s["identity"] for s in out["slow_tail"]} == {"pkg::T"}


# ── ratchet ──────────────────────────────────────────────────────────────────


def _report_with(flaky=(), order=(), slow=()):
    return {
        "flakiness": {"flaky": [{"identity": i} for i in flaky]},
        "independence": {"order_dependent": [{"identity": i} for i in order]},
        "speed": {"slow_tail": [{"identity": i} for i in slow]},
    }


def test_ratchet_passes_when_all_bad_is_baselined():
    report = _report_with(flaky=["pkg::Old"])
    baseline = tq.Baseline(flaky={"pkg::Old"})
    out = tq.ratchet(report, baseline)
    assert out["regressed"] is False
    assert out["new_flaky"] == []
    assert out["baselined"]["flaky"] == ["pkg::Old"]


def test_ratchet_fails_on_new_regression():
    report = _report_with(flaky=["pkg::Old", "pkg::New"], slow=["pkg::SlowNew"])
    baseline = tq.Baseline(flaky={"pkg::Old"})
    out = tq.ratchet(report, baseline)
    assert out["regressed"] is True
    assert out["new_flaky"] == ["pkg::New"]
    assert out["new_slow"] == ["pkg::SlowNew"]


def test_baseline_roundtrips_through_json(tmp_path):
    b = tq.Baseline(flaky={"a"}, order_dependent={"b"}, slow={"c"})
    p = tmp_path / "baseline.json"
    p.write_text(json.dumps(b.to_json()))
    loaded = tq.Baseline.load(p)
    assert loaded.flaky == {"a"}
    assert loaded.order_dependent == {"b"}
    assert loaded.slow == {"c"}


def test_baseline_load_missing_file_is_empty(tmp_path):
    loaded = tq.Baseline.load(tmp_path / "nope.json")
    assert loaded.flaky == set()


# ── collect_runs: shuffle gives distinct seeds, runner injected ──────────────


def test_collect_runs_shuffle_uses_distinct_seeds():
    runner = StubRunner([_raw(("T", "pass"))])
    runs = tq.collect_runs(runner, tq.GoAdapter, n=3, shuffle=True, seed=1)
    assert len(runs) == 3
    assert all(c["shuffle"] for c in runner.calls)
    seeds = [c["seed"] for c in runner.calls]
    assert len(set(seeds)) == 3  # each run got its own shuffle seed


def test_collect_runs_no_shuffle_keeps_order():
    runner = StubRunner([_raw(("T", "pass"))])
    tq.collect_runs(runner, tq.GoAdapter, n=2, shuffle=False, seed=None)
    assert all(c["shuffle"] is False for c in runner.calls)


# ── full report orchestration ────────────────────────────────────────────────


def test_build_report_runs_all_three_lenses():
    runner = StubRunner([_raw(("TestA", "pass"), durations={"TestA": 2.0})])
    report = tq.build_report(
        runner, tq.GoAdapter, n=2, slow_seconds=1.0, seed=7
    )
    assert set(report) >= {"flakiness", "independence", "speed"}
    assert report["speed"]["slow_tail"][0]["identity"] == "pkg::TestA"


# ── CLI / gate contract (the EC2 contract 0182 depends on) ───────────────────


def _patch_go_runner(monkeypatch, runner):
    """Make _make_go return our stub runner + the real GoAdapter."""
    monkeypatch.setattr(tq, "_make_go", lambda args: (runner, tq.GoAdapter))


def test_flakiness_subcommand_exit_zero_when_stable(monkeypatch, capsys):
    runner = StubRunner([_raw(("TestA", "pass"), ("TestB", "fail"))])
    _patch_go_runner(monkeypatch, runner)
    rc = tq.main(["flakiness", "--package-dir", "/x", "--runs", "3"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["gate"] == "pass"
    assert out["new_flaky"] == []


def test_flakiness_subcommand_exit_nonzero_when_flaky(monkeypatch, capsys):
    runner = StubRunner([_raw(("T", "pass")), _raw(("T", "fail"))])
    _patch_go_runner(monkeypatch, runner)
    rc = tq.main(["flakiness", "--package-dir", "/x", "--runs", "2"])
    assert rc == tq.EXIT_REGRESSION
    out = json.loads(capsys.readouterr().out)
    assert out["gate"] == "fail"
    assert out["new_flaky"] == ["pkg::T"]


def test_flakiness_subcommand_baseline_suppresses_known_flake(
    monkeypatch, capsys, tmp_path
):
    bpath = tmp_path / "b.json"
    bpath.write_text(json.dumps({"flaky": ["pkg::T"]}))
    runner = StubRunner([_raw(("T", "pass")), _raw(("T", "fail"))])
    _patch_go_runner(monkeypatch, runner)
    rc = tq.main(
        ["flakiness", "--package-dir", "/x", "--runs", "2", "--baseline", str(bpath)]
    )
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["new_flaky"] == []
    assert out["baselined_flaky"] == ["pkg::T"]


def test_run_subcommand_emits_report_and_exits_zero(monkeypatch, capsys):
    runner = StubRunner([_raw(("TestA", "pass"))])
    _patch_go_runner(monkeypatch, runner)
    rc = tq.main(["run", "--package-dir", "/x", "--runs", "2"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert "flakiness" in out and "independence" in out and "speed" in out


def test_run_subcommand_gates_on_ratchet_regression(monkeypatch, capsys, tmp_path):
    # New slow test, empty baseline -> regression -> exit nonzero.
    runner = StubRunner([_raw(("Slow", "pass"), durations={"Slow": 5.0})])
    _patch_go_runner(monkeypatch, runner)
    bpath = tmp_path / "b.json"
    rc = tq.main(
        [
            "run",
            "--package-dir",
            "/x",
            "--runs",
            "1",
            "--slow-seconds",
            "1.0",
            "--baseline",
            str(bpath),
        ]
    )
    assert rc == tq.EXIT_REGRESSION
    out = json.loads(capsys.readouterr().out)
    assert out["ratchet"]["regressed"] is True
    assert "pkg::Slow" in out["ratchet"]["new_slow"]


def test_run_subcommand_update_baseline_never_gates(monkeypatch, capsys, tmp_path):
    runner = StubRunner([_raw(("Slow", "pass"), durations={"Slow": 5.0})])
    _patch_go_runner(monkeypatch, runner)
    bpath = tmp_path / "b.json"
    rc = tq.main(
        [
            "run",
            "--package-dir",
            "/x",
            "--runs",
            "1",
            "--slow-seconds",
            "1.0",
            "--baseline",
            str(bpath),
            "--update-baseline",
        ]
    )
    assert rc == 0
    written = json.loads(bpath.read_text())
    assert "pkg::Slow" in written["slow"]


# ── CLI flag presence (source inspection, not subprocess --help) ─────────────


def test_cli_exposes_flakiness_gate_and_run_subcommands():
    src = (SCRIPTS / "test-quality.py").read_text()
    assert '"flakiness"' in src
    assert '"run"' in src
    assert "EXIT_REGRESSION" in src
    assert "--baseline" in src
    assert "--update-baseline" in src
