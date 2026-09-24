---
name: gate-fork-returns-without-verdict
description: "A forked /verify-gate can return a mid-run progress note as its result with no verdict posted; the PR page, not the fork's return text, says whether a gate happened — read it back before merging, and re-run when empty."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: cee6070c-3acb-4389-866d-46222da655df
  modified: 2026-09-22T18:54:39.019Z
---

On 2026-09-22 (PR #610, a one-file STATE refresh) the `/verify-gate` fork
returned after a few seconds with a paragraph beginning "While `make check`
runs: scope containment is trivial…" and no YAML verdict. `ListAgents` showed
no subagent left; the PR page carried no comment and no review. The fork had
stopped mid-run and its last paragraph was handed back as if it were the
result. A second invocation ran to the end and posted APPROVED.

**Why:** a fork's return text is whatever it last wrote, verdict or not, and
the merge rule in `AGENTS.md` § Merge authority is about the page: a reviewer
that has not reported leaves the PR BLOCKED, and a progress note reads like
a favourable start. Same family as [[verdicts-belong-on-the-forge]] and
[[merge-authority-needs-attached-verdict]]: the fork's prose is a relayed
claim, the page is the record.

**How to apply:** after any gate or review fork returns, read the PR's
comments and reviews back with `gh api` and look for the verdict token
before `erg-pr-merge`. No token on the page means no gate ran, whatever the
return text says; re-invoke the gate rather than inferring from the fragment.
Two of three gates this session posted first time; the check costs one call.
