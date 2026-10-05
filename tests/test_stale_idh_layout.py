"""
Ticket 1020: the retired ~/.idh layout must not survive in scripts/ as a live
reference. Ticket 1025 extends the same ratchet to skills/.

The ~/.idh layout was retired by the portable lifecycle (0987/0999, PR #1091);
the reference checkout is wherever the harness is installed. The agnostic gate
(check-agnostic.sh) checks class-level patterns, not retired layout names, so
this ratchet is the mechanical guard for the sweep: any NEW `~/.idh`-style
reference in scripts/ or skills/ fails, and the survivors that legitimately
remain are pinned line-by-line as provenance.
"""

import re
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).parent.parent / "scripts"
SKILLS = Path(__file__).parent.parent / "skills"

# A path-component `.idh` (the retired layout dir): `~/.idh`, `$HOME/.idh`,
# `<home>/.idh`, `"$HOMEDIR"/.idh` — but NOT the `.idh-checks.json` filename,
# which is a live convention, not a layout reference (the lookahead excludes it).
STALE_LAYOUT = re.compile(r"\.idh(?!-)")

# Provenance: path relative to scripts/ -> substrings each surviving line
# must carry. Keyed by full relative path (not basename) so a same-named
# file in a subdirectory cannot inherit another file's exemption. A match in
# any other path, or a surviving line that no longer carries one of its
# substrings, is a new live reference: red.
PROVENANCE = {
    # The 0984 probe emulates the pre-retirement layout in a disposable HOME
    # (a .idh symlink over the real checkout); the rig name is a fixture, not
    # a pointer at the live layout.
    "probe-memory-symlink.py": (
        "launch from <home>/.idh -> <home>/.claude",
        "Launch through <home>/.idh -> <home>/.claude",
        'link = rig_home / ".idh"',
    ),
    # Translates the retired `$HOME/.idh/scripts/...` hook-command form that
    # pre-0982 settings still carry, so merge_hooks can recognize an installed
    # predecessor and replace it instead of appending a duplicate. Moved here
    # from the retired derivation generator with the rest of the translator
    # (0887 activation); removing the translator is a separate retirement,
    # not this sweep.
    "validate-projections.py": (
        "`$HOME/.idh/scripts/x.sh a`",
        "when the ~/.idh pointer is missing",
        ".idh/scripts/(?P<name>",
        ".idh/scripts/(?P=name)",
    ),
}

# Provenance for skills/ (ticket 1025): path relative to skills/ -> substrings
# each surviving line must carry. Same path-scoped keying as PROVENANCE.
SKILLS_PROVENANCE = {
    # Containment self-test (0217): the sandbox must block secret reads from
    # every location, retired ones included.
    "coaching/seat-runner.sh": (
        "'/.idh/scripts/bash-env.sh",
    ),
    # The erg-pr-merge comment must stay accurate to the live operator-owned
    # settings, which still carry the retired-layout allow rule as a legacy
    # alias for migrated installs; quoting the rule means quoting its path.
    # The line is legitimate ONLY as that legacy-alias record.
    "merge/erg-pr-merge": (
        "legacy alias",
    ),
}


def _stale_matches_under(root):
    for path in sorted(root.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            if STALE_LAYOUT.search(line):
                yield path.relative_to(root).as_posix(), lineno, line


def _stale_matches():
    return _stale_matches_under(SCRIPTS)


def _is_exempt(name, line):
    return name in PROVENANCE and any(sub in line for sub in PROVENANCE[name])


@pytest.mark.adherence
def test_no_live_stale_layout_references_in_scripts():
    offenders = []
    for name, lineno, line in _stale_matches():
        if _is_exempt(name, line):
            continue
        offenders.append(f"{name}:{lineno}: {line.strip()}")
    assert not offenders, (
        "Live ~/.idh layout reference(s) in scripts/ (ticket 1020):\n"
        + "\n".join(offenders)
    )


@pytest.mark.adherence
def test_no_live_stale_layout_references_in_skills():
    offenders = []
    for name, lineno, line in _stale_matches_under(SKILLS):
        if name in SKILLS_PROVENANCE and any(
            sub in line for sub in SKILLS_PROVENANCE[name]
        ):
            continue
        offenders.append(f"{name}:{lineno}: {line.strip()}")
    assert not offenders, (
        "Live ~/.idh layout reference(s) in skills/ (ticket 1025):\n"
        + "\n".join(offenders)
    )


@pytest.mark.adherence
def test_provenance_exemptions_are_path_scoped(tmp_path, monkeypatch):
    # A same-basename file in a subdirectory must not inherit the root
    # file's exemption: PROVENANCE is keyed by path relative to scripts/,
    # so "census/probe-memory-symlink.py" is a different key from
    # "probe-memory-symlink.py".
    sub = tmp_path / "census"
    sub.mkdir()
    (sub / "probe-memory-symlink.py").write_text('link = rig_home / ".idh"\n')
    monkeypatch.setattr("test_stale_idh_layout.SCRIPTS", tmp_path)
    offenders = [
        f"{name}:{lineno}: {line.strip()}"
        for name, lineno, line in _stale_matches()
        if not _is_exempt(name, line)
    ]
    assert offenders, (
        "subdirectory file inherited the root file's provenance exemption"
    )
