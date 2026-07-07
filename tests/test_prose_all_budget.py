"""rules/prose/_all.md stays terse (ticket 0255).

The file is injected verbatim on the first prose edit of every session, in
every project, and composes with format + doctype + lang bodies under the
hook's MAX_CONTEXT cap (9500 chars). Two ratchets pin the "grow deliberately"
invariant before content grows:

1. Whole-file budget — well under the cap so the other axes fit.
2. One-line entries — every bullet stays a single terse line.
"""

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PROSE_ALL = REPO / "rules" / "prose" / "_all.md"

SIZE_BUDGET = 6000
ENTRY_BUDGET = 260  # chars per bullet line: one-line entries only


def test_prose_all_stays_under_size_budget():
    size = len(PROSE_ALL.read_text(encoding="utf-8"))
    assert size <= SIZE_BUDGET, (
        f"rules/prose/_all.md is {size} chars (> {SIZE_BUDGET}): it is "
        "injected verbatim every prose session and must compose with "
        "doctype/lang bodies under MAX_CONTEXT — trim before growing"
    )


def test_prose_all_entries_are_one_line():
    for i, line in enumerate(PROSE_ALL.read_text(encoding="utf-8").splitlines(), 1):
        if line.startswith("- "):
            assert len(line) <= ENTRY_BUDGET, (
                f"rules/prose/_all.md:{i} bullet is {len(line)} chars "
                f"(> {ENTRY_BUDGET}): entries must stay one terse line each"
            )
