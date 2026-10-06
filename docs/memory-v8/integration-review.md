# Memory v8 integration review (tracker 0909)

Recorded 2026-10-02, before the tracker's closure, by the raid-0909 final
wave on branch `t0909-tracker-closure` from main `a78b73ea`; the close
reason cites this document. Method: every claim below was verified against
the tree at `a78b73ea` by reading the cited file; blob ids are `git ls-tree
HEAD` values at that commit, cited where the convention cites them. Nothing
below certifies a runtime beyond what the evaluation record itself attests.

## Criterion 1 — every active deliverable has a verified realization or an explicit scope decision

Every deliverable workpackage of the [delivery plan](../2026-09-11-memory-implementation-plan.md)
was delivered through a merged PR and is filed under `tickets/closed/`:

| Ticket | Delivered by | Closed-ticket record |
|---|---|---|
| 0911 — v8 Markdown convention and templates | PR #1102 (merge `c596f3bb`) | [tickets/closed/0911-one-type-field-one-frontmatter-shape-val.erg](../../tickets/closed/0911-one-type-field-one-frontmatter-shape-val.erg) |
| 0917 — legacy source inventory and provenance | PR #1102 (merge `c596f3bb`) | [tickets/closed/0917-rescue-git-recency-before-the-frontmatte.erg](../../tickets/closed/0917-rescue-git-recency-before-the-frontmatte.erg) |
| 0920 — pilot: index, themes, journal, audience | PR #1109 (merge `ff9465b8`) | [tickets/closed/0920-pilot-portable-project-memory-and-shared-snapshot.erg](../../tickets/closed/0920-pilot-portable-project-memory-and-shared-snapshot.erg) |
| 0988 — capture at roar, committed and safe | PR #1117 (merge `758785ca`) | [tickets/closed/0988-session-memory-lands-uncommitted-and-sil.erg](../../tickets/closed/0988-session-memory-lands-uncommitted-and-sil.erg) |
| 0916 — versioned DREAM prompt v8-r1 | PR #1119 (merge `d68c57da`) | [tickets/closed/0916-model-judged-merge-reviewed-promotion-to.erg](../../tickets/closed/0916-model-judged-merge-reviewed-promotion-to.erg) |
| 0910 — lair dream suggestion at the threshold of five | PR #1127 (merge `5fed3482`) | [tickets/closed/0910-generate-the-memory-index-as-the-top-n-o.erg](../../tickets/closed/0910-generate-the-memory-index-as-the-top-n-o.erg) |
| 0923 — first runtime smoke | PR #1134 (merge `87ee07a8`) | [tickets/closed/0923-first-runtime-adapter-offline-pilot.erg](../../tickets/closed/0923-first-runtime-adapter-offline-pilot.erg) |
| 0924 — remaining three runtimes | PR #1135 (merge `d1c57bb3`) | [tickets/closed/0924-remaining-runtime-adapters.erg](../../tickets/closed/0924-remaining-runtime-adapters.erg) |
| 0918 — evaluate before rollout | protocol PR #1137 (merge `be1ea2fc`), trials PR #1142 (merge `a78b73ea`) | [tickets/closed/0918-ranking-miss-rate-instrument.erg](../../tickets/closed/0918-ranking-miss-rate-instrument.erg) |

Scoped out per the plan, verified open in `tickets/` with `Label: deferred`:
0925 (crystallisation only on explicit author request, plan line 31) and the
seven deferred workpackages 0908, 0912, 0914, 0915, 0919, 0921, 0922 (plan
line 49). No silent drops.

0913 is neither delivered nor closed: the author's scope decision of
2026-10-02, recorded verbatim in [0913's log](../../tickets/closed/0913-retire-the-dead-retention-machinery-and.erg),
keeps it open — "SCOPE DECISION (author, 2026-10-02, on the predeclared
No-rollout verdict from PR #1142): 0913 stays open as the standing rollout
workpackage, gated on the recorded blockers — codex's native-note
conflict-surfacing behavior (S9, external to this repo) and the pi re-run
(S3/S4, provider credits). No rollout proceeds under this tracker."

Verdict: MET.

## Criterion 2 — integrated result verified: sources, corrections, recent reminders, retired knowledge, amended procedures

Read from the tree, not from claims:

- Index: [memory/MEMORY.md](../../memory/MEMORY.md) (blob `70fcf8bb6289`)
  is 35 lines under the 100-line bound, ends in a newline, and links its
  topics, recent journal experiences, dreams and reference notes, with
  provenance pointers to the [source inventory](source-inventory.md)
  (blob `e58eddd6ed00`) and the per-file revision ledger
  [source-revisions.tsv](source-revisions.tsv) (blob `8afb2ccbe56a`).
- Topics with provenance: six files under `memory/topics/`, each carrying a
  Sources-and-exceptions section; read as the sample,
  [memory-v8 governance](../../memory/topics/memory-v8-governance.md)
  cites its journal sources and records the superseded private-companion
  clause as corrected by the [first dream](../../memory/dreams/2026-10-02-pilot-first-dream.md).
- Journal append-only: 35 entries under `memory/journal/2026/`; verified
  mechanically that no entry was modified after reaching main — every entry
  file appears in exactly one first-parent commit of `a78b73ea`.
- Corrections link unchanged originals: the post-merge-link-catch entry is
  corrected by two later entries
  ([withdrawn causal claim](../../memory/journal/2026/2026-10-02-memory-v8-0918-withdrawn-claim-local-gate-cause.md),
  [pre-merge framing](../../memory/journal/2026/2026-10-02-memory-v8-0918-correction-link-catch-was-pre-merge.md));
  the original entry stands unchanged in one commit, as the convention
  requires.
- Dream reports: `memory/dreams/` carries the pilot
  first dream and the trial passes 1 and 2, plus the interrupted pass 3 with
  `STATUS: INTERRUPTED` visible in the file; the versioned prompt
  [memory/DREAM.md](../../memory/DREAM.md) states revision v8-r1
  (blob `6087a0b3f641`).
- Retired legacy machinery: `skills/dream/read-index.py`, `commit.py` and
  `provenance.py` are absent; the [retirement record](legacy-retirement.md)
  (blob `213ea7b52628`) documents the consumer audit, the regression check
  `tests/test_legacy_memory_retired.py`, and recovery at parent commit
  `a849070d`. No compatibility shim reactivates legacy writes.
- Amended procedures: the v8 reading section is merged into the harness
  `AGENTS.md` (§ Project memory, linking `memory/MEMORY.md` with read,
  capture and DREAM boundaries); roar's capture discipline names
  `scripts/memory-capture.sh` (`skills/roar/SKILL.md`); lair step 11 counts
  journal blob ids against the accepted reports' ledgers and only suggests
  a separate dream at five uncovered experiences
  (`skills/lair/SKILL.md`); the pilot declaration
  [pilot.md](pilot.md) (blob `1b1574831385`) declares the pilot's audience,
  scope and rollback, and [README.md](README.md) (blob `4361d82596ea`)
  carries the pinned capture mechanics (0988).

Verdict: MET.

## Criterion 3 — 0988 proves conservation, integration and harness update without a capture-blocked pull

The delivered proof is
[tests/test_memory_stall_reproduction.sh](../../tests/test_memory_stall_reproduction.sh)
(blob `640b4a470d2f`), merged by PR #1117 (`758785ca`). It reproduces the
padme stall in a disposable HOME with three arms: arm 1 is the positive
control — old-style uncommitted memory writes plus an origin advance over
the same paths make the sync script refuse while every byte stays in place;
arm 2 surfaces that refusal at session start through `on-start.sh`; arm 3
is the treatment — capture at roar commits entries through origin on a
wrap-up branch, the same host fast-forwards the next night, and the note
set is byte-identical across the reproduction (public plaintext, private
`.age` ciphertext decryptable with the per-project key, no plaintext in
the tree). The suite runs under pytest through
[tests/test_bash_suites.py](../../tests/test_bash_suites.py)'s `tests/*.sh`
glob (integration tier; CI installs `age` so the private-capture
assertions execute).

Live corroboration outside the suite: the acceptance trial's S5.b ran two
simultaneous `memory-capture.sh` invocations and two full concurrent
sessions in one clone — all entries preserved and "no git pull or fetch of
the harness was blocked (captures write only a journal file; git
operations ran normally throughout)" ([results](evaluation-results.md), S5).

Verdict: MET.

## Criterion 4 — evaluation read, costs and limits explicit; design and plan describe the delivered

- The protocol was predeclared:
  [evaluation-protocol.md](evaluation-protocol.md) (blob `0a0714eacb7c`,
  PR #1137, on main at `be1ea2fc` before the first trial) fixes 31 cells,
  the verdict vocabulary and the rollout rule — any scenario fails, or any
  near-miss is unexplained, means No rollout.
- The trials ran under it and are recorded in
  [evaluation-results.md](evaluation-results.md) (blob `a694882a936c0`,
  PR #1142, merge `a78b73ea`): 31 cells — 22 pass, 3 no-event, 5 fail,
  1 absent; scenarios S1, S2, S5, S6, S7, S8, S10 pass; S3, S4, S9 fail.
  The recorded verdict is **No rollout**. Margins were not adjusted after
  observing any example.
- Limits, named in the record rather than smoothed: S9 — one codex session
  adopted a planted contradictory native note as authority without
  signalling the conflict (a runtime behavior external to this repo);
  S3/S4 — the pi leg was cut off by provider credit depletion mid-session,
  its re-run is an open question; single-session samples throughout, so no
  runtime is certified or condemned; both review rounds ran with degraded
  panels (the conductor runtime cannot spawn subagents). Costs are explicit
  recorded conditions — provider credits, degraded rounds, three
  conductor-side conduct errors with their consequences verified — not a
  monetary figure.
- Design and plan describe the delivered: the [v8 design](../2026-09-10-dragon-memory-design.md)
  (blob `74ff94ed5d56`) and the [delivery plan](../2026-09-11-memory-implementation-plan.md)
  (blob `7e83dd460a8a`) map onto the record above — same workpackage IDs,
  same boundaries (no TTL, no automatic promotion, no second index writer),
  same deferred set.
- F3 — the per-machine key story (author decision of 2026-10-02, recorded
  in [0913's log](../../tickets/closed/0913-retire-the-dead-retention-machinery-and.erg)):
  private capture uses one age X25519 identity per project, derived from
  the repository's normalized origin URL, stored under `~/.config/keys`
  and never tracked; per-machine keys stand, and the cross-machine
  unreadability of `.age` entries is a declared known limit — an entry
  pushed from one machine is unreadable on another until its key is copied
  by hand. This is consistent with the closed ticket
  [0937](../../tickets/closed/0937-a-keystore-diverging-between-machines-is.erg)'s
  invariant that the fleet keystore stays per-machine and no shared or
  synced secret store is proposed; the accepted cost, not an open defect.
  No `.age` file currently exists in the tree — nothing awaits that
  audience, so the limit is declared, not exercised.

Verdict: MET.

## Criterion 5 — integration review recorded before closure

This document, dated 2026-10-02, is committed on the closure branch before
the tracker's close; the close reason cites it together with the author's
0913 scope decision. The tracker's exit criteria are ticked in the same PR
that files the closed ticket under `tickets/closed/`.

Verdict: MET.

## What this review does not claim

0913 stays open as the standing rollout workpackage under the author's
scope decision; nothing here rolls the convention out to another project,
and no rollout proceeds under this tracker. The No-rollout verdict is a
record of single-session trials with predeclared margins, not a
condemnation of any runtime; its two blockers — codex's native-note
conflict-surfacing behavior (S9) and the pi re-run (S3/S4) — are recorded
on 0913 as the gate any future rollout must clear.
