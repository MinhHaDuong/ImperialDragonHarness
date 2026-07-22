---
name: feedback-erg-close-archive-staging-order
description: "manual erg close+archive needs a SECOND git add -u after erg archive runs, or the physical deletion of the old path never gets staged"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 4416da70-2381-4a58-904a-29125c1a1dde
---

The manual close+archive recipe (`rules/git.md`) already warns: run
`git add -u tickets/` BEFORE `erg archive` moves the file, or the commit
carries the rename with the pre-edit blob and drops the `Closed:` header.
That's necessary but not sufficient — `erg archive` physically moves the
file (creates it at `tickets/closed/<name>`, deletes it from the old path)
*after* that first `git add -u` runs, so the deletion of the OLD path is
never staged unless you run `git add -u tickets/` a **second time** after
the archive step (or `git rm` the old path explicitly).

**Why:** on 2026-07-15 (ticket 0264 close, PR #1044) this left a stale
tracked-but-absent blob on `main` at the pre-archive path
(`tickets/0264-....erg`) alongside the correctly archived
`tickets/closed/0264-....erg` — invisible in `git status` after the commit,
only surfaced later when a sibling branch's merge-base tree still showed
the old path. The pre-commit hook actually printed a warning at commit
time (`cannot open tickets/0264-...: No such file`) and it was misread as
benign. Fixed in PR #1046 with `git rm --cached`.

**How to apply:** the close+archive sequence is:
```bash
tickets/erg close <ID> <reason>
git add -u tickets/                                    # stage the Closed: header edit
tickets/erg archive tickets/ | sed -n 's#^ARCHIVED #tickets/closed/#p' | xargs -r git add --
git add -u tickets/                                    # stage the deletion of the OLD path — easy to skip
git status --porcelain tickets/                          # verify: no bare M/D at the old path, only the closed/ add
git commit ...
```
Never dismiss a pre-commit hook's "cannot open <file>" warning during a
ticket close as benign without checking `git status` for a stray
tracked-but-absent path first.
