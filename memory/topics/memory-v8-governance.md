# Architecture: the memory system

Scope: repository memory and runtime access, checked 2026-11-10.
Authority: the Smelt skill and `rules/guards.md`.

## Current guidance

- The as-built description of the system (stores, lifecycle, budgets, delivery per runtime, gaps, open design questions) is [the blueprint](../../design/memory-v8/README.md); this page keeps only what a session acts on beyond it.
- Fifth accepted smelt PR #2049 closed 1349 [accepted]; sixth accepted PR #2197 is the size baseline; seventh accepted PR #2263. Interrupted trial pass 3 and unmerged hoard PR #1975 remain unaccepted. A retirement citation is intentionally still listed on rerun [followup]; migration refuses an untracked or edited prompt [prompt].
- Native auto-memory stays by author choice (1350 option b). Nomination is for Brood, without destination, section or wording; promotion discussion needs a separate explicit request (1461/PR 2259) [brood]. The [User rulings][source1] register preserves contextual decisions and author edits.
- Native stores of v8 projects were pruned on both hosts on 2026-11-09 (1481: 265 notes on padme, 354 on doudou), each note deleted only when its blob was reachable from a repository and a project page disposed of it; audience-excluded notes stay. Native stores do not sync between hosts. Review at each project's next smelt or by 2026-11-23: regrowth reopens R4 of the 2026-10-29 audit [1481].
- The harness no longer tracks `projects/` (1480: 1,085 native copies of 44 projects); nothing moved into `memory/`. Those notes' only backup is the public history; a history scrub would void it and is the author's call [632b][1481].
- Archiving a ticket moves its file: before a close, grep `memory/` and `design/` for its open path and run `tests/test_memory_v8_pilot.py` (1506) [morn].
- Attribution capture is `attribution_record.py --capture-pr N` or `--capture-unit`; merge-commit capture was closed by the author [capture]. Failed-output retention landed as 1464; 1465 closed by the author's ruling 2026-11-10, to be re-filed when a consumer needs it [morn].

## Hazards

- Naming a path is not reading it: the 1346 census corrected 77% to 25% for Codex; Claude reads repo memory in 1/148 padme and 0/5 doudou sessions [census].
- A planted contradicting native note reached every probed runtime: Claude flagged it, Codex adopted it [trial]. Native-store figures (41% working rules, 52% uncaptured knowledge) are dated audit results.
- Capture writes nothing when gaze notes carry no `reviewer:` line or no `writer:` was recorded, and has marked `adopted:` wrongly both ways; read a record against the commits before trusting it [2365][2397]. Missing evidence stays unknown.

## Open questions

- Ticket 1443 closed 2026-11-10 as a parking decision; its questions live in the blueprint's Open design questions, deferred until the author reopens the design [2442]. The verbatim-journal comparison (95/180 vs 89/180, p=.52) remains inconclusive (1354). Append-in-place remains unresolved.

## Sources

- [Design and boundaries](../journal/2026/2026-10-01-memory-v8-design-and-boundaries.md), [helper retirement](../journal/2026/2026-10-01-memory-helper-retirement.md), [registration review](../journal/2026/2026-10-01-portable-registration-review.md), [PR 1102 merge](../journal/2026/2026-10-02-memory-v8-merge-under-parallel-housekeeping.md), [pilot](../journal/2026/2026-10-02-memory-v8-pilot-established.md), [0909 close](../journal/2026/2026-10-02-orchestrated-raid-closes-memory-v8-tracker.md)
- Trial: [link catch](../journal/2026/2026-10-02-memory-v8-0918-post-merge-link-catch.md), [withdrawal](../journal/2026/2026-10-02-memory-v8-0918-withdrawn-claim-local-gate-cause.md), [correction](../journal/2026/2026-10-02-memory-v8-0918-correction-link-catch-was-pre-merge.md), [detached flags](../journal/2026/2026-10-02-memory-v8-0918-detached-flags-consume-positional-prompt.md), [concurrent sessions](../journal/2026/2026-10-02-memory-v8-0918-concurrent-detached-claude-sessions.md), [no cwd](../journal/2026/2026-10-02-memory-v8-0918-background-launch-without-cwd.md), [Claude contradiction](../journal/2026/2026-10-02-memory-v8-0918-claude-surfaced-planted-contradiction.md), [misattribution](../journal/2026/2026-10-02-memory-v8-0918-correction-worktree-guard-misattribution.md), [step-6 conflict](../journal/2026/2026-10-02-worktree-guard-guidance-conflict-step6.md), Codex [read-index](../journal/2026/2026-10-02-memory-v8-0918-missing-read-index.md), [slug](../journal/2026/2026-10-02-memory-v8-0918-smoke-slug-collision.md), [loading](../journal/2026/2026-10-02-memory-v8-0918-instruction-loading-evidence.md); Claude [CLAUDE.md](../journal/2026/2026-10-02-untracked-claude-md-contradicts-memory.md), [read-index](../journal/2026/2026-10-02-retired-read-index-invoked-in-trial.md), [slug](../journal/2026/2026-10-02-capture-slug-collision-refused.md), [clone](../journal/2026/2026-10-02-trial-clone-carries-prior-session-entries.md); Vibe [read-index](../journal/2026/2026-10-02-t0918-trial-read-index-helper-absent.md), [slug](../journal/2026/2026-10-02-t0918-trial-smoke-slug-collision.md), [injection](../journal/2026/2026-10-02-t0918-trial-vibe-native-agents-injection.md), [aborted](../journal/2026/2026-10-02-skills-dream-read-index-not-found.md); Pi [credits](../journal/2026/2026-10-02-memory-v8-0918-pi-leg-interrupted-credit-depletion.md), [AGENTS.md](../journal/2026/2026-10-02-memory-v8-0918-pi-loaded-agents-not-planted-claude-md.md), [native load](../journal/2026/2026-10-02-memory-v8-0918-pi-native-load-delivered-contradictory-note.md); smokes [0923](../journal/2026/2026-10-02-memory-v8-smoke.md), [0924](../journal/2026/2026-10-02-memory-v8-runtimes-verified.md)
- [Brood adoption](../journal/2026/2026-10-05-brood-adoption-pr1187.md), [raid 926](../journal/2026/2026-10-05-raid-926-supersession-and-publication.md), [0913 close](../journal/2026/2026-10-06-0913-dispatch-close-path.md), [legacy import](../journal/2026/2026-10-09-import-2026-09-29-relocation-lessons.md), [index budget](../journal/2026/2026-10-10-permissions-allow-all-and-idh-install-sync.md), [roar survey](../journal/2026/2026-10-11-roar-clear-verdict-survey.md)
- Backfill [34](../journal/2026/2026-10-08-haiku55-arm-n-integration.md), [65](../journal/2026/2026-10-12-local-ci-wrap-up-inefficiency.md), [69](../journal/2026/2026-10-13-pr1374-author-scope-revision-and-merge.md); [third consolidation](../journal/2026/2026-10-13-third-dream-index-duplication-and-merge.md), [path migration](../journal/2026/2026-10-15-hoard-path-migration.md), [1101 checkpoint](../journal/2026/2026-10-15-raid-1101-1103-1104-integration-pending-attribution.md), [fourth hoard merge](../journal/2026/2026-10-15-fourth-hoard-merge-and-maintenance-fixture.md)
- [Capture one call](../journal/2026/2026-10-27-capture-pr-and-merge-commit-attribution.md), [redesign day](../journal/2026/2026-10-29-memory-redesign-day.md), [raid 0a53b8](../journal/2026/2026-10-29-raid-0a53b8-smelt-census-attribution.md), [2026-10-30 input](../journal/2026/2026-10-30-rulings-and-memory-design-input.md)
- [1349 closed](../journal/2026/2026-10-31-1349-closed-heading-renamed.md), [case-notes design](../journal/2026/2026-10-31-skill-case-notes-design.md), [raid 3d5ae7](../journal/2026/2026-10-31-raid-3d5ae7-skill-case-notes.md), [raid 1f0534 late merges](../journal/2026/2026-11-01-raid-1f0534-late-merges.md), [raid 829e9e](../journal/2026/2026-11-09-raid-829e9e-native-store-prune.md), [rollout session](../journal/2026/2026-11-09-erg-claims-rollout-session.md)
- Design: [audit](../../design/2026-10-29-memory-system-audit.md), [pilot](../../design/memory-v8/pilot.md), [protocol](../../design/memory-v8/evaluation-protocol.md), [results](../../design/memory-v8/evaluation-results.md), [legacy retirement](../../design/memory-v8/legacy-retirement.md), [brood evaluation](../../design/memory-v8/brood-evaluation.md), [inventory](../../design/memory-v8/source-inventory.md), [case notes](../../design/2026-10-31-skill-case-notes.md)
[census]: ../journal/2026/2026-10-29-raid-0a53b8-smelt-census-attribution.md
[capture]: ../journal/2026/2026-10-27-capture-pr-and-merge-commit-attribution.md
[accepted]: ../journal/2026/2026-10-31-1349-closed-heading-renamed.md
[prompt]: ../journal/2026/2026-11-07-smelt-prompt-folded-into-skill.md
[followup]: ../journal/2026/2026-11-07-smelt-1451-follow-ups-1452.md
[brood]: ../journal/2026/2026-11-07-raid-d35fb4.md
[trial]: ../journal/2026/2026-10-02-memory-v8-0918-claude-surfaced-planted-contradiction.md
[1481]: ../journal/2026/2026-11-09-native-store-prune-1481.md
[632b]: ../journal/2026/2026-11-09-raid-632b19-wave2-projects-untrack.md
[morn]: ../journal/2026/2026-11-10-roar-morning-landings-1369-1417-1465-1504-1505-1506.md
[2365]: ../journal/2026/2026-11-10-roar-pr2365-context-length-design-note.md
[2397]: ../journal/2026/2026-11-10-roar-pr2397-audit-names-runtimes-read.md
[2442]: ../journal/2026/2026-11-10-pr2442-gate-needs-author-on-conversation-ruling.md
- Superseded identity limit, in its episode: [PR 2217](../journal/2026/2026-11-05-pr2217-attribution-capture.md).
- Current dispositions: [1350](../../tickets/closed/1350-settle-the-two-memory-stores-in-claude-c.erg), [1354](../../tickets/closed/1354-memory-outcome-trial-on-dreambench-swe-a.erg), [1377](../../tickets/closed/1377-forward-structured-review-constraints-th.erg), [1443](../../tickets/closed/1443-repenser-la-m-moire-statut-de-premier-ra.erg), [1465](../../tickets/closed/1465-evidence-structured-review-constraints-a.erg), [1480](../../tickets/closed/1480-stop-publishing-per-project-native-memor.erg), [1481](../../tickets/closed/1481-prune-the-native-claude-memory-stores-of.erg).

[source1]: user-rulings.md#on-memory-and-rules

## Fallback
