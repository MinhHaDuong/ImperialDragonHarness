"""Behavioural tests for the review evidence core (ticket 1142).

The decision function, forge actor admission and criteria hash
are pure and run in the fast tier. The scenarios that need a repository
(unchanged-head reuse, report-only commits, rebases, relevant changes, the
gate's refusal of stale or missing proof) build a throwaway git repository
and are `integration`.
"""

import importlib.util
import json
import re
import shutil
import subprocess
import sys
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


DONE = {"hasNextPage": False, "endCursor": None}


def forge_payload(reviews=(), comments=(), threads=(), more=None):
    def page(nodes, key):
        return {"nodes": list(nodes),
                "pageInfo": {"hasNextPage": more == key, "endCursor": "c"}}

    return {"data": {"repository": {"pullRequest": {
        "reviews": page(reviews, "reviews"), "comments": page(comments, "comments"),
        "reviewThreads": page(threads, "reviewThreads")}}}}


def test_forge_reviews_are_classified_from_graphql():
    payload = forge_payload(
        reviews=[
            {"__typename": "PullRequestReview", "author": {"login": "MinhHaDuong", "id": HUMAN_ID},
             "lastEditedAt": None, "state": "APPROVED", "commit": {"oid": "a" * 40}},
            {"__typename": "PullRequestReview",
             "author": {"login": "copilot-pull-request-reviewer", "id": COPILOT_ID},
             "lastEditedAt": None, "state": "COMMENTED", "commit": {"oid": "a" * 40}},
            {"__typename": "PullRequestReview", "author": {"login": "mallory", "id": "U_x"},
             "lastEditedAt": None, "state": "APPROVED", "commit": {"oid": "a" * 40}},
        ],
        comments=[
            {"__typename": "IssueComment", "author": {"login": "MinhHaDuong", "id": HUMAN_ID},
             "lastEditedAt": "2026-10-20T00:00:00Z"},
        ])
    rows = re_mod.classify_forge(payload, "github.com")
    roles = [(r["login"], r["status"]) for r in rows]
    assert ("MinhHaDuong", "human: ran") in roles
    assert ("copilot-pull-request-reviewer", "copilot: ran") in roles
    assert ("mallory", "rejected") in roles
    edited = [r for r in rows if r["object_type"] == "IssueComment"]
    assert edited[0]["status"] == "rejected"


def test_inline_review_thread_comments_are_read():
    thread = {"isResolved": False, "comments": {"pageInfo": DONE, "nodes": [
        {"__typename": "PullRequestReviewComment",
         "author": {"login": "copilot-pull-request-reviewer", "id": COPILOT_ID},
         "lastEditedAt": None, "path": "scripts/x.py"}]}}
    rows = re_mod.classify_forge(forge_payload(threads=[thread]), "github.com")
    assert [(r["object_type"], r["status"], r["resolved"]) for r in rows] == [
        ("PullRequestReviewComment", "copilot: ran", False)]


@pytest.mark.parametrize("more", ["reviews", "comments", "reviewThreads"])
def test_truncated_forge_read_fails_closed(more):
    with pytest.raises(re_mod.ForgeReadError):
        re_mod.classify_forge(forge_payload(more=more), "github.com")
    thread = {"isResolved": True, "comments": {"pageInfo": {"hasNextPage": True}, "nodes": []}}
    with pytest.raises(re_mod.ForgeReadError):
        re_mod.classify_forge(forge_payload(threads=[thread]), "github.com")


def _forge_cli(monkeypatch, returncode, stdout):
    import types
    monkeypatch.setattr(re_mod.subprocess, "run", lambda *a, **k: types.SimpleNamespace(
        returncode=returncode, stdout=stdout, stderr="boom"))
    args = types.SimpleNamespace(forge_repo="o/n", pr=1, host="github.com")
    return re_mod.cmd_forge(args)


def test_forge_exit_codes_separate_a_failed_read_from_a_rejected_row(monkeypatch):
    mallory = {"__typename": "PullRequestReview", "author": {"login": "m", "id": "U_x"},
               "lastEditedAt": None}
    assert _forge_cli(monkeypatch, 1, "") == re_mod.EXIT_READ_FAILED
    truncated = json.dumps(forge_payload(more="reviews"))
    assert _forge_cli(monkeypatch, 0, truncated) == re_mod.EXIT_READ_FAILED
    assert _forge_cli(monkeypatch, 0, json.dumps(forge_payload(reviews=[mallory]))) == 1
    assert _forge_cli(monkeypatch, 0, json.dumps(forge_payload())) == 0
    assert re_mod.EXIT_READ_FAILED not in (0, 1, 2)


# --- criteria hash ---------------------------------------------------------

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
        [sys.executable, str(SCRIPT), *args, "--repo", str(repo), "--base", "main",
         "--policy-root", str(policy), "--ticket", str(repo / "tickets/0001-x.erg")],
        capture_output=True, text=True, env=child_env())


def run_gate(repo, policy, *args):
    return run_cli(repo, policy, "gate", *args)


def record_seat(repo, policy, seat, family="Anthropic", verdict="approve", kind="review"):
    out = subprocess.run(
        [sys.executable, str(SCRIPT), "record", "--repo", str(repo), "--base", "main",
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
def test_trailing_whitespace_on_the_final_diff_line_changes_identity(repo, policy):
    """The diff is hashed byte for byte: no strip of its last line."""
    record_seat(repo, policy, "correctness")
    commit_reports(repo)
    commit(repo, "app.py", "def f():\n    return 1 \n", "trailing space on the last line")
    gate = run_gate(repo, policy, "--seat", "correctness")
    assert gate.returncode != 0 and "stale" in gate.stdout


@pytest.mark.integration
def test_reports_are_read_from_the_head_commit_not_the_working_tree(repo, policy):
    """An uncommitted report, or a committed symlink to one, proves nothing."""
    report = record_seat(repo, policy, "correctness")
    assert "seat correctness: no-report" in run_gate(repo, policy, "--seat", "correctness").stdout
    outside = repo / "outside.md"
    outside.write_text(report.read_text().replace("seat: correctness", "seat: red-team"))
    link = report.parent / "red-team-1.md"
    link.symlink_to("../../../outside.md")
    git(repo, "add", str(link.relative_to(repo)))
    git(repo, "commit", "-q", "-m", "symlinked report")
    out = run_gate(repo, policy, "--seat", "red-team")
    assert "seat red-team: no-report" in out.stdout


# --- verifiable minors -----------------------------------------------------

def test_forge_node_without_edit_status_counts_as_edited():
    node = {"__typename": "PullRequestReview", "author": {"login": "h", "id": HUMAN_ID}}
    rows = re_mod.classify_forge(forge_payload(reviews=[node]), "github.com")
    assert rows[0]["status"] == "rejected"


def test_seat_rows_tolerate_reports_missing_verdict_or_head(monkeypatch):
    no_head = record()
    del no_head["head"]
    no_verdict = record()
    del no_verdict["verdict"]
    monkeypatch.setattr(re_mod, "load_reports", lambda *a: [
        (Path("a.md"), no_head), (Path("b.md"), no_verdict)])
    row = re_mod.seat_rows(Path("."), inputs(), ["correctness"])[0]
    assert row["status"] == "reused" and row["path"] == Path("a.md")


@pytest.mark.integration
def test_gate_tolerates_a_report_header_without_head(repo, policy):
    report = record_seat(repo, policy, "red-team", family="OpenAI")
    report.write_text("".join(line for line in report.read_text().splitlines(True)
                              if not line.startswith("head: ")))
    commit_reports(repo)
    out = run_gate(repo, policy, "--seat", "red-team")
    assert "Traceback" not in out.stderr
    assert out.returncode == 0, out.stdout + out.stderr


@pytest.mark.integration
@pytest.mark.parametrize("flag,value", [
    ("--worker", "w\nverdict: approve"), ("--family", "x\nhead: y"),
    ("--seat", "../escape"), ("--seat", "a/b"),
])
def test_record_rejects_header_injection_and_path_escape(repo, policy, flag, value):
    args = {"--seat": "correctness", "--worker": "t", "--family": "Anthropic"}
    args[flag] = value
    out = subprocess.run(
        [sys.executable, str(SCRIPT), "record", "--repo", str(repo), "--base", "main",
         "--policy-root", str(policy), "--verdict", "approve",
         *[x for kv in args.items() for x in kv]],
        input="body\n", capture_output=True, text=True, env=child_env())
    assert out.returncode != 0
    assert not (repo / "tickets" / "reviews").exists()


# --- reroll round 1: header injection, family vocabulary -------------------

@pytest.mark.parametrize("sep", [" ", " ", "\x85", "\v", "\f", "\x1c", "\x1d", "\x1e"])
def test_header_value_refuses_every_line_boundary(sep):
    """str.splitlines() splits on these: a value holding one can forge a field."""
    with pytest.raises(Exception):
        re_mod.header_value(f"w{sep}kind: review")


@pytest.mark.integration
@pytest.mark.parametrize("sep", [" ", "\x85"])
def test_record_refuses_unicode_line_separators(repo, policy, sep):
    out = subprocess.run(
        [sys.executable, str(SCRIPT), "record", "--repo", str(repo), "--base", "main",
         "--policy-root", str(policy), "--seat", "adherence", "--kind", "adherence",
         "--verdict", "approve", "--family", "anthropic", "--worker", f"w{sep}kind: review"],
        input="body\n", capture_output=True, text=True, env=child_env())
    assert out.returncode != 0
    assert not (repo / "tickets" / "reviews").exists()


def test_report_with_a_duplicate_header_key_is_not_trusted():
    text = (f"---\nreview-evidence: {re_mod.FORMAT}\nkind: adherence\nseat: a\n"
            "kind: review\n---\n\nbody\n")
    assert re_mod.parse_report(text) == {}


@pytest.mark.parametrize("value,expected", [
    ("anthropic ", "anthropic"), ("OpenAI", "openai"), (" Google", "google"),
])
def test_family_is_stripped_and_casefolded(value, expected):
    assert re_mod.family_name(value) == expected


@pytest.mark.parametrize("value", ["claude", "gpt", "", "x\nhead: y"])
def test_family_outside_the_vocabulary_is_refused(value):
    with pytest.raises(Exception):
        re_mod.family_name(value)


def test_family_vocabulary_covers_the_route_grid():
    grid = (REPO_ROOT / "skills" / "route" / "grid.json").read_text()
    found = {m.casefold() for m in re.findall(r'"family":\s*"([^"]+)"', grid)}
    assert found and found <= re_mod.FAMILIES


@pytest.mark.integration
def test_record_refuses_an_unknown_family(repo, policy):
    out = subprocess.run(
        [sys.executable, str(SCRIPT), "record", "--repo", str(repo), "--base", "main",
         "--policy-root", str(policy), "--seat", "red-team", "--verdict", "approve",
         "--family", "claude", "--worker", "t"],
        input="body\n", capture_output=True, text=True, env=child_env())
    assert out.returncode != 0
    assert not (repo / "tickets" / "reviews").exists()


@pytest.mark.integration
def test_record_writes_no_absolute_worktree_path_and_reads_body_file(repo, policy, tmp_path):
    body = tmp_path / "body.md"
    body.write_text(f"see {repo}/scripts/x.py and {repo}\n", encoding="utf-8")
    out = subprocess.run(
        [sys.executable, str(SCRIPT), "record", "--repo", str(repo), "--base", "main",
         "--policy-root", str(policy), "--ticket", str(repo / "tickets/0001-x.erg"),
         "--seat", "correctness", "--verdict", "approve", "--family", "Anthropic",
         "--worker", "test", "--body-file", str(body)],
        stdin=subprocess.DEVNULL, capture_output=True, text=True, env=child_env(), check=True)
    text = Path(out.stdout.strip()).read_text(encoding="utf-8")
    assert str(repo) not in text and "see scripts/x.py and ." in text


@pytest.mark.integration
def test_gate_survives_a_ticket_close_after_the_reports(repo, policy):
    """Ticket 1236 gaze finding: gaze, then close on the branch, then gate."""
    record_seat(repo, policy, "correctness")
    record_seat(repo, policy, "red-team")
    commit_reports(repo)
    git(repo, "mv", "tickets/0001-x.erg", "tickets/closed/0001-x.erg") if (repo / "tickets/closed").mkdir(exist_ok=True) is None else None
    closed = repo / "tickets/closed/0001-x.erg"
    closed.write_text(closed.read_text().replace("[ ]", "[x]") + "\n2026-10-27 closed\n")
    git(repo, "add", "-A", "tickets")
    git(repo, "commit", "-q", "-m", "ticket(1): close and archive")
    out = subprocess.run(
        [sys.executable, str(SCRIPT), "gate", "--repo", str(repo), "--base", "main",
         "--policy-root", str(policy), "--ticket", str(closed),
         "--seat", "correctness", "--seat", "red-team"],
        capture_output=True, text=True, env=child_env())
    assert out.returncode == 0, out.stdout + out.stderr
    assert "stale" not in out.stdout


@pytest.mark.integration
def test_ticket_edit_with_changed_criteria_is_still_caught(repo, policy):
    record_seat(repo, policy, "correctness")
    commit_reports(repo)
    (repo / "tickets/0001-x.erg").write_text(REPO_TICKET.replace("## Exit criteria\n", "## Exit criteria\n- [ ] new demand\n"))
    git(repo, "commit", "-qam", "criteria change")
    out = subprocess.run(
        [sys.executable, str(SCRIPT), "gate", "--repo", str(repo), "--base", "main",
         "--policy-root", str(policy), "--ticket", str(repo / "tickets/0001-x.erg"),
         "--seat", "correctness"], capture_output=True, text=True, env=child_env())
    assert out.returncode != 0 and "stale" in out.stdout


@pytest.mark.integration
def test_relativize_respects_path_boundaries_and_other_worktrees(repo, tmp_path):
    sibling = tmp_path / "repo-extra"
    other = tmp_path / "review-9"
    git(repo, "worktree", "add", "-q", "-b", "rv", str(other))
    text = f"a {repo}/x.py b {repo}-extra/y.py c {other}/z.py d {repo}."
    got = re_mod.relativize(text, repo)
    assert "a x.py" in got and f"{repo}-extra/y.py" in got and "c z.py" in got
    assert str(repo) + "/" not in got.replace(f"{repo}-extra/y.py", "")
    assert str(sibling) in got
    assert got.endswith("d ..")  # root becomes ".", the sentence period stays


def gate_with(repo, policy, ticket, *seats):
    args = [sys.executable, str(SCRIPT), "gate", "--repo", str(repo), "--base", "main",
            "--policy-root", str(policy), *sum((["--seat", x] for x in seats), [])]
    if ticket is not None:
        args += ["--ticket", str(ticket)]
    return subprocess.run(args, capture_output=True, text=True, env=child_env())


@pytest.mark.integration
def test_rewritten_criterion_is_stale_even_with_a_stale_ticket_copy(repo, policy, tmp_path):
    old_copy = tmp_path / "0001-x.erg"
    old_copy.write_text((repo / "tickets/0001-x.erg").read_text())
    record_seat(repo, policy, "correctness")
    commit_reports(repo)
    (repo / "tickets/0001-x.erg").write_text(REPO_TICKET.replace("## Exit criteria\n", "## Exit criteria\n- [ ] rewritten\n"))
    git(repo, "commit", "-qam", "rewrite criterion")
    for ticket in (repo / "tickets/0001-x.erg", old_copy):
        out = gate_with(repo, policy, ticket)
        assert out.returncode != 0, out.stdout
    out = gate_with(repo, policy, repo / "tickets/0001-x.erg", "correctness")
    assert out.returncode != 0 and "stale" in out.stdout
    # a stale copy passed by path is only a name: the committed text decides
    shadow = repo / "tickets/0001-x.erg"
    shadow.write_text(old_copy.read_text())
    out = gate_with(repo, policy, shadow, "correctness")
    assert out.returncode != 0 and "stale" in out.stdout


@pytest.mark.integration
def test_untracked_ticket_and_omitted_ticket_on_a_touched_range_are_refused(repo, policy, tmp_path):
    record_seat(repo, policy, "correctness")
    commit_reports(repo)
    stray = repo / "tickets/9999-nope.erg"
    stray.write_text(REPO_TICKET)
    out = gate_with(repo, policy, stray, "correctness")
    assert out.returncode != 0 and "not tracked" in out.stderr
    stray.unlink()
    (repo / "tickets/0001-x.erg").write_text(REPO_TICKET + "\nnote\n")
    git(repo, "commit", "-qam", "touch ticket")
    out = gate_with(repo, policy, None, "correctness")
    assert out.returncode != 0 and "pass --ticket" in out.stderr


@pytest.mark.integration
def test_executable_ticket_edit_is_not_exempt(repo, policy):
    record_seat(repo, policy, "correctness")
    commit_reports(repo)
    p = repo / "tickets/0001-x.erg"
    p.chmod(0o755)
    git(repo, "commit", "-qam", "chmod ticket")
    out = gate_with(repo, policy, p, "correctness")
    assert out.returncode != 0 and "stale" in out.stdout


@pytest.mark.integration
def test_probe_a_shadow_ticket_committed_after_review_is_not_the_reviewed_ticket(repo, policy):
    record_seat(repo, policy, "correctness")
    commit_reports(repo)
    commit(repo, "tickets/9999-shadow.erg", REPO_TICKET, "shadow")
    shadow = repo / "tickets/9999-shadow.erg"
    out = gate_with(repo, policy, shadow, "correctness")
    assert out.returncode != 0 and ("stale" in out.stdout or "ticket" in out.stderr)


@pytest.mark.integration
def test_probe_c_open_and_closed_copies_together_are_refused(repo, policy):
    record_seat(repo, policy, "correctness")
    commit_reports(repo)
    commit(repo, "tickets/closed/0001-x.erg",
           REPO_TICKET.replace("## Exit criteria\n", "## Exit criteria\n- [ ] rewritten\n"), "closed copy")
    out = gate_with(repo, policy, repo / "tickets/0001-x.erg", "correctness")
    assert out.returncode != 0 and "both open and closed" in out.stderr


@pytest.mark.integration
def test_probe_g_a_non_ticket_path_is_refused(repo, policy):
    subprocess.run([sys.executable, str(SCRIPT), "record", "--repo", str(repo), "--base", "main",
                    "--policy-root", str(policy), "--no-ticket", "--seat", "correctness",
                    "--verdict", "approve", "--family", "Anthropic", "--worker", "t"],
                   input="b\n", check=True, capture_output=True, text=True, env=child_env())
    commit_reports(repo)
    out = gate_with(repo, policy, repo / "README.md", "correctness")
    assert out.returncode != 0 and "not a ticket file" in out.stderr


@pytest.mark.integration
def test_a_second_exit_criteria_section_makes_the_review_stale(repo, policy):
    record_seat(repo, policy, "correctness")
    commit_reports(repo)
    p = repo / "tickets/0001-x.erg"
    p.write_text(p.read_text() + "\n## Exit criteria\n- [ ] sneaked in\n")
    git(repo, "commit", "-qam", "second section")
    out = gate_with(repo, policy, p, "correctness")
    assert out.returncode != 0 and "stale" in out.stdout


@pytest.mark.integration
def test_record_without_a_ticket_choice_is_refused(repo, policy):
    out = subprocess.run([sys.executable, str(SCRIPT), "record", "--repo", str(repo), "--base", "main",
                          "--policy-root", str(policy), "--seat", "correctness", "--verdict", "approve",
                          "--family", "Anthropic", "--worker", "t"],
                         input="b\n", capture_output=True, text=True, env=child_env())
    assert out.returncode != 0 and "--ticket" in out.stderr


# --- ticket 1261: heading variants and the PR's claim ------------------------

def _edit_after_review(repo, policy, edit):
    record_seat(repo, policy, "correctness")
    commit_reports(repo)
    p = repo / "tickets/0001-x.erg"
    p.write_text(edit(p.read_text()))
    git(repo, "commit", "-qam", "edit ticket")
    return gate_with(repo, policy, p, "correctness")


@pytest.mark.integration
@pytest.mark.parametrize("heading", ["## Exit Criteria", "### Exit criteria",
                                     "## Exit criteria (added)"])
def test_variant_criteria_heading_added_after_review_is_stale(repo, policy, heading):
    out = _edit_after_review(repo, policy, lambda t: t + f"\n{heading}\n- [ ] sneaked in\n")
    assert out.returncode != 0 and "stale" in out.stdout, out.stdout


@pytest.mark.integration
def test_rename_weaken_and_append_an_unchanged_copy_is_stale(repo, policy):
    def edit(text):
        old = text.split("## Exit criteria\n", 1)[1].split("\n## ", 1)[0]
        renamed = text.replace("## Exit criteria\n", "## Acceptance\n- [ ] weak\n# ", 1)
        return renamed.replace("# \n", "\n", 1) + "\n## Exit criteria\n" + old
    out = _edit_after_review(repo, policy, edit)
    assert out.returncode != 0 and "stale" in out.stdout, out.stdout


def test_criteria_hash_reads_heading_variants_and_sees_outside_checkboxes():
    base = re_mod.criteria_hash(TICKET)
    for heading in ("## Exit Criteria", "### Exit criteria", "## Exit criteria (added)"):
        assert re_mod.criteria_hash(TICKET + f"\n{heading}\n- [ ] more\n") != base
    assert re_mod.criteria_hash(TICKET + "\n## Acceptance\n- [ ] weak\n") != base
    assert re_mod.criteria_hash(TICKET.replace("irrelevant", "prose changes")) == base


def _two_tickets(repo):
    commit(repo, "tickets/0002-y.erg", REPO_TICKET.replace("Title: x", "Title: y"), "other ticket")


def _gate_claiming(repo, policy, tmp_path, body, ticket):
    body_file = tmp_path / "body.md"
    body_file.write_text(body)
    return subprocess.run(
        [sys.executable, str(SCRIPT), "gate", "--repo", str(repo), "--base", "main",
         "--policy-root", str(policy), "--ticket", str(repo / ticket),
         "--pr-body-file", str(body_file), "--seat", "correctness"],
        capture_output=True, text=True, env=child_env())


@pytest.mark.integration
def test_gate_refuses_a_recorded_ticket_the_pr_does_not_claim(repo, policy, tmp_path):
    _two_tickets(repo)
    subprocess.run(
        [sys.executable, str(SCRIPT), "record", "--repo", str(repo), "--base", "main",
         "--policy-root", str(policy), "--ticket", str(repo / "tickets/0002-y.erg"),
         "--seat", "correctness", "--verdict", "approve", "--family", "Anthropic",
         "--worker", "t"], input="b\n", capture_output=True, text=True,
        env=child_env(), check=True)
    commit_reports(repo)
    # the probe: without the claim, the unrelated ticket's report reads reused
    probe = gate_with(repo, policy, repo / "tickets/0002-y.erg", "correctness")
    assert probe.returncode == 0 and "stale" not in probe.stdout
    wrong = _gate_claiming(repo, policy, tmp_path, "**Ticket:** tickets/0001-x.erg\n",
                           "tickets/0002-y.erg")
    assert wrong.returncode != 0 and "claim" in (wrong.stdout + wrong.stderr), wrong.stdout
    right = _gate_claiming(repo, policy, tmp_path, "**Ticket:** tickets/0002-y.erg\n",
                           "tickets/0002-y.erg")
    assert right.returncode == 0, right.stdout + right.stderr
    none = _gate_claiming(repo, policy, tmp_path, "Ticket: none\n", "tickets/0002-y.erg")
    assert none.returncode != 0
    fenced = _gate_claiming(repo, policy, tmp_path,
                            "```\n**Ticket:** tickets/0002-y.erg\n```\n", "tickets/0002-y.erg")
    assert fenced.returncode != 0


@pytest.mark.parametrize("bullet", ["* [ ] weak", "+ [ ] weak", "1. [ ] weak", "- weak"])
def test_renamed_section_with_any_list_form_is_seen(bullet):
    base = re_mod.criteria_hash(TICKET)
    tampered = TICKET.replace("## Exit criteria\n- [ ] First criterion\n- [ ] Second criterion",
                              f"## Acceptance\n{bullet}") + "\n## Exit criteria\n- [ ] First criterion\n- [ ] Second criterion\n"
    assert re_mod.criteria_hash(tampered) != base


def test_comment_line_in_a_fence_does_not_close_the_criteria_section():
    plain = TICKET.replace("- [ ] Second criterion", "- [ ] Second criterion\n```\n# run this\n```\n- [ ] Third")
    weaker = plain.replace("- [ ] Third", "- [ ] Third, loosened")
    assert re_mod.criteria_hash(plain) != re_mod.criteria_hash(weaker)


@pytest.mark.integration
def test_gate_refuses_several_claims_and_disagreeing_grammars(repo, policy, tmp_path):
    _two_tickets(repo)
    record_seat(repo, policy, "correctness")
    commit_reports(repo)
    several = _gate_claiming(repo, policy, tmp_path,
                             "**Ticket:** tickets/0001-x.erg\n**Ticket:** tickets/0002-y.erg\n",
                             "tickets/0001-x.erg")
    assert several.returncode != 0 and "claim" in several.stdout
    split = _gate_claiming(repo, policy, tmp_path,
                           "Ticket: tickets/0001-x.erg (main)\nticket tickets/0002-y.erg\n",
                           "tickets/0002-y.erg")
    assert split.returncode != 0 and "claim" in split.stdout


def test_suffix_on_the_criteria_heading_changes_the_hash():
    soft = TICKET.replace("## Exit criteria", "## Exit criteria (advisory, none required)")
    assert re_mod.criteria_hash(soft) != re_mod.criteria_hash(TICKET)


# --- ticket 1261 fix round: HTML comments and fence indentation ---------------

@pytest.mark.parametrize("closer", ["\n## Notes\n-->", "\n# -->"])
def test_commenting_out_the_criteria_section_changes_the_hash(closer):
    head, tail = TICKET.split("## Exit criteria\n")
    section = "## Exit criteria\n" + tail.split("\n## ")[0]
    hidden = TICKET.replace(section, "<!--\n" + section + closer + "\n")
    assert re_mod.criteria_hash(hidden) != re_mod.criteria_hash(TICKET)


def test_unterminated_comment_is_refused():
    with pytest.raises(ValueError):
        re_mod.criteria_hash(TICKET + "\n<!-- never closed\n")


def test_comments_elsewhere_do_not_move_the_hash():
    noted = TICKET.replace("irrelevant", "irrelevant <!-- a\n- [ ] note\n# x\n-->")
    assert re_mod.criteria_hash(noted) == re_mod.criteria_hash(TICKET)
    real = (REPO_ROOT / "tickets/closed/0016-harness-project-leak-guard.erg").read_text()
    assert "<!--" in real
    assert re_mod.criteria_hash(real) == re_mod.criteria_hash(real + "\n<!-- extra\n- [ ] x\n-->\n")


def test_indented_fence_is_not_a_fence_and_closer_takes_no_info_string():
    # a 4-space indented ``` is text: the heading after it still counts
    lead = TICKET.replace("irrelevant", "    ```")
    sneaked = lead + "\n## Exit criteria (added)\n- [ ] sneaked\n"
    assert re_mod.criteria_hash(sneaked) != re_mod.criteria_hash(lead)
    ends = TICKET.replace("irrelevant", "```python\n## Exit criteria\nghost\n``` js\n## Exit criteria\nghost2\n```")
    # ``` js does not close: everything up to the bare closer is fenced text
    assert re_mod.criteria_hash(ends) == re_mod.criteria_hash(TICKET)


# --- ticket 1261, second fix round: spans, fences and headings before comments ---

def _with_criteria(*items, tail=""):
    body = "\n".join(f"- [ ] {i}" for i in items)
    return f"%erg 0.1\nTitle: x\n\n--- body ---\n## Context\nc\n\n## Exit criteria\n{body}\n{tail}\n## Notes\nn\n"


def test_inline_code_comment_markers_do_not_hide_criteria_between_them():
    mid = "`<!--` opens a comment"
    end = "`-->` closes it"
    one = _with_criteria(mid, "hidden demand", end)
    two = _with_criteria(mid, "hidden demand, loosened", end)
    assert re_mod.criteria_hash(one) != re_mod.criteria_hash(two)


def test_empty_comment_forms_are_complete_comments():
    for empty in ("<!-->", "<!--->"):
        one = _with_criteria("a", f"x {empty} y", "b", "later <!-- end --> z")
        two = _with_criteria("a", f"x {empty} y", "b changed", "later <!-- end --> z")
        assert re_mod.criteria_hash(one) != re_mod.criteria_hash(two)


# hashes of the pre-comment-strip code (613d45ad) on tickets whose inline code names a marker
PRE_STRIP_HASHES = {
    "0016-harness-project-leak-guard": "1a7a7bfdd1385859",
    "0124-fix-leak-guard-violation-raid-skill": "354b4d5746cd03d5",
    "0304-enrich-generated-state-status-block": "facb6547fd5982cc",
    "1233-harness-doctor-lints-harness-skills-and": "a2a0fff81954611c",
    "1246-raid-prints-a-portable-sitrep-every-15-minutes": "5312193c51eff06c",
}


@pytest.mark.parametrize("stem", sorted(PRE_STRIP_HASHES))
def test_inline_code_markers_in_real_closed_tickets_keep_their_hash(stem):
    text = (REPO_ROOT / f"tickets/closed/{stem}.erg").read_text()
    assert re_mod.criteria_hash(text) == PRE_STRIP_HASHES[stem]


@pytest.mark.parametrize("heading_block", [
    "  ## Exit criteria (added)\nsneaked demand",
    "Exit criteria (revised)\n-----------------------\nsneaked demand",
    "Exit criteria (revised)\n=======================\nsneaked demand",
])
def test_indented_and_setext_headings_are_criteria_sections(heading_block):
    lead = _with_criteria("a") + "\n## Notes\n"  # closed section; prose counts only under a criteria heading
    assert re_mod.criteria_hash(lead + "\n" + heading_block + "\n") != re_mod.criteria_hash(lead)


def test_backtick_info_string_with_a_backtick_is_no_fence():
    lead = _with_criteria("a") + "\n```x`y\n"
    sneaked = lead + "\n## Exit criteria (added)\nsneaked demand\n"
    assert re_mod.criteria_hash(sneaked) != re_mod.criteria_hash(lead)


def test_lone_code_span_or_fenced_open_comment_is_not_refused():
    re_mod.criteria_hash(_with_criteria("a `<!--` b"))
    re_mod.criteria_hash(_with_criteria("a", tail="```html\n<!-- never closed\n```\n"))
    with pytest.raises(ValueError):
        re_mod.criteria_hash(_with_criteria("a", tail="<!-- never closed\n"))
