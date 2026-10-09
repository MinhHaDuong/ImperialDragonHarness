"""CI must verify uv.lock matches pyproject.toml (ticket 1072).

`uv sync --frozen` trusts the lock blindly: a dev dependency added to
pyproject.toml but not re-locked is silently not installed. `--locked` (or an
explicit `uv lock --check`) fails instead. The Makefile keeps `--frozen` so
local runs never rewrite the lock; only CI needs the freshness check.
"""
import re
from pathlib import Path

CI = Path(__file__).resolve().parent.parent / ".github" / "workflows" / "CI.yml"


def test_ci_uv_sync_checks_lock_freshness():
    text = CI.read_text()
    syncs = re.findall(r"^\s*uv sync\b.*$", text, flags=re.M)
    assert syncs, "CI.yml has no `uv sync` step"
    checked = "uv lock --check" in text
    for line in syncs:
        assert checked or "--locked" in line, (
            f"`{line.strip()}` does not verify uv.lock freshness; "
            "use `uv sync --locked` or add `uv lock --check`"
        )
        assert "--frozen" not in line, f"`{line.strip()}` skips the lock check"
