"""Behavioural tests for the review evidence core (ticket 1142).

The decision function, forge actor admission, criteria hash and risk floor
are pure and run in the fast tier. The scenarios that need a repository
(unchanged-head reuse, report-only commits, rebases, relevant changes, the
gate's refusal of stale or missing proof) build a throwaway git repository
and are `integration`.
"""

import importlib.util
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from child_env import child_env

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "review_evidence.py"

_spec = importlib.util.spec_from_file_location("review_evidence", SCRIPT)
re_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(re_mod)

HUMAN_ID = "MDQ6VXNlcjE4NDc1MjA4"
COPILOT_ID = "BOT_kgDOCnlnWA"


def inputs(**over):
    base = dict(base="b" * 40, head="h" * 40, patch_id="p1", criteria_hash="c1",
                policy_version="v1")
    base.update(over)
    return re_mod.Inputs(**base)


def record(**over):
    rec = {"kind": "review", "seat": "correctness", "verdict": "approve",
           "base": "b" * 40, "head": "h" * 40, "patch-id": "p1",
           "criteria-hash": "c1", "policy-version": "v1"}
    rec.update(over)
    return rec


# --- decision function -----------------------------------------------------

def test_identical_inputs_reuse():
    assert re_mod.decide(record(), inputs())[0] == re_mod.REUSE


def test_moved_head_with_same_patch_id_reuses():
    """A rebase or a report-only commit moves the head, not the patch."""
    action, reason = re_mod.decide(record(head="o" * 40), inputs())
    assert action == re_mod.REUSE
    assert "o" * 12 in reason


@pytest.mark.parametrize("field,value", [
    ("patch_id", "p2"), ("criteria_hash", "c2"), ("policy_version", "v2"),
])
def test_changed_identity_is_stale(field, value):
    action, reason = re_mod.decide(record(), inputs(**{field: value}))
    assert action == re_mod.STALE
    assert field.replace("_", "-") in reason


@pytest.mark.parametrize("kind", ["check", "gate", "adherence"])
def test_checks_gate_and_adherence_are_never_reused(kind):
    """Even on the identical head: these results belong to one run (#1334)."""
    assert re_mod.decide(record(kind=kind), inputs())[0] == re_mod.RERUN


def test_missing_or_no_report_reruns():
    assert re_mod.decide(None, inputs())[0] == re_mod.RERUN
    assert re_mod.decide(record(verdict="no-report"), inputs())[0] == re_mod.RERUN


def test_findings_on_identical_diff_are_reused_not_rerun():
    """A seat that requested changes stands until the diff changes: no duplicate run."""
    assert re_mod.decide(record(verdict="changes"), inputs())[0] == re_mod.REUSE


# --- forge actor admission -------------------------------------------------

def forge(**over):
    rev = {"forge_host": "github.com", "actor_id": HUMAN_ID,
           "object_type": "PullRequestReview", "edited": False}
    rev.update(over)
    return rev


def test_pinned_actors_are_admitted_with_their_role():
    assert re_mod.admit_forge_review(forge()) == (True, "human")
    assert re_mod.admit_forge_review(forge(actor_id=COPILOT_ID)) == (True, "copilot")


@pytest.mark.parametrize("over", [
    {"actor_id": "U_unknown"},
    {"actor_id": None},
    {"forge_host": "gitlab.example"},
    {"edited": True},
    {"object_type": "Commit"},
])
def test_forge_review_fails_closed(over):
    ok, reason = re_mod.admit_forge_review(forge(**over))
    assert not ok and reason


def test_forge_reviews_are_classified_from_graphql():
    payload = {"data": {"repository": {"pullRequest": {
        "reviews": {"nodes": [
            {"__typename": "PullRequestReview", "author": {"login": "MinhHaDuong", "id": HUMAN_ID},
             "lastEditedAt": None, "state": "APPROVED", "commit": {"oid": "a" * 40}},
            {"__typename": "PullRequestReview",
             "author": {"login": "copilot-pull-request-reviewer", "id": COPILOT_ID},
             "lastEditedAt": None, "state": "COMMENTED", "commit": {"oid": "a" * 40}},
            {"__typename": "PullRequestReview", "author": {"login": "mallory", "id": "U_x"},
             "lastEditedAt": None, "state": "APPROVED", "commit": {"oid": "a" * 40}},
        ]},
        "comments": {"nodes": [
            {"__typename": "IssueComment", "author": {"login": "MinhHaDuong", "id": HUMAN_ID},
             "lastEditedAt": "2026-10-20T00:00:00Z"},
        ]},
    }}}}
    rows = re_mod.classify_forge(payload, "github.com")
    roles = [(r["login"], r["status"]) for r in rows]
    assert ("MinhHaDuong", "human: ran") in roles
    assert ("copilot-pull-request-reviewer", "copilot: ran") in roles
    assert ("mallory", "rejected") in roles
    edited = [r for r in rows if r["object_type"] == "IssueComment"]
    assert edited[0]["status"] == "rejected"


# --- criteria hash and risk floor -----------------------------------------

TICKET = """%erg 0.1
Title: x

--- body ---
## Context
Touches verify-gate.

## Exit criteria
- [ ] First criterion
- [ ] Second criterion

## Notes
irrelevant
"""


def test_criteria_hash_ignores_checkbox_state_and_other_sections():
    ticked = TICKET.replace("- [ ] First", "- [x] First").replace("irrelevant", "changed")
    assert re_mod.criteria_hash(TICKET) == re_mod.criteria_hash(ticked)
    reworded = TICKET.replace("Second criterion", "Second criterion, stricter")
    assert re_mod.criteria_hash(TICKET) != re_mod.criteria_hash(reworded)
    assert re_mod.criteria_hash(None) == "none"


def test_risk_floor_is_the_higher_of_paths_and_ticket_text():
    plain = "## Exit criteria\n- [ ] tidy a README\n"
    assert re_mod.risk_floor([("M", "README.md")], plain)["floor"] == "trivial"
    by_path = re_mod.risk_floor([("M", "rules/git.md")], plain)
    assert (by_path["paths"], by_path["ticket"], by_path["floor"]) == ("high", "trivial", "high")
    by_text = re_mod.risk_floor([("M", "README.md")], TICKET)
    assert (by_text["paths"], by_text["ticket"], by_text["floor"]) == ("trivial", "high", "high")
    deletion = re_mod.risk_floor([("D", "scripts/foo.py")], plain)
    assert deletion["floor"] == "high"
    closing = re_mod.risk_floor([("D", "tickets/0001-x.erg"), ("A", "tickets/closed/0001-x.erg")], plain)
    assert closing["floor"] == "trivial"


# --- repository scenarios --------------------------------------------------

# Same exit criteria as TICKET; its context names nothing high-risk.
REPO_TICKET = TICKET.replace("Touches verify-gate.", "Touches app.py.")

def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True,
                          text=True, env=child_env()).stdout.strip()


def commit(repo, path, text, msg, mode=None):
    p = repo / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)
    if mode:
        p.chmod(mode)
    git(repo, "add", path)
    git(repo, "commit", "-q", "-m", msg)
    return git(repo, "rev-parse", "HEAD")


@pytest.fixture
def repo(tmp_path):
    if shutil.which("git") is None:
        pytest.skip("git required")
    r = tmp_path / "repo"
    r.mkdir()
    git(r, "init", "-q", "-b", "main")
    git(r, "config", "user.email", "t@example.com")
    git(r, "config", "user.name", "T")
    commit(r, "README.md", "hello\n", "init")
    commit(r, "tickets/0001-x.erg", REPO_TICKET, "ticket")
    git(r, "switch", "-q", "-c", "feature")
    commit(r, "app.py", "def f():\n    return 1\n", "feature")
    return r


@pytest.fixture
def policy(tmp_path):
    root = tmp_path / "policy"
    (root / "skills" / "gaze").mkdir(parents=True)
    (root / "skills" / "gaze" / "SKILL.md").write_text("gaze v1\n")
    return root


def run_cli(repo, policy, *args):
    return subprocess.run(
        ["python3", str(SCRIPT), *args, "--repo", str(repo), "--base", "main",
         "--policy-root", str(policy), "--ticket", str(repo / "tickets/0001-x.erg")],
        capture_output=True, text=True, env=child_env())


def run_gate(repo, policy, *args, risk="ordinary"):
    return run_cli(repo, policy, "gate", "--risk", risk, *args)


def record_seat(repo, policy, seat, family="Anthropic", verdict="approve", kind="review"):
    out = subprocess.run(
        ["python3", str(SCRIPT), "record", "--repo", str(repo), "--base", "main",
         "--policy-root", str(policy), "--ticket", str(repo / "tickets/0001-x.erg"),
         "--seat", seat, "--kind", kind, "--verdict", verdict, "--family", family,
         "--worker", "test"],
        input="Report body.\n", capture_output=True, text=True, env=child_env(), check=True)
    return Path(out.stdout.strip())


def commit_reports(repo, msg="reviews: record"):
    git(repo, "add", "tickets/reviews")
    git(repo, "commit", "-q", "-m", msg)


@pytest.mark.integration
def test_record_writes_one_artifact_per_execution_under_the_range(repo, policy):
    first = record_seat(repo, policy, "correctness")
    second = record_seat(repo, policy, "correctness")
    base = git(repo, "merge-base", "main", "HEAD")
    head = git(repo, "rev-parse", "HEAD")
    assert first != second and first.parent == second.parent
    assert first.parent.name == f"{base[:7]}..{head[:7]}"
    assert first.parent.parent == repo / "tickets" / "reviews"
    header = re_mod.parse_report(first.read_text())
    assert header["base"] == base and header["head"] == head
    assert header["seat"] == "correctness" and "Report body." in first.read_text()


@pytest.mark.integration
def test_unchanged_head_reuses_without_dispatching_duplicates(repo, policy):
    record_seat(repo, policy, "correctness")
    record_seat(repo, policy, "red-team")
    commit_reports(repo)  # a report-only commit moves the head
    plan = run_cli(repo, policy, "plan", "--seat", "correctness", "--seat", "red-team")
    assert plan.returncode == 0, plan.stderr
    assert json.loads(plan.stdout)["dispatch"] == []
    gate = run_gate(repo, policy, "--seat", "correctness", "--seat", "red-team")
    assert gate.returncode == 0, gate.stdout + gate.stderr
    assert "seat correctness: reused" in gate.stdout


@pytest.mark.integration
def test_rebase_onto_unrelated_main_keeps_reuse(repo, policy):
    record_seat(repo, policy, "correctness")
    commit_reports(repo)
    git(repo, "switch", "-q", "main")
    commit(repo, "other.txt", "unrelated\n", "main moves")
    git(repo, "switch", "-q", "feature")
    git(repo, "rebase", "-q", "main")
    gate = run_gate(repo, policy, "--seat", "correctness")
    assert gate.returncode == 0, gate.stdout + gate.stderr


@pytest.mark.integration
def test_relevant_change_re_reviews_only_what_went_stale(repo, policy):
    record_seat(repo, policy, "correctness")
    commit_reports(repo)
    commit(repo, "app.py", "def f():\n    return 2\n", "fix")
    plan = json.loads(run_cli(repo, policy, "plan", "--seat", "correctness").stdout)
    assert plan["dispatch"] == ["correctness"]
    gate = run_gate(repo, policy, "--seat", "correctness")
    assert gate.returncode != 0
    assert "seat correctness: stale" in gate.stdout


@pytest.mark.integration
def test_whitespace_only_code_change_invalidates(repo, policy):
    record_seat(repo, policy, "correctness")
    commit_reports(repo)
    commit(repo, "app.py", "def f():\n  return 1\n", "reindent")
    assert run_gate(repo, policy, "--seat", "correctness").returncode != 0


@pytest.mark.integration
def test_executable_file_under_reviews_invalidates(repo, policy):
    record_seat(repo, policy, "correctness")
    commit_reports(repo)
    commit(repo, "tickets/reviews/hook.sh", "#!/bin/sh\n", "sneak", mode=0o755)
    gate = run_gate(repo, policy, "--seat", "correctness")
    assert gate.returncode != 0 and "stale" in gate.stdout


@pytest.mark.integration
def test_criteria_and_policy_changes_invalidate(repo, policy):
    record_seat(repo, policy, "correctness")
    commit_reports(repo)
    (policy / "skills" / "gaze" / "SKILL.md").write_text("gaze v2\n")
    assert "policy-version" in run_gate(repo, policy, "--seat", "correctness").stdout
    (policy / "skills" / "gaze" / "SKILL.md").write_text("gaze v1\n")
    commit(repo, "tickets/0001-x.erg", TICKET.replace("Second", "Third"), "rescope")
    assert "criteria-hash" in run_gate(repo, policy, "--seat", "correctness").stdout


@pytest.mark.integration
def test_gate_rejects_missing_report_and_never_reuses_checks(repo, policy):
    record_seat(repo, policy, "adherence", kind="adherence")
    commit_reports(repo)
    gate = run_gate(repo, policy, "--seat", "correctness", "--seat", "adherence")
    assert gate.returncode != 0
    assert "seat correctness: no-report" in gate.stdout
    assert "seat adherence: no-report" in gate.stdout


@pytest.mark.integration
def test_gate_high_row_needs_red_team_and_another_family(repo, policy):
    record_seat(repo, policy, "correctness", family="Anthropic")
    commit_reports(repo)
    args = ("gate", "--seat", "correctness", "--risk", "high", "--producer-family", "Anthropic")
    gate = run_cli(repo, policy, *args)
    assert gate.returncode != 0
    assert "red-team" in gate.stdout and "independence: missing" in gate.stdout
    record_seat(repo, policy, "red-team", family="OpenAI")
    commit_reports(repo)
    gate = run_cli(repo, policy, *args)
    assert gate.returncode == 0, gate.stdout
    assert "independent: OpenAI" in gate.stdout


@pytest.mark.integration
def test_gate_prints_floor_and_refuses_an_under_rated_plan(repo, policy):
    record_seat(repo, policy, "correctness")
    commit_reports(repo)
    commit(repo, "tickets/0001-x.erg", TICKET, "context names verify-gate")  # criteria unchanged
    gate = run_cli(repo, policy, "gate", "--seat", "correctness", "--risk", "ordinary")
    assert "risk: ordinary / floor: high" in gate.stdout  # the ticket text names verify-gate
    assert gate.returncode != 0


# --- seat table ------------------------------------------------------------

def _seat_report(n, **over):
    return (Path(f"tickets/reviews/r/correctness-{n}.md"), record(**over))


@pytest.mark.parametrize("order", [("approve", "changes"), ("changes", "approve")])
def test_changes_verdict_dominates_whatever_the_report_order(monkeypatch, order):
    """seat-10 sorts before seat-2: an earlier approve must not mask a recorded changes."""
    reports = [_seat_report(n, verdict=v) for n, v in zip((10, 2), order)]
    monkeypatch.setattr(re_mod, "load_reports", lambda *a: reports)
    row = re_mod.seat_rows(Path("."), inputs(), ["correctness"])[0]
    assert row["status"] == "ran" and row["header"]["verdict"] == "changes"


@pytest.mark.integration
def test_gate_without_a_plan_row_fails_closed(repo, policy):
    """No 'risk: unstated' pass: a gate run must name the plan row."""
    record_seat(repo, policy, "correctness")
    commit_reports(repo)
    out = run_cli(repo, policy, "gate", "--seat", "correctness")
    assert out.returncode != 0
    assert "unstated" not in out.stdout
