# Imperial Dragon Harness — State

Last updated: 2026-08-26T13:46Z

## North star

A reusable, science-backed personal harness for AI-assisted research: code and prose, day and night, across projects and machines. The harness itself is the deliverable.

## Status
<!-- generated 2026-08-26T13:46Z · as of 59c0ced -->

**Tickets:** 9 ready · 4 blocked — `erg ready tickets/` for full list
  next: 0207 Agnostic CLI reviewer seat — one config, OpenRo… · 0359 Spawn bash test children hermetically (env -i) …
**Recent (first-parent):**
  59c0ced Merge pull request #769 from MinhHaDuong/dream-consolidate-2026-08-22
  ebb0987 Merge pull request #777 from MinhHaDuong/claude/t0610-hook-catchall-ticket
  3a8692a Merge pull request #776 from MinhHaDuong/claude/t0590-ruff-clean

## Blockers

(none)

## Next actions

- **Cool-down doctrine in force** (2026-07-14): file a tooling ticket only if the defect blocks a merge, corrupts state, or bites a science project; throughput points at the science repos — run normal raids/reviews there. Raid closed 0348 (PR #634) and 0353 (PR #636).
- **External-reviewer advisory trial LIVE, hands-free**: seats openrouter-frontier (gpt-5.6-luna) and openrouter-budget (deepseek-v4-flash) enrolled in `skills/reviewers/panel.yml`; /gaze auto-requests, harvests, and scorecards them on substantive code reviews (PR #638). Each gazed science-repo PR feeds the trial; data accrues on ticket 0207 (needs ≥5 MRs across ≥3 projects per config, then the author's promote/drop call). Check `reviewers.sh scores` periodically.
- **0205 tracker** (blocked by 0207): author's squad-management model recorded — roster ≠ lineup, incumbent retro-assessment, continuous composition (PR #640); mechanisms deliberately deferred until the trial verdict.
- **0356 deferred**: cross-project mined-defect benchmark (challenger-vs-squad audition) — revisit after the 0207 promote/drop decision.
- **0062 trigger**: re-open Firecracker isolation when IDH agents run against secret-bearing projects
- **Lint gate now has no holes** (2026-08-26, tickets 0470 + 0590): `.ruff.toml` carries
  no suppression of any kind, and `test_config_declares_no_suppressions` fails on any
  `per-file-ignores` / `ignore` / `exclude` (and `extend-` forms, both scopes). Reopening
  one is meant to be argued in a ticket, not slipped into config.
- **0610 open — hook tests that cannot fail**: both hook scripts swallow every exception
  and exit 0, so a crash and a correct silence are identical on the channels the tests
  observe. Measured: 14 of 26 CLI-driven tests in `test_knowledge_hints` and 3 of 5 in
  `test_inject_rule_on_edit` still pass with the script fully broken — including the
  pointer-exfiltration guard and the body-omission guard. Fix is a test-only strict mode;
  watch the closed-`env` trap the ticket documents.
- **Stale branches on origin, all on still-open ready tickets**: `t0359-…`,
  `t0425-…`, `t0500-…`, `t393-openrouter-seat-credential` each carry 1–4 unmerged commits
  from 2026-08-14. Abandoned starts, not merged work — check them before re-attacking
  those tickets so the effort is not repeated. (`t-idh-mergeeffect` and
  `tickets/raid-0537-harness-findings` are long-diverged, 1330 and 1164 commits.)

## Backlog

- Streamline settings.json hook configuration
- Merge REALF guidelines and business rules
