---
name: worktree-guard-rtk-git-deadlock
description: "In a worktree session, bare `git ...` is refused -- rtk rewrites it to `rtk git ...` which the isolation guard cannot verify; use /usr/bin/git -C <worktree>"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d344415f-fe91-458d-aa20-c1b5c8a66772
  modified: 2026-09-16T06:28:32.234Z
---

In a worktree-isolated session in this repo, a bare `git fetch origin` is
**refused** -- not by rtk, and not really by the worktree guard either, but by
the two in series. The rtk PreToolUse hook rewrites `git X` into `rtk git X`;
the worktree isolation guard then cannot prove that what runs is confined to
the worktree, and denies it with "runs rtk with a git command among its
operands ... what it runs cannot be shown not to be git".

Piping or redirecting does **not** dodge it here (contrary to the output-rewrite
workaround in [[rtk-0421-status]] and git.md) -- the rewrite still happens, and
it is the rewrite the guard objects to, not the output framing.

**Why:** the guard's contract is "a worktree session's git operations must
target its own worktree", and it can only check that on a plain, readable
command line. Any launcher in front of `git` defeats the check, so it fails
closed. Both hooks are behaving correctly; the deadlock is emergent.

**How to apply:** in a worktree session, drive git through the absolute binary
with an explicit `-C`:

```bash
/usr/bin/git -C /path/to/worktree fetch origin
```

rtk only rewrites the bare token `git`, so `/usr/bin/git` passes through, and
`-C <worktree>` is exactly the confinement proof the guard wants. Two further
trip-wires in the same family, both hit on 2026-09-16:

- The guard also refuses commands that merely *mention* a git-ish path inside a
  compound construct -- a `W=/home/haduong/CNRS/code/git-erg/...` assignment was
  enough ("names git in a form too complex to verify"). Keep worktree commands
  to one plain invocation; put loops and multi-step logic in a script file under
  the scratchpad and run the script.
- Same for `gh ... --jq '.[].number'` inside a `for`: the jq expression made the
  construct unverifiable. Run `gh` once, plainly, and post-process separately.

Related: [[one-worktree-per-ticket]], [[git-in-a-worktree-session]].
