"""Attribution records live outside the memory journal (ticket 1347).

New captures land in `memory/evidence/attribution/`; the readers scan that root
and the legacy `memory/journal/` (consumer projects move their own records
later); ordinary captures still land in the journal.
"""

import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from child_env import child_env

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
NEW_ROOT = "memory/evidence/attribution"

RECORD = """kind: review-attribution
pr: 1164 · merged 2026-10-03 · project: fixture
writer: runtime=fixture · model=example/writer-v1 · effort=standard
reviewer: seat=correctness-round1 · runtime=fixture · model=example/reviewer-v1 · status: ran
  finding: verifiable · scripts/example.py:12 · adopted: yes
"""


def project(tmp_path):
    repo = tmp_path / "project"
    subprocess.run(["git", "init", "--quiet", str(repo)], env=child_env(), check=True)
    subprocess.run(["git", "-C", str(repo), "remote", "add", "origin", "https://example.invalid/o/p.git"],
                   env=child_env(), check=True)
    return repo


def capture(repo, audience="public", text=RECORD, env=None):
    return subprocess.run([sys.executable, str(SCRIPTS / "attribution_record.py"), "--capture", str(repo),
                           "--audience", audience], input=text, text=True, capture_output=True,
                          env=env or child_env())


def query(repo):
    result = subprocess.run([sys.executable, str(SCRIPTS / "attribution_query.py"), str(repo), "--json"],
                            text=True, capture_output=True, env=child_env())
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def load(name):
    sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.integration
def test_capture_lands_outside_the_journal_and_is_read(tmp_path):
    repo = project(tmp_path)
    result = capture(repo)
    assert result.returncode == 0, result.stderr
    assert len(list((repo / NEW_ROOT).glob("*-review-attribution-pr1164.md"))) == 1
    assert not (repo / "memory/journal").exists()
    assert query(repo)["records"]["valid"] == 1


@pytest.mark.integration
def test_legacy_journal_record_is_still_read(tmp_path):
    repo = project(tmp_path)
    legacy = repo / "memory/journal/2026"
    legacy.mkdir(parents=True)
    (legacy / "2026-10-03-review-attribution-pr1164.md").write_text(RECORD)
    (repo / NEW_ROOT).mkdir(parents=True)
    (repo / NEW_ROOT / "2026-10-04-review-attribution-pr1165.md").write_text(RECORD.replace("1164", "1165"))
    assert query(repo)["records"]["valid"] == 2
    stats = {"unresolved": 0}
    records = load("attribution_backfill").load_records(repo.resolve(), stats)
    assert sorted(records) == [1164, 1165] and stats["unresolved"] == 0


@pytest.mark.integration
def test_ordinary_capture_still_lands_in_the_journal(tmp_path):
    repo = project(tmp_path)
    result = subprocess.run([str(SCRIPTS / "memory-capture.sh"), str(repo), "public", "note"],
                            input="text\n", text=True, capture_output=True, env=child_env())
    assert result.returncode == 0, result.stderr
    assert len(list(repo.glob("memory/journal/*/*-note.md"))) == 1
    assert not (repo / NEW_ROOT).exists()


@pytest.mark.integration
def test_unknown_fourth_argument_is_refused(tmp_path):
    repo = project(tmp_path)
    result = subprocess.run([str(SCRIPTS / "memory-capture.sh"), str(repo), "public", "note", "journal"],
                            input="text\n", text=True, capture_output=True, env=child_env())
    assert result.returncode == 2
    assert not (repo / "memory").exists()


@pytest.mark.integration
@pytest.mark.skipif(not (shutil.which("age") and shutil.which("age-keygen")), reason="age not installed")
def test_private_capture_lands_in_the_new_root(tmp_path):
    repo = project(tmp_path)
    env = child_env()
    env["HOME"] = str(tmp_path / "home")
    result = capture(repo, "private", env=env)
    assert result.returncode == 0, result.stderr
    assert len(list((repo / NEW_ROOT).glob("*-review-attribution-pr1164.age"))) == 1
    assert not (repo / "memory/journal").exists()


@pytest.mark.integration
def test_harness_journal_holds_no_attribution_record():
    listed = subprocess.run(["git", "-C", str(ROOT), "ls-files", "memory/journal"], text=True,
                            capture_output=True, check=True, env=child_env()).stdout.splitlines()
    assert [name for name in listed if "review-attribution" in name] == []


def test_smelt_migration_refuses_attribution_records():
    migrate = load("smelt_migrate")
    with pytest.raises(migrate.MigrationError):
        migrate.plan_migration(ROOT, [f"{NEW_ROOT}/2026-10-03-review-attribution-pr1164.md"])
