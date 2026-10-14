# CI content review: forge CI against `make check` (ticket 1045, prerequisite)

Date: 2026-10-14. Read-only analysis, authorised by the author on 2026-10-14 as
the prerequisite of ticket 1045. Recorded here rather than as its own ticket, at
the author's request (the open-ticket count is to go down, not up). No design,
no ruleset change, no gate code: this answers "does the forge CI duplicate
`make check`, and what does it miss?" so that 1045's three open decisions can be
taken.

Sources read at `origin/main` 85d904da: `.github/workflows/CI.yml`,
`scripts/local-ci.sh`, `ci-local/`, `Makefile`, `hooks/pre-commit`, the guard
scripts and the tests that touch them; the ruleset `main-required-checks` read
from the forge API; the job-level outcome of every failed CI run the forge
still lists (403 runs, 2026-04-24 to 2026-10-14, out of 4316 CI runs).

## Answer in three lines

1. **Partly.** Two of the eleven CI jobs are the same thing as a `make check`
   target (pytest-guard ≈ check-tests; agnostic-guard ≈ the four
   check-agnostic-* targets); a third (personal-data-guard) is in both but not
   required. The other CI jobs have no counterpart in `make check`.
2. **CI misses** the README skills-catalog drift check, which only `make check`
   and the pre-commit hook run, and checks only the branch head locally while
   the forge checks the merge.
3. **`make check` misses** seven CI jobs: validate-tickets (covered in practice
   by the pre-commit hook), cross-pr-ticket-collision, skill-lint,
   status-verb-guard, pipefail-guard, grep-e-guard and tab-ifs-guard; the
   inline YAML guards (skill-lint, pipefail, grep-e, tab-ifs) exist only in the
   workflow file.

## The facts of 1045's Prerequisite, re-checked

| Claim (2026-10-06) | Today | Evidence |
|---|---|---|
| Ruleset requires seven checks: validate-tickets, skill-lint, agnostic-guard, status-verb-guard, pipefail-guard, grep-e-guard, pytest-guard | **True** | forge API, ruleset 17254040, `enforcement: active` |
| No bypass actor | **True** | `bypass_actors: []` |
| — (not stated) | Required checks are **not strict** | `strict_required_status_checks_policy: false`: a PR green on a stale base may merge |
| `make check` lacks validate-tickets, status-verb-guard, pipefail-guard, grep-e-guard, tab-ifs-guard | **True, incomplete**: it also lacks skill-lint and cross-pr-ticket-collision | `Makefile` line 61 |
| `make check` adds check-skills-drift and check-adapter-hooks | **Half stale**: check-skills-drift yes; check-adapter-hooks was retired on 2026-10-05 (commit 85037441, ticket 0887), the day before the ticket was written | `git log -S check-adapter-hooks -- Makefile` |
| — (not stated) | `make check` also runs check-personal-data | added with the privacy tiers, 2026-09-28 |
| Three CI jobs run but are not required: personal-data-guard, tab-ifs-guard, cross-pr-ticket-collision | **True** | ruleset vs `CI.yml` job list |

## Every check, where it runs, what it guards

Columns: **CI-R** forge job, required by the ruleset; **CI-n** forge job, not
required; **make** a `make check` target; **pre** `hooks/pre-commit`
(`core.hooksPath=hooks`); **pytest** an equivalent assertion inside the suite
that pytest-guard and check-tests both run. Fires: failed CI runs in which the
job failed (one PR pushed red ten times counts ten), from the forge's history.

| Check | CI-R | CI-n | make | pre | pytest | Guards | CI fires |
|---|---|---|---|---|---|---|---|
| validate-tickets (`erg check tickets/`) | ✓ | | | ✓ (when a `.erg` is staged) | | ticket file format, duplicate IDs | 98 (5 since July) |
| skill-lint (inline: `name:`, `description:` present in each SKILL.md frontmatter) | ✓ | | | | `description` yes (`test_skill_descriptions.py` loads it); `name` no | skill frontmatter | **0** |
| agnostic-guard (`check-agnostic.sh` on skills rules tickets scripts, + 2 self-tests) | ✓ | | ✓ as four targets | | partly: `test_real_skills_pass_agnostic_gate`, `test_real_scripts_dir_is_agnostic` scan the real tree | consumer-project assumptions: home paths, vendor env names, forge CLI/URLs, repo-relative script paths in skills | 147 (19 under its former name leak-guard; 83 since July) |
| status-verb-guard (`check-status-verb.sh`, + 3 self-tests) | ✓ | | | | | legacy `status <state>` erg verb in skill log examples | 14, **all 2026-05-09 to 05-12**, none since |
| pipefail-guard (inline grep over `scripts/*.sh`) | ✓ | | | | | `set -euo pipefail` in each script | 4 (last 2026-09-06, `scripts/on-end.sh`: genuine) |
| grep-e-guard (inline grep -P over `scripts/*.sh`) | ✓ | | | | | `grep -E/-G` with PCRE escapes `\b \s \w` | **0** since it landed 2026-05-29 |
| pytest-guard (`pytest tests/ -v -n 4 --cov=scripts`, `uv sync --locked`, `age` installed) | ✓ | | ✓ as check-tests (`pytest tests/ -n 4`) | | — | the whole suite | 187 |
| personal-data-guard (`check-personal-data.sh`, + 3 self-tests) | | ✓ | ✓ | ✓ (staged files) | | tier-2 personal data (access topology) | **0** since it landed 2026-09-28 |
| tab-ifs-guard (inline grep -P over `scripts/*.sh skills/*/*.sh`) | | ✓ | | | | `IFS=$'\t' read` with three or more fields | 1 (2026-09-10, `skills/roar/check-close-claims.sh:101`: genuine per the rule) |
| cross-pr-ticket-collision (`check-cross-pr-ticket-collision.sh`, needs the forge token) | | ✓ | | | the script's own tests only | a ticket ID added by two open PRs, or landed on main after the branch diverged | 11 (July to 2026-10-02) |
| check-skills-drift (`check-skills-drift.py`) | | | ✓ | regenerates the catalog when a SKILL.md is staged | **no**: `test_gen_skills_catalog.py` uses fixtures | README skills catalog in sync with SKILL.md files | n/a (not in CI) |
| other pre-commit sections: main-branch-guard, erg-source-guard | | | | ✓ | the hook's tests | no commit on main in the primary checkout; erg sources read-only | n/a |

`scripts/local-ci.sh` adds no check of its own: it runs every job of `CI.yml`
with `act` in podman, refuses a job list that differs from the workflow's, and
skips (never passes) cross-pr-ticket-collision without forge access unless
`LOCAL_CI_STRICT=1`. It therefore inherits every row above, with one
difference that matters to 1045: it checks the committed **branch head**, while
the forge's `pull_request` run checks the **merge** with the base.

## Duplicates

- **pytest-guard ≈ check-tests.** Same suite, both `-n 4`. Differences: CI uses
  `uv sync --locked` (the Makefile uses `uv run --frozen`, the same lock), adds
  coverage reporting (not gated) and installs `age`, so the memory-capture
  suites that skip on a host without `age` run on the forge. Not an exact
  duplicate where `age` is absent locally.
- **agnostic-guard ≈ check-agnostic-{tickets,skills,scripts,rules}.** Same
  script, same four directories (the CI calls it once with the default list).
  Two pytest tests re-scan the real `skills/` and `scripts/` again, so those two
  directories are checked three times per full gate.
- **personal-data-guard ≈ check-personal-data ≈ pre-commit section.** Three
  runs of one script, none of them required for a merge.
- **validate-tickets ≈ pre-commit erg section,** and partly
  **cross-pr-ticket-collision**: on 2026-09-16 (PR for ticket 0946) both jobs
  fired on the same duplicate ID, because the forge checks the merge ref and the
  ID had already landed on main. cross-pr-ticket-collision's unique catch is the
  open-PR-against-open-PR case (2026-10-02, ID 1018 added by PR #1143 too),
  which no other check sees.
- **skill-lint ⊂ pytest, almost.** `description:` is already enforced by
  `test_skill_descriptions.py` and the YAML validity by
  `test_skill_frontmatter.py`; only the presence of `name:` is skill-lint's
  alone. It has never failed in CI.

## Gaps

On the CI side:
- **Skills-catalog drift is not checked by the forge.** Only `make check` and
  the pre-commit regeneration cover it; a commit made with `--no-verify`, or a
  README edited by hand, reaches main unchecked.
- **The guards' scopes are narrower than the rules they enforce.**
  pipefail-guard and grep-e-guard read `scripts/*.sh` only, not
  `skills/*/*.sh` (tab-ifs-guard reads both) nor `hooks/`; `hooks/pre-commit`
  itself has no `set -euo pipefail` (it is `#!/bin/sh`, so the rule may not
  apply; noted, not judged).
- **Three inline self-tests test a copy, not the guard.** pipefail-guard,
  grep-e-guard and tab-ifs-guard paste their pattern into the self-test step;
  the pipefail self-test omits the exclusion list the real step applies
  (which has itself changed since September: `bashrc-loader.sh` added). A drift
  between copy and guard would not be seen. The script-backed guards
  (agnostic, status-verb, personal-data) self-test the script itself.
- **Non-strict required checks.** A PR green on an old base can merge into a red
  main: pytest-guard failed on `main` five times since 2026-10-01.

On the `make check` side:
- **Seven CI checks have no `make check` target**: validate-tickets,
  cross-pr-ticket-collision, skill-lint, status-verb-guard, pipefail-guard,
  grep-e-guard, tab-ifs-guard. Four of them (skill-lint, pipefail, grep-e,
  tab-ifs) are inline YAML, so they cannot be
  run outside a workflow runner at all (only through `local-ci.sh`).
- `make check` tests the working tree, `local-ci.sh` the branch head, the forge
  the merge: three different subjects. 1045's scope already asks for the
  candidate merge; this review confirms it is the only subject on which a
  duplicate-ID collision with main is visible.

## Guards that never fired, or misfired

The author's rule, in a tooling repo: prefer deleting a misfiring guard over
growing it. Limits of the evidence: a zero is in the forge's history only
(local pre-commit and `make check` runs leave no trace), and job logs older
than about 90 days have expired, so the July fires could not be re-read. Each
guard has a self-test showing it can fire (a positive control), so a zero here
means "caught nothing at the forge", not "cannot catch".

| Guard | Record | Reading |
|---|---|---|
| skill-lint | 0 fires since April | Never caught anything; nearly subsumed by pytest (`name:` alone is unique). Retirement candidate. |
| grep-e-guard | 0 fires since 2026-05-29 | Never caught anything in four and a half months. Retirement candidate, or move into pytest. |
| status-verb-guard | 14 fires, all within 2026-05-09 to 05-12 (the week the verb was removed), 0 since | Did its job during one migration; the `%erg` verb it guards against has been gone for five months. Retirement candidate. |
| personal-data-guard | 0 fires since 2026-09-28 | Young (two and a half weeks) and also enforced at pre-commit, which is where a leak would be caught first. Too early to judge. |
| tab-ifs-guard | 1 fire, genuine per its rule | Working; not required. |
| pipefail-guard | 4 fires; last one genuine (`scripts/on-end.sh`) | Working. |
| cross-pr-ticket-collision | 11 fires; the three readable logs (2026-09-16 ×2, 2026-10-02) are genuine | Working; not required; unique catch for open-vs-open collisions. |
| agnostic-guard | 147 fires; the most frequent since July, 34 pushes of one branch on 2026-10-06/07, were a skill pointing at `scripts/tournament-analysis.py`, a repo-relative path its rule forbids | No misfire found in the sample read (74 runs since 2026-07-20); its volume is repeated pushes of red branches, not false positives. |

No misfire was found in any guard. The two infrastructure failures in the
history (2026-09-28, 2026-10-07: the jobs API returned no job list) are runner
events, not guard behaviour.

## What this settles for 1045

- **Exit criterion 1** (the content review is done): this document.
- **Open decision 3** (which checks the gate runs) now has its inventory. A
  gate that runs `make check` alone would drop seven CI checks; a gate that runs
  `local-ci.sh` alone would drop the catalog drift check and check the branch
  head instead of the merge. The union, on the candidate merge, is the full
  set; three guards (skill-lint, grep-e-guard, status-verb-guard) are
  candidates to delete before that union is fixed, and the four inline guards
  would need to become scripts to run anywhere but in a workflow runner.
  Choosing among those is the author's decision, not this review's.
- Decisions 1 and 2 (where the record lives; harness or dyne first) are not
  touched by this review.
