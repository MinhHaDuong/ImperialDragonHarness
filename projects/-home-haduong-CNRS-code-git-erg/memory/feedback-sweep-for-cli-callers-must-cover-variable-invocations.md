---
name: feedback-sweep-for-cli-callers-must-cover-variable-invocations
description: "Grepping the literal command name misses `$ERG log` and returns a clean zero — sweep for CLI callers case-insensitively, through variables, and fire a positive control first"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 66e60b89-dd60-41a4-8f88-17567531b19a
  modified: 2026-09-10T10:03:51.902Z
---

A sweep for "who calls this command" that greps the literal name
(`erg log`) misses every invocation through a variable — `$ERG log`,
`"$ERG" log`, `${ERG} log`, `./tickets/erg log` — and reports zero callers.
Shell scripts almost always bind the binary to a variable first, so the literal
form is the rare case, not the common one.

**Why:** the zero is indistinguishable from "there are none". On 2026-09-10 a
literal sweep produced "no callers found" for git-erg's `erg log`, and that
false zero went into PR #334's body as a claim ("in-repo callers were swept").
The positive control is what caught it: re-running the same query against
`tests/test_log.sh` — a caller known to exist — also found nothing, proving the
query blind rather than the field empty. The corrected sweep found two harness
call sites (`~/.claude/skills/reviewers/reviewers.sh:616,776`), and a
decorrelated reviewer independently found two more the corrected sweep still
missed (`tests/test_datasafety.sh`).

**How to apply:** run the positive control **first**, against a caller you
already know exists, and print its result before the real sweep. Use a
case-insensitive pattern that admits a variable prefix, e.g.
`grep -rIniE '[a-z_$"{}/.]*erg["}]* log [0-9$"'"'"'{A-Za-z]'`. Exclude
`*.jsonl` session transcripts and `*.erg` ticket bodies — they quote commands
without calling them, and they dominate the noise. Never put a sweep's zero
into a PR body without having watched the query succeed on a known positive.

Related: [[feedback-bare-gh-pr-merge-drops-close-claim]].
