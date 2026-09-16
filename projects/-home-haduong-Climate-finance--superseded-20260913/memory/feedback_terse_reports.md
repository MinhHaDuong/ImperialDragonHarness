---
name: feedback_terse_reports
description: "Author wants short chat reports — findings and decisions only, no restating what the PR body already says"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 5dc4f34f-6be9-445c-ad64-4385a54f11f8
  modified: 2026-07-27T12:38:21.434Z
---

Keep chat responses terse. Report the finding, the decision, and anything
that needs the author's judgment — nothing else.

**Why:** the author reads the PR body and the ticket. Repeating their content
in chat is pure duplication, and it buries the one or two lines that actually
need attention. Told plainly on 2026-07-27 ("Too verbose.") after a
three-paragraph summary of a PR whose body already said the same things.

**How to apply:** when work lands in a PR or ticket, the chat message is a
pointer plus the delta — what surprised me, what I decided against, what is
still unverified. Not a summary of the artifact. Prose rules already forbid
recap endings; this extends the same rule to work reports. Related:
[[feedback_scope_discipline]].
