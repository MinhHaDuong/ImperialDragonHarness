"""pulse_profile turns a per-test duration record into the numbers a diagnosis needs.

The fixtures are built so every number can be checked by hand: ten tests of 1 s
and one of 90 s, a known tail concentration, and a worker lower bound that the
longest test dominates.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from child_env import child_env

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "pulse_profile.py"
sys.path.insert(0, str(REPO / "scripts"))

import pulse_profile as pp  # noqa: E402


def _junit(path: Path, cases: list[tuple[str, str, float]], skipped: tuple[str, ...] = ()) -> Path:
    body = "".join(
        f'<testcase classname="{cls}" name="{name}" time="{seconds}">'
        + ("<skipped/>" if f"{cls}::{name}" in skipped else "") + "</testcase>"
        for cls, name, seconds in cases
    )
    path.write_text(f'<?xml version="1.0"?><testsuites><testsuite>{body}</testsuite></testsuites>')
    return path


def _cases() -> list[tuple[str, str, float]]:
    return [("tests.test_a", f"t{i}", 1.0) for i in range(10)] + [("tests.test_b", "slow", 90.0)]


def test_junit_and_json_records_give_the_same_profile(tmp_path):
    junit = _junit(tmp_path / "r.xml", _cases())
    records = [{"nodeid": f"{c}::{n}", "duration": s} for c, n, s in _cases()]
    as_json = tmp_path / "r.json"
    as_json.write_text(json.dumps({"records": records}))
    assert pp.profile(pp.load(junit)).total == pp.profile(pp.load(as_json)).total == 100.0


def test_tail_concentration_is_exact_on_a_known_record(tmp_path):
    profile = pp.profile(pp.load(_junit(tmp_path / "r.xml", _cases())))
    assert profile.count == 11 and profile.total == 100.0
    assert profile.share_of_top[1] == pytest.approx(0.9)
    assert profile.share_of_top[5] == pytest.approx(0.94)
    assert profile.over_one_second == 1 and profile.over_ten_seconds == 1
    assert profile.files[0] == ("tests.test_b", 90.0)


def test_worker_lower_bound_is_set_by_the_longest_test(tmp_path):
    profile = pp.profile(pp.load(_junit(tmp_path / "r.xml", _cases())))
    assert pp.worker_bound(profile, 4) == 90.0  # 100/4 = 25 < the 90 s test
    assert pp.worker_bound(profile, 1) == 100.0
    flat = pp.profile([(f"a::t{i}", 10.0) for i in range(8)])
    assert pp.worker_bound(flat, 4) == pytest.approx(20.0)


def test_a_test_recorded_twice_counts_both_runs(tmp_path):
    prof = pp.profile([("a::t", 3.0), ("a::t", 4.0), ("a::u", 1.0)])
    assert prof.count == 2 and prof.total == 8.0 and prof.tests[0] == ("a::t", 7.0)


def test_a_record_with_no_timings_is_an_error_not_an_empty_profile(tmp_path):
    empty = tmp_path / "r.xml"
    empty.write_text('<?xml version="1.0"?><testsuites><testsuite></testsuite></testsuites>')
    with pytest.raises(ValueError, match="no timed tests"):
        pp.load(empty)


def test_compare_reports_the_change_and_what_moved(tmp_path):
    before = pp.profile(pp.load(_junit(tmp_path / "b.xml", _cases())))
    after_cases = [c for c in _cases() if c[1] != "slow"]
    after = pp.profile(pp.load(_junit(tmp_path / "a.xml", after_cases)))
    change = pp.compare(before, after)
    assert change["total_delta_s"] == -90.0 and change["tests_removed"] == 1
    assert change["files"][0][0] == "tests.test_b"


@pytest.mark.integration
def test_cli_profile_whatif_and_compare(tmp_path):
    before = _junit(tmp_path / "b.xml", _cases())
    after = _junit(tmp_path / "a.xml", [c for c in _cases() if c[1] != "slow"])

    def run(*args: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True,
                              env=child_env())

    shown = run("profile", str(before), "--workers", "4")
    assert shown.returncode == 0 and "90" in shown.stdout and "derived" in shown.stdout
    compared = run("compare", str(before), str(after), "--json")
    assert json.loads(compared.stdout)["total_delta_s"] == -90.0
    broken = tmp_path / "bad.xml"
    broken.write_text("not xml")
    assert run("profile", str(broken)).returncode == 2
