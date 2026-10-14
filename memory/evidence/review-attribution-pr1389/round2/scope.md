# Scope seat: round 2, PR 1389 (anchor 825b1eda)

**Method:** Read-only review of the supplied 12-path diff, ticket, skill, and frozen records. I did not run commands or write files; the collector materializes this stdout as `scope.md`.

**Scope check:** The diff touches exactly the 12 planned paths. `SKILL.md` frontmatter is unchanged (hunks start at lines 26 and 195), and phase 1 declaration discovery is untouched. The repo's real `rules/` is not edited; the fixture copy lives under `tests/fixtures/`. No catalog update is needed because the description line is unchanged. Scope is within the ticket.

**Prior round-1 items, checked against final source:**
- `rules/` substring test: resolved. `tests/test_verify_adherence_semantic.py:14` now asserts "Include existing conventional `rules/`", which appears in `skills/verify-adherence/SKILL.md` phase 3 and is absent from the legacy `.claude/rules/`-only text.
- Fresh-outer claim: resolved. `docs/2026-10-14-adherence-semantic.md` now says "empty-context outer," and `outer.jsonl` records `fork_turns: none` in the `observed_caller_launch` record.
- Worker severity boundary: resolved. `SKILL.md` phase 3 now states the caller "must not create findings, upgrade severity, or supply missing severity."
- Raw caller-plaintext and sanitized-extract provenance: resolved. The annotation is labeled as such in `outer.jsonl`.

**Findings**

1. **Closure chronology and attribution — verifiable (minor), confidence high on the facts.** `tickets/closed/1080-…erg` logs `2026-10-14T08:47Z Minh Ha-Duong closed — implemented` and marks all three exit criteria `[x]`. The accepted run that the ticket cites ("Implementation evidence") is the cold outer at `outer.jsonl` 09:30:03Z–09:32:36Z, about 45 minutes after the closure entry. The closure entry also attributes a human action at a time before the evidence it claims. Closing in the same PR is required by `tickets/AGENTS.md`, so I do not treat closure itself as a blocker (this differs from the scope dissent). Fix: correct the log author/timestamp to the actual actor and time, or let `/merge` apply the close claim at merge.

2. **Private memory in committed evidence — verifiable (minor), confidence high on presence, medium on severity.** `docs/adherence-semantic/outer.jsonl` retains verbatim output of `cat /home/haduong/.agents/rules/guards.md /home/haduong/.agents/memory/MEMORY.md /home/haduong/.agents/RTK.md` (cold ordinal 29, 09:30:32.470Z) and of memory topic files (cold ordinal 44, 09:30:56.733Z). `rg -n "Project memory|MEMORY.md|RTK" docs/adherence-semantic/outer.jsonl` reproduces this. The provenance paragraph in `docs/2026-10-14-adherence-semantic.md` lists omitted classes (account metadata, encrypted reasoning, runtime instructions) but does not disclose this memory content. Fix: redact these outputs, or name them in the provenance paragraph.

3. **Outer read beyond the skill procedure — consider (minor), confidence medium.** The final outer also read route grid and routes JSON, route recommendations, decorrelation doctrine, and memory topics (cold ordinals 25, 29, 40–44). The skill procedure needs `SKILL.md` and the route skill only. The prompt given to the worker contained no defect hint, so the worker-side neutrality holds. However, "empty-context outer" slightly overstates what the outer saw. Consider a sentence stating the extra reads.

4. **Evidence volume against the plan — consider (minor), confidence medium.** The ticket asked for "compact evidence/report artifacts." `evidence.json` embeds a full copy of `SKILL.md` as `loaded_skill.source`, which duplicates a blob already in git; `outer.jsonl` and `worker.jsonl` retain full prompts and tool outputs. The records are useful for audit, so this is not a defect; it is a size deviation from the plan that the author may accept or trim.

**Nofollow**

- The test `test_frozen_live_acceptance_record` checks the stored snapshot's internal hash consistency, not HEAD `SKILL.md`. This is the designed behavior: the frozen record proves only the recorded invocation.

**Verdict:** comment

Blocking scope issues: none. Items 1 and 2 are the fixes I would make before merge; items 3 and 4 are optional.