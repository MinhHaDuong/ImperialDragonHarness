"""Gaze runs the caller's brief: exactly the seats asked for, over exactly the scope asked for.

Ticket 1225. `scripts/gaze_brief.py resolve` turns the brief into the roster and
the file set gaze reviews, or refuses it; `panel-manifest-check.py --seats`
fails a manifest that adds or drops a seat the brief resolved.
"""

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BRIEF = ROOT / 'scripts' / 'gaze_brief.py'
MANIFEST = ROOT / 'scripts' / 'panel-manifest-check.py'

spec = importlib.util.spec_from_file_location('gaze_brief', BRIEF)
brief_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(brief_mod)


def git(repo, *args):
    return subprocess.run(['git', '-C', str(repo), *args], check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture
def repo(tmp_path):
    """main has base.txt; the PR branch adds a.py in commit 1 and b.md in commit 2."""
    r = tmp_path / 'repo'
    r.mkdir()
    git(r, 'init', '-q', '-b', 'main')
    git(r, 'config', 'user.email', 't@example.org')
    git(r, 'config', 'user.name', 't')
    (r / 'base.txt').write_text('base\n')
    git(r, 'add', '.')
    git(r, 'commit', '-qm', 'base')
    git(r, 'switch', '-qc', 'pr')
    (r / 'a.py').write_text('x = 1\n')
    git(r, 'add', '.')
    git(r, 'commit', '-qm', 'one')
    (r / 'b.md').write_text('text\n')
    git(r, 'add', '.')
    git(r, 'commit', '-qm', 'two')
    return r


def resolve(repo, brief):
    return subprocess.run(
        [sys.executable, str(BRIEF), 'resolve', '--brief', brief, '--base', 'main', '--head', 'HEAD', '--repo', str(repo)],
        capture_output=True, text=True,
    )


def fields(stdout):
    return dict(line.split(': ', 1) for line in stdout.splitlines() if ': ' in line)


def manifest_check(tmp_path, lines, seats):
    path = tmp_path / 'manifest.txt'
    path.write_text(''.join(f'{seat}\tsmall-model\tfamily-a\tbrief asked for it\n' for seat in lines))
    return subprocess.run([sys.executable, str(MANIFEST), str(path), '--seats', seats], capture_output=True, text=True)


def test_one_seat_brief_launches_one_seat(repo, tmp_path):
    out = resolve(repo, 'seats=correctness; scope=all')
    assert out.returncode == 0, out.stderr
    got = fields(out.stdout)
    assert got['panel_seats'] == 'correctness'
    assert got['simplify'] == 'no'
    assert got['brief'] == 'seats=correctness; scope=all'
    assert manifest_check(tmp_path, ['correctness'], got['panel_seats']).returncode == 0
    added = manifest_check(tmp_path, ['correctness', 'red-team'], got['panel_seats'])
    assert added.returncode == 1 and 'not in the brief' in added.stderr
    dropped = manifest_check(tmp_path, ['scope'], 'correctness,scope')
    assert dropped.returncode == 1 and 'missing from the manifest' in dropped.stderr


def test_adherence_only_brief_launches_no_panel(repo):
    got = fields(resolve(repo, 'seats=none').stdout)
    assert got['panel_seats'] == 'none'
    assert got['simplify'] == 'no'
    assert got['scope'] == 'all'


def test_scope_brief_reviews_only_that_range(repo):
    first = git(repo, 'rev-parse', 'HEAD~1')
    out = resolve(repo, f'seats=scope,simplify; scope={first}..HEAD')
    assert out.returncode == 0, out.stderr
    got = fields(out.stdout)
    assert got['scope_files'] == 'b.md'
    assert got['panel_seats'] == 'scope'
    assert got['simplify'] == 'yes'


def test_path_scope_reviews_only_those_paths(repo):
    got = fields(resolve(repo, 'seats=correctness; scope=paths:a.py').stdout)
    assert got['scope_files'] == 'a.py'


def test_whole_diff_scope_lists_every_changed_file(repo):
    got = fields(resolve(repo, 'seats=correctness').stdout)
    assert got['scope_files'] == 'a.py b.md'


@pytest.mark.parametrize('brief, reason', [
    ('seats=correctness,poet', 'unknown seat'),
    ('seats=correctness; scope=paths:base.txt', 'outside the diff'),
    ('seats=correctness; scope=HEAD~2..HEAD~2', 'empty range'),
    ('seats=correctness; colour=blue', 'unknown key'),
    ('scope=all', 'no seats'),
])
def test_brief_gaze_cannot_honour_is_refused(repo, brief, reason):
    out = resolve(repo, brief)
    assert out.returncode == 2
    assert out.stdout.startswith('brief: refused') and reason in out.stdout


def test_range_reaching_below_the_merge_base_is_refused(repo):
    out = resolve(repo, 'seats=correctness; scope=main~0..HEAD')
    assert out.returncode == 0  # base..head is the whole diff, inside it
    root = git(repo, 'rev-list', '--max-parents=0', 'HEAD')
    git(repo, 'switch', '-q', 'main')
    (repo / 'later.txt').write_text('y\n')
    git(repo, 'add', '.')
    git(repo, 'commit', '-qm', 'main moves')
    git(repo, 'switch', '-q', 'pr')
    below = resolve(repo, f'seats=correctness; scope={root}..HEAD')
    assert below.returncode == 0  # root is the merge-base itself
    outside = resolve(repo, 'seats=correctness; scope=main..HEAD')
    assert outside.returncode == 2 and 'outside the diff' in outside.stdout


def test_no_brief_is_the_default_brief(repo):
    got = fields(resolve(repo, '').stdout)
    assert got['brief'].startswith('default')
    assert got['panel_seats'] == 'auto'
    assert got['simplify'] == 'auto'


def test_echo_line_compares_brief_and_ran():
    line = brief_mod.echo('seats=correctness; scope=all', ['adherence', 'correctness'])
    assert line == 'brief: seats=correctness; scope=all → ran: adherence, correctness'
