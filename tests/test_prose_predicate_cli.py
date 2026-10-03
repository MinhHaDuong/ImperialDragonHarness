"""The prose_predicate CLI is the interface the skills name — test it (ticket 0550).

The library predicates (`is_manuscript`, `diff_is_prose`) are covered by
`test_gaze_prose_routing.py`; this module covers the entry point the skill
text tells agents to run, including the loud-failure contract: a path that
does not exist from the cwd is a routing error (exit 2, no verdict), never a
silent `code` — the parked-cwd failure mode returned a plausible wrong answer
twice in the very session that landed this fix.

Marked integration (spawns a subprocess), per the test-tier table.
"""

import subprocess
import sys
from pathlib import Path

import pytest

from child_env import child_env

pytestmark = pytest.mark.integration

REPO = Path(__file__).resolve().parent.parent
CLI = REPO / "scripts" / "prose_predicate.py"

MANIFEST = """\
[[map]]
glob = "article-*/**/*.tex"
doctype = "techreport"
lang = "en"
"""


def _run(*files: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(CLI), *files],
        capture_output=True,
        text=True,
        env=child_env(),
        cwd=cwd,
    )


def test_cli_prints_prose_then_code(tmp_path):
    repo = tmp_path / "repo"
    (repo / ".claude").mkdir(parents=True)
    (repo / ".claude" / "rules-map.toml").write_text(MANIFEST, encoding="utf-8")
    tex = repo / "article-x" / "manuscrit.tex"
    tex.parent.mkdir()
    tex.write_text("\\section{Introduction}\n", encoding="utf-8")
    note = repo / "conception" / "note.md"
    note.parent.mkdir()
    note.write_text("# Note\n", encoding="utf-8")

    mixed = _run(str(tex), str(note))
    assert mixed.returncode == 0 and mixed.stdout.strip() == "prose", mixed.stderr

    process_only = _run(str(note))
    assert process_only.returncode == 0 and process_only.stdout.strip() == "code", (
        process_only.stderr
    )


def test_cli_axes_reports_the_declared_rulebooks(tmp_path):
    """--axes hands the reviewer the doctype/lang instead of letting it infer."""
    repo = tmp_path / "repo"
    (repo / ".claude").mkdir(parents=True)
    (repo / ".claude" / "rules-map.toml").write_text(MANIFEST, encoding="utf-8")
    tex = repo / "article-x" / "manuscrit.tex"
    tex.parent.mkdir()
    tex.write_text("\\section{Introduction}\n", encoding="utf-8")
    note = repo / "conception" / "note.md"
    note.parent.mkdir()
    note.write_text("# Note\n", encoding="utf-8")

    result = _run("--axes", str(tex), str(note))
    assert result.returncode == 0, result.stderr
    lines = result.stdout.strip().splitlines()
    assert lines == [
        f"{tex} doctype=techreport lang=en",
        # An unresolved axis prints "-", never an empty field: a blank reads the
        # same as "not asked", which is the guess this flag exists to prevent.
        f"{note} doctype=- lang=-",
    ], result.stdout


def test_prose_predicate_emits_a_risk_band(tmp_path):
    """--risk emits the path-risk band from path patterns alone (ticket 0902).

    The fixture files below are NEVER created — their absence is the test:
    the anchor roster (`git diff --name-only --no-renames`) lists repo-relative
    paths, deleted and renamed among them, that do not exist at HEAD, so --risk
    must not inherit the missing-path refusal (exit 2) of the disk-reading
    prose/axes modes, or it would ESCALATE routine PRs. The paths are passed
    exactly as the roster lists them: repo-relative, with the cwd anchored to
    the repo root — an empty dir, so every fixture stays absent.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    guard = repo / "scripts" / "on-end.sh"
    assert not guard.exists(), "the fixture must be absent — that is the point"

    high = _run("--risk", "scripts/on-end.sh", cwd=repo)
    assert high.returncode == 0, (high.returncode, high.stderr)
    assert high.stdout.strip() == "high", (high.stdout, high.stderr)

    docs = _run("--risk", "docs/a.md", "docs/b.md", cwd=repo)
    assert docs.returncode == 0, (docs.returncode, docs.stderr)
    assert docs.stdout.strip() == "low", (docs.stdout, docs.stderr)

    removed = _run("--risk", "scripts/removed.sh", cwd=repo)
    assert removed.returncode == 0, (removed.returncode, removed.stderr)
    assert removed.stdout.strip() == "high", (removed.stdout, removed.stderr)

    mixed = _run("--risk", "scripts/x.sh", "docs/y.md", cwd=repo)
    assert mixed.returncode == 0, (mixed.returncode, mixed.stderr)
    assert mixed.stdout.strip() == "high", (mixed.stdout, mixed.stderr)


def test_cli_refuses_missing_path(tmp_path):
    """Wrong cwd → missing path → exit 2 and no verdict, never a silent code."""
    ghost = tmp_path / "no-such-checkout" / "manuscrit.tex"
    result = _run(str(ghost))
    assert result.returncode == 2, (result.returncode, result.stderr)
    assert "not found" in result.stderr
    assert result.stdout.strip() == "", "a refusal must not carry a verdict"
