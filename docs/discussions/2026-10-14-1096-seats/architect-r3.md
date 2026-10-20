# Lead architect, round 3: the current plan as an attackable design (condensed faithfully)

## (a) Gaze's responsibilities and contracts
`gaze <mr> mode=code|prose|both [risk=<row>]`, no second battery; `auto` (prose_predicate.py) resolves a mixed MR to `both` (code seats on code paths, prose seats on prose paths, one evidence block).
Per call: anchor head → ask reuse script which seats are valid → launch only missing seats → collect and publish reports as controller → post one review comment with the evidence block → return:
gaze: CLEAN|FINDINGS|DEGRADED|NOT-RUN; seats [{perspective, worker, family, status ran|reused(<head>)|no-report|human, verdict}]; findings {blockers, minors tagged}; evidence_comment id; independence: other-family ran | inherited from <head> | same-family | unavailable.
Hunt owns the plan: passes risk=<row> + reason; the reuse script computes a mechanical floor (panel-width.json pipeline_paths, high-risk globs in prose_predicate.py, decorrelation rows); hunt may raise, never lower below floor. High row: red-team + one other-family seat always. Loop: hunt → gaze → fix → gaze (≤3 rounds) → verify-gate; hunt fixes REROLL itself; gaze's fix subagent deleted.
Raid: after rebase, `gaze <mr>` reads the plan recorded in the block; unchanged diff identity → launches nothing; then `verify-gate <mr>`, merge sequentially. Raid selects no panel.
Standalone gaze: uses the mechanical floor, records plan-source: floor.
verify-gate: decision rules unchanged; validates evidence blocks; refuses stale evidence or required no-report; prints seat table; returns current YAML.
Nesting: gaze loaded inline in caller (drop `context: fork` from gaze). Seats are subagents at depth 2 under delegated hunt, depth 1 under raid, or detached headless (no nesting). No gaze→Agent C→perspectives chain. Max depth 2; 0 with detached seats.

## (b) Gaze's current content
Deleted: tier tables and band rules (gaze:213-257); Agent A (adherence → hunt step 9 + re-run on changed head, recorded as evidence); Agent B native /review (→ optional adapter seat); phase-6 gate launch (→ caller); REROLL fix-agent contract; battery parts of the containment section; agents/gaze-pr-review.md; skills/gaze/telemetry.yml (→ per-phase timings in the block).
Kept: review-worktree anchor; artifact-polling collection (controller-owned, transport-neutral); NOT-RUN / PANEL-INTEGRITY semantics; prose routing as mode resolution; portable simplify route (gaze:556-571) as a declared seat native|portable|none, required for code at ordinary row and above; 15-file breaker counting.

## (c) Evidence record and reuse script
scripts/review-evidence.py absorbs review-pr-anchor.py (renamed in child 1 so the lint does not flag it). Subcommands: anchor; identity (git patch-id --stable of base...head + git diff --raw -M + context paths); plan (per-seat reuse decisions + mechanical floor); validate (schema, actor allow-list, unedited).
Block per seat: forge+repo identity, base, head, diff identity, context paths; exit-criteria hash; policy version (harness commit of gaze and its references); producer identity/family; worker, family, effort, transport; report hash + location; per-phase timestamps; check, adherence, gate results each keyed to its head.
Admission: three pinned numeric forge actor IDs; server-reported unedited (edit-flag query behind a harness extension point). Copilot = seat of family `unknown`, never satisfies other-family (default awaiting author confirmation). Humans `human: ran`, binding, never reused.
Reuse: same diff identity; base movement disjoint from scope+context; same criteria hash and policy version; status ran/approve; report readable. High-row inheritance only under the same conditions, printed `inherited`. Never reused across heads: checks, adherence (#1334). Legacy reviews before child 1 carry no block → never reused; re-review is the fail-safe.

## (d) Child PRs (breaker at ≥15 content-bearing files; pure git mv counts 0)
1. Evidence core (~9 files): new script, renamed anchor, config/review-evidence-actors.json, tests, verify-gate, review-pr and review-pr-prose emit blocks via the script, gaze Agent C prompt emits the block, anchor tests. Fixture repos + stubbed forge JSON prove: unchanged head → zero seats; disjoint base change reuses, context-path change re-runs; same blobs with mode change/rename/deletion invalidates; criteria hash change invalidates; edited comment or non-allow-listed actor rejected; Copilot never other-family; required no-report → ESCALATE; checks not reused across heads; re-gate of identical diff after APPROVED is a confirmation, not a new round.
2. Gaze rebuilt, raid calls the gate (~14 files, at breaker): gaze SKILL, telemetry deleted, agents/gaze-pr-review.md deleted, raid, README, ~9 gaze/raid tests rewritten or deleted (move gate-identity and breaker-counting tests to child 1 if over). Gaze's code/prose modes point to skills/review-pr/SKILL.md and skills/review-pr-prose/SKILL.md as panel references. Tests prove: head already reviewed by hunt → no seats; delta re-runs only objecting seats + one regression seat; high row always plans red-team + other-family; missing seat → DEGRADED, not approval.
3a. Hunt owns the plan, review-pr retired (~15 files): git mv skills/review-pr/SKILL.md → skills/gaze/references/code.md, panel-width.json alongside; hunt steps 11-13 call gaze then verify-gate; verify-gate, profiles/code-reviewer, decorrelation.md, prose_predicate.py; 12 tests repointed. Tests: hunt's plan survives into raid's continuation; floor overrides an under-rated risk row.
3b. Remaining text references + lint (~8 files); planted reference fails, marked reference passes.
Measured raid: timings from the blocks.
4. Prose fold: git mv review-pr-prose → gaze/references/prose.md, rewrite 20 live references, extend lint, mode=both fixture tests. ~20 files → 4a (move + executable refs), 4b (text + lint).

## (e) Transition with no aliases
After 1: blocks exist and the gate enforces them; old gaze battery still runs but posts a block; in-flight MRs re-reviewed, never falsely reused.
After 2: hunt still calls review-pr (still exists); raid's gaze reuses hunt's block; most of the duplication saving lands here. Inconsistency: gaze points to another skill's file as its panel procedure (a reference, not an alias) — two entry points for one release interval.
After 3a: review-pr gone, executable callers repointed; text mentions in 3b's files stale for one merge; tests green because the lint lands last.
After 3b: live tree consistent for code; prose still via review-pr-prose until child 4 (live, not linted).

## (f) Lint scope
Live paths: skills/ tests/ profiles/ agents/ adapters/ scripts/ rules/ README.md. Pattern review-pr(?!-prose) from 3b; review-pr-prose from child 4. Exempt: history paths per author's list. Exemption marker for scripts parsing historical traces, following scripts/trace-stats.py:122-124 (`# historical-skill: verify -> gaze`); coaching benchmark titles (scripts/coaching/benchmark-board.yml:133) need the marker or exemption as data. Gaze never retired, not linted.

## (g) Price
1: 3 agent-h, 0.4 author-h; 2: 3, 0.4; 3a: 2, 0.3; 3b: 1, 0.2; measured raid: —, 0.25; 4a+4b: 2.5, 0.4. Through 3b ≈ 9 agent-h, 1.3 author-h; total ≈ 11.5 agent-h, 2 author-h. Seat USD roughly flat.

## (h) Weakest points (architect's own)
1. Gate round accounting: verify-gate counts its own verdict comments, ESCALATEs at round 3; a raid's post-rebase gate after hunt's gate can ESCALATE a clean MR. Child 1 must make a re-gate on identical diff after APPROVED a `round: confirm`, and count rounds per diff identity.
2. Report durability: "readable at gate time" means reports on the forge: comment size limits (~64K chars on GitHub), more forge writes, a GitHub-specific edit flag; GitLab untested.
3. Producer-chosen risk: hunt rates its own risk; the mechanical floor bounds it but misses semantic risk (#1377 was under scripts/**, happens to be caught).
4. Breaker pressure: children 2, 3a, 4 at or above 15 files; no aliases → windows of inconsistent text between children.
5. Small measured benefit: same-head repeats 2 of 63 MRs; prose 3 vs 336 (13 vs 501 on both hosts); the 20-minute goal rides on 1099; child 4 buys one contract, not speed.
