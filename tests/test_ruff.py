"""ruff adherence gate — lint failures are caught locally before CI.

Ticket 0470. ``rules/coding-python.md`` makes this test mandatory per
project; until now `make lint` selected only grep/AST ratchets and ruff ran
by hand, outside any guard.

Pinning (documented deviation from the rule's uv-lock path, decided in the
ticket): IDH has no pyproject.toml/uv by design, so the version is pinned as
a range in ``requirements-dev.txt`` and the series is asserted here — an
ambient ruff that drifts to another minor series silently changes rules,
which is exactly what the rule forbids.

Scope lives in ``.ruff.toml``: ruff's default rule set, and **no per-file
ignores** — 0470 grandfathered nine pre-existing violations to land the gate
without opening a cleanup, and ticket 0590 cleaned them and removed the last
entry. ``test_no_per_file_ignores`` below keeps it that way.
"""

import re
import shutil
import subprocess
import tomllib
from pathlib import Path

import pytest

# adherence: this is the lint gate, selected by `make lint`. integration: it
# spawns subprocesses, which the marker-hygiene lens (scripts/test-quality.py)
# requires to be declared; both tiers exclude it from `make check-fast`.
pytestmark = [pytest.mark.adherence, pytest.mark.integration]

REPO = Path(__file__).resolve().parents[1]


def _pinned_bounds() -> tuple[tuple[int, ...], tuple[int, ...]]:
    # Single source of truth: the `ruff>=A,<B` range in requirements-dev.txt.
    # Both bounds are consulted — the upper one is the half of the pin that
    # actually bounds drift. A second hardcoded copy here would drift from
    # the declaration on the next bump.
    text = (REPO / "requirements-dev.txt").read_text(encoding="utf-8")
    m = re.search(r"^ruff\s*>=\s*([\d.]+)\s*,\s*<\s*([\d.]+)", text, re.MULTILINE)
    assert m, (
        "no `ruff>=A,<B` range found in requirements-dev.txt — the pin and "
        "this gate must move together (ticket 0470)"
    )
    return _vtuple(m.group(1)), _vtuple(m.group(2))


def _vtuple(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


def _ruff() -> str:
    ruff = shutil.which("ruff")
    assert ruff is not None, (
        "ruff not found — install the pinned dev dependency "
        "(pip install -r requirements-dev.txt, ticket 0470)"
    )
    return ruff


def test_ruff_version_satisfies_pinned_range():
    out = subprocess.run([_ruff(), "--version"], capture_output=True, text=True)
    # A binary that exists but cannot run (stale pipx shim after a Python
    # upgrade, rules/coding-python.md) must not read as version drift.
    assert out.returncode == 0, f"ruff --version failed: {out.stderr.strip()}"
    lower, upper = _pinned_bounds()
    version = out.stdout.strip().removeprefix("ruff ")
    assert lower <= _vtuple(version) < upper, (
        f"ruff {version} is outside the pinned range (requirements-dev.txt) — "
        "an unpinned ruff drifts between machines and silently changes rules "
        "on upgrade (rules/coding-python.md)"
    )


def test_ruff():
    # Reference implementation from rules/coding-python.md: shutil.which, no
    # nested `uv run`. stderr included: ruff reports a broken .ruff.toml
    # there, with nothing on stdout.
    result = subprocess.run([_ruff(), "check", "."], capture_output=True,
                            text=True, cwd=REPO)
    assert result.returncode == 0, result.stdout + result.stderr


# Every way .ruff.toml can suppress a finding. A per-file ignore is the one
# that bit (ticket 0470 opened four, 0590 closed them), but `lint.ignore` or
# `exclude` reopens the same hole repo-wide — so the guard names the class,
# not the single spelling that happened to bite.
SUPPRESSION_KEYS = ("per-file-ignores", "extend-per-file-ignores",
                    "ignore", "extend-ignore", "exclude", "extend-exclude")


def _suppressions() -> list[str]:
    """Every suppression declared in .ruff.toml, each naming where it lives.

    Both scopes are read: `[lint.x]` is current, bare `[x]` the legacy
    top-level spelling. Reporting the scope matters — an entry under
    `lint.extend-per-file-ignores` and one at top level are different lines
    to delete, and a message that merged them would send you to the wrong
    place.
    """
    cfg = tomllib.loads((REPO / ".ruff.toml").read_text(encoding="utf-8"))
    return [f"{scope}{key} = {table[key]!r}"
            for scope, table in (("", cfg), ("lint.", cfg.get("lint") or {}))
            for key in SUPPRESSION_KEYS
            # Truthiness on purpose: an empty table suppresses nothing.
            if table.get(key)]


def test_config_declares_no_suppressions():
    """The lint gate has no holes in it (ticket 0590).

    A suppression is a hole, not an exemption: while it stands, a NEW
    violation passes unseen. That is true of a per-file ignore and equally
    true of `lint.ignore` or `exclude`, so this asserts the class.

    Do not answer "is this entry still load-bearing?" instead — that needs
    ruff's own glob matching re-implemented, and `fnmatch` is not globset:
    it matches `tests/*.py` against `tests/sub/deep.py` and misses
    `**/conftest.py` against a root-level `conftest.py`, so it errs in both
    directions. If an ignore is ever genuinely needed, delegate the matching
    to ruff rather than modelling it. History in ticket 0590.
    """
    found = _suppressions()
    assert not found, (
        "the lint gate declares a suppression — a violation it covers would "
        "pass unseen. Ticket 0590 closed the last one; reopening one should "
        "be argued in a ticket, not slipped into config:\n  "
        + "\n  ".join(found)
    )
