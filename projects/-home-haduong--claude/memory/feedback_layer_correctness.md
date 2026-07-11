---
name: layer correctness — harness vs consumer project
description: When designing IDH skills/tickets, keep harness generic; project-specific pain (pytest commands, PR numbers, body conventions) belongs in the consumer repo.
type: feedback
originSessionId: de328483-9e54-44dc-a2ec-5bb34ca10ef1
---
IDH skills and tickets must stay project-agnostic. Consumer-project
reflection memos (e.g. from Climate_finance PR 691/692) often drive
IDH ticket creation, but the fix should expose an extension point in
the harness — never bake consumer assumptions (`uv run pytest`,
PR-body patterns, hard-coded paths) into `skills/*/SKILL.md` or IDH
ticket bodies.

**Why:** user pushed back firmly on two instances in one session.
Tickets 0001, 0002, 0003, 0006 were all carved out of IDH after
leaking project pain upstream. User's phrasing: *"What's that doing
in IDH repo?"*

**How to apply:** when drafting an IDH ticket, ask "is every line
here true for any project using this harness?" If not, split: keep
the generic piece in IDH (extension point, hook, interface), file the
specific piece in the consumer repo. See IDH ticket 0016 for the
standing guard work filed as the class-level regression test.
