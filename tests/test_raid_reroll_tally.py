"""scripts/raid-reroll-tally.py: RAID wrap-up step 1b, ported from the inline awk.

Ticket 1086. The awk program in AWK_ORACLE is the pre-port recipe, kept
verbatim as a test oracle: the differential test fails if the port drifts
from it on any fixture. The oracle is skipped where awk is absent.
"""

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from child_env import child_env

pytestmark = pytest.mark.integration

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/raid-reroll-tally.py"

AWK_ORACLE = r"""
  FNR == 1 { in_log = 0; in_body = 0 }
  in_body { next }
  /^--- log ---$/ { in_log = 1; next }
  /^--- body ---$/ { in_log = 0; in_body = 1; next }
  in_log && /^[0-9][0-9][0-9][0-9]-/ {
    if (match($0, / (bump|note) /)) {
      split(substr($0, RSTART + 1), fields, " ")
      if (fields[1] == "note" && fields[2] == "bump" &&
          fields[3] == "verify-reroll") fields[2] = fields[3]
      if (fields[1] == "note" && fields[2] != "verify-reroll" &&
          fields[2] != "circuit-breaker") next
      ticket = FILENAME
      sub(/^.*\//, "", ticket)
      ticket = substr(ticket, 1, 4)
      count[ticket " " fields[2]]++
    }
  }
  END {
    for (key in count) {
      split(key, fields, " ")
      printf "Ticket %s: %d %s\n", fields[1], count[key], fields[2]
    }
  }
"""

MAIN_FIXTURE = {
    "closed/0879-example.erg": (
        "%erg 0.1\nTitle: archived\nClosed: 2026-10-05\n\n--- log ---\n"
        "2026-10-05T10:00Z reviewer note verify-reroll — round 1: fix\n"
        "\n--- body ---\nMerged tickets retain their bump history.\n"
    ),
    "1023-example.erg": (
        "%erg 0.1\nTitle: example\n\n--- log ---\n"
        "2026-10-05T10:00Z Minh Ha Duong note verify-reroll — round 1: fix\n"
        "2026-10-05T10:01Z reviewer note verify-reroll — round 2: fix\n"
        "2026-10-05T10:02Z reviewer bump permission — historical\n"
        "2026-10-05T10:03Z reviewer note circuit-breaker — timeout\n"
        "2026-10-05T10:04Z reviewer note discussion quoting note verify-reroll\n"
        "2026-10-05T10:04Z reviewer note discussion quoting bump permission\n"
        "\n--- body ---\n"
        "2026-10-05T10:05Z quoted note verify-reroll — not a log entry\n"
    ),
    "1005-example.erg": (
        "%erg 0.1\nTitle: example\n\n--- log ---\n"
        "2026-10-05T10:00Z reviewer note verify-reroll — round 1: fix\n"
        "2026-10-05T10:01Z reviewer bump verify-reroll — historical\n"
        "2026-10-05T10:02Z reviewer note bump verify-reroll — historical\n"
        "\n--- body ---\nNo bumps here.\n"
    ),
}

EXPECTED_MAIN = {
    "Ticket 0879: 1 verify-reroll",
    "Ticket 1005: 3 verify-reroll",
    "Ticket 1023: 2 verify-reroll",
    "Ticket 1023: 1 permission",
    "Ticket 1023: 1 circuit-breaker",
}


def write_tickets(root: Path, files: dict[str, str]) -> Path:
    tickets = root / "tickets"
    for name, text in files.items():
        path = tickets / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    return tickets


def run_script(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=cwd,
        env=child_env(),
        capture_output=True,
        text=True,
    )


def test_unparsed_log_is_flagged_not_zeroed(tmp_path):
    t = tmp_path / "tickets"
    t.mkdir()
    (t / "1023-x.erg").write_text(
        "%erg 0.1\nTitle: x\n\n--- log ---\n"
        "2026/10/05 10:00 reviewer bump permission\n\n--- body ---\n")
    r = subprocess.run([sys.executable, SCRIPT, "tickets"], cwd=tmp_path,
                       env=child_env(), capture_output=True, text=True)
    assert r.stdout == ""
    assert "drift" in r.stderr


def test_drift_flag_fires_on_unparsed_log(tmp_path):
    # Positive control: an awk-equivalent that prints nothing and exits 0
    # passes the stdout check but fails here, since it never warns.
    write_tickets(tmp_path, {
        "1023-x.erg": (
            "%erg 0.1\nTitle: x\n\n--- log ---\n"
            "2026/10/05 10:00 reviewer bump permission\n\n--- body ---\n"),
    })
    r = run_script(tmp_path, "tickets")
    assert r.returncode == 0
    assert "drift" in r.stderr
    assert "1023-x.erg" in r.stderr


def test_clean_log_emits_no_drift_warning(tmp_path):
    write_tickets(tmp_path, MAIN_FIXTURE)
    r = run_script(tmp_path, "tickets", "tickets/closed")
    assert r.returncode == 0
    assert "drift" not in r.stderr


def test_empty_log_section_is_not_drift(tmp_path):
    write_tickets(tmp_path, {
        "1030-x.erg": "%erg 0.1\nTitle: x\n\n--- log ---\n\n--- body ---\n",
    })
    r = run_script(tmp_path, "tickets")
    assert r.returncode == 0
    assert r.stdout == ""
    assert "drift" not in r.stderr


@pytest.mark.parametrize("regression", ["baseline", "quoted_body_log"])
def test_body_log_lines_ignored(tmp_path, regression):
    files = dict(MAIN_FIXTURE)
    if regression == "quoted_body_log":
        # Positive control: a parser that skips the body terminator counts this
        # line and reports 1005 as 4 instead of 3.
        files["1005-example.erg"] += (
            "--- log ---\n2026-10-05T10:03Z quoted note verify-reroll — body sample\n")
    write_tickets(tmp_path, files)
    r = run_script(tmp_path, "tickets", "tickets/closed")
    assert r.returncode == 0
    assert set(r.stdout.splitlines()) == EXPECTED_MAIN


def test_first_occurrence_match(tmp_path):
    # A naive re.search for "bump" counts this as a bump; the first " (bump|note) "
    # is " note ", so the entry is a discussion note and must not count.
    write_tickets(tmp_path, {
        "1040-x.erg": (
            "%erg 0.1\nTitle: x\n\n--- log ---\n"
            "2026-10-05T10:00Z reviewer note discussion quoting bump permission\n"
            "\n--- body ---\n"),
    })
    r = run_script(tmp_path, "tickets")
    assert r.returncode == 0
    assert r.stdout == ""


def test_bare_bump_keeps_awk_trailing_space(tmp_path):
    # awk prints an empty kind as "... N " with a trailing space; the port keeps it.
    write_tickets(tmp_path, {
        "1041-x.erg": "%erg 0.1\nTitle: x\n\n--- log ---\n"
                      "2026-10-05T10:00Z reviewer bump \n\n--- body ---\n",
    })
    r = run_script(tmp_path, "tickets")
    assert r.returncode == 0
    assert r.stdout == "Ticket 1041: 1 \n"


def test_missing_ticket_dirs_exit_2(tmp_path):
    # aedist-style repo with no tickets/: could-not-look, never an all-clear.
    r = run_script(tmp_path, "tickets", "tickets/closed")
    assert r.returncode == 2
    assert r.stdout == ""
    # Python's own missing-script exit is also 2; pin the script's message too.
    assert "no ticket directory" in r.stderr


@pytest.mark.skipif(shutil.which("awk") is None, reason="awk oracle needs awk")
def test_differential_against_awk_oracle(tmp_path):
    files = dict(MAIN_FIXTURE)
    files["1041-x.erg"] = ("%erg 0.1\nTitle: x\n\n--- log ---\n"
                           "2026-10-05T10:00Z reviewer bump \n\n--- body ---\n")
    files["1040-x.erg"] = ("%erg 0.1\nTitle: x\n\n--- log ---\n"
                           "2026-10-05T10:00Z reviewer note discussion quoting bump permission\n"
                           "2026/10/05 10:01 reviewer bump permission\n\n--- body ---\n")
    files["1042-x.erg"] = ("%erg 0.1\nTitle: x\n\n--- log ---\n"
                           "2026/10/05 10:00 reviewer bump permission\n\n--- body ---\n")
    tickets = write_tickets(tmp_path, files)
    closed = tickets / "closed"
    erg_files = sorted(str(p) for p in tickets.glob("*.erg")) + sorted(
        str(p) for p in closed.glob("*.erg"))
    awk = subprocess.run(["awk", AWK_ORACLE, *erg_files], capture_output=True,
                         text=True, env=child_env(), check=True)
    oracle = subprocess.run(["sort"], input=awk.stdout, capture_output=True,
                            text=True, env={**child_env(), "LC_ALL": "C"}, check=True)
    port = run_script(tmp_path, "tickets", "tickets/closed")
    assert port.returncode == 0
    assert port.stdout == oracle.stdout
