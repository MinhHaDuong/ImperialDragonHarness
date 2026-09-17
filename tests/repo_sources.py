"""Where harness code lives — the one walk every adherence guard scans.

Ticket 0531. Two guards landed with the same traversal typed twice (one
importing the other's constants and re-typing the loop beneath them), which
is precisely the divergence-by-duplication those guards exist to forbid.
The walk lives here instead, owned by no single ticket's guard.

Cached: `make lint` runs every adherence guard in one session, and the tree
is ~270 files. One walk, one read, one definition of the surface.
"""

import functools
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# Where harness code lives. adapters/ joined the list when it gained its
# first python (ticket 0802); until then the guard's silence about it could
# not be told from a pass. hooks/ and bin/ host python too (bin/usage-report
# is an extensionless python-shebang program), so a scan limited to scripts/
# and tests/ would miss real consumers. skills/ bundles executable Python too
# (ticket 0950). projects/ stays out intentionally: its Python files are
# user/project memory artifacts, not harness runtime source.
SCAN_DIRS = ("scripts", "tests", "hooks", "bin", "adapters", "skills")

# Mutation-audit samples follow pytest.ini's norecursedirs (ticket 0219).
# Synced skills are external runtime content, not shipped harness source;
# their dependencies belong to their own installers (ticket 0950).
EXCLUDED_DIRS = ("tests/fixtures", "skills/synced")


@functools.lru_cache(maxsize=1)
def source_texts() -> tuple[tuple[str, str], ...]:
    """(repo-relative path, file text) for every readable file under the
    code roots. Undecodable files are skipped: a binary is not a source."""
    out = []
    for dirname in SCAN_DIRS:
        for path in sorted((REPO / dirname).rglob("*")):
            if not path.is_file() or any(
                path.is_relative_to(REPO / excluded) for excluded in EXCLUDED_DIRS
            ):
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            out.append((path.relative_to(REPO).as_posix(), text))
    return tuple(out)
