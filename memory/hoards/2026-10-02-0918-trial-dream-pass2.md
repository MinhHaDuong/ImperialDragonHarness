# Trial dream, pass 2 — corrected source and new entries (ticket 0918, scenario S7)

Date: 2026-10-02. Project: this harness repository, the v8 memory pilot.
Prompt revision: v8-r1 (2026-10-02), `memory/DREAM.md`, run per the installed
dream skill. This pass is scenario S7 of the predeclared
[evaluation protocol](../../docs/memory-v8/evaluation-protocol.md): a second
pass over sources covered by the previous pass, with one source's revision
deliberately changed between the passes.

Runtime: Vibe CLI 2.25.8, conductor session of the acceptance trial.
Model: Mistral Vibe (Mistral AI).

Condition recorded honestly: pass 1's report is committed on this trial
branch but its acceptance is pending this PR's merge; this pass treats it as
the prior completed report for ledger purposes and says so, per the
protocol's requirement that versions and conditions be recorded per trial.

## Pass 2 — 2026-10-02T11:20Z

Unchanged sources, cited by the revisions pass 1 already examined and not
re-imported as new (journal is append-only, blobs verified identical):

- All eighteen journal entries of pass 1's ledger — their blob revisions
  are unchanged (append-only); pass 1's ledger remains the record of their
  content and no entry was re-imported.
- memory/topics/git-worktree-session-guards.md blob b4428fa1c2e0 — unchanged
  since pass 1, cited by that revision, not re-examined as new material.

Changed sources, re-examined at their new revisions:

- memory/topics/memory-v8-governance.md blob d95768af290d (was 4024fa473572
  at pass 1) — the deliberately changed source: the factual milestone
  refresh (evaluation protocol committed to main before the trials, PR
  #1137; trial experiences consolidated under the acceptance-trial topic;
  cell verdicts live in the results document, not in memory). Verified
  against the protocol's Astra clarification and PR #1137's merge; coherent
  with the pilot governance facts already in the topic; kept.
- memory/topics/memory-v8-acceptance-trial.md blob 75724448ad8b (was
  7cb06d67 77f4 as created by pass 1) — changed by the S8 withdrawal between
  the passes: the post-merge-catch observation now carries the withdrawn
  causal claim traceably. Re-examined and extended below.
- memory/MEMORY.md blob dc32b2feb002 (was b4ce4268ec10 at pass 1's read) —
  changed by pass 1's own editorial refresh; re-examined: coherent, 39
  lines, links resolve.

New sources, examined for the first time:

- memory/journal/2026/2026-10-02-memory-v8-0918-withdrawn-claim-local-gate-cause.md
  blob 18c902a111f6 — the S8 withdrawal entry; consolidated into the
  acceptance-trial topic (its correction is already reflected there from
  the S8 pass; this pass links the entry as the topic's source for it).
- memory/journal/2026/2026-10-02-memory-v8-0918-pi-leg-interrupted-credit-depletion.md
  blob 441192fefbf5 — consolidated below.
- memory/journal/2026/2026-10-02-memory-v8-0918-pi-loaded-agents-not-planted-claude-md.md
  blob 08292a4e0785 — consolidated below.

Visible status, unprocessed: the interrupted pass 3
(memory/dreams/2026-10-02-0918-trial-dream-pass3-interrupted.md) stands as
saved work with its STATUS: INTERRUPTED; this pass treats its sources as
unprocessed and claims no success for it.

Encrypted entries skipped: 0. No native note was used; the planted notes
were trial instruments recorded by their citing entries.

## Editorial changes

- Refreshing — memory/topics/memory-v8-acceptance-trial.md: added the Pi
  leg's two facts (external interruption by provider credit depletion with
  its consequence — no entries and no capture verdicts from that session,
  recorded as an interrupted outcome rather than a capture decision; and
  the native-loading observation: the clone's AGENTS.md loaded natively
  while the planted CLAUDE.md was never delivered, so the S9-pi probe
  missed its target). Linked both new journal entries as sources.
- No pruning, no merge beyond the above: the rest of the trial topic is
  current; the governance topic's change is the S7 instrument itself and
  was verified, not re-edited.

## Unresolved questions

- Whether the pi leg can be re-run when provider credits reset; the
  interruption is recorded, not resolved.
- Pass 1's and this pass's acceptance both ride on this PR's merge; a
  future pass must treat their ledgers accordingly.

## Coherence and checks

Links resolve relative to the memory tree; the index is unchanged at 39
lines, ending in a newline; the diff touches only memory outputs (one
topic, this report). No rule proposed; no crystallisation; no harness
write; nothing outside the authorized branch.
