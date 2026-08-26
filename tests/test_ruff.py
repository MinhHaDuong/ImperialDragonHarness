"""ruff adherence gate — lint failures are caught locally before CI.

Ticket 0470. ``rules/coding-python.md`` makes this test mandatory per
project; until now `make lint` selected only grep/AST ratchets and ruff ran
by hand, outside any guard.

Pinning (documented deviation from the rule's uv-lock path, decided in the
ticket): IDH has no pyproject.toml/uv by design, so the version is pinned as
a range in ``requirements-dev.txt`` and the series is asserted here — an
ambient ruff that drifts to another minor series silently changes rules,
which is exactly what the rule forbids. The scope ratchet lives in
``.ruff.toml``: default rules, with the pre-existing violations
grandfathered per file × rule.
"""

import re
import shutil
import subprocess
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
