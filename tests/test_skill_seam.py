"""The loaded-skill path seam (ticket 0803).

The seam every script-backed skill body carries:

    IDH_ROOT="${IDH_ROOT:-$(p="<loaded-SKILL.md>"; [ -d "$p" ] || p=$(dirname "$p"); cd -P "$p/../.." && pwd -P)}"

A session launched through scripts/shell-init.sh already exports IDH_ROOT
(ticket 1247) and the line keeps it. Otherwise the runtime supplies the
absolute projected path of the SKILL.md it loaded (Claude Code 2.1.x supplies
the skill directory instead; both resolve the same); the body substitutes it
for ``<loaded-SKILL.md>``. ``cd -P`` resolves the
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

import importlib.util
import os
import re
import subprocess
from pathlib import Path

import pytest

from child_env import child_env
from tracked_tree import tracked_checkout

REPO = Path(__file__).resolve().parent.parent

SEAM_LINE = (
    'IDH_ROOT="${IDH_ROOT:-$(p="<loaded-SKILL.md>"; [ -d "$p" ] || p=$(dirname "$p");'
    ' cd -P "$p/../.." && pwd -P)}"'
)
SEAM_RE = re.compile(re.escape(SEAM_LINE))


def seam_env():
    """Child env without an inherited IDH_ROOT, which the seam line would keep."""
    return {k: v for k, v in child_env().items() if k != "IDH_ROOT"}


def bodies_with_seam():
    return sorted(p for p in REPO.glob("skills/*/SKILL.md") if "IDH_ROOT" in p.read_text())


def run_idiom(projected_skill_path, preset=None):
    script = (
        SEAM_LINE.replace("<loaded-SKILL.md>", projected_skill_path)
        + '\necho "$IDH_ROOT"\n'
    )
    # LC_ALL=C: the dangling-projection test matches bash's English
    # "No such file" diagnostic, which a localized shell translates.
    env = seam_env()
    if preset is not None:
        env["IDH_ROOT"] = preset
    return subprocess.run(
        ["bash", "-c", script],
        capture_output=True,
        text=True,
        timeout=10,
        env={**env, "LC_ALL": "C"},
    )


def make_tree(root: Path):
    (root / "skills" / "probe").mkdir(parents=True)
    (root / "skills" / "probe" / "SKILL.md").write_text("---\nname: probe\n---\n")
    (root / "scripts").mkdir()
    (root / "scripts" / "hello.sh").write_text('#!/usr/bin/env bash\necho ok\n')


def test_every_seam_body_derives_from_the_runtime_supplied_path():
    """The invariant: any body that sets IDH_ROOT derives it from the
    runtime-supplied loaded-skill path via cd -P — one line (yawn,
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


def test_yawn_body_invokes_the_probe_through_the_seam():
    body = (REPO / "skills" / "yawn" / "SKILL.md").read_text()
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
def test_skill_directory_and_skill_file_resolve_the_same_root(tmp_path):
    # Claude Code 2.1.x supplies the skill's base directory, not its SKILL.md.
    root = tmp_path / "real-tree"
    make_tree(root)
    projected = tmp_path / "agents" / "skills" / "probe"
    projected.parent.mkdir(parents=True)
    os.symlink(root / "skills" / "probe", projected)
    by_file = run_idiom(str(projected / "SKILL.md"))
    by_dir = run_idiom(str(projected))
    assert by_file.returncode == 0 and by_dir.returncode == 0, by_dir.stderr
    assert by_dir.stdout.strip() == by_file.stdout.strip() == str(root)


@pytest.mark.integration
def test_a_preset_idh_root_wins(tmp_path):
    root = tmp_path / "real-tree"
    make_tree(root)
    r = run_idiom(str(root / "skills" / "probe" / "SKILL.md"), preset="/wrapper/exported")
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "/wrapper/exported"


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
        ["bash", "-c", script], capture_output=True, text=True, timeout=10,
        env=seam_env(),
    )
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "probe-found"


@pytest.mark.integration
def test_hoard_real_migration_from_another_project_cwd(tmp_path):
    body = (REPO / "skills/hoard/SKILL.md").read_text()
    seam = SEAM_RE.search(body).group(0)
    commands = re.findall(r'^python3 "\$IDH_ROOT/scripts/hoard_migrate.py".*$', body, re.MULTILINE)
    preflight, apply = commands
    projected = tmp_path / "installed/skills/hoard"
    projected.parent.mkdir(parents=True)
    projected.symlink_to(REPO / "skills/hoard", target_is_directory=True)
    env = {**seam_env(), "GIT_AUTHOR_NAME": "fixture", "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
           "GIT_COMMITTER_NAME": "fixture", "GIT_COMMITTER_EMAIL": "fixture@example.invalid"}

    def git(root, *args):
        # Keep background maintenance from racing the fixture's byte snapshots.
        return subprocess.run(["git", "-c", "maintenance.auto=false", "-c", "gc.auto=0",
                               "-C", str(root), *args], check=True,
                              capture_output=True, text=True, env=env).stdout

    def bytes_in(root):
        return {str(path.relative_to(root)): path.read_bytes()
                for path in root.rglob("*") if path.is_file()}

    def old_project(root):
        (root / "memory/dreams").mkdir(parents=True)
        (root / "memory/DREAM.md").write_text(
            "# DREAM\nPrompt revision: v8-r1\nReports: memory/dreams/\n")
        (root / "memory/MEMORY.md").write_text("[report](dreams/old.md)\n")
        (root / "memory/dreams/old.md").write_bytes(b"Prompt v8-r1; ledger blob abc123\x00\xff")
        (root / "AGENTS.md").write_text("Read memory/DREAM.md; invoke /dream\n")
        git(root, "init", "-b", "main")
        git(root, "add", ".")
        git(root, "commit", "-m", "fixture")

    selected, other = tmp_path / "selected", tmp_path / "other"
    old_project(selected)
    old_project(other)
    other_before = bytes_in(other)
    primary_memory = bytes_in(selected / "memory")
    refs_before = git(selected, "for-each-ref")
    selected_before = bytes_in(selected)

    def run(command, target):
        script = (seam.replace("<loaded-SKILL.md>", str(projected / "SKILL.md"))
                  + '\nREFERENCES=(--reference AGENTS.md)\n' + command)
        return subprocess.run(["bash", "-c", script], cwd=other, env={**env, "PROJECT": str(target)},
                              capture_output=True, text=True, timeout=20)

    dry = run(preflight, selected)
    assert dry.returncode == 0, dry.stderr
    assert bytes_in(selected) == selected_before
    assert git(selected, "for-each-ref") == refs_before
    isolated = tmp_path / "isolated"
    git(selected, "worktree", "add", "-b", "hoard-fixture", str(isolated), "main")
    result = run(apply, isolated)
    assert result.returncode == 0, result.stderr
    assert (isolated / "memory/HOARD.md").is_file()
    assert not (isolated / "memory/DREAM.md").exists()
    assert (isolated / "memory/MEMORY.md").read_text() == "[report](hoards/old.md)\n"
    assert (isolated / "AGENTS.md").read_text() == "Read memory/HOARD.md; invoke /hoard\n"
    assert (isolated / "memory/hoards/old.md").read_bytes() == primary_memory["dreams/old.md"]
    after = bytes_in(isolated)
    repeat = run(apply, isolated)
    assert repeat.returncode == 0, repeat.stderr
    assert bytes_in(isolated) == after
    assert bytes_in(selected / "memory") == primary_memory
    assert (selected / "AGENTS.md").read_bytes() == selected_before["AGENTS.md"]
    assert bytes_in(other) == other_before


@pytest.mark.integration
def test_hoard_installs_across_runtimes_without_legacy_skill(tmp_path, monkeypatch):
    repo = tracked_checkout()
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("USERPROFILE", raising=False)
    monkeypatch.delenv("XDG_STATE_HOME", raising=False)

    def load(name):
        spec = importlib.util.spec_from_file_location(name, repo / "adapters" / f"{name}.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    perch, lifecycle = load("perch"), load("lifecycle")
    monkeypatch.setattr(perch, "check_version", lambda *a, **k: "9.9.9")
    assert lifecycle.install_links() == 0
    assert "hoard" in perch.known_skills()
    assert "dream" not in perch.known_skills()
    for runtime, relative in (
        ("claude", ".claude/skills/hoard"),
        ("codex", ".agents/skills/hoard"),
        ("pi", ".agents/skills/hoard"),
    ):
        perch.install(runtime, "hoard")
        projected = home / relative
        assert projected.resolve() == repo / "skills/hoard"
        assert "already discoverable" in perch.install(runtime, "hoard")
        assert not (projected.parent / "dream").exists()
        assert not (projected.parent / "dream").is_symlink()


def test_no_skill_derives_the_root_unconditionally_from_dirname():
    """Ticket 1253: a `$(dirname "<loaded path>")` skill location ignores a
    preset IDH_ROOT and, given the skill directory, lands one level too high.
    The fallback's own `p=$(dirname "$p")` does not match."""
    bad = re.compile(r'\$\(dirname "(?:<loaded|\$\{?[A-Z_]*SKILL_MD)[^"]*"\)')
    hits = [
        f"{p.relative_to(REPO)}:{n}"
        for p in sorted((REPO / "skills").rglob("*"))
        if p.is_file() and p.suffix in {".md", ".sh"}
        for n, line in enumerate(p.read_text().splitlines(), 1)
        if bad.search(line)
    ]
    assert not hits, f"unconditional dirname root derivation: {hits}"
