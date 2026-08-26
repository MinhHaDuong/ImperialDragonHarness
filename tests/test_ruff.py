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


# Every spelling ruff honours for per-file suppressions. Reading only
# `lint.per-file-ignores` would let an entry in either of the others sit
# unexamined, and the guard would report all-clear without having looked.
IGNORE_TABLES = ("per-file-ignores", "extend-per-file-ignores")


def _grandfather_entries() -> dict[str, set[str]]:
    """{glob-or-path: {rule selector}} across every per-file ignore table."""
    cfg = tomllib.loads((REPO / ".ruff.toml").read_text(encoding="utf-8"))
    entries: dict[str, set[str]] = {}
    # `[lint.x]` is current; bare `[x]` is the legacy top-level spelling.
    for scope in (cfg.get("lint") or {}, cfg):
        for table in IGNORE_TABLES:
            for pattern, rules in (scope.get(table) or {}).items():
                entries.setdefault(pattern, set()).update(rules)
    return entries


def test_no_per_file_ignores():
    """The repo carries no per-file suppression at all (ticket 0590).

    A per-file ignore is a hole, not an exemption: while it stands, a NEW
    violation of that rule in that file passes unseen. Ticket 0470 opened
    four of them to land the gate without a cleanup; 0590 cleaned the nine
    violations and closed all four.

    This states the invariant that was actually reached, rather than
    tolerating an entry and trying to notice later that it went stale. The
    weaker "is this entry still load-bearing?" check was written first and
    dropped on review: answering it means re-implementing ruff's own glob
    matching and config precedence in Python, and `fnmatch` is not globset —
    it matches `tests/*.py` against `tests/sub/deep.py` (a stale entry then
    reads as live) and fails to match `**/conftest.py` against a root-level
    `conftest.py` (a live entry then reads as stale). A second, unverified
    model of ruff's semantics guarding an empty table is worse than no
    machinery at all.

    If a future change genuinely needs an ignore, this test is the place the
    decision surfaces: opening a hole should be deliberate and argued, and
    whoever opens one has a real entry to build a staleness check against.
    """
    entries = _grandfather_entries()
    assert not entries, (
        "per-file ignores are holes in the lint gate — a new violation of "
        "that rule in that file would pass unseen. Ticket 0590 closed the "
        "last one. If you need this, say why in the ticket and reintroduce "
        "a staleness check with it:\n  "
        + "\n  ".join(f"{pattern}: {sorted(rules)}"
                      for pattern, rules in sorted(entries.items()))
    )
