"""touched-tests.py: a review runs the tests that name what the change touched (ticket 1283).

Raid 2026-10-27: PR #1799 moved `GhForge` out of raid_land.py; an integration
test still used the old name, and every review that day ran check-fast only.
The script selects the tests whose text names a changed file (import, path or
file name), runs them with no marker filter, and falls back to the whole
integration tier for a changed source file no test names. Real git, real
pytest, a throwaway project.
"""

import subprocess
import sys
from pathlib import Path

import pytest

from child_env import child_env

pytestmark = pytest.mark.integration

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "touched-tests.py"

PYTEST_INI = """[pytest]
markers =
    integration: spawns subprocesses
"""

USES_ALPHA = '''import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from {module} import Thing

pytestmark = pytest.mark.integration


def test_thing():
    assert Thing().ok
'''

# Unmarked and failing: selected by nothing the branch touches, outside the integration tier.
OTHER = "def test_unrelated_and_red():\n    assert False\n"


def git(cwd, *args):
    return subprocess.run(
        ["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True, env=child_env()
    ).stdout.strip()


def write(root, files):
    for name, text in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def commit(root, message):
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", message)


def project(tmp_path, files):
    root = tmp_path / "project"
    root.mkdir()
    git(root, "init", "-q", "-b", "main")
    for key, value in (("user.email", "t@example.com"), ("user.name", "Fixture"), ("commit.gpgsign", "false")):
        git(root, "config", key, value)
    write(root, files)
    commit(root, "base")
    git(root, "switch", "-q", "-c", "change")
    return root


def touched(root, *args):
    env = child_env()
    env.pop("VIRTUAL_ENV", None)
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--base", "main", *args],
        cwd=root, capture_output=True, text=True, env=env, timeout=300,
    )
    return proc.returncode, proc.stdout, proc.stderr


def line(out, key):
    return next(x for x in out.splitlines() if x.startswith(f"{key}:"))


def alpha_project(tmp_path):
    return project(tmp_path, {
        "pytest.ini": PYTEST_INI,
        "scripts/alpha.py": "class Thing:\n    ok = True\n",
        "tests/test_uses_alpha.py": USES_ALPHA.format(module="alpha"),
        "tests/test_other.py": OTHER,
    })


def test_moved_symbol_fails_the_touched_check(tmp_path):
    """The #1799 shape: a symbol moves to a new file; the integration test still importing it fails the run."""
    root = alpha_project(tmp_path)
    (root / "scripts" / "alpha.py").write_text("# Thing moved to beta.py\n", encoding="utf-8")
    write(root, {"scripts/beta.py": "class Thing:\n    ok = True\n"})
    commit(root, "move Thing to beta")

    code, out, err = touched(root)
    assert code == 1, out + err
    selected = line(out, "selected")
    assert "tests/test_uses_alpha.py" in selected
    assert "test_other.py" not in selected
    assert "scripts/beta.py" in line(out, "fallback")  # a new file no test names: the integration tier runs
    assert line(out, "result").startswith("result: fail")

    # Positive control: fix the stale import and the same run passes.
    write(root, {"tests/test_uses_alpha.py": USES_ALPHA.format(module="beta")})
    commit(root, "import Thing from beta")
    code, out, err = touched(root)
    assert code == 0, out + err
    assert "tests/test_uses_alpha.py" in line(out, "selected")
    assert line(out, "result").startswith("result: pass")


def test_a_named_change_runs_its_tests_and_no_fallback(tmp_path):
    root = alpha_project(tmp_path)
    (root / "scripts" / "alpha.py").write_text("class Thing:\n    ok = False\n", encoding="utf-8")
    commit(root, "break Thing")
    code, out, err = touched(root)
    assert code == 1, out + err
    assert line(out, "selected") == "selected: tests/test_uses_alpha.py"
    assert line(out, "fallback") == "fallback: none"


def test_a_multi_commit_branch_is_judged_from_the_merge_base(tmp_path):
    root = alpha_project(tmp_path)
    (root / "scripts" / "alpha.py").write_text("class Thing:\n    ok = False\n", encoding="utf-8")
    commit(root, "break Thing")
    write(root, {"notes.md": "unrelated\n"})
    commit(root, "a later docs-only commit")
    code, out, err = touched(root)
    assert code == 1, out + err
    assert "tests/test_uses_alpha.py" in line(out, "selected")


def test_a_docs_only_change_runs_nothing_and_claims_no_pass(tmp_path):
    root = alpha_project(tmp_path)
    write(root, {"README.md": "docs\n"})
    commit(root, "docs")
    code, out, err = touched(root)
    assert code == 4, out + err
    assert line(out, "result").startswith("result: skipped")


def test_a_project_without_a_test_layout_is_skipped_not_passed(tmp_path):
    root = project(tmp_path, {"src/tool.py": "X = 1\n"})
    write(root, {"src/tool.py": "X = 2\n"})
    commit(root, "change")
    code, out, err = touched(root)
    assert code == 4, out + err
    assert "result: skipped (no test layout)" in out
    assert "pass" not in line(out, "result")


def test_an_uncovered_source_file_without_an_integration_marker_is_not_a_pass(tmp_path):
    root = project(tmp_path, {
        "scripts/alpha.py": "class Thing:\n    ok = True\n",
        "tests/test_uses_alpha.py": USES_ALPHA.format(module="alpha").replace("pytestmark = pytest.mark.integration\n", ""),
    })
    write(root, {"scripts/alpha.py": "class Thing:\n    ok = 1\n", "scripts/gamma.py": "X = 1\n"})
    commit(root, "touch a named and an unnamed file")
    code, out, err = touched(root)
    assert code == 4, out + err
    assert "scripts/gamma.py" in line(out, "fallback")
    assert line(out, "result").startswith("result: incomplete")


def test_a_selection_that_collects_no_test_is_not_a_pass(tmp_path):
    root = alpha_project(tmp_path)
    write(root, {"tests/test_empty.py": "# no test here yet\n"})
    commit(root, "an empty test file")
    code, out, err = touched(root)
    assert code == 4, out + err
    assert line(out, "selected") == "selected: tests/test_empty.py"
    assert line(out, "result") == "result: skipped (no test collected)"


def test_a_module_in_a_comma_import_list_is_named(tmp_path):
    """gaze finding (OpenAI seat): `import os, alpha` was missed, and another test naming alpha hid the fallback."""
    root = project(tmp_path, {
        "pytest.ini": PYTEST_INI,
        "scripts/alpha.py": "OK = True\n",
        "tests/test_comma.py": (
            "import sys\nfrom pathlib import Path\n\n"
            "sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))\n"
            "import os, alpha  # noqa: E401\n\n\ndef test_ok():\n    assert alpha.OK and os.sep\n"
        ),
        "tests/test_unit.py": "def test_names_it():\n    assert 'scripts/alpha.py'\n",
    })
    write(root, {"scripts/alpha.py": "OK = False\n"})
    commit(root, "break alpha")
    code, out, err = touched(root)
    assert code == 1, out + err
    assert "tests/test_comma.py" in line(out, "selected")


def test_an_integration_fallback_that_collects_nothing_says_so(tmp_path):
    """gaze finding (correctness seat): the result named the integration tier when it ran no test of its own."""
    root = project(tmp_path, {
        "pytest.ini": PYTEST_INI,
        "scripts/alpha.py": "class Thing:\n    ok = True\n",
        "tests/test_uses_alpha.py": USES_ALPHA.format(module="alpha"),
    })
    write(root, {"scripts/alpha.py": "class Thing:\n    ok = 1\n", "scripts/gamma.py": "X = 1\n"})
    commit(root, "a named and an unnamed file; the only integration test is selected")
    code, out, err = touched(root)
    assert code == 0, out + err
    assert line(out, "result") == "result: pass (1 selected file(s), integration tier: no test outside the selection)"


def test_selected_tests_run_whatever_marker_filter_the_project_sets(tmp_path):
    root = alpha_project(tmp_path)
    write(root, {"pytest.ini": PYTEST_INI + 'addopts = -m "not integration"\n'})
    commit(root, "a project that filters integration by default")
    (root / "scripts" / "alpha.py").write_text("class Thing:\n    ok = False\n", encoding="utf-8")
    commit(root, "break Thing")
    code, out, err = touched(root)
    assert code == 1, out + err
    assert line(out, "selected") == "selected: tests/test_uses_alpha.py"
