"""What a session pays outside the rules tree, before the first question.

``tests/test_rules_resident_budget.py`` caps ``rules/**.md``. It asks the right
question and looks at half the answer: the rules tree is one of three blocks the
runtime loads unconditionally, and it is the only one that was ever gated. The
other two grew unmeasured while it was being cut in half.

Measured on ``origin/main``, 2026-09-10, right after the rules tree reached
35 525 chars:

===============================  =======  ==========================
block                            chars    gate before this file
===============================  =======  ==========================
``rules/`` (resident bodies)      35 525  yes, 36 000
``projects/<p>/memory/MEMORY.md`` 26 531  none  (worst of 46)
``CLAUDE.md`` + its ``@`` chain    9 646  none
===============================  =======  ==========================

Growth over the three months to that date: the preamble 1 862 -> 9 646 chars
(x4.3), the harness memory index 5 725 -> 20 759 (x3.6, 21 -> 100 entries). Both
by accretion, one bullet and one entry at a time — the drift the review-cadence
marker in ``rules/README.md`` cannot see, because nothing about a growing file
looks stale.

Two ratchets, same contract as ``RESIDENT_BUDGET``: lowering a number here is
the deliverable of a trimming pass, raising one is a decision to pay more on
every session forever, and it is argued in a ticket rather than edited in.

What these gates do **not** claim to catch:

- The memory ceiling is one number shared by every project index, set just above
  the largest. It stops the worst offender from growing and names the target for
  the next pass; a small index can still triple inside it. A per-file baseline
  would catch that and would also make every legitimate memory write edit this
  test, which is a worse trade.
- Neither gate reads *content*. ``skills/memory/SKILL.md`` caps feedback entries
  at 5 per index and the harness index holds 78; that contradiction is a
  question about what the caps mean, not a byte count, and it is not settled
  here.
"""

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.adherence

REPO = Path(__file__).resolve().parents[1]

# 9646 chars measured 2026-09-10: CLAUDE.md (719) plus the two bodies it pulls
# in, tickets/AGENTS.md (7969) and RTK.md (958). Headroom is thin on purpose, as
# it is for the rules tree: it fits a clarifying sentence, not a section.
PREAMBLE_BUDGET = 9800

# 26531 chars measured 2026-09-10, the aedist-technical-report index at 121
# entries. Every other project sits below it; this is a ceiling on the worst,
# not a baseline per file — see the module docstring.
MEMORY_INDEX_BUDGET = 27000

# The runtime pulls a body into CLAUDE.md for each `@relative/path` on a line of
# its own. Following the chain is the point: a gate that hardcoded the current
# three would stop seeing the block on the day a fourth is added, and an
# all-clear that cannot tell "nothing grew" from "I stopped looking" is not a
# gate.
INCLUDE = re.compile(r"^@(\S+)\s*$", re.MULTILINE)


def preamble_files() -> list[Path]:
    """CLAUDE.md and every body reachable from it through ``@`` includes."""
    root = REPO / "CLAUDE.md"
    seen: list[Path] = []
    pending = [root]
    while pending:
        path = pending.pop(0)
        resolved = path.resolve()
        if not path.is_file() or resolved in {p.resolve() for p in seen}:
            continue
        seen.append(path)
        text = path.read_text(encoding="utf-8")
        for rel in INCLUDE.findall(text):
            pending.append(path.parent / rel)
    return seen


def memory_indexes() -> list[Path]:
    return sorted((REPO / "projects").glob("*/memory/MEMORY.md"))


def test_the_preamble_chain_is_followed():
    """A positive control: the walker must find the includes that exist today.

    Without it, a typo in the regex or a moved CLAUDE.md turns the budget test
    into a check on an empty set, which passes forever and reports nothing.
    """
    found = {p.relative_to(REPO).as_posix() for p in preamble_files()}
    assert "CLAUDE.md" in found, "the preamble walker lost its root"
    assert len(found) > 1, (
        f"the preamble walker followed no `@` include from CLAUDE.md (found "
        f"{found}) — either the include syntax changed or the regex is broken"
    )


def test_preamble_stays_within_budget():
    sizes = {
        p.relative_to(REPO).as_posix(): len(p.read_text(encoding="utf-8"))
        for p in preamble_files()
    }
    total = sum(sizes.values())
    detail = ", ".join(
        f"{name} {size}" for name, size in sorted(sizes.items(), key=lambda kv: -kv[1])
    )
    assert total <= PREAMBLE_BUDGET, (
        f"CLAUDE.md and its `@` chain total {total} chars (> {PREAMBLE_BUDGET}), "
        f"~{total // 4} tokens in every session of every project, on top of the "
        f"rules tree. Sizes: {detail}. Trim a body, or move the procedure to "
        "whoever runs it — raising the budget is a ticket, not an edit."
    )


def test_every_memory_index_stays_within_budget():
    oversize = {
        p.relative_to(REPO).as_posix(): len(p.read_text(encoding="utf-8"))
        for p in memory_indexes()
        if len(p.read_text(encoding="utf-8")) > MEMORY_INDEX_BUDGET
    }
    assert not oversize, (
        f"memory index over {MEMORY_INDEX_BUDGET} chars: {oversize}. The index "
        "is resident in every session of its project and holds one line per "
        "memory — a hook, not a summary. Distil the entries whose lesson is now "
        "a rule, drop what is contradicted, and shorten the hooks; the bodies "
        "they point at are not loaded and cost nothing."
    )
