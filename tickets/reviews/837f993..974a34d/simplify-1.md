---
review-evidence: 1
kind: review
seat: simplify
verdict: approve
family: anthropic
worker: claude-sonnet-5-5
base: 837f99369eba180d3680a283a599b18ac974120b
head: 974a34d3cf1f5685702ca49d3cc4cf791446f6bc
patch-id: b1c61de53a1c79b91e8cd46fbe92c18b61011f8c+790dbfe803c22991252028a1dcc30192617752a5
criteria-hash: 16765aa9a3f14bad
policy-version: f78a1b40e2adb3e1
recorded: 2026-10-27T07:52:12Z
---

Re-recorded at the close head: the seat reviewed the PR content at the head named in its report; the only change since is commit 974a34d (ticket 1233 close and archive, merge-gate tier: bookkeeping, 2 ticket paths), which changed the patch-id. Verdict unchanged, not re-run.

Simplify seat on PR #1699, range 40c2d9bdbbb3e58e1038eb5bf4bb310f0a25baae..586fa3f6d4a380ed5510ed3ebd59c11f215a7ce4 (reviewed diff content). Launched by the coder, read-only; worker self-reported as claude-sonnet-5-5. Report verbatim:

Reviewed by claude-sonnet-5-5 (SIMPLIFY seat), read-only. I read the SKILL.md, the four references, `scripts/harness_here.sh`, the `rules/authoring-skills.md` stub and `tests/test_harness_doctor_skill.py`. I did not run the tests.

- **consider (medium):** `skills/harness-doctor/SKILL.md` step 4 repeats rules that `references/runtime-diagnostics.md` already owns. These are the "spends needs the author's agreement and a cost cap" rule and "ships nothing is recorded against the control the reference names". Two copies can drift, and the SKILL's own stance says "Point, do not restate". Cut step 4 to a pointer plus the record format.
- **consider (medium):** `tests/test_harness_doctor_skill.py::test_skill_names_its_references_and_script` only checks that strings appear in SKILL.md, and the `POINTER` regex plus the set-superset check restate the prose. Keep just the two script-path assertions, or drop the test. A missing reference file is a better thing to assert than a mention of it.
- **consider (low):** `test_stub_keeps_paths_and_points_to_reference` checks the stub's `paths` set, the pointer string and that the file exists. The `is_file()` check is the only part with value. The `paths` equality duplicates frontmatter that `tests/test_skill_frontmatter.py` already covers.
- **consider (low):** `skills/harness-doctor/references/evidence.md` is a 10-line file of two pointers. Fold it into SKILL.md or `checklist.md` as one sentence to save a reference file and the `evidence.md` entry in the test's set.
- **nit (high):** The `references/checklist.md` row on SKILL.md length repeats "splitting follows exclusivity, not length", which the authoring guide owns. Keep only "warning over 150 lines; see the guide".
- **nit (medium):** The credentials-never-displayed rule is stated in `references/runtime-diagnostics.md` in the preamble and again in the Pi section, and a third time in `rules/guards.md`. The Pi restatement can shrink to listing the forbidden forms.
- **nit (low):** `scripts/harness_here.sh` is a clean fit. The `common_dir` helper has two uses and no dead text.

VERDICT: approve
