"""Fast-tier rule guards for the global Zotero-management rule (ticket 0257).

The Zotero-management discipline (formerly "EDM", ticket 0257) — Zotero is the
system of record; `docs/` and `.bib` are git-ignored staging — lives in
`rules/zotero.md`. These fast-tier ratchets catch index drift and a missing
cross-reference from `git.md`, mirroring `tests/test_rules_axis_bodies.py`.
"""

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RULES = REPO / "rules"


def test_zotero_rule_file_exists():
    assert (RULES / "zotero.md").is_file(), (
        "rules/zotero.md must exist — the globalized Zotero-management "
        "discipline (ticket 0257)"
    )


def test_readme_indexes_zotero_rule():
    """zotero.md must stay discoverable from the index.

    Until 2026-09-09 this asserted an index-table *row*. The table now names
    only the conditional rules — the ones an agent does not already have —
    because the runtime loads every unscoped body in full, and describing a
    body it ships is paying for it twice. zotero.md is scoped (`paths:`
    frontmatter), so the index declares it in the conditional table;
    discoverability is unchanged, the duplicate description is gone.
    """
    readme = (RULES / "README.md").read_text(encoding="utf-8")
    assert re.search(r"^\|\s*\[zotero\.md\]", readme, re.M) or "`zotero.md`" in readme, (
        "rules/README.md must name zotero.md — as a conditional-table row if it "
        "gains `paths:` frontmatter, else in the resident list"
    )


def test_git_md_cross_references_zotero():
    git_md = (RULES / "git.md").read_text(encoding="utf-8")
    assert "zotero.md" in git_md, (
        "rules/git.md must cross-reference zotero.md — source-document staging "
        "follows a separate discipline from generated handoff artifacts"
    )
