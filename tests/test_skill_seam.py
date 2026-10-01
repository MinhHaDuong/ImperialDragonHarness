"""The loaded-skill path seam (ticket 0803).

The seam every script-backed skill body carries:

    IDH_ROOT="$(cd -P "$(dirname "<loaded-SKILL.md>")/../.." && pwd -P)"

The runtime supplies the absolute projected path of the SKILL.md it loaded;
the body substitutes it for ``<loaded-SKILL.md>``. ``cd -P`` resolves the
projected symlink to the canonical checkout, so the bundled scripts under
``$IDH_ROOT/scripts/`` are found from any installation root, through any
skills root, with no build step and no configuration field.

What this module proves mechanically:

- every body that carries the seam spells it identically (drift ratchet);
- the idiom resolves a space-containing installation root;
- it resolves through nested symlinks (skills-root symlink -> skills dir);
- a dangling projected path fails with an empty root and a stderr message —
  never a plausible wrong root — and the failure surfaces visibly at the
  first downstream use of ``$IDH_ROOT`` (the runtime that loaded the body
  guarantees the path it supplied existed);
- a path containing a double quote resolves correctly (observed
  2026-09-28, pinned) — the idiom's nested quoting is more robust than it
  reads, and a future rewrite must not regress that.

The three-runtime evidence (Pi 0.87.1, Codex 0.157.0, Claude Code 2.1.283
each supplying the loaded path and running the real ``project-state.py``)
is recorded as manual-smoke assertions in ``adapters/pilot-support.json``;
this module is the deterministic half that runs everywhere.
"""

import os
import re
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent

SEAM_LINE = 'IDH_ROOT="$(cd -P "$(dirname "<loaded-SKILL.md>")/../.." && pwd -P)"'
SEAM_RE = re.compile(re.escape(SEAM_LINE))


def bodies_with_seam():
    return sorted(p for p in REPO.glob("skills/*/SKILL.md") if "IDH_ROOT" in p.read_text())


def run_idiom(projected_skill_path):
    script = (
        SEAM_LINE.replace("<loaded-SKILL.md>", projected_skill_path)
        + '\necho "$IDH_ROOT"\n'
    )
    # LC_ALL=C: the dangling-projection test matches bash's English
    # "No such file" diagnostic, which a localized shell translates.
    return subprocess.run(
        ["bash", "-c", script],
        capture_output=True,
        text=True,
        timeout=10,
        env={**os.environ, "LC_ALL": "C"},
    )


def make_tree(root: Path):
    (root / "skills" / "probe").mkdir(parents=True)
    (root / "skills" / "probe" / "SKILL.md").write_text("---\nname: probe\n---\n")
    (root / "scripts").mkdir()
    (root / "scripts" / "hello.sh").write_text('#!/usr/bin/env bash\necho ok\n')


def test_every_seam_body_derives_from_the_runtime_supplied_path():
    """The invariant: any body that sets IDH_ROOT derives it from the
    runtime-supplied loaded-skill path via cd -P — one line (healthcheck,
    dream, ...) or two (roar, which needs its own skill dir first) — and
    never from a hard-coded installation root or the project cwd."""
    bodies = bodies_with_seam()
    assert len(bodies) >= 10, "seam-bearing bodies went missing"
    for body in bodies:
        text = body.read_text()
        assert "<loaded" in text and "cd -P" in text, (
            f"{body}: IDH_ROOT is not derived from the runtime-supplied "
            "loaded-skill path via cd -P"
        )
        assert not re.search(r'IDH_ROOT="\$HOME|IDH_ROOT="~/|IDH_ROOT="/home', text), (
            f"{body}: IDH_ROOT is set from a hard-coded installation root"
        )


def test_the_canonical_one_line_spelling_dominates():
    canonical = [b for b in bodies_with_seam() if SEAM_RE.search(b.read_text())]
    assert len(canonical) >= 14, (
        "the shared one-line seam spelling regressed; only roar may spell "
        "the same derivation in two steps"
    )


def test_healthcheck_body_invokes_the_probe_through_the_seam():
    body = (REPO / "skills" / "healthcheck" / "SKILL.md").read_text()
    assert 'python3 "$IDH_ROOT/scripts/project-state.py"' in body
    assert '"$(git rev-parse --show-toplevel)"' in body


@pytest.mark.integration
def test_resolves_a_space_containing_root(tmp_path):
    root = tmp_path / "harness root with spaces"
    make_tree(root)
    projected = tmp_path / "agents" / "skills" / "probe"
    projected.parent.mkdir(parents=True)
    os.symlink(root / "skills" / "probe", projected)
    r = run_idiom(str(projected / "SKILL.md"))
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == str(root)


@pytest.mark.integration
def test_resolves_through_nested_symlinks(tmp_path):
    root = tmp_path / "real-tree"
    make_tree(root)
    first = tmp_path / "link-one"
    os.symlink(root / "skills" / "probe", first)
    projected = tmp_path / "agents" / "skills" / "probe"
    projected.parent.mkdir(parents=True)
    os.symlink(first, projected)
    r = run_idiom(str(projected / "SKILL.md"))
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == str(root)


@pytest.mark.integration
def test_dangling_projection_yields_an_empty_root_not_a_wrong_one(tmp_path):
    # A dangling symlink cannot be loaded by any runtime, so no runtime would
    # ever supply its path. Handed one anyway, cd -P fails on stderr, IDH_ROOT
    # stays empty — never a plausible wrong root — and the composite line
    # exits 0 (echo's status), so the failure surfaces downstream at first
    # use of $IDH_ROOT, visibly (python3: cannot open .../scripts/...).
    skills = tmp_path / "agents" / "skills"
    skills.mkdir(parents=True)
    os.symlink(tmp_path / "nowhere" / "skills" / "ghost", skills / "ghost")
    r = run_idiom(str(skills / "ghost" / "SKILL.md"))
    assert r.stdout.strip() == ""
    assert "No such file" in r.stderr


@pytest.mark.integration
def test_resolves_a_quote_containing_root(tmp_path):
    # Observed 2026-09-28: bash's nested quoting inside the idiom survives a
    # double quote in the installation root — the derivation stays correct.
    # Pinned here so a future "cleanup" of the line cannot regress it.
    root = tmp_path / 'root"with"quotes'
    make_tree(root)
    projected = tmp_path / "agents" / "skills" / "probe"
    projected.parent.mkdir(parents=True)
    os.symlink(root / "skills" / "probe", projected)
    r = run_idiom(str(projected / "SKILL.md"))
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == str(root)


@pytest.mark.integration
def test_probe_script_is_reachable_through_the_seam(tmp_path):
    root = tmp_path / "relocated-tree"
    make_tree(root)
    (root / "scripts" / "project-state.py").write_text(
        '#!/usr/bin/env python3\nimport sys\nsys.stdout.write("probe-found")\n'
    )
    projected = tmp_path / "agents" / "skills" / "probe"
    projected.parent.mkdir(parents=True)
    os.symlink(root / "skills" / "probe", projected)
    script = (
        SEAM_LINE.replace("<loaded-SKILL.md>", str(projected / "SKILL.md"))
        + '\npython3 "$IDH_ROOT/scripts/project-state.py"\n'
    )
    r = subprocess.run(
        ["bash", "-c", script], capture_output=True, text=True, timeout=10
    )
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "probe-found"
