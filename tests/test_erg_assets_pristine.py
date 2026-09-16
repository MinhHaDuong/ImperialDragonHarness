"""`tickets/` assets must stay byte-identical to what the vendored erg ships.

Ticket 0906: this repo edited `tickets/AGENTS.md` in place for two months, as if
it owned a file that `erg init` writes and `erg migrate` may force-overwrite.
The fork reached 8005 chars against a shipped 2356, and it was resident in every
session of every project.

An equality gate is preferred over a size budget: it makes the drift impossible
rather than merely expensive, and it self-heals after any path that reinstalls
the asset. The reference is `tickets/.erg-assets`, the provenance manifest
`erg init` writes, which records the SHA-256 of each embedded asset. Local lore
belongs in `tickets/LOCAL.md`, which erg never touches.
"""

import hashlib
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
MANIFEST = REPO / "tickets" / ".erg-assets"

ENTRY = re.compile(r"^\s+(?P<name>\S+)\s+sha256:(?P<sha>[0-9a-f]{64})\s*$")


def manifest_entries() -> dict[str, str]:
    assert MANIFEST.is_file(), f"{MANIFEST} missing -- run `./tickets/erg init`"
    out = {}
    for line in MANIFEST.read_text().splitlines():
        m = ENTRY.match(line)
        if m:
            out[m.group("name")] = m.group("sha")
    return out


def test_manifest_lists_the_shipped_assets():
    """Guard the guard: an empty parse would make every check below vacuous."""
    assert set(manifest_entries()) == {"AGENTS.md", ".ergrc"}


@pytest.mark.parametrize("name", ["AGENTS.md", ".ergrc"])
def test_asset_is_pristine(name):
    path = REPO / "tickets" / name
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    expected = manifest_entries()[name]
    assert actual == expected, (
        f"tickets/{name} has diverged from the asset embedded in tickets/erg.\n"
        "Do not edit it: `erg init` writes it and `erg migrate` may overwrite it.\n"
        "Project-specific lore goes in tickets/LOCAL.md; generic conventions are\n"
        "upstream. To restore: `./tickets/erg init --force`."
    )
