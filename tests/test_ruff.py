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


def _per_file_ignores() -> dict[str, list[str]]:
    cfg = tomllib.loads((REPO / ".ruff.toml").read_text(encoding="utf-8"))
    return cfg.get("lint", {}).get("per-file-ignores", {})


def test_no_stale_grandfather_entries():
    """Every per-file-ignores entry must still suppress a real violation.

    Ticket 0590. A grandfather entry is a hole: while it stands, a NEW
    violation of that same rule in that same file passes unseen. Nothing
    otherwise notices when the file is cleaned, so the entry — and the hole —
    outlive their reason. This makes the entry self-retiring: clean the file
    and the guard tells you to remove it.

    Same shape as test_worktree_predicate_ratchet's stale-allowlist check.
    An empty per-file-ignores passes trivially, which is the intended end
    state, not a blind spot: test_ruff above is what keeps the tree clean.
    """
    stale, broken = [], []
    for rel, rules in sorted(_per_file_ignores().items()):
        for rule in rules:
            r = subprocess.run(
                [_ruff(), "check", "--isolated", "--select", rule,
                 "--output-format", "concise", rel],
                capture_output=True, text=True, cwd=REPO)
            if r.returncode == 0:
                stale.append(f"{rel}: {rule} no longer fires")
            elif r.returncode != 1:
                # 2 = ruff could not look (missing file, bad rule code). That
                # must not read as "still load-bearing".
                broken.append(f"{rel}: {rule} → rc={r.returncode} {r.stderr.strip()}")
    assert not broken, (
        "could not evaluate a grandfather entry — a renamed or deleted file "
        "leaves a stale entry invisible (ticket 0590):\n  " + "\n  ".join(broken)
    )
    assert not stale, (
        "stale .ruff.toml grandfather entries — the file is clean, so the "
        "entry only holds a hole open for future violations of that rule. "
        "Remove it (ticket 0590):\n  " + "\n  ".join(stale)
    )
