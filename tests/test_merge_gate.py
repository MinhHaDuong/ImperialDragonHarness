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


# ── before set (ticket 1245) and tier (ticket 1221) ─────────────────────────────

BEFORE = {
    **CONFIG,
    "checks": [*CONFIG["checks"], {"name": "full-only", "argv": ["false"]}],
    "before": ["always-pass"],
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


def test_run_records_only_the_before_set(repo):
    """Ticket 1245: the record before the merge runs the declared before set, whatever the diff."""
    set_base_config(repo, json.dumps(BEFORE))
    branch = branch_touching(repo, "scripts/x.py")
    result = gate(repo, "run", "--no-push", "--base", "main", "--head", branch)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "scope: fixture-set/before-merge: always-pass" in result.stdout
    assert "full-only" not in result.stdout
    check = gate(repo, "check", "--no-fetch", "--local", "--base", "main", "--head", branch)
    assert check.returncode == 0, check.stdout


def test_without_a_before_set_run_records_the_full_set(repo):
    config = {k: v for k, v in BEFORE.items() if k != "before"}
    set_base_config(repo, json.dumps(config))
    branch = branch_touching(repo, "STATE.md")
    result = gate(repo, "run", "--no-push", "--base", "main", "--head", branch)
    assert result.returncode == 1
    assert "scope: fixture-set: always-pass marker-absent full-only" in result.stdout
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


def test_a_record_of_another_scope_does_not_pass(repo, module):
    set_base_config(repo, json.dumps(BEFORE))
    branch = branch_touching(repo, "scripts/x.py")
    _forge(repo, module, branch, "fixture-set/bookkeeping: always-pass")
    assert gate(repo, "check", "--no-fetch", "--base", "main", "--head", branch).returncode == 1
    _forge(repo, module, branch, "fixture-set/before-merge: always-pass")
    assert gate(repo, "check", "--no-fetch", "--base", "main", "--head", branch).returncode == 0


@pytest.mark.parametrize("before", [["no-such-check"], [], "always-pass", [1], None])
def test_bad_before_declaration_fails_closed(repo, before):
    set_base_config(repo, json.dumps({**BEFORE, "before": before}))
    assert gate(repo, "enabled", "--base", "main").returncode == 3


def test_a_legacy_tiers_key_has_no_effect(repo):
    """Bases older than ticket 1245 carry "tiers": read without error, never applied."""
    set_base_config(repo, json.dumps({**BEFORE, "tiers": {"bookkeeping": ["full-only"]}}))
    branch = branch_touching(repo, "STATE.md")
    result = gate(repo, "run", "--no-push", "--base", "main", "--head", branch)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "scope: fixture-set/before-merge: always-pass" in result.stdout


def test_the_harness_declares_a_cheap_before_set():
    """Ticket 1245: lint before the merge, the test suite only after it."""
    config = json.loads((ROOT / ".merge-gate.json").read_text(encoding="utf-8"))
    checks = {c["name"]: c["argv"] for c in config["checks"]}
    assert checks.get("lint") == ["make", "lint"]
    assert "lint" in config["before"] and "pytest-guard" not in config["before"]
    assert "pytest-guard" in checks
    assert set(config["before"]) <= set(checks)
    assert "tiers" not in config and "rerun" not in config


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


# ── cwd and config independence (ticket 1221, gaze round 1) ───────────────────


def test_tier_ignores_cwd_and_diff_relative(repo):
    """A code-only head read from a subdirectory with diff.relative=true once
    reported "bookkeeping: 0 path(s) changed"; the read is from the toplevel."""
    (repo / "memory").mkdir()
    (repo / "memory" / "keep.md").write_text("k\n", encoding="utf-8")
    git(repo, "add", ".")
    git(repo, "commit", "-q", "-m", "memory dir on feature")
    git(repo, "config", "diff.relative", "true")
    result = gate(repo / "memory", "tier", "--base", "main", "--head", "feature")
    assert result.returncode == 1, result.stdout + result.stderr
    assert "b.txt" in result.stdout


def test_tier_sees_submodule_changes_despite_ignore_config(repo, tmp_path):
    sub = tmp_path / "sub"
    subprocess.run(["git", "init", "-q", "-b", "main", str(sub)], check=True, env=child_env())
    for key, value in (("user.email", "t@example.com"), ("user.name", "Fixture"), ("commit.gpgsign", "false")):
        git(sub, "config", key, value)
    git(sub, "commit", "-q", "--allow-empty", "-m", "s")
    git(repo, "switch", "-q", "-c", "withsub", "main")
    oid = git(sub, "rev-parse", "HEAD")
    git(repo, "update-index", "--add", "--cacheinfo", f"160000,{oid},vendor")
    git(repo, "commit", "-q", "-m", "submodule")
    git(repo, "config", "diff.ignoreSubmodules", "all")
    result = gate(repo, "tier", "--base", "main", "--head", "withsub")
    assert result.returncode == 1 and "vendor" in result.stdout, result.stdout


def test_an_empty_diff_is_never_bookkeeping(repo):
    result = gate(repo, "tier", "--base", "main", "--head", "main")
    assert result.returncode == 1, result.stdout
    assert result.stdout.startswith("full")


def test_since_the_same_tip_reads_unchanged(repo):
    tip = git(repo, "rev-parse", "feature")
    result = gate(repo, "tier", "--base", "main", "--head", "feature", "--since", tip)
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.startswith("unchanged")


def test_enabled_and_config_do_not_depend_on_cwd(repo):
    (repo / "memory").mkdir()
    assert gate(repo / "memory", "enabled", "--base", "main").returncode == 0
    assert gate(repo, "enabled", "--base", "main").returncode == 0


# ── modes, not only paths (ticket 1221, gaze round 2) ─────────────────────────


def _branch_with_entry(repo, name, mode, path, oid=None):
    git(repo, "switch", "-q", "-c", name, "main")
    if oid is None:
        oid = subprocess.run(
            ["git", "-C", str(repo), "hash-object", "-w", "--stdin"],
            input="target\n", capture_output=True, text=True, check=True, env=child_env(),
        ).stdout.strip()
    git(repo, "update-index", "--add", "--cacheinfo", f"{mode},{oid},{path}")
    git(repo, "commit", "-q", "-m", name)
    git(repo, "reset", "-q", "--hard")
    return name


@pytest.mark.parametrize("path", ["STATE.md", "memory/tool.py"])
def test_a_symlink_on_a_bookkeeping_path_is_full(repo, path):
    branch = _branch_with_entry(repo, "link", "120000", path)
    result = gate(repo, "tier", "--base", "main", "--head", branch)
    assert result.returncode == 1, result.stdout


def test_a_gitlink_under_memory_is_full(repo):
    oid = git(repo, "rev-parse", "main")
    branch = _branch_with_entry(repo, "sub", "160000", "memory/sub", oid=oid)
    result = gate(repo, "tier", "--base", "main", "--head", branch)
    assert result.returncode == 1, result.stdout


def test_an_executable_file_and_a_deletion_stay_bookkeeping(repo):
    branch = _branch_with_entry(repo, "exe", "100755", "memory/run.md")
    assert gate(repo, "tier", "--base", "main", "--head", branch).returncode == 0
    git(repo, "rm", "-q", "memory/run.md")
    git(repo, "commit", "-q", "-m", "drop")
    approved = git(repo, "rev-parse", "HEAD~1")
    since = gate(repo, "tier", "--base", "main", "--head", branch, "--since", approved)
    assert since.returncode == 0 and since.stdout.startswith("bookkeeping"), since.stdout


def test_tier_since_ignores_added_seat_reports_and_ticket_close(repo):
    """Ticket 1236: recording seat reports after a review must not void it."""
    approved = git(repo, "rev-parse", "feature")
    (repo / "tickets/reviews/main..abc").mkdir(parents=True)
    (repo / "tickets/reviews/main..abc/correctness-1.md").write_text("report\n", encoding="utf-8")
    (repo / "tickets").mkdir(exist_ok=True)
    (repo / "tickets/0001-x.erg").write_text("closed\n", encoding="utf-8")
    git(repo, "add", ".")
    git(repo, "commit", "-q", "-m", "reviews: record")
    assert gate(repo, "tier", "--base", "main", "--head", "feature", "--since", approved).returncode == 0


def test_tier_since_rejects_edited_or_executable_seat_reports(repo):
    d = repo / "tickets/reviews/main..abc"
    d.mkdir(parents=True)
    (d / "correctness-1.md").write_text("report\n", encoding="utf-8")
    git(repo, "add", ".")
    git(repo, "commit", "-q", "-m", "reviews: record")
    recorded = git(repo, "rev-parse", "feature")
    (d / "correctness-1.md").write_text("edited\n", encoding="utf-8")
    git(repo, "commit", "-qam", "edit report")
    assert gate(repo, "tier", "--base", "main", "--head", "feature", "--since", recorded).returncode == 1
    after_edit = git(repo, "rev-parse", "feature")
    (d / "hook-1.md").write_text("#!/bin/sh\n", encoding="utf-8")
    (d / "hook-1.md").chmod(0o755)
    git(repo, "add", ".")
    git(repo, "commit", "-q", "-m", "executable report")
    assert gate(repo, "tier", "--base", "main", "--head", "feature", "--since", after_edit).returncode == 1


# ── append_and_push: the record must reach the remote (ticket 1366) ─────────────


def remote_tip(repo):
    out = git(repo, "ls-remote", "origin", "refs/notes/gate")
    return out.split()[0] if out else ""


def on_remote(repo, candidate):
    """The remote's notes ref, fetched into a probe ref, carries a note for `candidate`."""
    git(repo, "fetch", "-q", "origin", "+refs/notes/gate:refs/notes/probe")
    shown = subprocess.run(
        ["git", "-C", str(repo), "notes", "--ref=refs/notes/probe", "show", candidate],
        capture_output=True, text=True, env=child_env(),
    )  # fmt: skip
    return shown.stdout


@pytest.fixture
def seeded(repo, module, monkeypatch):
    """A repo whose remote already holds one gate note, with the module's cwd on it."""
    monkeypatch.chdir(repo)
    head = git(repo, "rev-parse", "HEAD")
    module.append_and_push(head, "first\nresult: pass", "origin")
    return repo, head


def test_a_forced_fetch_between_append_and_push_does_not_lose_the_record(seeded, module, monkeypatch):
    repo, head = seeded
    old = remote_tip(repo)
    real = module.git

    def racing(*args, **kw):
        if args[:2] == ("push", "-q"):  # another process force-fetches the shared ref just before the push
            real("fetch", "-q", "origin", "+refs/notes/gate:refs/notes/gate")
        return real(*args, **kw)

    monkeypatch.setattr(module, "git", racing)
    module.append_and_push(head, "second\nresult: fail", "origin")
    assert remote_tip(repo) != old
    assert "second" in on_remote(repo, head)


def test_a_push_that_exits_0_without_the_record_warns_and_retries(seeded, module, monkeypatch, caplog):
    repo, head = seeded
    real = module.git
    swallowed = []

    def lossy(*args, **kw):
        if args[:2] == ("push", "-q") and not swallowed:  # exit 0, nothing sent
            swallowed.append(args)
            return subprocess.CompletedProcess(args, 0, "", "")
        return real(*args, **kw)

    monkeypatch.setattr(module, "git", lossy)
    monkeypatch.setattr(module, "READBACK_WAIT", 0)
    with caplog.at_level("WARNING"):
        module.append_and_push(head, "second\nresult: fail", "origin")
    assert "remote lacks the record" in caplog.text
    assert "second" in on_remote(repo, head)


def test_a_failing_readback_warns_without_raising(seeded, module, monkeypatch, caplog):
    repo, head = seeded
    old = remote_tip(repo)
    real = module.git

    def blind(*args, **kw):
        if args[:1] == ("ls-remote",) and "--exit-code" not in args:  # the read-back, not fetch_notes' probe
            return subprocess.CompletedProcess(args, 128, "", "forge down")
        return real(*args, **kw)

    monkeypatch.setattr(module, "git", blind)
    with caplog.at_level("WARNING"):
        module.append_and_push(head, "second\nresult: fail", "origin")
    assert "cannot verify" in caplog.text
    assert remote_tip(repo) != old


def test_a_record_that_never_arrives_raises(seeded, module, monkeypatch):
    repo, head = seeded
    real = module.git

    def black_hole(*args, **kw):
        if args[:2] == ("push", "-q"):
            return subprocess.CompletedProcess(args, 0, "", "")
        return real(*args, **kw)

    monkeypatch.setattr(module, "git", black_hole)
    monkeypatch.setattr(module, "READBACK_WAIT", 0)
    with pytest.raises(module.GateError, match="remote lacks the record"):
        module.append_and_push(head, "second\nresult: fail", "origin")
