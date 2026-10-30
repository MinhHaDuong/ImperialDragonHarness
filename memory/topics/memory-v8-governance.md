# Architecture: the memory system

Scope: this repository's project memory (prompt `memory/SMELT.md` v8-r4) and
how runtimes reach it. Checked against the tree 2026-10-30.

## Current guidance

- **Stores.** `memory/journal/YYYY/` is the intact, append-only source;
  corrections are new entries linking the original. Department pages under
  `memory/topics/` are as-built guides to it, 4 KB each, index 40 lines
  (author rulings on 1348, see Commission; [redesign day](../journal/2026/2026-10-29-memory-redesign-day.md)).
  Review-attribution records live in `memory/evidence/attribution/`, outside
  smelt input (PR #2002, [raid 0a53b8](../journal/2026/2026-10-29-raid-0a53b8-smelt-census-attribution.md)).
  Uncleared material is age ciphertext in the repo, key never tracked
  ([pilot](../journal/2026/2026-10-02-memory-v8-pilot-established.md)); none exist today.
- **Pipeline.** Roar captures facts (`skills/roar/runbooks/capture.md`, steps
  2-3, before cleanup) and ends with a `/clear` verdict
  ([survey](../journal/2026/2026-10-11-roar-clear-verdict-survey.md)). Smelt
  rebuilds every page per department and measures net bytes with
  `scripts/memory_sizes.py --before` (1349: this is the first rebuild; it closes on
  author acceptance). Brood is
  explicit-only and has never run on the harness (1351, blocked by 1349)
  ([adoption](../journal/2026/2026-10-05-brood-adoption-pr1187.md)). No stage
  promotes rules; crystallisation needs the author's request (AGENTS.md).
- `skills/dream/` helpers are removed; calling them fails ([retirement](../journal/2026/2026-10-01-memory-helper-retirement.md)).
- **Attribution capture** is one call, `attribution_record.py --capture-pr N`
  (PR #1719); merge-commit storage (1243) was closed by the author
  ([entry](../journal/2026/2026-10-27-capture-pr-and-merge-commit-attribution.md)).

## Hazards

- **Claude Code does not read repository memory.** Census
  (`scripts/census/repo-memory-reads.py`, read operations only, with control):
  Claude main-working 1/148 on padme, 0/5 on doudou; Codex 142/570 on padme
  (ticket 1346 log). The index is not injected at session start
  (`tests/test_on_start_memory_injection.py`). Counting tool calls that merely
  name a path overcounts: the audit's 77 % was 25 % (audit § Correction).
- **Native notes can override silently.** In the 0918 trial a planted
  contradicting note was delivered natively on every runtime probed; Claude
  flagged it, Codex adopted it without signal
  ([Claude](../journal/2026/2026-10-02-memory-v8-0918-claude-surfaced-planted-contradiction.md)).
  Pi loads only the first of `AGENTS.override.md`, `AGENTS.md`, `AGENTS.MD`,
  `CLAUDE.md` per directory, and also delivers a home-level `AGENTS.md`
  ([rerun](../journal/2026/2026-10-02-memory-v8-0918-pi-native-load-delivered-contradictory-note.md); placement intent unverified). Single samples, 2026-10-02 versions.
- **The harness native store** holds rules in disguise (41 %) and knowledge
  the repo never captured (52 %): one coder, padme, 2026-10-29 (ticket 1349).
- **The journal exceeds one context** (723 KB, 2026-10-30): work per department.
- **Attribution capture refuses** two findings at one anchor, fact order
  other than kind, pr, writer, and ticket-only PRs; one writer line per step
  (native note, 2026-10-29).
- Interrupted trial pass 3 and the fifth hoard (PR #1975, closed unmerged)
  are not accepted processing.

## Open questions

- Which store Claude Code uses (1350: off, list per smelt, or restore an index
  / `autoMemoryDirectory`); blocked by 1346. Author input for it is in the
  [2026-10-30 entry](../journal/2026/2026-10-30-rulings-and-memory-design-input.md) (Commission).
- Accepted input shape (1349, author): native stores are inboxes smelt
  drains; the drain is not built.
- Does consolidation beat the verbatim journal? Hypothesis from
  DreamBench-SWE (typed 95/180 vs verbatim 89/180, p = .52); trial 1354 needs
  spend approval.
- Departments are provisional until 1349 closes.
- The append-in-place question of earlier reports stays unresolved.

## Retired

- Index hook budget refusal (2100 chars): the index is no longer injected (`test_on_start_memory_injection.py`); `test_resident_census.py` no longer pins it.
- Separate private companion for uncleared material: superseded by encrypted-in-repo (PR #1112).
- Delivery PR list (#1093-#1102, #1137, #1147, #1150), 0909/0913/0912/0919 closures, 1106 path migration, third-consolidation test-pin removal: completed history, kept in journal and git.
- Attribution backfill counts (34/65/69) and producer-versus-recorder notes for #1423-#1430: history; records now in `memory/evidence/attribution/`.
- Trial details (relocated-clone link catch, detached flags eating positional prompts on Claude Code 2.1.286 / Vibe 2.25.8, background launch without cwd, concurrent detached sessions, Pi credit depletion, retired-helper and slug-collision probes): single-sample history; runtime launch facts belong to the runtimes page.
- AGENTS.md append-only wording versus the attribution move: resolved by f78334e6 and the SMELT.md Bounds carve-out.
- Legacy advice to derive rules from consolidation (`memory/feedback_rules_come_from_memory_consolidation.md`): retired by v8 and the author's 2026-10-01 RETIRE LEGACY direction.
- `memory/pending-capture-pr1211.md.txt`: resolved by 1038, record in `memory/evidence/attribution/2026-10-06-review-attribution-pr1211.md`.
- Merged page `memory-v8-acceptance-trial.md`: folded into this page.

## Sources

- [Design and boundaries](../journal/2026/2026-10-01-memory-v8-design-and-boundaries.md), [helper retirement](../journal/2026/2026-10-01-memory-helper-retirement.md), [registration review](../journal/2026/2026-10-01-portable-registration-review.md), [PR 1102 merge](../journal/2026/2026-10-02-memory-v8-merge-under-parallel-housekeeping.md), [pilot](../journal/2026/2026-10-02-memory-v8-pilot-established.md), [0909 close](../journal/2026/2026-10-02-orchestrated-raid-closes-memory-v8-tracker.md)
- Trial: [link catch](../journal/2026/2026-10-02-memory-v8-0918-post-merge-link-catch.md), [withdrawal](../journal/2026/2026-10-02-memory-v8-0918-withdrawn-claim-local-gate-cause.md), [correction](../journal/2026/2026-10-02-memory-v8-0918-correction-link-catch-was-pre-merge.md), [detached flags](../journal/2026/2026-10-02-memory-v8-0918-detached-flags-consume-positional-prompt.md), [concurrent sessions](../journal/2026/2026-10-02-memory-v8-0918-concurrent-detached-claude-sessions.md), [no cwd](../journal/2026/2026-10-02-memory-v8-0918-background-launch-without-cwd.md), [Claude contradiction](../journal/2026/2026-10-02-memory-v8-0918-claude-surfaced-planted-contradiction.md), [misattribution correction](../journal/2026/2026-10-02-memory-v8-0918-correction-worktree-guard-misattribution.md), [step-6 conflict](../journal/2026/2026-10-02-worktree-guard-guidance-conflict-step6.md), Codex [read-index](../journal/2026/2026-10-02-memory-v8-0918-missing-read-index.md), [slug](../journal/2026/2026-10-02-memory-v8-0918-smoke-slug-collision.md), [loading](../journal/2026/2026-10-02-memory-v8-0918-instruction-loading-evidence.md); Claude [CLAUDE.md](../journal/2026/2026-10-02-untracked-claude-md-contradicts-memory.md), [read-index](../journal/2026/2026-10-02-retired-read-index-invoked-in-trial.md), [slug](../journal/2026/2026-10-02-capture-slug-collision-refused.md), [clone](../journal/2026/2026-10-02-trial-clone-carries-prior-session-entries.md); Vibe [read-index](../journal/2026/2026-10-02-t0918-trial-read-index-helper-absent.md), [slug](../journal/2026/2026-10-02-t0918-trial-smoke-slug-collision.md), [injection](../journal/2026/2026-10-02-t0918-trial-vibe-native-agents-injection.md), [aborted](../journal/2026/2026-10-02-skills-dream-read-index-not-found.md); Pi [credits](../journal/2026/2026-10-02-memory-v8-0918-pi-leg-interrupted-credit-depletion.md), [AGENTS.md](../journal/2026/2026-10-02-memory-v8-0918-pi-loaded-agents-not-planted-claude-md.md), [native load](../journal/2026/2026-10-02-memory-v8-0918-pi-native-load-delivered-contradictory-note.md); smokes [0923](../journal/2026/2026-10-02-memory-v8-smoke.md), [0924](../journal/2026/2026-10-02-memory-v8-runtimes-verified.md)
- [Brood adoption](../journal/2026/2026-10-05-brood-adoption-pr1187.md), [raid 926](../journal/2026/2026-10-05-raid-926-supersession-and-publication.md), [0913 close](../journal/2026/2026-10-06-0913-dispatch-close-path.md), [legacy import](../journal/2026/2026-10-09-import-2026-09-29-relocation-lessons.md), [index budget](../journal/2026/2026-10-10-permissions-allow-all-and-idh-install-sync.md), [roar survey](../journal/2026/2026-10-11-roar-clear-verdict-survey.md)
- Backfill [34](../journal/2026/2026-10-08-haiku55-arm-n-integration.md), [65](../journal/2026/2026-10-12-local-ci-wrap-up-inefficiency.md), [69](../journal/2026/2026-10-13-pr1374-author-scope-revision-and-merge.md); [third consolidation](../journal/2026/2026-10-13-third-dream-index-duplication-and-merge.md), [path migration](../journal/2026/2026-10-15-hoard-path-migration.md), [1101 checkpoint](../journal/2026/2026-10-15-raid-1101-1103-1104-integration-pending-attribution.md), [fourth hoard merge](../journal/2026/2026-10-15-fourth-hoard-merge-and-maintenance-fixture.md)
- [Capture one call](../journal/2026/2026-10-27-capture-pr-and-merge-commit-attribution.md), [redesign day](../journal/2026/2026-10-29-memory-redesign-day.md), [raid 0a53b8](../journal/2026/2026-10-29-raid-0a53b8-smelt-census-attribution.md), [2026-10-30 input](../journal/2026/2026-10-30-rulings-and-memory-design-input.md)
- Conception: [audit](../../conception/2026-10-29-memory-system-audit.md), [pilot](../../conception/memory-v8/pilot.md), [protocol](../../conception/memory-v8/evaluation-protocol.md), [results](../../conception/memory-v8/evaluation-results.md), [legacy retirement](../../conception/memory-v8/legacy-retirement.md), [brood evaluation](../../conception/memory-v8/brood-evaluation.md), [inventory](../../conception/memory-v8/source-inventory.md)

## Fallback
