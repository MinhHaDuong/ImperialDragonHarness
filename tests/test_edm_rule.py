"""Fast-tier rule guards for the global EDM rule (ticket 0257).

The EDM (electronic document management) discipline — Zotero is the system of
record; `docs/` and `.bib` are git-ignored staging — is globalized as
`rules/edm.md`. These fast-tier ratchets catch index drift and a missing
cross-reference from `git.md`, mirroring `tests/test_rules_axis_bodies.py`.
"""

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RULES = REPO / "rules"


def test_edm_rule_file_exists():
    assert (RULES / "edm.md").is_file(), (
        "rules/edm.md must exist — the globalized EDM discipline (ticket 0257)"
    )


def test_readme_indexes_edm_rule():
    readme = (RULES / "README.md").read_text(encoding="utf-8")
    assert re.search(r"^\|\s*\[edm\.md\]", readme, re.M), (
        "rules/README.md must carry an index-table row for edm.md — the index "
        "is the single source of truth on when each rule file applies"
    )


def test_git_md_cross_references_edm():
    git_md = (RULES / "git.md").read_text(encoding="utf-8")
    assert "edm.md" in git_md, (
        "rules/git.md must cross-reference edm.md — source-document staging "
        "follows a separate discipline from generated handoff artifacts"
    )
