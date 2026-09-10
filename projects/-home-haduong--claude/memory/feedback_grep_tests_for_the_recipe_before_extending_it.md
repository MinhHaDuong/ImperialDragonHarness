---
name: feedback_grep_tests_for_the_recipe_before_extending_it
description: "Before adding a line to a documented shell recipe, grep tests/ for the recipe's own strings — a ratchet file may already pin it, and the new line silently escapes coverage"
metadata:
  type: feedback
---

`/roar` step 10's branch sweep gained a fifth guard on 2026-09-10, and its prose
was updated from "Four lines are load-bearing" to "Five". The commit shipped no
test. A Sonnet reviewer on PR #860 found `tests/test_branch_cleanup_recipes.py`,
which already string-match-ratchets the four existing guards — one test each,
extracting the fenced block through a `cleanup_recipe()` helper. The fifth line
would have sat outside coverage from birth, in a file whose entire purpose is
preventing exactly that.

**Why:** these ratchets are invisible from the file being edited. Nothing in
`skills/roar/SKILL.md` says a test pins its shell blocks, and the test file is
named for the *defect* (`branch_cleanup_recipes`) rather than for the skill, so
neither the path nor the skill's own text leads you to it. The prose counter
("Four lines are load-bearing") is the tell that coverage exists somewhere, and
incrementing it is the moment to look.

**How to apply:** before extending a documented recipe, grep `tests/` for a
literal string from the recipe body — `git branch -D "$b"`, a flag name, the
block's distinctive comment — not for the skill's name, which matches too much
and returns everything. Then write the ratchet as part of the same commit and
prove it red: extract the recipe from `origin/main`'s copy and confirm the
assertion string is absent there. A ratchet that also passes without its subject
is not coverage. Related: [[feedback_tests_pinning_prompt_prose]] (pinning
narrative prose blocks rewriting; pinning a *guard line* is the case where it is
right), [[feedback_red_step_before_editing_callers]].
