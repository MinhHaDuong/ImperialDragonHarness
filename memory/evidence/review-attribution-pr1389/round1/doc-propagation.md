# Doc-propagation review: PR1389 at HEAD 00c5a33

**Scope:** the twelve changed paths in the supplied diff, judged against the original ticket exit criteria. I read the diff and the embedded transcript extracts. I ran no commands and changed nothing. Items marked "not run" need a live check.

## Findings

### 1. Frozen loaded-skill source does not match its recorded hash (blocking)

- `docs/adherence-semantic/evidence.json:6` (`loaded_skill.source`) quotes the superseded skill text: "Enforce the project's declared rules on a branch or **PR**", and the verdict placeholders `<.claude/rules/foo.md#section>` and `<.claude/rules/architecture.md#phase-2-rule-4>`.
- `skills/verify-adherence/SKILL.md:29` in the final tree reads "...on a branch or **merge request**". Its verdict block uses `<project-rule-path#section>`.
- The same `evidence.json` declares `loaded_skill.sha256` = `e457cd8e…`, which is the final file's hash. The transcript's read of the earlier file hashed to `4435caf5…` (`outer.jsonl`, ordinal 143). The read of the final file hashed to `e457cd8e…` (ordinal 395).
- So the stored source text is the pre-fix snapshot, and the hash field is the post-fix file.
- `tests/test_verify_adherence_semantic.py:26` asserts `loaded_skill.sha256 == sha256(source)`. If the source text is as quoted, that assertion fails. The stored green output (`development_check_output`, stage green, 8 passed in this file) cannot then be current.
- The ticket and doc both say the frozen record proves "the exact skill hash". This artifact does not.
- **Needed:** replace the source with the final `SKILL.md` bytes, or correct the hash field, then re-run `tests/test_verify_adherence_semantic.py` and store fresh output.
- Confidence: high that the text and hash disagree (verifiable from the diff). Medium on the test outcome, because it was not run.

### 2. The live run does not exercise phase-3 rule discovery (medium, reproducible evidence)

- Ticket defect: phase 3 "still misses the harness rules/ tree." Ticket acceptance: "invoke the complete skill with branch/worktree only."
- The stored accepted worker prompt (`worker.jsonl`, `accepted_worker_prompt`) hard-codes the rule universe: "Complete rule universe is AGENTS.md and rules/worktrees.md; no other instruction or rule files exist."
- The outer session ran `make syntax`, `git show main:…`, and built the prompt with a Python script (`outer.jsonl`, ordinals 404–413). It did not run discovery as the skill defines it.
- `docs/2026-10-14-adherence-semantic.md` ("Execution and limits") calls this a complete invocation of the complete modified skill. That wording overstates what was tested.
- **Needed:** say in the doc that the outer assembled the prompt and rule list by hand. Or run a fixture where discovery happens inside the skill's own procedure.

### 3. Route claim not visible in stored evidence (consider)

- `evidence.json` `accepted_run.semantic_review.route` reads "loaded route grid economical cluster".
- The `outer.jsonl` extract has ordinal gaps and no read of `skills/route/` is visible. Absence in an extract is not proof, but the stored record does not support the claim.

### 4. Base and head SHAs belong to a disposable fixture repo (consider)

- `base e89dda96…` and `head e6b36baf…` come from `/tmp/idh-1080-live-final`, a fixture repo built by the reproduce recipe. Neither SHA appears in this PR's recent history.
- The doc does not say so. Rebuilding the fixture yields different SHAs.

### 5. Ticket closure is attributed to a human before merge (reproducible evidence)

- `tickets/closed/1080-…erg:9` logs "2026-10-14T08:47Z Minh Ha-Duong closed — implemented". The agent wrote this line in a branch commit before the PR merged, and nothing in the PR shows that action.
- All exit-criteria boxes are ticked while the ticket's own Test section says the evidence "proves this run only".
- **Needed:** leave closure to the normal close-claim path, or make the log entry say the closure is pending merge.

### 6. Recorded gate does not match the ticket's pre-PR gate (reproducible evidence)

- Ticket Feasibility baseline is full `make check` (1577 passed). Ticket action 4 asks for "the normal pre-PR project gate."
- The doc's Verification section records only `make check-fast` (945 passed) and `make lint` (185 passed).
- `make check-fast` deselects 645 tests marked integration or slow, and `make lint` runs only the `adherence` marker. No recorded run covers those 645.
- **Needed:** run `make check`, or state which scoped gate was chosen and why.

### 7. Evidence file labels overstate provenance (consider)

- `outer.jsonl` is described as "sanitized native execution extracts." It also contains hand-written kinds: `validation_correction`, `selfgate_disposition_correction`, and `development_check_output`. The last cites `/tmp/idh-1080-*.txt` files that are not in the repo.
- Relabel these records as annotations.

### 8. Test assertions are weaker than the docstring implies (consider)

- The module docstring says "the separate live acceptance proves execution." Nothing in the repo re-checks the live run.
- `test_frozen_live_acceptance_record` checks that `"blocking"` appears as a substring of the raw result text. That passes for any text containing the word.

### 9. Stale phase-3 heading (consider)

- `SKILL.md` still titles phase 3 "Semantic subagent (fallback only)" while the new text says it is "required whenever" a rule file changes. Retitle the section, or add one sentence reconciling the two.

### 10. Suggested test for the blocking finding is not usable as written (consider)

- The accepted finding's `suggested_test` is a grep. `verdict.json` notes that this grep would match the rule's own quoted predicate. The doc says the behavioral test is the usable proposal.
- The ratchet discipline needs a usable suggestion, so the record should say which one the follow-up ticket should use.

### 11. Checked and consistent (nofollow)

- Prompt and stdout SHA-256 values in `worker.jsonl` match the transcript: `0d177cd2…`, `6a7d005e…`, `921ce7f6…`, `dbb9f1e2…`, `7bd228f4…`.
- Worker cost ($0.00469613) and duration (16.648 s) match.
- The `worktrees.md` line-7 correction is confirmed by the transcript.
- The red and green counts match the recorded check output.
- The skill hash `e457cd8e…` matches the transcript's read of the final file.
- "Sol 6.1" is a gloss on the observed `gpt-6.1-sol`. Treat as nofollow.

## Verdict

**request-changes.** Finding 1 is a blocker: the frozen evidence the PR calls proof does not correspond to its recorded hash. Findings 2, 5, and 6 should be corrected in the same pass. Findings 3, 4, and 7–10 are nonblockers.