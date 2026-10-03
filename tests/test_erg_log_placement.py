"""erg log placement and erg check's advisory log warnings (ticket 0879).

Two consecutive gaze rerolls each had to hand-revert a malformed journal line:
the bump landed after the log block's terminal blank (out of section, glued to
`--- body ---`) and carried a regressive timestamp, and `erg validate` passed
it because the parser drops blank lines and never looks at position.

Fixed upstream (git-erg ticket 0304): `erg log` normalises then appends (the
new entry lands contiguous with the previous entries and the terminal blank
is restored), and `erg check` warns -- advisory only, exit 0 -- on a
displaced entry and on regressive timestamps. Advisory because the displaced
shape is erg's own systematic historical output (460/534 corpus files carry
it; callers include molt/roar/merge/housekeeping) and non-monotone entries
are routine git-rebase replay: a rejection would wedge the corpus gates.

Hermetic: every erg write or check runs against a tmp_path copy of the
fixtures; only the corpus-gate regression check reads the real tickets/
store (read-only, via the committed binary).
"""

import shutil
import subprocess
from pathlib import Path

import pytest

from child_env import child_env

REPO = Path(__file__).resolve().parent.parent
ERG = REPO / "tickets" / "erg"
FIXTURES = REPO / "tests" / "fixtures" / "erg"

DISPLACED = "0001-displaced-entry.erg"
REGRESSIVE = "0002-regressive-timestamp.erg"
CONTROL = "0003-wellformed-control.erg"


def run_erg(*args):
    """Run the committed binary with a loader-free child environment."""
    return subprocess.run(
        [str(ERG), *args], capture_output=True, text=True, env=child_env()
    )


@pytest.fixture()
def store(tmp_path):
    """A private copy of the fixture store; erg never touches the repo copies."""
    dst = tmp_path / "tickets"
    shutil.copytree(FIXTURES, dst)
    return dst


@pytest.mark.integration
def test_log_on_displaced_fixture_lands_contiguous_and_restores_blank(store):
    """The incident shape, repaired on append: the new entry joins the entry
    run (no blank between it and the previous entry) and the terminal blank
    is restored before `--- body ---`."""
    result = run_erg("log", "0001", "note probe", str(store))
    assert result.returncode == 0, result.stdout + result.stderr
    lines = (store / DISPLACED).read_text().splitlines()
    body_idx = lines.index("--- body ---")
    # Terminal blank restored: a blank directly before the body separator.
    assert lines[body_idx - 1] == "", "terminal blank not restored before --- body ---"
    # Contiguous: the new entry sits directly above that blank, glued to the
    # previous (displaced) entry -- not after the blank.
    new_entry = lines[body_idx - 2]
    assert "note probe" in new_entry, f"new entry displaced: {lines[body_idx - 3:]}"
    displaced = lines[body_idx - 3]
    assert displaced.endswith("bumped by an isolated gate"), (
        f"new entry not contiguous with the previous entry: {lines}"
    )


@pytest.mark.integration
def test_check_warns_on_displaced_and_regressive_fixtures(store):
    """Advisory WARN naming the two malformed fixtures; exit 0."""
    result = run_erg("check", str(store))
    assert result.returncode == 0, result.stdout + result.stderr
    assert f"WARN {DISPLACED}: log entry after the entry run's terminal blank" in (
        result.stderr
    ), f"no displaced-entry warning: {result.stderr}"
    assert f"WARN {REGRESSIVE}: regressive log timestamps" in result.stderr, (
        f"no regressive-timestamp warning: {result.stderr}"
    )


@pytest.mark.integration
def test_control_fixture_draws_no_warning_and_keeps_shape(store):
    """The normative shape: no placement warning, and erg log preserves it."""
    check = run_erg("check", str(store))
    assert check.returncode == 0, check.stdout + check.stderr
    assert CONTROL not in check.stderr, (
        f"control fixture drew a warning: {check.stderr}"
    )
    logged = run_erg("log", "0003", "note after", str(store))
    assert logged.returncode == 0, logged.stdout + logged.stderr
    lines = (store / CONTROL).read_text().splitlines()
    body_idx = lines.index("--- body ---")
    assert lines[body_idx - 1] == "", "terminal blank lost by erg log"
    assert "note after" in lines[body_idx - 2], (
        f"new entry not contiguous: {lines}"
    )


@pytest.mark.integration
def test_real_corpus_check_still_passes():
    """The advisory warnings must not break the corpus gate (exit 0)."""
    result = run_erg("check", "tickets")
    assert result.returncode == 0, result.stdout + result.stderr
