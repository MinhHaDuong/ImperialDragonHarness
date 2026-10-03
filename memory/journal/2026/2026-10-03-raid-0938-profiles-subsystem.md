# 0938 raid 2026-10-03 — profiles subsystem landed, premise dissolved, salvage under fire

Raid on ticket 0938 (agent profiles) in four waves: guards hoist +
role inventory (#1172), five shells + contracts + doc-pins (#1173),
review-pr pilot conversion + defect replay (#1174), Pi portability
demonstration + close (#1175). All merged; ticket closed and archived;
main at 1395 passed / 2 skipped.

## Observable events

- **The premise dissolved between filing and raiding.** The ticket's
  2026-09-16 baseline (86 `subagent_type: "fork"` launches) was zero on
  the raided tree: the attribution train (1004-1009), detached-seat
  substitution (1017), and orchestrator-run shapes (0990) had already
  replaced the forks. The raid's recount (prescribed by the ticket's own
  2026-09-23 roster-audit note) re-targeted it at the remaining
  embedded-role fan-outs instead. Tickets age; recount before raiding.
- **A census lesson on shared checkouts.** `git add tickets/` in the
  shared main checkout swept a parallel session's untracked ticket into
  the raid's feasibility commit; caught by `git show --stat` immediately
  after, repaired by soft reset + explicit-file recommit before push.
  Named files only in shared checkouts.
- **Crash, salvage, finish worked as designed.** A wave-2 executor died
  on a harness notification error mid-edit;
  `scripts/worktree-salvage.sh` committed and pushed its WIP; the
  relaunch judged the salvage, kept all four file changes, and completed
  the wave on the existing branch (PR #1174).
- **The pilot replay passed with contracts only.** Five detached codex
  seats, each given `profiles/code-reviewer/PROFILE.md` + perspective +
  diff, with no rails restated in prompts: correctness and red-team both
  caught the replayed defect class (PR #1164's cwd-dependent test) with
  non-root reproductions, and all five honored the contract rails
  unprompted — the lean doctrine (lean on training, no guard machinery)
  validated behaviorally.
- **The portability gate demonstrated live on Pi.** Frontmatter-only
  translation of `agents/code-reviewer.md` into
  `~/.pi/agent/agents/code-reviewer.md` (subagent extension,
  padme/qwen3.8-27b): the extension registered the agent, and a live
  run's first action read `~/.agents/profiles/code-reviewer/PROFILE.md`
  and quoted the contract's first Rules line back verbatim — the pointer
  followed end to end on a second runtime.
- **The round-1 gate caught the exit-criterion half-truth.** The close
  ticked "roles declared" while five inventory-justified call sites
  still embedded their roles; the caller ruled convert-not-rescope and
  the fix round converted all five (gaze Agent A → adherence-seat,
  gaze phase-6 gate → gate-seat, review-pr-prose panel → prose-reviewer,
  gaze REROLL fix + raid Phase 5 → coder), each pinned by
  mutation-verified bounded-slice tests.

## Outcome

- Roster: 5 shells + 5 contracts, agents channel 761/800 (no raise);
  guards hoisted to rules/guards.md (audience pass); AGENTS.md import
  channel relieved to 4132/4500; the owning rules budget raise
  17500→17800 was argued in-test and survived gate scrutiny.
- Waves: every PR individually gazed (two required one REROLL round
  each; one required the caller-side fix loop), merged sequentially,
  main green throughout (baseline 1371 → final 1395 passed).

## Decisions already made (recorded in the tickets)

- Convert-not-rescope on the remaining call sites — orchestrator ruling,
  gate-confirmed (tickets/closed/0938 log).
- The Pi template body carries one provenance comment (Pi rejects files
  not starting with `---`), so the accurate claim is pointer-paragraph
  byte-identity, not whole-body — corrected in ticket log, PR body, and
  pinned by test.
