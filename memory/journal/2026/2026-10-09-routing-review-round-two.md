# Routing review round two, ticket 1071 (2026-10-09)

Continues [review round and host hygiene](2026-10-09-routing-review-round-and-host-hygiene.md). PRs #1337 (rules, profiles, ticket log) and #1338 (route and review skills), merged 2026-10-09 through `/raid 1071`.

## Observed
- The raid skipped Imagine, Plan and Verify (the ticket body was the plan) and launched one `coder` on `opus` that ran `/hunt 1071`. It ran the seats itself: a `gpt-6.1-sol` seat through `codex exec` (header read `model: gpt-6.1-sol`, 62,753 tokens, subscription), Opus seats for contradiction, prompt level and the mechanical suite, Sonnet seats for efficiency, traces, open gaps and memory.
- Resident context (AGENTS.md plus always-loaded rules): 20,298 B before #1286, 19,476 B after, 19,532 B on main before this round, 19,043 B with #1337.
- Launch line written before 4 of 154 traced launches (2.6%), all in the 1071 session; about 98% of launches pin the model. No script reads `~/.codex/sessions`.
- Suite on main before the fixes: padme 1556 passed, 3 skipped; doudou 1546 passed, 2 failed (ruff missing, uv not installed there), 11 skipped; secretless box (`env -i`, network cut) 1 failed (`tests/test_zotero_import.py` network test, fixed in #1337). After rebase `make check` on padme: 1556 passed, 3 skipped, also on merged main.
- Codex `fork_turns` "all": 109 `spawn_agent` calls, 46 with a model override (recount by the #1338 gate matched); whether the override is honoured under "all" is not measured. Pi `reviewer` and `planner` ran; `code-reviewer` never did.
- Both `/gaze` runs were inline substitutions by the forked skill, not agent batteries: #1337 one inline reviewer pass, #1338 one combined review seat plus the adherence pass. Both verdicts say `panel integrity: DEGRADED`, APPROVED at tips `140108fd` and `c11fb0d9`.
- Both PR bodies first carried `**Ticket:** 1071 (part N of 2 ...)`, which the merge helper's grammar does not read; the orchestrator rewrote them to `Ticket-ref:` (#1338) and a canonical `**Ticket:**` path (#1337) and read them back before merging, #1338 first.

## Outcome
- Ticket 1071 closed by #1337. No new tickets were opened. Findings recorded as accepted: remaining prompt-level duplicates, `adapters/pi/agents/code-reviewer.md:5` model pin (seats disagreed), the launch-line rate, Codex trace ingestion, the 1070 adherence criterion met by rule text only, subagent-levers note missing the `fable` token.
- Gate non-blockers left unfixed: five `profiles/*/PROFILE.md` line 4 still say "both guards"; `tests/test_guards_rule.py:35` comment; the zotero test skips on `URLError` only.

## Attribution capture
Review attribution records for #1337 and #1338 were not written: the gate comments do not name the reviewer models, and the fork transcripts do not carry verbatim provider ids. Pending capture failure, missing fact: reviewer and writer model ids.
