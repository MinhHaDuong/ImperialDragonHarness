"""Forbid weak worktree predicates re-entering scripts/ and skills/ (ticket 0310).

A `[ -f .git ]` test — "this dir has a `.git` FILE, so it must be a linked
worktree" — is the weak class shape: it also fires on a submodule and on any
ad-hoc worktree outside the harness convention, and trusts the path blindly.
It bit erg-pr-merge (fixed, 0301) and two sibling guards (fixed, 0308:
scripts/pretooluse-worktree-path-guard.sh and
scripts/block-pr-merge-in-worktree.sh — both merged, no live predicate left).
The correct detection resolves git's own dirs (`git rev-parse
--absolute-git-dir` vs `--git-common-dir`) or verifies the harness
`.claude/worktrees/<name>` identity against the resolved toplevel.

A green per-PR gate does not stop the class from re-entering in an unrelated
future script; this standing ratchet does. It greps scripts/ and skills/ for
the weak predicate and fails on any hit outside the explicit allowlist below.

The allowlist holds only the three surviving *explanatory comments* that name
the old check to warn against regressing to it — no live code. When 0308
landed, the live predicates in the two guard scripts were removed; what remains
in those files is documentation, not behaviour (cross-ref: tickets 0301, 0308).

RED proof (2026-07-13): adding `[ -f .git ]` to a scratch script under scripts/
made this test fail with that line reported as a non-allowlisted hit; removing
it restored green.
"""

import functools
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]

# A `-f`/`-e` file-test on a `.git` path: `[ -f .git ]`, `test -f .git`,
# `[ -f "$dir/.git" ]`, `[ -f "${dir}/.git" ]`, `[[ -e ${worktree}/.git ]]`,
# `[ -e .git ]`. The literal dot before `git` is what distinguishes the weak
# predicate from the strong `git rev-parse --absolute-git-dir` /
# `--git-common-dir` form (hyphen, no dot). Braces are included in the prefix
# and path classes so the house `${var}/.git` idiom cannot slip past the grep.
WEAK_PREDICATE = re.compile(r"""-[fe][ \t]+["'${}]*[\w./{}-]*\.git\b""")

# Explicit allowlist: (relative path, exact stripped line). Every entry is an
# explanatory comment that names the old weak check to warn against it — none is
# live code. Shrinks only when such a comment is removed; a NEW hit (live or
# comment) that is not listed here fails the ratchet.
ALLOWLIST: set[tuple[str, str]] = {
    (
        "scripts/block-pr-merge-in-worktree.sh",
        "# The old `[ -f .git ] && grep gitdir:` check had one real false positive: a",
    ),
    (
        "scripts/pretooluse-worktree-path-guard.sh",
        "# would satisfy the old `[ -f .git ] && grep gitdir:` check and trip a spurious",
    ),
    (
        "skills/merge/erg-pr-merge",
        "# `[ -f .git ]`: that matched ANY dir with a `.git` FILE — a submodule, or a",
    ),
}

SCAN_ROOTS = ("scripts", "skills")


@functools.lru_cache(maxsize=1)
def all_hits() -> tuple[tuple[str, int, str], ...]:
    """(relpath, lineno, stripped_line) for every weak-predicate match.

    Cached: both tests below share one walk of scripts/ and skills/.
    """
    return tuple(_iter_hits())


def _iter_hits():
    for root in SCAN_ROOTS:
        for path in sorted((REPO / root).rglob("*")):
            if not path.is_file():
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue  # binary (e.g. an `erg` helper) — no shell predicate
            rel = path.relative_to(REPO).as_posix()
            for lineno, line in enumerate(text.splitlines(), 1):
                if WEAK_PREDICATE.search(line):
                    yield rel, lineno, line.strip()


@pytest.mark.adherence
@pytest.mark.parametrize(
    "line",
    [
        "[ -f .git ]",
        "test -f .git",
        "[ -e .git ]",
        '[ -f "$dir/.git" ]',
        '[ -f "${dir}/.git" ]',
        "[[ -e ${worktree}/.git ]]",
    ],
)
def test_weak_predicate_regex_catches_known_forms(line):
    """The ratchet must catch the weak predicate in the house `${var}` idiom.

    Brace-expansion forms (`${dir}/.git`) are the common shell style here, so a
    regressed weak predicate written that way must not slip past the grep.
    """
    assert WEAK_PREDICATE.search(line), line


@pytest.mark.adherence
@pytest.mark.parametrize(
    "line",
    [
        "[ -f .gitignore ]",
        "git rev-parse --absolute-git-dir",
        "[ -f .gitmodules ]",
    ],
)
def test_weak_predicate_regex_ignores_safe_forms(line):
    """Strong detection (`git rev-parse`) and sibling dotfiles are not weak."""
    assert not WEAK_PREDICATE.search(line), line


@pytest.mark.adherence
def test_no_weak_worktree_predicate_outside_allowlist():
    offenders = [
        f"{rel}:{lineno}: {stripped}"
        for rel, lineno, stripped in all_hits()
        if (rel, stripped) not in ALLOWLIST
    ]
    assert not offenders, (
        "weak worktree predicate `[ -f .git ]` (or a close variant) found "
        "outside the allowlist (ticket 0310). Detect a linked worktree by "
        "resolving git's own dirs (`git rev-parse --absolute-git-dir` vs "
        "`--git-common-dir`) or the harness `.claude/worktrees/<name>` identity, "
        "not by the presence of a `.git` file — that also matches submodules "
        "and ad-hoc worktrees. If this is a deliberate explanatory comment, add "
        "it to ALLOWLIST:\n" + "\n".join(offenders)
    )


@pytest.mark.adherence
def test_allowlist_has_no_stale_entries():
    """Every allowlisted line must still exist verbatim — remove it once gone."""
    live = {(rel, stripped) for rel, _, stripped in all_hits()}
    stale = sorted(ALLOWLIST - live)
    assert not stale, (
        "ALLOWLIST entries no longer present in the tree — the weak-predicate "
        "comment was removed or reworded; drop the stale entry:\n"
        + "\n".join(f"{rel}: {stripped}" for rel, stripped in stale)
    )
