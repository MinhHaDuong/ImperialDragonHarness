---
name: feedback-line-citations-rot
description: "A file:line citation in a ticket decays at every merge — quote the statement and mark the number perishable, because a handoff document is read against a tree that has moved"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 3cdf4883-8bf7-4ffa-8060-2e328114969d
  modified: 2026-09-15T21:27:07.112Z
---

A ticket is a handoff document read days or weeks later, against a tree that has
moved. A bare `file.js:NNNN` citation in it is a claim whose truth decays with
every merge that touches the file, and nothing announces the decay: the number
still resolves, it just resolves to something else.

**Why:** on 2026-09-15, one site in `plugins/sdt-sitter/bootstrap.js` — the
uninstall write `if (named === 'uninstall' && readSDTSwitch() !== null)
writeSDTSwitch(false);` — was cited as **3548**, **3560** and **3569** within a
single evening, by three readers on three trees, none of them wrong at the
moment they read. A sibling PR merged between the readings and shifted the file.
The same evening's sweep of open tickets found 26 distinct `bootstrap.js:NNNN` /
`scheduler.js:NNNN` citations; a six-item spot check against `origin/main` found
three still exact, one drifted three lines within its block, and one rotted to a
bare `}` — a citation that now says nothing while looking authoritative.

**How to apply:** quote the *statement* — the line of code, the sentence of
prose — and let the number be an aid, written `~3569` or "as of `<sha>`", never
the load-bearing part. Where a symbol exists, cite the symbol: `writeSDTSwitch`
outlives its line number. When a ticket must pin a passage, name the sha the
numbers were read at, so a later reader knows what to diff against instead of
guessing whether the citation or the tree moved. Re-verify every line citation
in a ticket against the tree it will actually be executed on — after a rebase,
not before it.

Distinct from [[feedback_verify_your_own_citations]], which is about re-deriving
a citation from source rather than re-reading your prose: that one catches a
citation that was wrong when written, this one catches a citation that was right
when written and is wrong now. Both were learned the same night, one from a
sibling session's review and one from a gate's.
