---
name: feedback_rtk_rewrites_grep_output
description: "The rtk Bash hook silently replaces some grep output with a summary, producing plausible wrong counts — re-derive any grep-based tally in Python before trusting it"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e1a2a449-f55d-4143-847e-e015213fee2a
  modified: 2026-07-27T18:46:16.400Z
---

The rtk command-rewriting hook intercepts `grep` and can return a **condensed
summary in place of the matched lines**. The substitution is silent and the
output still looks like grep output, so a count derived from it is wrong in a
way that reads as plausible.

**Why:** during the 0339/0340/0341 raid, an anchored `grep -E` tally of `bump`
log lines across `tickets/` returned 13. Re-running the same logic in Python
returned 3 — the correct answer. Nothing in the shell output flagged a
rewrite. The same trap reproduced at the wrap-up: `grep -n '^class \|def test_'
tests/test_hover_text_escaping.py` returned the header `22 matches in 22 files`
followed by rows of the form `110:0:`, `125:0:` — line numbers with no content,
and a file count of 22 for a single-file argument. Python reported the truth: 3
classes, 19 test functions in that one file.

The precedent for this class is already in `rules/git.md`: the
`git branch -vv | awk '/: gone]/'` pipeline "silently no-ops under rtk output
rewriting", which is why the branch-hygiene loop keys on exit codes instead of
parsed stdout.

**How to apply:**
- **Never let a grep pipeline produce a number you will act on.** Counts,
  tallies, and inventories go through Python (`pathlib` + `re`) or through a
  loop keyed on exit status, not through `grep -c` or `grep | wc -l`.
- **Read the shape of the output, not just the values.** `N matches in N files`
  against a single-file argument, or `line:0:` rows with empty content, means
  the output was rewritten. So does a suspiciously round or suspiciously large
  count.
- `rtk proxy <cmd>` runs the raw command without filtering. Use it when the
  literal output matters and Python would be awkward. This is the same escape
  hatch the pytest-spawn workaround uses.
- Structural inspection of source (classes, functions, imports) is Python work
  anyway — `ast` or a line scan beats an anchored regex and does not depend on
  hook behaviour.

Related: [[feedback_check_the_detector_first]],
[[feedback_assert_on_written_artifact]].
