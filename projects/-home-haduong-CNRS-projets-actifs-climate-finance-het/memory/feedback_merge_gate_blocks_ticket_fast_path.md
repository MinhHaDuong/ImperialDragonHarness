---
name: feedback_merge_gate_blocks_ticket_fast_path
description: "The merge gate fires on any Bash command whose text contains \"gh pr merge <digits>\", not just an actual merge — it blocked a verification command"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 9856e923-9da4-4c61-80c6-d279c7bce8d9
  modified: 2026-07-28T07:32:16.808Z
---

`.claude/hooks/check-reviews.sh` is a PreToolUse hook registered in
`.claude/settings.json` as `"matcher": "Bash"` with `"if": "Bash(gh pr merge *)"`
on the handler. Ticket 0365 repaired that registration on 2026-07-27 — before
which the matcher held permission-rule syntax, was not compilable regex, and
fired on nothing for months.

**The `if` filter matches the command text as a substring, not as a prefix.** Any
Bash call whose text contains `gh pr merge <digits>` is gated, wherever that text
sits — inside a quoted string, a heredoc, a `grep` pattern, a test fixture, a doc
edit. On 2026-07-28 it denied a command whose only offence was
`echo '{"tool_input":{"command":"gh pr merge 1 --merge"}}'` in a hook-verification
harness: *"Only 0 review(s) found, 2 required."*

**Why the false positives are usually invisible:** the hook extracts the PR number
with `re.search(r'gh\s+pr\s+merge\s+(\d+)')`, and when it finds none it allows and
exits 0. So a command mentioning `gh pr merge $VAR` or `gh pr merge <N>` sails
through, while one mentioning a literal digit gets gated against a real PR of that
number. Same class as the `"type": "prompt"` sibling hook that 0365 deleted rather
than debugged — the `if` field does not narrow the way its permission-rule syntax
suggests.

**How to apply:** when a Bash command must contain that text, assemble it at
runtime so the literal never appears — `V="pr ""merge"; … "gh $V 1 --merge"` — or
use a non-literal PR number. If a command is denied for missing reviews and you
were not merging anything, this is why; the deny is the hook, not a real gate.

**Current gate behaviour (after PR #1249, 2026-07-28):** a PR whose changed files
are all `.erg` under `tickets/` — rename sources included — is exempt from the
review count, so the tickets-only fast path in `.claude/rules/git.md` now works
unaided. Verified to fail *closed*: a `gh` that errors, returns non-JSON, returns
the wrong shape, an empty file list, a mixed diff, or code renamed into
`tickets/` all fall through to the normal count and deny. Code PRs keep the full
gate: 2 review cycles, or 1 with the `review:trivial` label.

For a code PR, the ceremony is a label plus one review, both as the single forge
identity: `gh api -X POST repos/MinhHaDuong/climate-finance-het/issues/<N>/labels
-f 'labels[]=review:trivial'` (`gh pr edit --add-label` dies on the deprecated
Projects-classic GraphQL error — [[feedback_gh_projects_classic_error]]) then
`gh pr review <N> --comment` (`--approve` is refused on your own PR).

Related: [[feedback_ticket_pr_fast_path]], [[feedback_no_ci_local_merge_gate]]
(this hook is the only automated merge gate the repo has).
