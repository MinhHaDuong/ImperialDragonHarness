---
name: feedback-a-move-can-leave-the-gate
description: "A hand-listed gate scope fails asymmetrically: guarding it against a file leaving is easy and feels complete, and it leaves a file ARRIVING entirely unguarded"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 51ae61d2-1e06-4fcf-97e1-66b572d68709
  modified: 2026-08-29T11:55:49.335Z
---

On PR 33 (2026-08-29) a convention landed mid-flight registering
`verification/probes/` for platform-probe scripts, so `sdt_read.py` moved there
from `bench/`. `make lint` runs `ruff check … bench/ tests/`, a hand-written
directory list. The move took the file **out of the lint gate** and nothing
failed, because the file was clean — the gate simply stopped looking. A probe
script already sitting in that directory had been unlinted the whole time.

**Why:** a gate scoped by a directory list has no way to notice a file that left
its scope. Its output is identical whether it examined the file and approved it
or never saw it, which is the "all-clear indistinguishable from I-could-not-look"
shape the harness rules already name — here arriving one level up, at *which
files are in scope* rather than *what the check says about them*. A `git mv` is
the cheapest way to trigger it, and a green build is its cover.

**The asymmetry, found 2026-08-29 on ticket 0053.** Guarding a scope list
against *removal* is easy, and it feels like the job is done. I wrote
`check_governance.py` with a hand-listed `SCANNED`, gave it a loud
`MISSING DOCUMENT` failure, tested that path, and watched it fire — a guard that
cannot be silenced by a document vanishing. It is silent when a document
**appears**. The same day, `bench/check_figures.py` sat one directory away
carrying a comment about the exact same defect in the removal direction, which
is what made me guard removal and stop there. Ticket 0051 will add
`spec/TERMINOLOGY.md` straight into the blind spot; filed as 0221.

**Why the addition direction hides better:** removal has an event you can
picture — you moved the file, so you can ask what stopped seeing it. Addition
has no event at the gate at all. Nobody edits the guard when writing a new
document, so there is no moment at which the question arises, and every run
stays green. Guarding removal also *inoculates*: the loud failure is evidence
the scope list works, so the list stops being suspect.

**How to apply:** after moving a file between directories, grep the build and CI
config for the old directory and ask which gates enumerate directories by hand —
lint targets, test paths, coverage includes, figure-guard maps, packaging
manifests. Fix scope in the same commit as the move. And when you write a gate
whose scope is a list, invert the default: discover candidates from the tree and
require every one to be either covered or explicitly excused, so adding a file
forces a decision instead of defaulting to silence. Test both directions —
delete a covered file AND plant a new one; a suite that only does the first
certifies half a gate. When adding a new
top-level directory for code, add it to the gates before putting anything in
it. The general check on a directory-scoped gate: does it fail if you plant a
deliberately broken file in each directory it claims to cover? Same family as
[[feedback-guard-the-silent-failure-first]]; the repo-side instance of the
figure guard not scanning `CONSTRAINTS.md` is ticket 0161.

**Resolved 2026-08-29, and the prediction above was right twice over.** Raid
50/52/54 closed 0221. `spec/FIELD-REVIEW.md` had indeed been sitting outside
`check_governance.py`'s `SCANNED` — 114 kB of public prose, unguarded, and
nobody noticed until a ticket went looking for something else. And
`spec/TERMINOLOGY.md` landed on main *while the new chain-dedup guard was being
written*, straight into that guard's brand-new hand-written list. Two arrivals,
one session, one of them into a hole created the same day.

**The fix that worked, in both guards:** a `COVERED_GLOBS` / `untriaged()` pair
— glob the real tree, subtract `SCANNED ∪ OUT_OF_SCOPE`, and fail on the
remainder with "add it to one of them". The `OUT_OF_SCOPE` list ships **empty**
in one of the two guards and exists anyway; that is the point, since its job is
to force a decision, not to record one. Cost: about twelve lines and one
`glob`. Tested in the direction that hides — plant a new document, assert red —
because the removal test was already there and had never been the problem.

**The generalisable inversion:** never let a gate's scope be a list that only
grows by someone remembering. Derive the candidate set from the tree, and make
every candidate either covered or explicitly excused. Then adding a file forces
a one-line decision at the only moment anyone has the context to make it.

**One level down, 2026-08-29 (roar sweep after the spec/README.md work).** The
inversion above fixes a scope made of *files*, because a tree can be globbed.
It does nothing for a scope made of *declarations inside a guard*, and that is
the same defect with no tree to enumerate. Measured, not reasoned: deleting one
entry from `check_figures.py`'s hand-written `FIGURES` moved the report from
183 pairs to 181 and the guard still exited 0. That guard's own docstring
narrates the identical event — archiving ticket 0008 dropped 23 declarations,
coverage fell 68 → 45, "and nothing failed" — and the repair made then fixed
that one *cause* (a ticket path that moves on close) while leaving the class
open for months. Filed as ticket 0420.

The discriminator is where a guard gets its scope, and it splits three ways:
**derived** cannot shrink quietly (`check_normative` reads its R-items from
REQUIREMENTS.md; `check_progress` reads coverage from the sheet rather than
from the page it guards — losing one means the source lost it, which is loud);
**hand-maintained** shrinks in silence; and a **zero-floor is not a ratchet** —
`check_terminology` fails on an empty glossary and passes at 45 → 3.

**The fix when nothing can be globbed: ratchet the coverage count.** Record the
expected number where the guard reads it, fail when the live count falls below,
let it rise freely. An equality would make every new declaration a two-place
edit, and a gate people route around is worse than none.

**Same family, third instance, same session:** a check only sees what parses,
so a malformed entry is *invisible rather than wrong*, and the guard then emits
the all-clear it would emit if the entry were absent. `check_progress.py`
carried it twice — a summary row left in superseded glyphs after a vocabulary
change, and a standing row missing a column — each found only because a fixture
test mutated a row into the broken shape and the guard went green on the
mutation. Remedy: assert that every line which *opens* like a row parses as
one, and that every section is accounted for by name. Write that check when you
write the parser, not after the vocabulary changes under it.
