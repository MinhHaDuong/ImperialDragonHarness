"""Merge gate record on the candidate merge commit (ticket 1156, tracker 1045).

The gate builds the candidate merge commit of a branch head into its base,
runs the declared check set in a throwaway worktree of that commit, and writes
a record as a git note under refs/notes/gate. `check` answers from the latest
entry for that candidate. Every fixture is a local repository with a bare
origin: no forge, no network.
"""

import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

from child_env import child_env

pytestmark = pytest.mark.integration

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "merge-gate.py"

CONFIG = {
    "gate": "on",
    "scope": "fixture-set",
    "checks": [
        {"name": "always-pass", "argv": ["true"]},
        {"name": "marker-absent", "argv": ["sh", "-c", "! test -e FAIL_MARKER"]},
    ],
    "versions": [{"name": "git", "argv": ["git", "--version"]}],
}


def git(cwd, *args, env=None):
    return subprocess.run(
        ["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True, env=env or child_env()
    ).stdout.strip()


def gate(cwd, *args, env=None):
    return subprocess.run(
        ["python3", str(SCRIPT), *args], cwd=cwd, capture_output=True, text=True, env=env or child_env()
    )


@pytest.fixture
def module():
    spec = importlib.util.spec_from_file_location("merge_gate", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def repo(tmp_path):
    origin = tmp_path / "origin.git"
    work = tmp_path / "work"
    subprocess.run(["git", "init", "-q", "--bare", str(origin)], check=True, env=child_env())
    subprocess.run(["git", "init", "-q", "-b", "main", str(work)], check=True, env=child_env())
    for key, value in (("user.email", "t@example.com"), ("user.name", "Fixture"), ("commit.gpgsign", "false")):
        git(work, "config", key, value)
    (work / ".merge-gate.json").write_text(json.dumps(CONFIG), encoding="utf-8")
    (work / "a.txt").write_text("a\n", encoding="utf-8")
    git(work, "add", ".")
    git(work, "commit", "-q", "-m", "base")
    git(work, "remote", "add", "origin", str(origin))
    git(work, "push", "-q", "origin", "main")
    git(work, "switch", "-q", "-c", "feature")
    (work / "b.txt").write_text("b\n", encoding="utf-8")
    git(work, "add", ".")
    git(work, "commit", "-q", "-m", "feature")
    git(work, "push", "-q", "origin", "feature")
    return work


def test_candidate_is_deterministic_merge_of_base_and_head(repo):
    first = gate(repo, "candidate", "--base", "main", "--head", "feature")
    assert first.returncode == 0, first.stderr
    oid = first.stdout.strip()
    second = gate(repo, "candidate", "--base", "main", "--head", "feature", env={**child_env(), "TZ": "Asia/Tokyo"})
    assert second.stdout.strip() == oid
    parents = git(repo, "rev-list", "--parents", "-n", "1", oid).split()
    assert parents[1:] == [git(repo, "rev-parse", "main"), git(repo, "rev-parse", "feature")]


def test_no_record_is_missing(repo):
    result = gate(repo, "check", "--base", "main", "--head", "feature")
    assert result.returncode == 2
    assert "missing" in result.stdout


def test_run_records_every_field_on_the_candidate_and_pushes(repo):
    env = {**child_env(), "MERGE_GATE_RUNTIME": "fixture", "MERGE_GATE_MODEL": "example/model-v1"}
    run = gate(repo, "run", "--base", "main", "--head", "feature", env=env)
    assert run.returncode == 0, run.stderr
    candidate = gate(repo, "candidate", "--base", "main", "--head", "feature").stdout.strip()
    note = git(repo, "notes", "--ref=gate", "show", candidate)
    for field in ("time:", "actor:", "host:", "revision:", "command:", "scope:", "versions:"):
        assert f"\n{field} " in "\n" + note, field
    assert "result: pass" in note
    assert "scope: fixture-set: always-pass marker-absent" in note
    assert "runtime=fixture" in note and "model=example/model-v1" in note
    assert f"candidate={candidate}" in note
    remote = subprocess.run(
        ["git", "ls-remote", "--exit-code", "origin", "refs/notes/gate"], cwd=repo, capture_output=True, env=child_env()
    )
    assert remote.returncode == 0
    check = gate(repo, "check", "--base", "main", "--head", "feature")
    assert check.returncode == 0, check.stdout + check.stderr


def test_failing_check_records_fail_and_check_refuses(repo):
    (repo / "FAIL_MARKER").write_text("x\n", encoding="utf-8")
    git(repo, "add", ".")
    git(repo, "commit", "-q", "-m", "break")
    run = gate(repo, "run", "--base", "main", "--head", "feature")
    assert run.returncode == 1
    assert gate(repo, "check", "--base", "main", "--head", "feature").returncode == 1


def test_latest_entry_for_the_candidate_decides(repo, module):
    candidate = gate(repo, "candidate", "--base", "main", "--head", "feature").stdout.strip()
    base, head = git(repo, "rev-parse", "main"), git(repo, "rev-parse", "feature")
    scope = module.scope_line(CONFIG)

    def entry(result):
        return module.format_entry(
            {
                "result": result,
                "time": "2026-10-21T00:00:00Z",
                "actor": "runtime=not-stated",
                "host": "fixture",
                "revision": f"candidate={candidate} base={base} head={head}",
                "command": "fixture",
                "scope": scope,
                "versions": "git fixture",
            }
        )

    git(repo, "notes", "--ref=gate", "add", "-m", entry("pass"), candidate)
    git(repo, "notes", "--ref=gate", "append", "-m", entry("fail"), candidate)
    assert gate(repo, "check", "--no-fetch", "--base", "main", "--head", "feature").returncode == 1
    git(repo, "notes", "--ref=gate", "append", "-m", entry("pass"), candidate)
    assert gate(repo, "check", "--no-fetch", "--base", "main", "--head", "feature").returncode == 0


def test_record_for_another_scope_does_not_pass(repo, module):
    candidate = gate(repo, "candidate", "--base", "main", "--head", "feature").stdout.strip()
    base, head = git(repo, "rev-parse", "main"), git(repo, "rev-parse", "feature")
    text = module.format_entry(
        {
            "result": "pass",
            "time": "2026-10-21T00:00:00Z",
            "actor": "runtime=not-stated",
            "host": "fixture",
            "revision": f"candidate={candidate} base={base} head={head}",
            "command": "fixture",
            "scope": "older-set: always-pass",
            "versions": "git fixture",
        }
    )
    git(repo, "notes", "--ref=gate", "add", "-m", text, candidate)
    result = gate(repo, "check", "--no-fetch", "--base", "main", "--head", "feature")
    assert result.returncode == 1
    assert "scope" in result.stdout


def test_record_on_a_moved_base_is_missing(repo):
    assert gate(repo, "run", "--base", "main", "--head", "feature").returncode == 0
    git(repo, "switch", "-q", "main")
    (repo / "c.txt").write_text("c\n", encoding="utf-8")
    git(repo, "add", ".")
    git(repo, "commit", "-q", "-m", "main moved")
    git(repo, "push", "-q", "origin", "main")
    assert gate(repo, "check", "--base", "main", "--head", "feature").returncode == 2


def test_conflicting_merge_has_no_candidate(repo):
    (repo / "a.txt").write_text("feature side\n", encoding="utf-8")
    git(repo, "commit", "-q", "-am", "feature edits a")
    git(repo, "switch", "-q", "main")
    (repo / "a.txt").write_text("main side\n", encoding="utf-8")
    git(repo, "commit", "-q", "-am", "main edits a")
    result = gate(repo, "candidate", "--base", "main", "--head", "feature")
    assert result.returncode == 3
    assert "conflict" in result.stderr


def test_actor_model_reuses_attribution_vocabulary(module):
    assert "model=example/model-v1" in module.actor_line("fixture", "example/model-v1", "not-stated")
    with pytest.raises(ValueError):
        module.actor_line("fixture", "bare-model-name", "not-stated")
    assert "model=not-stated" in module.actor_line("human", "", "")


def test_unconfigured_base_reports_gate_off(repo):
    git(repo, "switch", "-q", "main")
    git(repo, "rm", "-q", ".merge-gate.json")
    git(repo, "commit", "-q", "-m", "drop config")
    result = gate(repo, "enabled", "--base", "main")
    assert result.returncode == 1
    git(repo, "switch", "-q", "feature")
    assert gate(repo, "enabled", "--base", "feature").returncode == 0


def set_base_config(repo, text):
    git(repo, "switch", "-q", "main")
    (repo / ".merge-gate.json").write_text(text, encoding="utf-8")
    git(repo, "commit", "-q", "-am", "config")
    git(repo, "switch", "-q", "feature")


@pytest.mark.parametrize("text", ["[]", '"on"', '{"gate": true}', '{"gate": "On"}', "{not json"])
def test_unrecognised_declaration_fails_closed(repo, text):
    set_base_config(repo, text)
    assert gate(repo, "enabled", "--base", "main").returncode == 3
    assert gate(repo, "check", "--no-fetch", "--base", "main", "--head", "feature").returncode == 3


def test_explicit_off_is_off(repo):
    set_base_config(repo, '{"gate": "off"}')
    assert gate(repo, "enabled", "--base", "main").returncode == 1


def test_missing_scope_is_named(repo):
    set_base_config(repo, json.dumps({"gate": "on", "checks": CONFIG["checks"]}))
    result = gate(repo, "run", "--no-push", "--base", "main", "--head", "feature")
    assert result.returncode == 3
    assert '"scope"' in result.stderr


@pytest.mark.parametrize("value", ["fixture\nresult: pass", "fixture\rmerge-gate-record: v1"])
def test_line_break_in_a_field_cannot_forge_an_entry(repo, value):
    env = {**child_env(), "MERGE_GATE_RUNTIME": value}
    result = gate(repo, "run", "--no-push", "--base", "main", "--head", "feature", env=env)
    assert result.returncode == 3
    candidate = gate(repo, "candidate", "--base", "main", "--head", "feature").stdout.strip()
    shown = subprocess.run(
        ["git", "notes", "--ref=gate", "show", candidate], cwd=repo, capture_output=True, env=child_env()
    )
    assert shown.returncode != 0


def test_missing_check_program_records_fail(repo):
    config = {**CONFIG, "checks": [{"name": "absent", "argv": ["no-such-program-1156"]}]}
    set_base_config(repo, json.dumps(config))
    result = gate(repo, "run", "--no-push", "--base", "main", "--head", "feature")
    assert result.returncode == 1, result.stderr
    assert "absent fail(cannot run" in result.stdout


@pytest.mark.parametrize("sep", ["\x0b", "\x0c", "\x1c", "\x1e", "\x85", " ", " "])
def test_unicode_line_boundaries_cannot_forge_an_entry(repo, module, sep):
    for var in ("MERGE_GATE_RUNTIME", "MERGE_GATE_MODEL"):
        env = {**child_env(), var: f"fixture{sep}merge-gate-record: v1{sep}result: pass"}
        result = gate(repo, "run", "--no-push", "--base", "main", "--head", "feature", env=env)
        assert result.returncode == 3, (var, result.stderr)
    with pytest.raises(ValueError):
        module.format_entry({f: "x" for f in module.FIELDS} | {"actor": f"a{sep}result: pass"})
    fields = {f: "x" for f in module.FIELDS} | {"result": "fail", "revision": "candidate=C base=B head=H"}
    genuine = module.format_entry(fields)
    forged = genuine.replace("actor: x", f"actor: x{sep}{module.HEADER}{sep}result: pass{sep}revision: candidate=C ")
    entries = module.parse_note(forged)
    assert len(entries) == 1 and entries[0]["result"] == "fail"


def test_bad_versions_declaration_fails_before_any_check(repo):
    set_base_config(repo, json.dumps({**CONFIG, "versions": [{"name": "git"}]}))
    assert gate(repo, "enabled", "--base", "main").returncode == 3


@pytest.mark.parametrize("sep", ["\x85", " ", " ", "\x0b", "\t", "\x1b"])
def test_separator_at_the_end_of_a_value_is_refused(repo, module, sep):
    with pytest.raises(ValueError):
        module.format_entry({f: "x" for f in module.FIELDS} | {"actor": f"runtime=x{sep}"})
    env = {**child_env(), "MERGE_GATE_EFFORT": f"standard{sep}"}
    assert gate(repo, "run", "--no-push", "--base", "main", "--head", "feature", env=env).returncode == 3


def test_no_push_record_is_never_published(repo):
    head = git(repo, "rev-parse", "feature")
    git(repo, "notes", "--ref=gate", "add", "-m", "hand-made note", head)
    assert gate(repo, "run", "--no-push", "--base", "main", "--head", "feature").returncode == 0
    assert gate(repo, "check", "--no-fetch", "--base", "main", "--head", "feature").returncode == 2
    assert gate(repo, "check", "--no-fetch", "--local", "--base", "main", "--head", "feature").returncode == 0
    assert gate(repo, "run", "--base", "main", "--head", "feature").returncode == 0
    git(repo, "fetch", "-q", "origin", "refs/notes/gate:refs/notes/probe")
    listed = git(repo, "notes", "--ref=refs/notes/probe", "list").splitlines()
    assert len(listed) == 1, listed
    candidate = gate(repo, "candidate", "--base", "main", "--head", "feature").stdout.strip()
    published = git(repo, "notes", "--ref=refs/notes/probe", "show", candidate)
    assert published.count("merge-gate-record: v1") == 1


@pytest.mark.parametrize(
    "check",
    [
        {"name": "trailing ", "argv": ["true"]},
        {"name": "ctl\x1b", "argv": ["true"]},
        {"name": "tab-argv", "argv": ["sh", "-c", "true\t"]},
        {"name": "esc-argv", "argv": ["echo", "\x1b[1m"]},
    ],
)
def test_bad_check_declaration_fails_before_any_check_runs(repo, tmp_path, check):
    marker = tmp_path / "ran"
    config = {**CONFIG, "checks": [{"name": "first", "argv": ["touch", str(marker)]}, check]}
    set_base_config(repo, json.dumps(config))
    assert gate(repo, "enabled", "--base", "main").returncode == 3
    assert gate(repo, "run", "--no-push", "--base", "main", "--head", "feature").returncode == 3
    assert not marker.exists()


def test_tool_version_output_is_sanitized(repo):
    config = {**CONFIG, "versions": [{"name": "tool", "argv": ["printf", "\\033[1mv1\\0132\\n"]}]}
    set_base_config(repo, json.dumps(config))
    result = gate(repo, "run", "--no-push", "--base", "main", "--head", "feature")
    assert result.returncode == 0, result.stderr
    line = next(ln for ln in result.stdout.splitlines() if ln.startswith("versions: "))
    assert "\x1b" not in line and "v1 2" in line


# ── gating tiers (ticket 1221) ────────────────────────────────────────────────

TIERED = {
    **CONFIG,
    "checks": [*CONFIG["checks"], {"name": "full-only", "argv": ["false"]}],
    "tiers": {"bookkeeping": ["always-pass"]},
}


def branch_touching(repo, *paths, name="books"):
    """A branch off main changing only `paths`."""
    git(repo, "switch", "-q", "-c", name, "main")
    for path in paths:
        (repo / path).parent.mkdir(parents=True, exist_ok=True)
        (repo / path).write_text(f"{path}\n", encoding="utf-8")
    git(repo, "add", ".")
    git(repo, "commit", "-q", "-m", name)
    return name


@pytest.mark.parametrize(
    "path,expected",
    [
        ("tickets/1221-x.erg", True),
        ("tickets/closed/1221-x.erg", True),
        ("STATE.md", True),
        ("memory/journal/2026-10-26.md", True),
        ("tickets/erg", False),
        ("tickets/AGENTS.md", False),
        ("tickets/closed/sub/1-x.erg", False),
        ("docs/STATE.md", False),
        ("scripts/merge-gate.py", False),
    ],
)
def test_bookkeeping_paths(module, path, expected):
    assert module.is_bookkeeping(path) is expected


def test_bookkeeping_diff_records_its_tier_checks_only(repo):
    set_base_config(repo, json.dumps(TIERED))
    branch = branch_touching(repo, "tickets/0001-x.erg", "STATE.md", "memory/note.md")
    result = gate(repo, "run", "--no-push", "--base", "main", "--head", branch)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "scope: fixture-set/bookkeeping: always-pass" in result.stdout
    assert "full-only" not in result.stdout
    check = gate(repo, "check", "--no-fetch", "--local", "--base", "main", "--head", branch)
    assert check.returncode == 0, check.stdout


def test_code_diff_runs_the_full_set(repo):
    set_base_config(repo, json.dumps(TIERED))
    branch = branch_touching(repo, "tickets/0001-x.erg", "scripts/x.py")
    result = gate(repo, "run", "--no-push", "--base", "main", "--head", branch)
    assert result.returncode == 1
    assert "full-only fail" in result.stdout


def test_without_declared_tier_checks_a_bookkeeping_diff_runs_the_full_set(repo):
    set_base_config(repo, json.dumps({**TIERED, "tiers": {}}))
    branch = branch_touching(repo, "STATE.md")
    result = gate(repo, "run", "--no-push", "--base", "main", "--head", branch)
    assert result.returncode == 1
    assert "full-only fail" in result.stdout


def _forge(repo, module, branch, scope):
    candidate = gate(repo, "candidate", "--base", "main", "--head", branch).stdout.strip()
    base, head = git(repo, "rev-parse", "main"), git(repo, "rev-parse", branch)
    text = module.format_entry(
        {
            "result": "pass",
            "time": "2026-10-26T00:00:00Z",
            "actor": "runtime=not-stated",
            "host": "fixture",
            "revision": f"candidate={candidate} base={base} head={head}",
            "command": "fixture",
            "scope": scope,
            "versions": "git fixture",
        }
    )
    git(repo, "notes", "--ref=gate", "add", "-f", "-m", text, candidate)


def test_a_bookkeeping_record_does_not_pass_a_code_diff(repo, module):
    set_base_config(repo, json.dumps(TIERED))
    branch = branch_touching(repo, "scripts/x.py")
    _forge(repo, module, branch, "fixture-set/bookkeeping: always-pass")
    assert gate(repo, "check", "--no-fetch", "--base", "main", "--head", branch).returncode == 1


def test_a_full_record_passes_a_bookkeeping_diff(repo, module):
    set_base_config(repo, json.dumps(TIERED))
    branch = branch_touching(repo, "STATE.md")
    _forge(repo, module, branch, module.scope_line(TIERED))
    assert gate(repo, "check", "--no-fetch", "--base", "main", "--head", branch).returncode == 0


@pytest.mark.parametrize("tiers", [{"bookkeeping": ["no-such-check"]}, {"bookkeeping": "always-pass"},
                                   {"other": ["always-pass"]}, []])
def test_bad_tier_declaration_fails_closed(repo, tiers):
    set_base_config(repo, json.dumps({**TIERED, "tiers": tiers}))
    assert gate(repo, "enabled", "--base", "main").returncode == 3


def test_tier_of_the_whole_diff(repo):
    books = branch_touching(repo, "tickets/0001-x.erg")
    assert gate(repo, "tier", "--base", "main", "--head", books).stdout.startswith("bookkeeping")
    assert gate(repo, "tier", "--base", "main", "--head", books).returncode == 0
    code = gate(repo, "tier", "--base", "main", "--head", "feature")
    assert code.returncode == 1 and code.stdout.startswith("full")


def test_tier_since_an_approved_tip_judges_only_the_follow_up(repo):
    approved = git(repo, "rev-parse", "feature")
    (repo / "STATE.md").write_text("follow-up\n", encoding="utf-8")
    git(repo, "add", ".")
    git(repo, "commit", "-q", "-m", "state follow-up")
    since = gate(repo, "tier", "--base", "main", "--head", "feature", "--since", approved)
    assert since.returncode == 0, since.stdout + since.stderr
    (repo / "c.txt").write_text("code\n", encoding="utf-8")
    git(repo, "add", ".")
    git(repo, "commit", "-q", "-m", "code follow-up")
    assert gate(repo, "tier", "--base", "main", "--head", "feature", "--since", approved).returncode == 1


def test_a_clean_rebase_after_approval_is_bookkeeping(repo):
    approved = git(repo, "rev-parse", "feature")
    git(repo, "switch", "-q", "main")
    (repo / "z.txt").write_text("main moved\n", encoding="utf-8")
    git(repo, "add", ".")
    git(repo, "commit", "-q", "-m", "main moves")
    git(repo, "switch", "-q", "feature")
    git(repo, "rebase", "-q", "main")
    assert git(repo, "rev-parse", "feature") != approved
    result = gate(repo, "tier", "--base", "main", "--head", "feature", "--since", approved)
    assert result.returncode == 0, result.stdout + result.stderr
