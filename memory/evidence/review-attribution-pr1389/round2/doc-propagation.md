# Doc-propagation review, round 2 (PR 1389, HEAD 825b1eda)

**Scope and method.** I read only the supplied complete diff, the ticket, the profile and the skill. I did not run tools, recompute hashes, or touch the tree. Where a claim needs a hash or a test run, I say so.

## Prior concerns, checked against the final diff

| Round-1 concern | Status | Evidence |
|---|---|---|
| `rules/` substring test passes legacy text | Resolved | `tests/test_verify_adherence_semantic.py` now requires "Include existing conventional `rules/`". The base SKILL has no such clause. |
| "fresh/neutral" outer overclaimed | Resolved in wording, qualified by B1 | Doc says "empty-context outer seat". `outer.jsonl` line 60 shows `fork_turns: none`, and the warm runs are labeled as warm. |
| Caller messages, identity, discovery and route load missing from extract | Resolved | Identity at `outer.jsonl:61`; caller text at line 59, labeled `caller_plaintext_annotation`; discovery at line 64; route SKILL load at line 65. |
| Native extracts mixed with annotations, provenance unlabeled | Resolved | Typed kinds: `caller_plaintext_annotation`, `validation_correction`, `selfgate_disposition_correction`, `observed_caller_launch`. |
| Validation may reject but may not invent severity or anchors | Resolved | `SKILL.md` phase 3 ("The caller may reject worker findings, but must not create findings…"); doc lines 5–7. |
| Ticket closure chronology | Unchanged, nofollow | See N7. |
| Round-1 dissent: frozen hash ≠ recorded hash | Not supported by this seat | The supplied SKILL text matches the 09:30 cold `cat` at `outer.jsonl:63`, which printed `70146986…`. I did not recompute the hash. The frozen test checks `sha256(source)` against the recorded hash, so a passing `make check-fast` covers that. |

## Findings

**B1: blocker (request-changes). Confidence high on the fact, medium on severity.**
The doc says "User/account metadata, encrypted reasoning and unrelated runtime instructions are omitted" (doc ~lines 75–78). `docs/adherence-semantic/outer.jsonl` does not omit them:
- Line 67 (cold ordinal 29) contains the verbatim contents of `/home/haduong/.agents/rules/guards.md`, `~/.agents/memory/MEMORY.md` and `~/.agents/RTK.md`, plus the user's memory index and host names.
- Line 71 (ordinal 44) contains `~/.agents/memory/topics/subagent-model-effort-levers.md` and `runtime-observations.md`.

The "empty-context" claim (doc line 32) is also incomplete: the cold outer read the user's global memory before producing the verdict.
Fix: remove lines 67 and 71, or replace them with a labeled marker stating which files were read, and correct the omission sentence. Global private memory should not be committed to a project PR.

**N1: consider. Confidence high.**
The retained green evidence does not match the current test module. `outer.jsonl:55` shows `tests/test_verify_adherence_semantic.py ........` (8 passed, 945 total). The current file has 8 parametrized requirements plus `test_frozen_live_acceptance_record` (about `:14–17` and `:26`), so 9 tests. The doc's "then passed after the repair" therefore cites a run that predates the frozen test. Fix: rerun `make check-fast`, retain the output, or label the green record as pre-frozen-test.

**N2: consider. Confidence high.**
The caller was told the expected hash ("expected 70146986…", `outer.jsonl:59`) and the output fields. Doc lines 32–34 and 44–45 say the caller received only "contract loading, neutral branch/worktree and evidence instructions" and was given no expected verdict. Name the expected hash in the doc.

**N3: consider. Confidence medium.**
The reproduction step (doc lines 24–29) says to "append the following line" to `rules/worktrees.md`. The candidate diff adds a blank line first (`+` blank, then `+Apply this rule…`), so following the doc literally gives different bytes. State the blank separator.

**N4: consider. Confidence medium.**
The accepted worker prompt is "retained verbatim" (`worker.jsonl`, `accepted_worker_prompt`), but it has no sha256, unlike the superseded and invalid prompts in the same file. Add one so the verbatim claim can be checked against `/tmp/idh-1080-final-fresh-invocation/worker.prompt.txt`.

**N5: consider. Confidence medium.**
The old phase-3 trigger on `.claude/rules/*.md` may still be described in documents outside this 12-path diff. Run `rg -n '\.claude/rules/\*\.md' skills rules docs profiles adapters` and fix any hits, or record why they are out of scope.

**N6: nofollow. Confidence high.**
`tickets/closed/…erg` line 9 records "Minh Ha-Duong closed — implemented" at 08:47Z, before the 08:55–08:56 acceptance evidence in the same ticket. The git user is Minh Ha-Duong, so this is ordinary `erg close` attribution. Recorded only.

## Verdict

**request-changes**, scoped to B1. Everything else is nonblocking. Once B1 is fixed, the doc's claims about the cold run, the hash chain and the retained records are consistent with the supplied evidence.