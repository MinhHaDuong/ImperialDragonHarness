# Guichet design: from a dialogue session to C1 over git

Date: 2026-11-12 · host: padme · drafter anthropic/claude-opus-5-5 ·
author in the loop throughout

## Context

The author asked for the inter-repo communication protocol, then for a
design where the receiving repository talks first and tickets, amends or
pushes back ("guichet"). Design case named by the author: projects reporting
bugs in the harness, git-erg and padme services. Note:
`design/2026-11-12-guichet-inter-repo-dialogue.md`, Status provisional.

## Events

- Eight design PRs merged the same day: #2460 (first note), #2465 (two
  observed cases per receiver from history), #2467 (runtime-neutral
  transport after a bibliographic saturation pass), #2468 (one Pi-hosted
  path), #2470 (flock lock, self-closing session), #2473 (C1 rewrite),
  #2475 (intake file under `tickets/intake/`), #2476 (verdict launcher,
  answer pickup, blocked askers park).
- The guichet-session design went through seven amendments driven by author
  questions: `claude --bg` as host; a Vibe MOE cannot list Claude sessions,
  so discovery moved to card files; two paths judged one too many; Pi as the
  single host because `idh-wake.ts` exists and Pi on padme reaches every
  model family; a `flock` lock instead of the card.
- Gaze reproduced a lock flaw (`flock -n lock cmd` leaks the lock to the
  command's children; `-o` fixes it, util-linux 2.39.3) and a probe race.
- A red-team round (gpt-6-astra via `codex exec`, Claude Fable as subagent,
  same brief) returned NEEDS-REDESIGN from both seats on the guichet session:
  peer text delivered as a user turn into a session with bash;
  `idh-guard.ts` on Pi inspects only `--hard` commands and fails open;
  `replyTo` an arbitrary write; clearance read from the receiver only; a
  wedged session holding its lock; tickets laundering authority into raid.
  Both seats also judged the value weak: none of the six observed cases
  needed a question round. The drafter verified each code claim.
- The author restated the redesign as "drop a ticket, then wake someone",
  chose C1 variant 1 out of five, ruled no forge (git branches and notes),
  then the landing option where the triager never lands.
- The bibliographic saturation pass (three blind sonnet searchers, a Fable
  judge re-fetching primaries, a gpt-6-astra critic on logs) found peer
  messaging across vendors' coding CLIs anticipated (synapse-a2a,
  a2abridge, a2a-serve), an A2A filesystem binding partly anticipated, and
  no matching study of agents' cross-repository bug reports with measured
  outcomes; coverage partial for all three claims.
- Gaze rounds on the C1 lifecycle kept finding neighbouring gaps after each
  local fix (six rounds on #2473); the drafter then stated the lifecycle as
  one state table with a tip invariant per state, after which rounds
  converged.
- Facts established by probe or source during the session: `erg check`
  ignores a non-erg file under `tickets/intake/`; a `tickets/intake/*.md`
  diff is full tier for `merge-gate.py`; erg's ticket header set is
  strictly closed (author); `Blocked-by:` accepts another repository's
  ticket as a URI reference and treats unresolved references as optimistic
  for readiness (git-erg `design/erg-manual.md`, rule 9); `raid_land.py`
  refuses a `branch:` unit in a repository with an `origin`.
- The classifier refused one `git push --force-with-lease` after a rebase;
  the branch was rebuilt by merging `origin/main` instead.

## Outcome

C1 on main: an intake file and notes thread on an intake branch, a
launcher job running a sandboxed read-only triager and a verdict script
that never lands, owner promotion, a lifecycle table, asker pickup by a
pending log line and a bounded wake, blocked askers parked with
`deferred` and released on `resolved`. Not yet accepted by the author.
At roar time the author asked how C1 beats the status quo; the drafter's
answer proposed running the triage profile by hand on the observed cases
before building the plumbing. Undecided.
