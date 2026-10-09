"""CI must verify uv.lock matches pyproject.toml (ticket 1072).

`uv sync --frozen` trusts the lock blindly: a dev dependency added to
pyproject.toml but not re-locked is silently not installed. `--locked` on the executed
`uv sync` line fails instead. The Makefile keeps `--frozen` so
local runs never rewrite the lock; only CI needs the freshness check.
"""
import re
from pathlib import Path

CI = Path(__file__).resolve().parent.parent / ".github" / "workflows" / "CI.yml"


def test_ci_uv_sync_checks_lock_freshness():
    text = CI.read_text()
    syncs = re.findall(r"^\s*uv sync\b.*$", text, flags=re.M)
    assert syncs, "CI.yml has no `uv sync` step"
    for line in syncs:
        assert "--locked" in line, (
            f"`{line.strip()}` does not verify uv.lock freshness; "
            "use `uv sync --locked` (a `uv lock --check` elsewhere, even in "
            "a comment, does not count)"
        )
        assert "--frozen" not in line, f"`{line.strip()}` skips the lock check"
