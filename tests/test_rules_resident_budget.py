"""What the rules tree costs before the first question (ticket 0572).

The runtime loads every ``~/.claude/rules/**.md`` whose frontmatter declares no
``paths:`` into the system prompt of every session, in every project. That set
is a standing tax on every conversation the author has, and on every adapter
that must reproduce it on a runtime without the auto-load (tickets 0800, 0802).

Measured 2026-09-09, before this gate existed: ~39 200 resident tokens per
session, 73% of them this tree. Two ratchets:

1. **Budget** — the resident set may not grow. The review-cadence marker in
   ``rules/README.md`` catches age, not accumulation: a body that gains one
   incident bullet per week keeps a fresh stamp while it doubles. This is the
   half of the drift that a date cannot see.
2. **Declared** — a resident file must be named in the index's resident list,
   so the adapter port has one honest inventory of what it has to ship.

Lowering ``RESIDENT_BUDGET`` is the deliverable of a trimming pass. Raising it
is a decision to pay more on every session, in every project, forever: argue it
in a ticket, as ``.ruff.toml`` suppressions are argued (tickets 0470, 0590).
"""

import re
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.adherence

REPO = Path(__file__).resolve().parents[1]
RULES = REPO / "rules"

sys.path.insert(0, str(REPO / "scripts"))

import skill_frontmatter as sf  # noqa: E402

# 61 876 chars measured 2026-09-09 after the 0572 trimming pass (workflow.md and
# git.md cut by half, skill authoring made conditional, runtime specifics split
# into claude-code.md). Headroom is deliberately thin: it fits a clarifying
# sentence, not a section.
RESIDENT_BUDGET = 63_000

def is_resident(path: Path) -> bool:
    """True when the runtime loads this body unconditionally.

    The rule is the frontmatter's ``paths:`` key: with it the body arrives only
    when a matching file is touched, without it the body is always in context.
    """
    m = sf.FRONTMATTER.match(path.read_text(encoding="utf-8"))
    return not (m and re.search(r"^paths:", m.group(1), re.MULTILINE))


def resident_files() -> list[Path]:
    return sorted(p for p in RULES.rglob("*.md") if is_resident(p))


def test_resident_rules_stay_within_budget():
    sizes = {p.relative_to(RULES): len(p.read_text(encoding="utf-8")) for p in resident_files()}
    total = sum(sizes.values())
    worst = sorted(sizes.items(), key=lambda kv: -kv[1])[:3]
    detail = ", ".join(f"{name} {size}" for name, size in worst)
    assert total <= RESIDENT_BUDGET, (
        f"resident rules total {total} chars (> {RESIDENT_BUDGET}), "
        f"~{total // 4} tokens in every session of every project. "
        f"Biggest: {detail}. Trim a body, or scope one with `paths:` "
        "frontmatter — raising the budget is a ticket, not an edit."
    )


def test_every_resident_file_is_declared_in_the_index():
    index = (RULES / "README.md").read_text(encoding="utf-8")
    section = index.split("## Resident rules", 1)
    assert len(section) == 2, "rules/README.md lost its '## Resident rules' section"
    declared = section[1]
    for path in resident_files():
        rel = path.relative_to(RULES).as_posix()
        if rel == "README.md":
            continue  # the index does not list itself
        assert f"`{rel}`" in declared, (
            f"rules/{rel} is loaded into every session but the index does not "
            "list it under '## Resident rules' — the adapter port reads that "
            "list as its inventory"
        )
