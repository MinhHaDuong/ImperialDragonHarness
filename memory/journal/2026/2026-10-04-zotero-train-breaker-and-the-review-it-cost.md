# Zotero train raid 2026-10-03/04 — the breaker that fired on arithmetic, and the review it cost

Overnight autonomous raid on the Zotero train (author mandate: robust,
slice the monsters): 1018 sliced into wave A (backend rename) + wave B
(skill consolidation), rider 1025 (filed as such; the roadmap's "1020"
was never filed), plus a breaker repair (1026) that the raid itself
forced. All merged; 1018, 1025, 1026 closed and archived.

## Observable events

- **The un-reviewable breaker fired on rename arithmetic.** Wave B
  (#1179): gate-rule count 26 (`--no-renames` counts every `git mv` as
  delete+add), `--name-status -M` 19 entries, content-bearing ~15 — the
  breaker pre-empted the whole battery on consolidation arithmetic, not
  review substance. Wave A had sat at the same boundary (14 vs 15).
  The breaker also meant the PR had received ZERO independent review —
  a question the author asked point-blank the next morning.
- **The repair got reviewed, and the review caught the repair's own
  defect.** #1180 (content-bearing counting, pure R100 renames
  excluded): gaze round 1 found that git's similarity index ignores
  line order — a reordered file scores R100 with all lines churned —
  fixed by cross-referencing `--numstat -M` (pure rename = `0 0`), with
  a red-first regression test. The review machinery applied to itself
  found what the author's own fix missed.
- **The review the breaker cost #1179 found a real introduced blocker.**
  A full panel (five detached codex seats under the code-reviewer
  profile contract + openrouter-frontier) ran on the parked PR:
  doc-propagation caught the new safety-contract sentence promising
  backup → dry-run → apply + `If-Unmodified-Since-Version` for "every
  mutation" — while `attach` has none of it (creation with
  `If-None-Match: *`; the version guard exists exactly once, in
  enrich). Every mechanical layer — executor gates, the gaze's own
  mechanical verification — had passed that sentence. Fixed in e3ca5b1d;
  scoped round-2 re-review approved. The mechanical-vs-panel division
  of labor demonstrated in one artifact: gates prove what is tested;
  panels catch what the prose promises and the code does not do.
- **The author force-approved on evidence, not on fatigue.** After the
  evidence stack was presented (gates + mechanical verification + full
  review round approve), the breaker override was exercised loudly per
  the contract; 1018 closed. The force-approve path was NOT taken the
  night before, when the evidence was mechanical-only — the refusal to
  self-authorize a human override held under autonomy pressure.
- **Night robustness data point:** zero executor crashes this train
  (contrast: 0938's wave-2 crash + salvage earlier the same day); the
  rider's make-check red was pre-existing at the wave base, fixed by
  wave A, and the rider merged only after a rebase picked the fix up —
  the wave-sequencing rule earning its keep.

## Outcome

Catalog: one `zotero` skill (six verbs, reference files, probe-url and
selftest under its scripts/), backend `scripts/zotero.py` answering all
ten subcommands, rules and cross-references naming the consolidated
skill, ratchets with proven teeth (exact-name record exclusions — the
substring blind spot closed per the review), main at `make check` 1410
passed / 2 skipped.

## Decisions already made (recorded in the tickets)

- Content-bearing counting adopted for the breaker; 15 threshold
  untouched; review-pr width gate out of scope (fail-safe direction).
- `INDEX_CACHE_DIR` stays `~/.cache/zotero-import/` (KISS — an orphaned
  index re-pull buys name coherence nothing).
- Force-approve is the author's gesture; under overnight autonomy the
  PR parks instead (1018 waited one morning, with a review run in the
  gap).
