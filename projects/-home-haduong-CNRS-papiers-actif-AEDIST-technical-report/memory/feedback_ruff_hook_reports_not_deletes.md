---
name: feedback_ruff_hook_reports_not_deletes
description: "The global ruff post-edit hook now reports (not deletes/rewrites) F401/I001/UP — the import-in-same-Edit workaround is hygiene, no longer trap-avoidance"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d9b81d4e-10df-4c13-976b-36187baec21d
---

The global PostToolUse hook `~/.claude/scripts/lint-on-edit.sh` runs
`ruff check --fix --unfixable F401,I001,UP` (ImperialDragonHarness PR #401,
2026-06-16). F401 (unused import), I001 (import sort), and UP (pyupgrade
body rewrites: `List[str]`→`list[str]`, `Optional`→`| None`, `.format`→
f-string) are still **reported** but never auto-applied — so the hook no
longer mutates a `.py` file between two of an agent's Edits.

**Why:** Those three autofixes were a "swordfight" trap: the agent adds an
`import X` in Edit 1 and its usage in Edit 2; the hook fired in between and
deleted/reordered/rewrote the code, leaving the next Edit's `old_string`
stale → NameError or failed Edit → re-add → repeat (token waste). A sweep of
621 transcripts found the pattern in 19 sessions. F841 stays fixable (its fix
is unsafe, never fires without `--unsafe-fixes`); whitespace/E-class fixes
stay on (they never desync).

**How to apply:** The AEDIST rule "import + first usage go in the same Edit,
always" (`.claude/rules/workflow.md` § *Ruff post-edit hook strips unused
imports*) is now **good hygiene, not trap-avoidance** — a split import/usage
across Edits will no longer be silently broken by the hook; ruff just reports
it and the agent finishes the usage. That rule doc is stale and worth
relaxing/updating. Guard: `tests/test_lint_on_edit.sh` in IDH ratchets the
three codes into `--unfixable`. See [[feedback_no_typo_callouts]] for the
broader "fix the tool, not the workaround" instinct.
