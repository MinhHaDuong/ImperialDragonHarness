---
name: the-resident-memory-index-is-the-one-for-the-starting-cwd-not-the-repo-you-end-up-in
description: "A session opened at $HOME loads $HOME's memory index; moving into a repo later does not load that repo's store, so its lessons never fire"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 8338b22f-c41f-4090-8d0f-128df0e26867
  modified: 2026-09-15T16:30:01.265Z
---

The memory index injected at session start is chosen by the session's **starting
working directory**, and nothing reloads it when the work moves elsewhere. Open a
session at `/home/haduong`, then work in
`~/CNRS/code/search-works-for-zotero`, and the resident index is the 19-entry
`-home-haduong` one — not that repo's 118-entry store.

**Why:** the failure is silent and reads like health. No index says "this is the
wrong store"; it presents as a project that happens to have little memory. So the
usual signal for "check memory" — a task that feels unfamiliar — never fires,
because the index in front of you looks complete.

**How to apply:** when a session's work settles in a repo other than the one it
started in, list that repo's own store before doing anything the store might
already know:

```bash
ls ~/.claude/projects/*<repo-name>*/memory/ | head
grep '^- \[' ~/.claude/projects/*<repo-name>*/memory/MEMORY.md
```

Cost, 2026-09-15, in one session in that exact configuration: three traps hit
that the unloaded store already held entries for, one of which turned
`origin/main` red. `feedback_erg_log_stamp_must_match_wall_clock` says, in its
description, that a ticket-log stamp must be read in the same tool call that
writes it and that `bench/check_ticket_logs.py` fails a stamp postdating the
commit — I invented four stamps and the gate failed exactly as written.
`feedback_gh_pr_edit_broken_use_api_patch` names the `gh pr edit` silent-failure
workaround; I hit the failure and rediscovered the workaround from
`rules/git.md`. `feedback_worktree_guard_refuses_rewritten_git` covers the
`rtk`-rewrite-versus-worktree-guard interaction I spent five attempts on.

The repo-level rule is not the fix: those entries were correctly written,
correctly indexed, and unreachable. Read the right index.

Related: [[reference_padme_display]] — the other thing this session got wrong by
assuming the machine it ran on was the machine the author sat at.
