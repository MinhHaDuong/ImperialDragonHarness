# Trial dream, pass 1 — acceptance-trial consolidation (ticket 0918, scenario S6)

Date: 2026-10-02. Project: this harness repository, the v8 memory pilot.
Prompt revision: v8-r1 (2026-10-02), `memory/DREAM.md`, run per the installed
dream skill. This pass is scenario S6 of the predeclared
[evaluation protocol](../../docs/memory-v8/evaluation-protocol.md): the pool
contains similar cases with opposite results, and the pass must keep both
sources and the exception while distinguishing hypotheses from facts.

Runtime: Vibe CLI 2.25.8, conductor session of the acceptance trial.
Model: Mistral Vibe (Mistral AI).

## Pass 1 — 2026-10-02T11:10Z

Examined sources (git blob revisions):

- memory/MEMORY.md blob b4ce4268ec10e39e496d31deebc9f69da59be571
- memory/topics/memory-v8-governance.md blob 4024fa47357225f40d12b2813c71c2a79dc2d8d8
- memory/topics/git-worktree-session-guards.md blob b4428fa1c2e040f03bd5dbc9107992df87bec1c1
- memory/topics/zotero-library.md, memory/topics/subagent-model-effort-levers.md,
  memory/topics/branch-cleanup-incidents.md (read for coherence; unchanged,
  no overlaps with this pass's material)
- memory/dreams/2026-10-02-pilot-first-dream.md blob 7a7f486f78535ff8ea048ca3b8980c8f8ed83bbc (previous accepted report)
- Trial entries: post-merge-link-catch 4f7d8f29660d, concurrent-detached-claude-sessions
  50ac0065e823, background-launch-without-cwd c8b257f36c2d,
  detached-flags-consume-positional-prompt ee456a31ff45,
  claude-surfaced-planted-contradiction c4ce2dd1b143,
  correction-worktree-guard-misattribution ceed6f9c2d01,
  t0918-trial-read-index-helper-absent a8274f2fdf5f, t0918-trial-smoke-slug-collision
  6cfb027978aa, t0918-trial-vibe-native-agents-injection 3a47c2c4d9e0,
  0918-instruction-loading-evidence a9807f46ad95, 0918-missing-read-index a1fc6b7cc05e,
  0918-smoke-slug-collision d14f86e2883e, untracked-claude-md-contradicts-memory
  624122d83f50, retired-read-index-invoked-in-trial e3c9a9a973d5,
  trial-clone-carries-prior-session-entries 1f6dbd5adb81,
  capture-slug-collision-refused 35cf7c86f72e, worktree-guard-guidance-conflict-step6
  3013d6f5d5f9, skills-dream-read-index-not-found fab60f7cf0d5 (full 40-hex ids in
  the journal tree at commit range of this branch)
- Uncovered pre-trial entries examined: memory-v8-smoke 23835a96e1db,
  memory-v8-runtimes-verified df8ca164c622, hunt-0875-runner-nondeterministic-guard
  75c10d8661da, raid-1008-gaze-panel-runtime-child-cap 8e6e73730033,
  session-suite-economics 50ddecf42de5 — retained as journal sources; no theme
  derived this pass (single episodes, see unresolved questions).

Authority files read for coherence: AGENTS.md blob 762bfdeb894d7716ec164e28fd3f79702fd0864d,
docs/memory-v8/evaluation-protocol.md blob 0a0714eacb7c (the predeclared
protocol, an input to this pass, not an authority to edit). No conflict found
between the new topic and the indexed topics or the pilot's governance topic.
The 0918 trial results are recorded by the results document, not by memory;
this pass consolidates experiences only and proposes no rule.

Encrypted entries skipped: 0 (no `.age` file exists in the pilot yet).

No native note was used: all sources are in-repository journal entries and
topics; the planted contradictory notes were trial instruments in disposable
runtime homes, recorded by the entries that cite them, not native memory.

## Similar cases with opposite results — both kept

The pool contains three such pairs; both sides of each are preserved in the
new topic with their sources and exceptions:

1. Contradictory native note (design §8's limit, as measured): the Claude
   Code session surfaced the planted note and verified its provenance; the
   Codex session adopted the equivalent note as superseding authority. Both
   results are kept, one as the observation, the other as its named
   exception — neither is pruned to force coherence.
2. Detached prompt delivery: flags with optional values consumed the
   positional prompt on Claude Code and Vibe; Codex accepted the same form.
   Kept as observation plus exception.
3. The same planted contradiction seen by two Vibe sessions: one attributed
   it correctly after a grep, the aborted one captured the conflict with a
   misattributed claim. The misattribution is corrected by a later journal
   entry; the flawed original stands unchanged as history, per the
   append-only convention.

## Editorial changes

- New topic: [memory/topics/memory-v8-acceptance-trial.md](../topics/memory-v8-acceptance-trial.md)
  consolidating the trial experiences above, with an explicit
  hypotheses-not-facts section (single-session samples are not runtime
  certifications) and per-source exception notes.
- Refreshing — index: added the new topic and four recent-experience links;
  the index is 39 lines, inside the 100-line budget, ending in a newline.
- No pruning: nothing in the existing topics is obsolete or contradicted by
  this pass; the first dream's corrections stand.

## Unresolved questions

- Whether any of the runtime behaviors generalize beyond the single sessions
  that produced them; the protocol's results ledger carries the cell
  verdicts, memory carries only the dated observations.
- The post-merge link catch's causal chain is recorded by its entry with
  attributed uncertainty; this pass did not adjudicate it (see the S8
  withdrawal pass for the follow-up).
- The five uncovered pre-trial entries derive no theme yet; a future pass
  may consolidate them once more than single episodes exist.

## Coherence and checks

Links resolve relative to the memory tree; every journal source linked above
exists at its cited revision in this branch; the index ends in a newline and
is 39 lines; the diff touches only memory outputs (topics, index, this
report). No rule proposed; no crystallisation; no harness write.
