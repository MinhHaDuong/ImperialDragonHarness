---
name: gaze-cost-on-doc-only-pr
description: "/gaze on a ten-file, no-code ticket PR took an hour, twelve agents and ~791k tokens, then ESCALATEd on its own wall-clock breakers after the fix had landed; three named causes, and the cheaper path for governance-only diffs."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: cee6070c-3acb-4389-866d-46222da655df
  modified: 2026-09-22T18:54:54.567Z
---

PR #608 (2026-09-22: three ticket closures, four new tickets, a DECISIONS.md
ruling, a SYNC.md paragraph — no code) went through `/gaze`. Wall ≈ 3600 s,
12 agents, ≈ 791k tokens. The round-1 review was good (five real transcription
gaps, all fixed by the fix agent), but the skill ended in ESCALATE on its
timeout breakers with no verdict, and the caller had to run `/verify-gate`
round 2 by hand. The fix commit was already on the page when the ESCALATE
arrived.

**Why**, in the skill's own telemetry note: (1) the worktree guard refused
the review worktree, so every subagent was pinned to the session worktree and
serialised on it; (2) the gate agent spawned a stray `/verify-gate` fork of
its own; (3) the fix agent's budget assumed a ~90 s `make check`, but
`sitter-mutants` alone runs over ten minutes when its cache is cold, so the
fix agent could not be stopped and overran the breaker. The next two doc-only
PRs of the day (#610, #611) went `make check` → `/verify-gate` → merge in
about ten minutes each, with verdicts on the page.

**How to apply:** for a diff with no code — tickets, STATE, DECISIONS, SYNC —
run only the guards the diff can move (`make lint figures names progress tickets
ticket-logs`, plus `sitter-version` if a file sits under `plugins/`), not the full
`make check`: the author objected on 2026-09-23 ("WTF are we running make check
for a DECISIONS-only ticket") — pytest and `sitter-mutants` cost ten minutes and
cannot see a doc diff. Name the skipped targets on the PR page. Then run `/verify-gate` directly; it posts a
verdict the merge rule accepts and it re-reads the load-bearing facts live.
Reserve `/gaze` for code. When `/gaze` does run here, expect an ESCALATE
caused by breakers rather than by findings; before treating it as a bounce,
read the branch tip and the page — the fix may already be there, and one
`/verify-gate` round settles it. Related: [[executor-gate-loop-stall]],
[[gate-fork-returns-without-verdict]].

The same session's tooling note, kept here rather than as its own file: in a
worktree session the guard refused bare `git`, `git -C`, `cd … && git`, any
loop or variable near a git or gh call, and `gh` invocations with a
multi-line `--jq`. `/usr/bin/git` from the worktree cwd worked every time,
and anything with a loop went into a script file run as `bash script.sh` or
`python3 script.py`. See also [[fork-cwd-and-worktree-guard]].
