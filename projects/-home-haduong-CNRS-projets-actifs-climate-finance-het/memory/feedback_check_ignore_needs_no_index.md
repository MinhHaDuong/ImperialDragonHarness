---
name: feedback_check_ignore_needs_no_index
description: "git check-ignore skips paths in the index, so \"not ignored\" on a tracked file proves nothing — use --no-index and fire a positive control"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 78accd55-356d-44d9-b79e-e6471e94c518
  modified: 2026-09-10T09:08:32.734Z
---

`git check-ignore` silently skips any path present in the index. On a **tracked**
file it therefore exits 1 — "not ignored" — regardless of whether a rule matches.
Exit 1 there means "I did not look", not "no rule applies". Pass `--no-index` to
make it answer the question actually asked.

**Why:** on 2026-09-10 this was used to prove that a new class rule
(`deliverables/*/.gitignore`) spared `deliverables/slides-gide/slides-assets/.gitignore`,
a tracked file holding three copyrighted images out of a public repo. The exit 1
looked like proof and was a false negative in the making — the right answer, by
luck, but obtained from a probe that could not have said otherwise. A Sonnet
reviewer flagged the gap; the fix was to re-run with `--no-index` **and** fire a
positive control on `tickets/erg`, a file both tracked and ignored: exit 1
without the flag, `.gitignore:166` with it. Same file, two answers — that is what
makes the instrument trustworthy.

**How to apply:** any time an ignore question is asked about a file that might be
tracked, use `git check-ignore --no-index -v`. Then pick a file known to be both
tracked and ignored and confirm the two modes disagree on it. This is the general
rule from `~/.claude/rules/workflow.md` § Diagnosis discipline — a null result is
not a finding until a positive control has fired — in its cheapest concrete form.
See [[feedback_gitignore_class_rule_depth]].
