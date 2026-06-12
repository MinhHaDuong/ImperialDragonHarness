---
name: cleanroom-force-rebuild-test
description: "When asserting a Makefile rule is clean-room (no analysis-pipeline leakage), test with `make -B -n` not just `make -n`. Plain `-n` can pass spuriously when committed artifacts are timestamp-fresh."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a42e00f0-1b22-46b9-8a4f-b9cf581d7ec6
---

Rule: when verifying a writing-side build (`make report`, `make slides`) is
clean-room with respect to the analysis workpackage, always run the dry-run
with `-B` (force rebuild) — not just `make -n`. Both must show zero `uv run`
invocations.

**Why:** Ticket 0352 used `make -n report` as the verification baseline and
the recipe trace looked nearly clean (only 4 uv-run lines, because most
committed artifacts were timestamp-fresh). The advisor flagged that `make -B
-n report` is the actual structural test — and indeed on the slides side,
plain `make -n slides` shows 0 uv-run lines but `make -B -n slides` shows
42, because the prereqs still wire writing-side rules to uv-run recipes.
0345 closed the slides workpackage split based on the weaker `-n` test and
the regression escaped. 0352 caught it via the celebrate sweep using `-B
-n`, leading to follow-up ticket 0370.

**How to apply:** In any Makefile-cleanroom adherence test ([[ticket-0353]]
class guard, [[ticket-0352]]-style per-target tests, and any future
workpackage-split work), assert against both `make -n <target>` AND `make
-B -n <target>`. The new `tests/test_report_build_clean_room.py` does this
explicitly. The class regression in `tests/` should follow the same
pattern. Pattern: `subprocess.run(["make", "-B", "-n", target], ...)` then
`assert not [l for l in stdout if "uv run" in l]`.

**Second incident — same lesson, different application (2026-05-28):**
`tests/test_make_slides_prereqs.py` (introduced by ticket 0367) used
plain `make -n slides` to assert `fig_capability_dag.pdf` appears in
the prereq list. Test passed locally on a clean tree (file missing →
recipe shown) but failed in PR #636's docs-build CI run *after*
`make slides` had built the file (mtime fresh → recipe omitted →
output was just `make: Nothing to be done for 'slides'.`). Fix landed
in PR #636 commit `7d1307a`: switched to `make -B -n slides`. The
state-dependency was missed by /verify on PR #635 because the verify
worktree was clean. The principle generalises beyond clean-room
checks — any `make -n` assertion that depends on a recipe appearing
in stdout is state-dependent unless `-B` is added.
