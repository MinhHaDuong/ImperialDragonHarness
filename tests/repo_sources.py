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

# Where harness code lives. hooks/ and bin/ host python too (bin/usage-report
# is an extensionless python-shebang program), so a scan limited to scripts/
# and tests/ would miss real consumers.
SCAN_DIRS = ("scripts", "tests", "hooks", "bin")

# Mutation-audit sample files, not code this repo runs — same policy as
# pytest.ini's norecursedirs (ticket 0219), stated there for collection and
# here for scanning.
EXCLUDED_ROOT = REPO / "tests" / "fixtures"


@functools.lru_cache(maxsize=1)
def source_texts() -> tuple[tuple[str, str], ...]:
    """(repo-relative path, file text) for every readable file under the
    code roots. Undecodable files are skipped: a binary is not a source."""
    out = []
    for dirname in SCAN_DIRS:
        for path in sorted((REPO / dirname).rglob("*")):
            if not path.is_file() or path.is_relative_to(EXCLUDED_ROOT):
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            out.append((path.relative_to(REPO).as_posix(), text))
    return tuple(out)
