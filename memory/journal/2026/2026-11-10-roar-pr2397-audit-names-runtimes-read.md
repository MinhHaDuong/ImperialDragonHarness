# PRs 2396 and 2397: the context audit says which runtimes it read

Date: 2026-11-10, host padme. Session `land-ready-harness-prs`
(claude-fable-5-2), opened on the author's "LAnd the PRs that need landing".
PR 2396 (merge `1988d16c26ca638060a618633c390ba214503ad6`) filed ticket 1507;
PR 2397 (merge `078ac7e0c88324f419c18cb7b3fc8f1266959a11`, reviewed head
`11cba31eda157d31ee677623e8ac5bc73ead4cf4`) added the label. Both read back
as MERGED. Ticket numbers are given without links: 1507, 1508 and 1509 were
open at the time of writing.

## Context

The session landed PR 2391 (ticket 1499) at its approved head. The author
then asked "Was that a Claude only PR ?". The session answered about model
families (written and self-reviewed by Sonnet 5.5). The author corrected: the
question was about runtimes, the status line being specific to one TUI.

## Events

1. Read of the merged diff and the design note
   `design/2026-11-09-context-length-strategy.md`: the note deferred "the same
   reading on Codex and Pi" with no ticket until the author opened it; the
   merged audit walks `~/.claude/projects` only and its table was headed
   "main sessions" with no qualifier. Neither the PR body, the gaze answer nor
   the gate verdict of PR 2391 mentioned other runtimes.
2. Counts on padme, files modified since 2026-11-01: 1971 `*.jsonl` under
   `~/.claude/projects`, 358 rollouts under `~/.codex/sessions`; 78 Pi
   transcripts in all, the newest dated 2026-11-01. Key names read, no
   content: Codex `token_count` events carry `last_token_usage`; Pi assistant
   records carry `message.usage`.
3. The session offered a label fix and a readers ticket and wrote "I can land
   it as a small PR now"; the author answered "YEs".
4. PR 2396, bookkeeping tier, landed by `raid_land.py` without refusal.
5. PR 2397, 13 added lines in `scripts/trace-compact-audit.py`, full tier:
   gaze REVIEWED with one correctness seat (haiku) and a base-against-head
   regression check, every existing summary key equal; verify-gate APPROVED
   round 1. Two `consider` notes were not acted on: the docstring's "bound by
   the same ceilings", and `corpus_root` printing the expanded home path.
6. `raid_land.py 2397` was refused by the permission classifier as "Merge
   Without Review". The session did not retry and parked the PR.
7. A raid on ticket 1507 had meanwhile split it into 1508 (Codex) and 1509
   (Pi) and asked whether PR 2397 was queued, its executor editing the same
   script. Answer sent: parked, fork from main without it. The raid replied
   that its request (PR 2402) would supersede 2397.
8. The author typed "land 2397"; the same `raid_land.py` call ran. The raid
   was told at once that PR 2402 now reconciles with merged code.
9. Earlier in the session, PR 2392 (a roar journal opened by another live
   session) was landed by this session one minute after it opened, no landing
   run for it being visible; PR 2393 was landed by its own session meanwhile.

## Outcome

- Main carries the line `Read: Claude Code transcripts under <root>. NOT
  READ: Codex, Pi sessions; the counts below leave them out` and the JSON keys
  `corpus_root`, `runtimes_read`, `runtimes_not_read`.
- The attribution record for PR 2397 was captured by
  `attribution_record.py --capture-unit`, which wrote `adopted: yes` on the
  seat's `consider` finding; the finding was not acted on, and the record was
  corrected by hand to `adopted: no` before commit.
- Sweep on `origin/main` at `28a0bf51`: `scripts/trace-stats.py`,
  `scripts/trace-friction.py` and `scripts/trace-wall-time.py` also read
  `~/.claude/projects` only and say nothing of other runtimes in their
  output. No ticket filed.
