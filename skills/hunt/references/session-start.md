# Session start: worktree name, phase and opening line

The procedure behind `rules/workflow.md` § Session start. The rule keeps the
principle: work that writes starts in the conversation's own worktree, made by
the plain-git recipe of hunt's § Worktree, except for manuscript prose and
`/hunt N`.

## Worktree name and phase

| Context | Worktree name | Phase |
|---------|---------------|-------|
| Fresh conversation, no ticket | `explore-{topic}` | `[→ Imagine]` |
| Ticket reference but no branch | `t{N}-{pid}` | `[→ Plan]` |
| `/hunt N` | *decided inside hunt* | `[→ Plan]` |
| Active feature branch + open MR | `t{N}-{pid}` | `[→ Execute]` |
| MR review | `review-{N}` | `[→ Verify]` |

`{pid}` is `$PPID-$RANDOM`, as in hunt's § Worktree: subagents share `$PPID`.
Legacy bare `t{N}` names remain valid. A read-only answer (a question, a
dashboard) needs no worktree.

## Opening line

Open with the phase label heading one self-presentation line, in the
conversation's language, then answer:

`[→ Execute] · <model> · effort <level, when the runtime states it> · MOE N+2 — government by intention via team leads; I filter, verify, surface, advise.`

## Startup warnings

Surface any disk-headroom warning from
`python3 "$IDH_ROOT/scripts/tmp_report.py" --disk-warning` (the session-start
hooks print it); if unavailable, continue.
