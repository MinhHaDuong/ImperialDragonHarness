# Reviewer-attribution design and celebration telemetry teardown

## Context

Session of 2026-10-02, harness repo, prompted by afterthoughts on ticket 0205
(external-reviewer panel). PRs #1114 (spec + tracker 1004 with children
1005-1009) and #1115 (sequencing decision) merged. Vibe runtime.

## Observable events

- Review of the 0205 trial record: the audition board's `defects:` anchors
  are empty on all 10 entries, so the UVER column is structurally pinned at
  0; 21 of the 31 most recent scorecards use prose variants the scores
  parser rejects; the trial statistics (Wilson/Fisher, power calculations)
  showed only large effects reach significance at the recorded n.
- Celebration telemetry investigation: `~/.claude/telemetry/celebrations.jsonl`
  holds 2,182 records (2026-04-06 to 2026-10-02, 26 projects, all git
  projects, zero non-git records), is gitignored in the ~/.claude clone of
  this repo, and has zero readers in the harness (only roar's writer and
  its tests reference it). Every record is reconstructible from git history
  and the forge.
- Author decisions, recorded in the spec (docs/2026-10-02-reviewer-
  attribution-design.md): coaching by attribution replaces seat execution;
  runtimes review their own way (no seat-runner requirement); roar captures
  writer/reviewer/finding/defect facts in project memory journals; coaching
  is ex-post and offline; the reviewers skill splits into a thin descriptor
  and a separate coaching replay skill over shared substrate; celebration
  telemetry is torn down, not demoted; capture (1005) is blocked on the
  memory v8 tracker 0909 — the attribution record is a memory-journal entry
  and follows whatever v8 settles. 1008 (board seeding) stays independent.
- Copilot external review of PR #1114: 13 findings (4 high, 9 medium), all
  correctness-class, all adopted — including a dependency-cycle defect
  (children blocked by their own open tracker) and a pre-merge label gap
  (adopted findings are the only countable catches). Its review of #1115
  caught the tracker prose still gating the independent 1008.
- Forge incident during #1114 merge: the tab-ifs-guard check-run stayed
  `in_progress` with `conclusion: success` after the job completed;
  `gh run rerun --job` finalized it. CI was green throughout.

## Outcome

Spec, tracker and sequencing merged; tickets 1005-1009 open with 1005
gated on 0909. The old panel's trial verdicts stand as recorded
(frontier retained; budget and padme-qwen not promoted). Post-roar sweep
of the dependency-cycle class across 41 open tickets: no further instances.

## References

- docs/2026-10-02-reviewer-attribution-design.md
- tickets/1004, 1005-1009; annotations on 0205, 0356, 0980
- PRs #1114, #1115; celebration teardown rationale in spec §9
