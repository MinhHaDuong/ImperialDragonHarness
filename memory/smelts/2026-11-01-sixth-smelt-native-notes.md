# Sixth smelt — native notes used (annex)

Date: 2026-11-01. Companion to [the report](2026-11-01-sixth-smelt.md).
Source store: Claude Code auto-memory of the harness, `~/.claude/projects/-home-haduong--agents/memory/`, read 2026-11-01 (39 notes; full listing with proposed dispositions is in the report's triage table). The notes below are the ones whose text this run used, preserved here adapted for this public repository (no credentials; none present). Blob ids of the notes as read are in the report ledger. The notes were read, not edited or drained.

## feedback_dont_idle_on_background (blob f7579ac3, updated 2026-11-01 22:10Z)

Description line: "Never end a turn on a background job while independent work exists; ask the top model (Fable) before EVERY author decision, even ones that look like the author's by right". Body: when a background agent, gaze run or external seat is pending, start every other independent piece of work in the same turn before yielding (author, 2026-10-21: "you end turn and block"). Ask up first for reversible calls; the 2026-11-01 body update scopes this: a call that is the author's by right (scope, money, irreversible) waits for the author per `rules/workflow.md` § Escalation protocol and is never handed to an advisor to settle. Night mode (author, 2026-10-26): "Not to me, it goes to Fable for finishing. You are in night mode autonomous" — reversible escalations go to a Fable agent with a self-contained brief; author-by-right decisions are queued for the morning report. Used for: Commission pinned lines and the exposed contradiction ticketed as 1439 (the description line still carries the unscoped wording; the rule governs).

## feedback_prose_edits_are_on_main (blob 2233661e, updated 2026-11-01 07:19Z)

Description line: "Author edits in the primary checkout; agents land those edits by branch on request; trivial ones the author may commit to main via ALLOW_MAIN_COMMIT=1 git -c idh.mainGuard=warn commit (ruling 2026-11-01, rules/git.md)". Body: now written law (`rules/git.md` § Branch and commit, ticket 1372); worktrees isolate the agents, so the primary checkout is the author's workspace. Both guards refuse a main commit in the primary (pre-commit and the main guard); the override journals as warned. Principle: "every fortification needs a backdoor". Used for: the 1372 resolution (Commission Retired line, git page workspace bullets); proposed disposition in the triage table: delete, in force in `rules/git.md`.

## reference_padme_llm_service (blob f303e369, 2026-10-31)

padme runs a configurable LLM service: default Qwen 3.8 Flash Next on strata, Nemotron 74B on llama.cpp, Gemma also served, each on one or two GPUs; the lineup changes within days — in docs say "the Padmé LLM service" and ask the server what it serves; never hard-code an engine or model. "Local" is never a lineage: a local seat can share the producer's family. (The note's sentence "a local seat is stamped family `Local`" is stale since PR 2093: the family now comes from the served model's grid row.) Used for: runtime-observations padme-service bullet.

## reference_pi_print_stdin (blob 9a14edea, 2026-11-01)

`pi --print` (Pi 1.4.0, padme) blocks on an open stdin: three 300 s timeouts with empty output, first misread as a dead local model; with `</dev/null` the same call returned at once. Run every non-interactive Pi call with stdin closed, and still assert the served provider. Used for: runtime-observations `pi --print` bullet.
