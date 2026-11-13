"""Foreign dependency reads and explicit, evidence-bearing asker release."""

import subprocess
from pathlib import Path

import pytest

from child_env import child_env

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/cross_repo_blockers.py"
pytestmark = pytest.mark.integration


def ticket(root, number, headers="", body="Needs parser fix"):
    path = root / "tickets" / f"{number}-fixture.erg"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"%erg 0.1\nTitle: fixture\nCreated: 2026-11-13\nAuthor: test\n{headers}\n--- log ---\n\n--- body ---\n{body}\n")
    return path


def run(root, *args):
    return subprocess.run(
        ["python3", str(SCRIPT), "--project", str(root), *args],
        capture_output=True, text=True, env=child_env(),
    )


def commit(root, message):
    for args in (["init", "-q"], ["add", "tickets"],
                 ["-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                  "commit", "-qm", message]):
        subprocess.run(["git", "-C", str(root), *args], check=True,
                       capture_output=True, env=child_env())
    return subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"],
                                   text=True, env=child_env()).strip()


@pytest.mark.parametrize("uri", [False, True])
def test_closed_dependency_requires_result_before_release(tmp_path, uri):
    asker, receiver = tmp_path / "asker", tmp_path / "receiver"
    reference = receiver.as_uri() + "/0042" if uri else "../receiver/0042"
    local = ticket(asker, "0001", f"Blocked-by: {reference}\nLabel: deferred\nLabel: needs-human\n")
    remote = ticket(receiver, "0042", "Closed: fixed parser; tests pass\n")
    if uri:
        (receiver / "tickets/closed").mkdir()
        remote = remote.rename(receiver / "tickets/closed" / remote.name)
    commit(receiver, "Fix parser and close ticket")
    before = remote.read_bytes()
    result = run(asker)
    assert result.returncode == 0, result.stderr
    assert '"state": "closed"' in result.stdout
    assert "fixed parser" in result.stdout
    assert "Label: deferred" in local.read_text()
    result = run(asker, "--release", "0001", "--reference", reference,
                 "--verified-result", "Parser fix meets the asker's failure fixture")
    assert result.returncode == 0, result.stderr
    assert "Blocked-by:" not in local.read_text()
    assert "Label: deferred" not in local.read_text()
    assert "Label: needs-human" in local.read_text()
    assert "unblocked by" in local.read_text()
    assert "Parser fix meets" in local.read_text()
    assert remote.read_bytes() == before


@pytest.mark.parametrize("headers,state", [
    ("", "open"),
    ("Closed: rejected: outside scope\n", "closed"),
    ("Closed: duplicate\nSuperseded-by: ../replacement/0043\n", "replaced"),
])
def test_scan_keeps_unresolved_dependencies_parked(tmp_path, headers, state):
    asker, receiver = tmp_path / "asker", tmp_path / "receiver"
    local = ticket(asker, "0001", "Blocked-by: ../receiver/0042\nLabel: deferred\n")
    ticket(receiver, "0042", headers)
    before = local.read_bytes()
    result = run(asker)
    assert result.returncode == 0, result.stderr
    assert f'"state": "{state}"' in result.stdout
    assert local.read_bytes() == before


def test_one_release_preserves_other_blockers_and_deferred(tmp_path):
    asker, receiver = tmp_path / "asker", tmp_path / "receiver"
    local = ticket(asker, "0001", "Blocked-by: ../receiver/0042\nBlocked-by: 0002\nLabel: deferred\n")
    ticket(receiver, "0042", "Closed: fixed\n")
    commit(receiver, "Close receiver")
    result = run(asker, "--release", "0001", "--reference", "../receiver/0042",
                 "--verified-result", "Confirmed result")
    assert result.returncode == 0, result.stderr
    assert "Blocked-by: 0002" in local.read_text()
    assert "Label: deferred" in local.read_text()


def test_missing_receiver_is_visible_and_unchanged(tmp_path):
    asker = tmp_path / "asker"
    local = ticket(asker, "0001", "Blocked-by: ../missing/0042\nLabel: deferred\n")
    before = local.read_bytes()
    result = run(asker)
    assert result.returncode == 0, result.stderr
    assert '"state": "unavailable"' in result.stdout
    assert local.read_bytes() == before


@pytest.mark.parametrize("uri", [False, True])
def test_fixed_closure_restores_erg_ready_with_commit_evidence(tmp_path, uri):
    asker, receiver = tmp_path / "asker", tmp_path / "receiver"
    reference = receiver.as_uri() + "/0042" if uri else "../receiver/0042"
    local = ticket(asker, "0001", f"Blocked-by: {reference}\nLabel: deferred\n")
    ticket(receiver, "0042", "Closed: fixed parser\n")
    closure_commit = commit(receiver, "Fix parser and close ticket")
    remote = next((receiver / "tickets").glob("0042-*.erg"))
    remote.write_text(remote.read_text() + "Later explanatory note\n")
    commit(receiver, "Explain the fixture")
    (receiver / "tickets/closed").mkdir()
    remote.rename(receiver / "tickets/closed" / remote.name)
    commit(receiver, "Archive the closed ticket")
    erg = SCRIPT.parent.parent / "tickets/erg"

    def ready():
        return subprocess.check_output([str(erg), "ready", str(asker / "tickets"), "--json"],
                                       text=True, env=child_env())

    assert '"0001"' not in ready()
    result = run(asker, "--release", "0001", "--reference", reference,
                 "--verified-result", "Receiver result fixes parser fixture")
    assert result.returncode == 0, result.stderr
    assert '"0001"' in ready()
    assert f"closed in {closure_commit}" in local.read_text()


def test_duplicate_continues_at_replacement_before_release(tmp_path):
    asker, receiver = tmp_path / "asker", tmp_path / "receiver"
    local = ticket(asker, "0001", "Blocked-by: ../receiver/0042\nLabel: deferred\n")
    ticket(receiver, "0042", "Closed: duplicate\nSuperseded-by: ../receiver/0043\n")
    ticket(receiver, "0043", "Closed: fixed parser\n")
    commit(receiver, "Close original and replacement")
    before = local.read_bytes()
    result = run(asker, "--release", "0001", "--reference", "../receiver/0042",
                 "--verified-result", "Closed duplicate does not deliver fix")
    assert result.returncode != 0
    assert local.read_bytes() == before
    # Molt follows the receiver's replacement in the asker's own ticket.
    local.write_text(local.read_text().replace("../receiver/0042", "../receiver/0043"))
    result = run(asker, "--release", "0001", "--reference", "../receiver/0043",
                 "--verified-result", "Replacement delivers parser fix")
    assert result.returncode == 0, result.stderr
    assert "Label: deferred" not in local.read_text()


def test_release_needs_assessment_and_closed_dependency(tmp_path):
    asker, receiver = tmp_path / "asker", tmp_path / "receiver"
    local = ticket(asker, "0001", "Blocked-by: ../receiver/0042\nLabel: deferred\n")
    ticket(receiver, "0042")
    before = local.read_bytes()
    for extra in ([], ["--verified-result", "Still open"]):
        result = run(asker, "--release", "0001", "--reference", "../receiver/0042", *extra)
        assert result.returncode != 0
        assert local.read_bytes() == before
    remote = next((receiver / "tickets").glob("0042-*.erg"))
    remote.write_text(remote.read_text().replace("Author: test\n", "Author: test\nClosed: fixed\n"))
    result = run(asker, "--release", "0001", "--reference", "../receiver/0042",
                 "--verified-result", "Closure not committed")
    assert result.returncode != 0
    assert "closure commit unavailable" in result.stderr
    assert local.read_bytes() == before
