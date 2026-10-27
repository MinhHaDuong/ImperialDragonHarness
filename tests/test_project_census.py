"""The project channel: what a consumer project adds to every session (0971).

``resident_census.py`` measured the harness and stopped at its edge, so a
project's own resident text grew unwatched: climate-finance-het carried about
28 000 chars of project rules on 2026-09-24, most of it one body scoped
``paths: "**/*"`` — a catch-all, which the runtime loads on every session just
as if it declared no ``paths:`` at all.

The harness cannot gate a project's CI, so the budget is surfaced, not
enforced: the SessionStart hook prints one declarative line when a
project is over budget or declares a catch-all. These tests pin the counting
and that line, each with a positive control.
"""

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from child_env import child_env

pytestmark = pytest.mark.adherence

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import resident_census as rc  # noqa: E402

HOOK = REPO / "scripts" / "on-start-context.sh"


def _rule(path: Path, paths: list[str] | None, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    front = ""
    if paths is not None:
        items = "".join(f'  - "{p}"\n' for p in paths)
        front = f"---\npaths:\n{items}---\n"
    path.write_text(front + body, encoding="utf-8")


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """A project with every kind of source, and one of each rule scoping."""
    (tmp_path / "AGENTS.md").write_text("agents\n@CONV.md\n", encoding="utf-8")
    (tmp_path / "CONV.md").write_text("c" * 100, encoding="utf-8")
    rules = tmp_path / ".claude" / "rules"
    _rule(rules / "resident.md", None, "r" * 200)
    _rule(rules / "catchall.md", ["**/*"], "k" * 300)
    _rule(rules / "scoped.md", ["scripts/**"], "s" * 400)
    return tmp_path


def _paths(entries: list[rc.Entry]) -> set[str]:
    return {e.path for e in entries}


def test_counts_agents_md_its_imports_and_resident_rules(project):
    entries = rc.project_entries(project)
    assert _paths(entries) == {
        "AGENTS.md",
        "CONV.md",
        ".claude/rules/resident.md",
        ".claude/rules/catchall.md",
    }
    assert all(e.channel == "project" for e in entries)


def test_a_catch_all_glob_is_resident(tmp_path):
    for glob in ("**/*", "**", "*", "**/*.*"):
        rule = tmp_path / f"{len(glob)}.md"
        _rule(rule, [glob], "x")
        assert rc.is_auto_loaded(rule), glob
    _rule(tmp_path / "narrow.md", ["**/*.py"], "x")
    assert not rc.is_auto_loaded(tmp_path / "narrow.md")


def test_catch_all_rules_are_named(project):
    assert rc.catch_all_rules(project) == [".claude/rules/catchall.md"]


def test_warning_names_the_catch_all_even_under_budget(project):
    line = rc.project_warning(project, budget=10_000)
    assert line and "catchall.md" in line and "catch-all" in line


def test_warning_fires_over_budget(tmp_path):
    (tmp_path / "AGENTS.md").write_text("a" * 500, encoding="utf-8")
    line = rc.project_warning(tmp_path, budget=100)
    assert line and "500" in line and "AGENTS.md" in line


def test_no_warning_when_small_and_scoped(tmp_path):
    (tmp_path / "AGENTS.md").write_text("small", encoding="utf-8")
    _rule(tmp_path / ".claude" / "rules" / "s.md", ["scripts/**"], "x" * 50_000)
    assert rc.project_warning(tmp_path, budget=1000) is None


def _run_hook(project: Path, hook: Path = HOOK, home: Path | None = None) -> str:
    return subprocess.run(
        ["bash", str(hook)],
        capture_output=True, text=True, timeout=60, check=True,
        # The fixture is not a git repository: stop git from walking up into the
        # repository that holds the temp folder (hunt sets TMPDIR inside a worktree).
        env={**child_env(), "CLAUDE_PROJECT_DIR": str(project),
             "HOME": str(home or project.parent), "BASH_ENV": "",
             "GIT_CEILING_DIRECTORIES": str(project.parent)},
    ).stdout


def test_startup_prompt_carries_the_warning(project):
    """Positive control on the delivery channel, not just the function."""
    assert "catchall.md" in _run_hook(project)


def test_startup_prompt_is_silent_on_budget_for_a_small_project(tmp_path):
    (tmp_path / "AGENTS.md").write_text("small", encoding="utf-8")
    assert "budget" not in _run_hook(tmp_path).lower()


def test_session_start_emits_no_coherence_prompt(tmp_path):
    project = tmp_path / "project"
    skill = project / ".claude/skills/x/SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("# X\n", encoding="utf-8")
    (project / "AGENTS.md").write_text("local\n", encoding="utf-8")
    assert "PROJECT DIRECTIVE COHERENCE" not in _run_hook(project)
    assert not list((REPO / "scripts").glob("prompt-project-*"))


def test_over_budget_project_line_comes_from_the_start_hook(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "AGENTS.md").write_text("a" * (rc.PROJECT_BUDGET + 1), encoding="utf-8")
    assert "PROJECT RESIDENT TEXT" in _run_hook(project)


@pytest.mark.integration
def test_harness_linked_worktree_gets_no_census_line(tmp_path):
    """Fail-closed guard: a catch-all rule in the harness stays unreported."""
    harness = tmp_path / "harness"
    scripts = harness / "scripts"
    scripts.mkdir(parents=True)
    for name in ("on-start-context.sh", "resident_census.py", "skill_frontmatter.py"):
        shutil.copy2(REPO / "scripts" / name, scripts)
    _rule(harness / ".claude/rules/catchall.md", ["**/*"], "k" * 300)
    git = lambda *a: subprocess.run(["git", "-C", str(harness), *a], check=True,  # noqa: E731
                                    capture_output=True, env=child_env())
    git("init", "-b", "main")
    git("config", "user.email", "t@example.com")
    git("config", "user.name", "T")
    git("add", ".")
    git("commit", "-m", "fixture")
    linked = tmp_path / "linked"
    git("worktree", "add", "-b", "linked", str(linked))
    # Positive control: the same hook copy does warn for a foreign project.
    foreign = tmp_path / "foreign"
    _rule(foreign / ".claude/rules/catchall.md", ["**/*"], "k" * 300)
    assert "catchall.md" in _run_hook(foreign, scripts / "on-start-context.sh")
    for proj in (linked, harness):
        assert "PROJECT RESIDENT TEXT" not in _run_hook(proj, scripts / "on-start-context.sh")


@pytest.mark.integration
def test_unreadable_harness_git_keeps_census_silent(tmp_path):
    """A foreign git project, but no git-common-dir for the harness: not provably foreign, so silent."""
    scripts = tmp_path / "harness" / "scripts"
    scripts.mkdir(parents=True)
    for name in ("on-start-context.sh", "resident_census.py", "skill_frontmatter.py"):
        shutil.copy2(REPO / "scripts" / name, scripts)
    foreign = tmp_path / "foreign"
    _rule(foreign / ".claude/rules/catchall.md", ["**/*"], "k" * 300)
    subprocess.run(["git", "init", "-b", "main", str(foreign)], check=True,
                   capture_output=True, env=child_env())
    out = _run_hook(foreign, scripts / "on-start-context.sh")
    assert "PROJECT RESIDENT TEXT" not in out


def test_worktree_instruction_carries_the_prose_exception(tmp_path):
    """0968: the startup line must state the harness rule by kind of work.

    It said "every conversation works in its own worktree", contradicting
    the prose-workpackages rule, so a paper repo that edits prose in the
    author's checkout opened every session on an instruction its own
    AGENTS.md overruled. No per-repo pass: the rule is by kind of work.
    """
    project = tmp_path / "project"
    project.mkdir()
    output = _run_hook(project)
    assert "Worktree isolation is enabled" in output
    assert "every conversation works in its own worktree" not in output
    assert "manuscript prose" in output and "in place" in output
    assert "rules/prose/workpackages.md" in output
