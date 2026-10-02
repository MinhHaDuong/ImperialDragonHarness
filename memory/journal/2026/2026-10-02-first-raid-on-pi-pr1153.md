# First raid run on the pi runtime — PR #1153 (ticket 1020)

2026-10-02. Harness checkout. Single-session raid on the pi runtime, first
raid run the author has watched end-to-end in this runtime (author's first
use of pi; the session was an observation experiment).

## Context

`/raid` with one simple ticket. 16 tickets ready after skip labels
(`needs-human`, `deferred`). 1020 chosen: mechanical, on the STATE roadmap,
no external coupling. 0879 declined (entangled with the upstream `erg`
validator), 1021 declined (a runtime spawn bug — not a fit for an
observation session).

## Observable events

- Drift check before implementation: the ticket's finding 2 understated the
  surface — `scripts/check-primary-checkout.sh:18` carried a **live default**
  (`REPO="${1:-$HOME/.idh}"`), not only a stale comment. Fixed in the same
  PR; the usage comment states the actual default.
- Red → green: `tests/test_stale_idh_layout.py` (ratchet `\.idh(?!-)` over
  `scripts/` with a provenance whitelist) red on the 6 in-scope lines at
  cbe5e3ca, green at 55802864 (census README pipeline, check-agnostic
  comments, check-primary-checkout default).
- **Runtime adaptation — no `Agent` tool in pi.** The raid/hunt/review-pr
  skills assume agent spawning (parallel waves, detached workers, the
  five-perspective panel). pi has no spawn tool, so every spawn site ran
  inline in this one session. For `/review-pr` this is the skill's own
  fan-out preflight path: manifest written (`.panel/1153/manifest.json`,
  removed before merge), `PANEL-INTEGRITY: DEGRADED — Agent tool unavailable
  or spawn failed; independent perspectives not run`, `dissent:
  unavailable`, single posted review. The orchestrator's own diff analysis
  was posted in that review explicitly labelled as the author's own
  analysis, not an independent perspective.
- **External reviewer panel routed by the runtime** (`/reviewers request
  1153`, a shell job — works in pi because it is not an agent spawn):
  openrouter-frontier (openai/gpt-5.6-luna) `verdict=approve`, 0 findings;
  openrouter-budget (deepseek-v4.1-flash) SEAT-FAILED — the known litellm
  reasoning-field hang class (ticket 0347), fail-open; copilot forge bot
  requested, reviewed async.
- Copilot returned four correctness findings; each was verified against the
  code before disposition (two had already been flagged as `consider:` in
  the inline review, at lower severity than the verification warranted).
  Gate verdict round 1: **REROLL** (`root_cause_class: Agent Error`),
  erg log bump committed (975cb21b).
- Round-1 fix (ef73f390): two no-argument probe cases (probe installed in a
  temp checkout, run from an outside cwd — pins the script-relative
  default); ratchet moved to `@pytest.mark.adherence` per
  `rules/coding-python.md:61-68` (hygiene/contract ratchets gate via
  `make lint`); `PROVENANCE` keyed by path relative to `scripts/` with a
  red-first regression test (a same-named file in a subdirectory could
  otherwise inherit the exemption); census README derived expansions quoted
  and executed from a spaced-path worktree (exit 0).
- Round 2: **APPROVED** at tip 975cb21b (full `make check` 1345 passed / 2
  skipped on ef73f390; tip delta = the log line only). `gh pr review
  --approve` refused by the forge for a self-PR ("Can not approve your own
  pull request") — the verdict YAML block in the comment is the decision
  record.
- Merge: `erg-pr-merge` closed and archived 1020 atomically (d6019c1d),
  merge commit 35e36db7, local main synced by the script.
- Roar: 3 celebrations logged from the sentinel (it covered the
  #1149/#1152-era merges too). Post-merge sweep of the change class over
  `origin/main`: below the severity floor, reported not ticketed —
  `adapters/lifecycle.py:122,129` (legacy hook-format matchers, the same
  retirement class as the `gen-claude-code-adapter-hooks.py` translator
  already flagged in the PR body), `skills/` comments and docstrings
  (`skills/merge/erg-pr-merge:31`, `skills/reviewers/reviewers.sh:313,321`,
  `skills/external-peer-review/peer_review.py:142`,
  `skills/update-publist/resolve_hal_credentials.sh:12,50`), and a project
  memory reference (`projects/-home-haduong--claude/memory/
  project_harness_repo.md:11`). STATE/ROADMAP mention the sweep itself
  (meta, updated by `/lair`).

## Outcome

Ticket 1020 closed, PR #1153 merged. The full raid loop (hunt →
verify-adherence → review → REROLL → fix → re-gate → merge → roar)
completed on pi with inline substitution at every spawn site; the
decorrelated review evidence came from the external seats, with the
integrity limitations carried verbatim into the verdict.
