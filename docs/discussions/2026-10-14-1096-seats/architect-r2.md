# Lead architect, round 2 (summary of its report)

Benefit restated: the 10-25 min/MR claim is withdrawn. Same-head repeats were 2 of 63 sampled PRs and 3 of 182 anchored heads; the 1080/1089 delays were startup failures, an exit-124 timeout and an interrupted gate; no per-phase timings exist. 1096 CAN: remove a second orchestrator and one nesting level (behind depth/no-agent-tool degradations; effect on failure rate unmeasured), replace hand blob checks, avoid the rare repeat battery, instrument per-phase timings. 1096 CANNOT: fix reviewer startup/timeouts, reduce REROLL rounds (quality-driven). Startup reliability needs its own ticket; without it, raids will not close in 20 min.

Evidence record, revised: per-seat entries in a structured forge comment block: forge + repo identity, base/head SHAs, diff identity (git patch-id --stable of base...head plus git diff --raw -M for modes/renames/deletions), context paths each seat read, exit-criteria hash, policy version (harness commit of review skill, references, panel-width.json), producer identity/family, reviewer worker/family/effort/transport, hash of each published report, check/adherence/gate results each keyed to its head. Counts only if posted by the expected controller account and never edited; edited/malformed/unreadable fails closed with a one-line fix message. Controller collects and publishes artifacts; seats return text only (no hooks, fork lifetime or nesting).

Reuse rule: one script scripts/review-evidence.py (grown from review-pr-anchor.py). Seat reused only if ran/approve, identical patch-id and raw diff, base moved without touching scope or context paths, criteria hash and policy version unchanged. Never reused across heads: check and gate results (gate recomputes; #1334), adherence (cheap, re-runs). Re-review triggers = existing round scoping keyed to evidence. Prose AI-tells auditor runs whenever prose text changed.

Risk rows: high row always includes red-team + one other-family seat; single-seat width gate never applies there (#1377). Inherited other-family seat counts at high row only with identical patch-id and context, printed `independent: inherited from <head>`; else re-run. Replication = named, priced plan entry (`replicate: <perspective> — <reason>` or label review:replicate).

Gate visibility: verify-gate comment adds a seat table ran / reused (origin head) / no-report + independence line. Stale/unproven → REROLL; required no-report → ESCALATE.

Native /review and /simplify: optional adapter seats. Simplify is a declared seat (native/portable/none); portable route required for code at ordinary row and above (verify-gate non-negotiable 4). Codex native review remains one route to an other-family seat.

Naming qualified: `review` bound by Codex native CLI command and (per gaze docs, unverified) Claude Code /review; Pi binds none. No collision found for review-pr or gaze. Contracts name the skill, never a literal slash command.

## Design C: delete the second battery, one shared reuse script
hunt owns the plan (risk row, seats, budget, reuse) and runs verify-gate at the end. review-pr and review-pr-prose both call the shared script, made transport-neutral (capability discovery instead of Agent check). gaze → one-release alias (review-pr plan continuation + verify-gate), no battery. raid phase 6: rebase, continue hunt's plan, gate. Deleted: gaze battery and tier tables, agents/gaze-pr-review.md, skills/gaze/telemetry.yml. New: per-phase timings in the evidence block.
Price: two children (~6 and ~14 files); ~7 agent-hours, ~1.25 author-hours; review USD roughly flat.
Residual risk: naming clash justified not resolved; two panel bodies can drift in panel policy (prose rare: 3 vs 336 calls).

## Design A: one review skill with modes = C + prose fold
mode code|prose|both; auto resolves mixed MR to both (code seats on code paths, prose seats on prose paths, one gate). Simplify declared seat. review-pr-prose one-release alias. Third child: prose panel → skills/review-pr/references/prose.md, delete review-pr-prose after alias, profiles/tests/catalog.
Price: third child ~12 files, 3 agent-hours, 0.75 author-hours; total ~10 agent-hours, ~2 author-hours.
Residual risk: `both` composition is new logic on a rare path; little time benefit; value is one contract and naming.

Dropped: Design B (no episode where it helps; costliest; needs the same shared script).

Ranking: (1) C now, A's third child later after one measured raid; (2) A in one go.

Decisions for the author (architect defaults):
1. Sequencing: C, measure next raid, then decide prose fold; separate ticket for startup/timeout reliability.
2. Inherited other-family seat at high risk: counts only with identical patch-id and context, printed; else re-run.
3. Native /review, /simplify optional; portable simplify required at ordinary+; other-family seat at high row via any transport.
4. Required no-report: ESCALATE, no merge-with-gap path.
5. Keep review-pr with modes code|prose|both; gaze (and review-pr-prose under A) one-release aliases, then delete.
