# Two sessions acted on one set of routing remarks; the shared checkout was edited live

Context: 2026-10-06, the routing doctrine brief (PR #1223, tracker 0974) was
written in a worktree session. The author reports that a second session, a
Mistral Vibe session running the model tournament (ticket 1024) in the primary
checkout on branch work/model-tournament-20261006, received the author's review
remarks on the routing doctrine as well.

Observations:
- The tournament session acted on the remarks. Its own report lists what it
  made, all uncommitted in the primary checkout: untracked skills/route/
  (SKILL.md and routes.json), untracked skills/arena/ (SKILL.md), an AGENTS.md
  edit (+10/-1) and a regenerated README.md. It states the directives were meant
  for the other agent.
- ~/.claude/CLAUDE.md is a symlink to ~/.agents/AGENTS.md. The uncommitted
  AGENTS.md edit therefore reached running sessions: the routing session was
  told mid-session that the file had changed on disk, and found its open PR
  #1223 contradicting the new text on pairing frontier with intensive effort. It
  corrected the PR before merge.
- Read from the primary checkout, skills/route/SKILL.md has 5 lines matching
  the concrete-model expression in tests/test_model_rightsizing.py (counted with
  grep, the suite was not run on that tree). routes.json holds route status and a
  monthly cap, with no quota windows and no environment dimension.
- ListAgents showed one peer, a Claude session; whether a Vibe session can be
  messaged from there was not established. Coordination went through the author,
  git and the PR list.
- The tournament session committed AGENTS.md as PR #1225 from a disposable
  worktree and removed the on-disk edit. CI pytest-guard failed on
  tests/test_resident_census.py::test_channel_budgets: the import channel is 4910
  characters against a cap of 4500. skills/route/ and skills/arena/ were still
  untracked when this was written.

Outcome: no work was lost. PR #1223 merged at daaa215b042511b6b368e8fd54d0f0ae84504b37.
PR #1225 is open and blocked. A split was proposed and awaits the author: the
tournament session keeps the grid content and arena, the routing session reworks
the structure of route.

Evidence: PRs #1223 and #1225; tickets 0974 and 1024; the tournament session's
report as relayed by the author; the CI log of PR #1225.
