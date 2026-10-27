"""A failed check of the merge gate names the tests that failed (ticket 1254).

`run_checks` keeps pytest's `FAILED <nodeid>` summary lines, one record line
each, after the check's own line; the after-merge red report still names the
failing checks, not the test lines.
"""

import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "merge-gate.py"

PYTEST_TAIL = (
    "= short test summary info =\\n"
    "FAILED tests/test_a.py::test_one - assert 1 == 2\\n"
    "FAILED tests/test_b.py::test_two[x y]\\n"
    "= 2 failed, 5 passed =\\n"
)


@pytest.fixture(scope="module")
def gate():
    spec = importlib.util.spec_from_file_location("merge_gate_1254", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def check(name, script):
    return {"name": name, "argv": [sys.executable, "-c", script]}


def test_a_failed_check_records_one_line_per_failed_test(gate, tmp_path, capsys):
    cfg = {"checks": [check("tests", f"import sys; sys.stdout.write('{PYTEST_TAIL}'); sys.exit(1)")]}
    ok, results = gate.run_checks(cfg, tmp_path)
    assert not ok
    assert results[0].startswith("tests fail(exit 1) ")
    assert results[1:] == [
        "failed-test tests tests/test_a.py::test_one",
        "failed-test tests tests/test_b.py::test_two[x y]",
    ]
    assert "FAILED tests/test_a.py::test_one" in capsys.readouterr().err  # output still echoed


def test_a_passing_check_adds_no_lines(gate, tmp_path):
    cfg = {"checks": [check("tests", "print('FAILED x::y in a log line')")]}
    ok, results = gate.run_checks(cfg, tmp_path)
    assert ok and len(results) == 1


def test_red_report_names_checks_despite_extra_lines(gate, tmp_path, monkeypatch):
    cfg = {"checks": [check("lint", "pass"), check("tests", "pass")]}
    results = [
        "lint pass 1.0s :: x",
        "tests fail(exit 1) 2.0s :: x",
        "failed-test tests tests/test_a.py::test_one",
    ]
    monkeypatch.setattr(gate, "last_green", lambda tip: None)
    monkeypatch.setattr(gate, "git", lambda *a, **k: type("R", (), {"stdout": ""})())
    text = gate.red_report("a" * 40, cfg, results)
    assert "Failing checks: tests\n" in text
